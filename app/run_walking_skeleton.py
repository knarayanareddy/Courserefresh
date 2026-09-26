#!/usr/bin/env python3
"""Courserefresh offline twin — the loop, end to end, on labelled fixtures.

This is the demo's fallback and the tests' engine (constitution Art. XIII.3): the SAME rules as the
oracle (`specs/courserefresh/skin/policy.py`) and the n8n node (`app/n8n/policy_node.js`), driven by
`app/fixtures/**.` It writes real artifacts — lesson versions, diffs, micro-lessons, a chained
receipt log, a digest — so the evidence trail is produced by running, not by prose.

Modes
    --run        execute the loop over app/fixtures/events (default; mutates course/ and app/out/)
    --selftest   run in a sandbox (app/out/selftest/) and assert the loop's invariants
    --report     print the digest from receipts
    --replay <run_id/dir>  re-execute recorded inputs (fallback ladder rung 2)
    --pause / --resume     kill switch (freeze file in the state dir)
    --root <dir>           operate on another tree (used by --selftest and tests)

Exit codes: 0 ok · 1 verification failed · 2 build-breaking invariant · 3 usage/config · 4 refused.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / "specs" / "courserefresh" / "skin"
sys.path.insert(0, str(SKIN))

import policy  # noqa: E402  (the oracle — same rules as the n8n node)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.guard import host_allowed, safe_course_path, within_size_cap  # noqa: E402

THRESHOLDS = policy.THRESHOLDS
MODES = policy.TAXONOMY["modes"]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y.%m.%dT%H:%M:%SZ")


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def run_id() -> str:
    return "cr-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M") + f"-{int(time.time()*1000) % 1000:03d}"


class Tree:
    """One working tree: the course artifact plus the state/evidence directory."""

    def __init__(self, root: Path, out: Path, mode: str = "sim", chaos: str | None = None):
        self.root = root
        self.out = out
        self.mode = mode
        self.chaos = chaos
        self.state = out / "state"
        self.state.mkdir(parents=True, exist_ok=True)
        self.receipts_path = out / "receipts.jsonl"
        self.run_log_path = out / "run_log.jsonl"
        self.digest_path = out / "digest.md"
        self.freeze_path = self.state / "FREEZE"

    # state ---------------------------------------------------------------------------------
    def seen(self) -> set[str]:
        path = self.state / "seen.json"
        return set(json.loads(path.read_text())) if path.exists() else set()

    def mark_seen(self, event_id: str) -> None:
        path = self.state / "seen.json"
        seen = sorted(self.seen() | {event_id})
        path.write_text(json.dumps(seen))

    def frozen(self) -> bool:
        return self.freeze_path.exists()

    # receipts ------------------------------------------------------------------------------
    def rows(self) -> list[dict]:
        if not self.receipts_path.exists():
            return []
        return [json.loads(l) for l in self.receipts_path.read_text().splitlines() if l.strip()]

    def append_receipt(self, row: dict) -> dict:
        rows = self.rows()
        prev = rows[-1]["row_hash"] if rows else "genesis"
        row = {"prev": prev, **row}
        row["row_hash"] = sha(json.dumps(row, sort_keys=True))
        with self.receipts_path.open("a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        return row

    def verify_chain(self) -> tuple[bool, int]:
        prev, count = "genesis", 0
        for row in self.rows():
            body = {k: v for k, v in row.items() if k != "row_hash"}
            if body.get("prev") != prev or sha(json.dumps(body, sort_keys=True)) != row["row_hash"]:
                return False, count
            prev, count = row["row_hash"], count + 1
        return True, count


# --- course artifact helpers ---------------------------------------------------------------------

def read_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("no front matter")
    _, fm, body = text.split("---\n", 2)
    return {k: json.loads(v) for k, v in (l.split(": ", 1) for l in fm.strip().splitlines())}, body


def write_front_matter(fm: dict, body: str) -> str:
    return "---\n" + "\n".join(f"{k}: {json.dumps(v)}" for k, v in fm.items()) + "\n---\n" + body


def design_tokens() -> dict:
    """Every colour comes from specs/design/MASTER.md; the console may not invent one (Art. XV)."""
    text = (ROOT / "specs" / "design" / "MASTER.md").read_text()
    return dict(re.findall(r"(--[a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})", text))


def load_curriculum() -> dict:
    return json.loads((ROOT / "course" / "agent-ops" / "curriculum.json").read_text())


def downstream_lessons(lesson_id: str) -> list[str]:
    """Lessons whose prereq chain includes the changed one: named for revisit, never rewritten tonight."""
    curriculum = load_curriculum()["lessons"]
    out: list[str] = []
    grown = True
    while grown:
        grown = False
        for lesson in curriculum:
            if lesson["lesson_id"] in out or lesson["lesson_id"] == lesson_id:
                continue
            if any(p in out or p == lesson_id for p in lesson["prereqs"]):
                out.append(lesson["lesson_id"])
                grown = True
    return out


def versions(lesson_dir: Path) -> list[int]:
    return sorted(int(p.stem[1:]) for p in lesson_dir.glob("v*.md") if p.stem[1:].isdigit())


def apply_patch(tree: Tree, event: dict, decision: dict, run: str) -> dict | None:
    """Write the new lesson version, its diff, the changelog entry. Returns the artifact record."""
    patch = event.get("patch")
    if not patch:
        return None
    lesson_dir = tree.root / "agent-ops" / event["parent"]
    src = safe_course_path(tree.root, str(lesson_dir.relative_to(tree.root) / patch["file"].split("/")[-1]), prefix="")
    lesson_dir = src.parent
    text = src.read_text()
    if patch["find"] not in text:
        # one failure, one receipt: the loop records the escalation, this function only reports it
        return {"_failed": "patch anchor not found"}
    fm, body = read_front_matter(text)
    n = max(versions(lesson_dir))
    fm["version"] = f"v{n+1}"
    fm["generated"] = True
    fm["reviewed_by"] = ""
    fm["sources"] = [s["url"] for s in event.get("sources", [])]
    fm["revert_gate"] = event.get("gate", fm.get("revert_gate"))
    new_body = body.replace(patch["find"], patch["replace"])
    new_path = lesson_dir / f"v{n+1}.md"
    new_text = write_front_matter(fm, new_body)
    new_path.write_text(new_text)
    diffs = lesson_dir / "diffs"
    diffs.mkdir(exist_ok=True)
    import difflib
    diff = "\n".join(difflib.unified_diff(text.splitlines(), new_text.splitlines(),
                                          fromfile=f"v{n}.md", tofile=f"v{n+1}.md", lineterm=""))
    (diffs / f"v{n+1}.diff").write_text(diff + "\n")
    with (tree.root / "agent-ops" / "CHANGELOG.md").open("a") as fh:
        fh.write(f"\n## {fm['lesson_id']} {fm['version']} — {now()}\n{event['summary']}\n"
                 f"- diff: {lesson_dir.name}/diffs/v{n+1}.diff\n")
    update_readme(tree, fm["lesson_id"], fm["version"])
    record = {"lesson_id": fm["lesson_id"], "previous_version": f"v{n}", "new_version": fm["version"],
            "body_path": str(new_path.relative_to(tree.root)), "diff_path": str((diffs / f'v{n+1}.diff').relative_to(tree.root)),
            "payload_hash": sha(new_text), "diff_hash": sha(diff), "revert_gate": fm["revert_gate"]}
    if event.get("quiz_patch"):
        record.update(apply_quiz_patch(tree, event))
    return record


def apply_quiz_patch(tree: Tree, event: dict) -> dict:
    """A lesson change regenerates the affected item; the JSON is versioned like the lesson (AC-4.1)."""
    spec = event["quiz_patch"]
    path = ROOT / "course" / "agent-ops" / "quizzes" / f"{spec['lesson_id']}.json"
    data = json.loads(path.read_text())
    for item in data["items"]:
        if item["id"] == spec["item_id"]:
            item["prompt"] = spec["prompt"]
            item["options"] = spec["options"]
            item["answer"] = spec["answer"]
            item["regenerated_by"] = event["event_id"]
            break
    target = tree.root / "agent-ops" / "quizzes" / f"{spec['lesson_id']}.json"
    target.write_text(json.dumps(data, indent=2) + "\n")
    with (tree.root / "agent-ops" / "CHANGELOG.md").open("a") as fh:
        fh.write(f"- quiz: quizzes/{spec['lesson_id']}.json item {spec['item_id']}\n")
    return {"quiz_path": str(target.relative_to(tree.root)), "quiz_item": spec["item_id"]}


def revert_version(tree: Tree, event: dict, run: str) -> dict | None:
    target = event["target"]
    lesson_dir = tree.root / "agent-ops" / target["lesson_id"]
    restore = lesson_dir / f"{target['restore_version']}.md"
    if not restore.exists():
        return None
    source_text = restore.read_text()
    fm, body = read_front_matter(source_text)
    n = max(versions(lesson_dir))
    fm["version"] = f"v{n+1}"
    fm["generated"] = True
    fm["revert_of"] = target["published_version"]
    body = body.rstrip() + f"\n\n> **Reverted.** This version restores {target['restore_version']}: the published change was measured and did not help (see the receipt). Sources and gate for the reverted change remain in the changelog.\n"
    new_text = write_front_matter(fm, body)
    new_path = lesson_dir / f"v{n+1}.md"
    new_path.write_text(new_text)
    import difflib
    diff = "\n".join(difflib.unified_diff(source_text.splitlines(), new_text.splitlines(),
                                          fromfile=f"{target['published_version']}.md", tofile=f"v{n+1}.md", lineterm=""))
    (lesson_dir / "diffs").mkdir(exist_ok=True)
    (lesson_dir / "diffs" / f"v{n+1}.diff").write_text(diff + "\n")
    with (tree.root / "agent-ops" / "CHANGELOG.md").open("a") as fh:
        fh.write(f"\n## {target['lesson_id']} {fm['version']} — {now()}\nREVERT to {target['restore_version']}: {event['summary']}\n"
                 f"- diff: {lesson_dir.name}/diffs/v{n+1}.diff\n")
    update_readme(tree, target["lesson_id"], fm["version"])
    return {"lesson_id": target["lesson_id"], "previous_version": target["published_version"],
            "new_version": fm["version"], "body_path": str(new_path.relative_to(tree.root)),
            "diff_path": str((lesson_dir / 'diffs' / f'v{n+1}.diff').relative_to(tree.root)),
            "payload_hash": sha(new_text), "diff_hash": sha(diff)}


def update_changelog_receipt(tree: Tree, lesson_id: str, version: str, receipt_id: str) -> None:
    """The receipt id is only known after the row is chained; stamp it into the right entry."""
    changelog = tree.root / "agent-ops" / "CHANGELOG.md"
    if not changelog.exists():
        return
    lines = changelog.read_text().splitlines()
    header = f"## {lesson_id} {version} —"
    for i, line in enumerate(lines):
        if line.startswith(header):
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].startswith("- diff:"):
                    lines.insert(j + 1, f"- receipt: {receipt_id}")
                    changelog.write_text("\n".join(lines) + "\n")
                    return


def _notification_age(ts: str) -> float:
    moment = datetime.strptime(ts, "%Y.%m.%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - moment).total_seconds()


def concept_recently_dispatched(tree: Tree, event: dict) -> bool:
    """The per-concept micro-lesson cap, decided here and consumed by the policy branch."""
    concept = event["input"].get("concept", "")
    window = int(THRESHOLDS["budgets"]["micro_lesson_per_concept_days"]) * 86400
    for path in (tree.out / "micro-lessons").glob(f"ml-{concept}-*.md"):
        if time.time() - path.stat().st_mtime < window:
            return True
    return False


def notify_cohort(tree: Tree, event: dict, record: dict) -> dict:
    """PA2 publishes notify the consented cohort (Art. IV.3) inside the per-learner caps (Art. XIV.2)."""
    materiality = event["input"]["materiality"]
    if event["input"]["authority"] != "PA2" or materiality not in policy.COHORT_NOTIFY:
        return {"notified": [], "skipped": []}
    history = []
    if (tree.out / "notifications.jsonl").exists():
        history = [json.loads(l) for l in (tree.out / "notifications.jsonl").read_text().splitlines() if l.strip()]
    refs, skipped = [], []
    for path in sorted((ROOT / "app" / "fixtures" / "telemetry").glob("*.json")):
        learner = json.loads(path.read_text())
        if not learner.get("consent"):
            continue
        mine = [_notification_age(r["ts"]) for r in history if r["learner_ref"] == learner["learner_ref"]]
        if sum(1 for age in mine if age < 86400) >= THRESHOLDS["budgets"]["notify_per_learner_day"]:
            skipped.append({"learner_ref": learner["learner_ref"], "reason": "notify_per_learner_day"})
            continue
        if sum(1 for age in mine if age < 7 * 86400) >= THRESHOLDS["budgets"]["notify_per_learner_week"]:
            skipped.append({"learner_ref": learner["learner_ref"], "reason": "notify_per_learner_week"})
            continue
        refs.append(learner["learner_ref"])
        what_changed = event.get("learner_facing") or event["summary"]
        row = {"ts": now(), "learner_ref": learner["learner_ref"], "lesson_id": record["lesson_id"],
               "from": record["previous_version"], "to": record["new_version"],
               "what_changed": what_changed, "opt_out": "one-click",
               "diff_path": record["diff_path"],
               **({"rehearsal": True} if event.get("seed") else {})}
        with (tree.out / "notifications.jsonl").open("a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return {"notified": refs, "skipped": skipped}


def update_readme(tree: Tree, lesson_id: str, version: str) -> None:
    readme = tree.root / "agent-ops" / "README.md"
    if not readme.exists():
        return
    num = lesson_id.split("-")[1]
    lines = []
    for line in readme.read_text().splitlines():
        if line.startswith(f"| {num} |"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            cells[2] = version
            line = "| " + " | ".join(cells) + " |"
        lines.append(line)
    readme.write_text("\n".join(lines) + "\n")


def dispatch_micro_lesson(tree: Tree, event: dict, run: str) -> dict:
    mid = f"ml-{event['input']['concept']}-{event['event_id'][-4:]}"
    path = tree.out / "micro-lessons" / f"{mid}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""# {event['input']['concept']} — two minutes

1. What it is: the setting this lesson uses was renamed; the old name still works until 1.86.
2. Worked example: `permissions.mode.tools` replaces `tool_permissions.tools`.
3. Practice: which key would you edit to allow only `docs.n8n.io`?

[Stop these messages]  [See what changed]
""")
    return {"kind": "micro_lesson", "learner_ref": event["learner_ref"], "path": str(path.relative_to(tree.out)),
            "payload_hash": sha(path.read_text())}


# --- the loop ------------------------------------------------------------------------------------

def event_input(event: dict, tree: Tree, publishes_used: int) -> dict:
    inp = json.loads(json.dumps(event["input"]))
    inp["freeze_active"] = tree.frozen()
    inp["sources"] = event.get("sources") or []
    if event["kind"] == "learner":
        inp["concept_recently_dispatched"] = concept_recently_dispatched(tree, event)
    budgets = inp.get("budgets")
    if budgets:  # the fixture may pre-load a spent budget; the run counts its own publishes too
        budgets["publishes_used"] = max(int(budgets.get("publishes_used", 0)), publishes_used)
    return inp


def run(tree: Tree, events: list[dict], label: str = "") -> dict:
    run = run_id()
    decisions: dict[str, int] = {}
    artifacts: list[dict] = []
    publishes_used = 0
    seen = tree.seen()
    for event in events:
        key = event["event_id"]
        if event["kind"] == "change" and key in seen:
            continue
        if tree.chaos == "write-fail" and event.get("patch"):
            event = json.loads(json.dumps(event))
            event["patch"]["find"] = "text that is not in the lesson (chaos rehearsal)"
            tree.chaos = None      # one failed write per run, then normal service
        inp = event_input(event, tree, publishes_used)
        out = policy.decide(inp)
        record = None
        if out["action"] == "PUBLISH" and event["kind"] == "change":
            record = apply_patch(tree, event, out, run)
            if record and record.get("_failed"):
                out = {"action": "ESCALATE", "reason_codes": ["write_failed"],
                       "authority": out["authority"], "notes": record["_failed"]}
                record = None
            elif record:
                notify_result = notify_cohort(tree, event, record)
                record["notified"] = notify_result["notified"]
                if notify_result["skipped"]:
                    record["notification_skips"] = notify_result["skipped"]
                publishes_used += 1
            else:
                out = {"action": "ESCALATE", "reason_codes": ["write_failed"], "authority": out["authority"],
                       "notes": "no patch in the event"}
        elif out["action"] == "REVERT":
            record = revert_version(tree, event, run)
            if record is None:
                out = {"action": "ESCALATE", "reason_codes": ["previous_version_missing"],
                       "authority": out["authority"], "notes": "restore source missing"}
        elif out["action"] == "DISPATCH":
            record = dispatch_micro_lesson(tree, event, run)
        decisions[out["action"]] = decisions.get(out["action"], 0) + 1
        if event["kind"] == "change":
            tree.mark_seen(key)
        cohort_label = None
        if event["kind"] == "revert":
            cohort_label = "fixture (simulated)" if tree.mode != "live" else "telemetry"
        row = {
            "receipt_id": f"rcpt-{run[-6:]}-{len(tree.rows()):03d}", "ts": now(), "run_id": run,
            **({"cohort_source": cohort_label} if cohort_label else {}),
            "event_id": key, "mode": tree.mode, "stream": event["kind"],
            "sources": event.get("sources", []), "quotes": event.get("quotes", []),
            "judge": {"model": "fixture-judge", "answers": {"q1_materiality": inp["materiality"]}},
            "decision": {"action": out["action"], "reason_codes": out["reason_codes"], "authority": out["authority"]},
            "artifact": record,
            "cost": {"tokens": 0, "apify_units": 0, "eur": None,
                     "cost_state": "unmeasured (no vendor prices captured)"},
            "actor": "system", "label": event.get("summary", "")[:160],
        }
        tree.append_receipt(row)
        if row["artifact"] and row["artifact"].get("new_version"):
            update_changelog_receipt(tree, row["artifact"]["lesson_id"], row["artifact"]["new_version"], row["receipt_id"])
        if record:
            artifacts.append(record)
    ok, n = tree.verify_chain()
    log = {"run_id": run, "mode": tree.mode, "started_at": now(), "ended_at": now(),
           "label": label, "sources_scanned": sum(len(e.get("sources", [])) for e in events),
           "deltas": sum(1 for e in events if e["kind"] == "change"),
           "decisions": decisions, "publishes_used": publishes_used,
           "receipts": len(tree.rows()), "chain_verified_at_end": ok, "chain_rows": n,
           "freeze_at_end": tree.frozen()}
    with tree.run_log_path.open("a") as fh:
        fh.write(json.dumps(log, sort_keys=True) + "\n")
    tree.digest_path.write_text(render_digest(tree, log))
    (tree.out / "digest.html").write_text(render_html(tree, log))
    return log


def render_digest(tree: Tree, log: dict) -> str:
    rows = tree.rows()
    lines = [
        f"# Courserefresh digest — {now()}",
        "",
        f"mode: **{tree.mode}** · run `{log['run_id']}` · chain: {'ok' if log['chain_verified_at_end'] else 'BROKEN'} ({log['chain_rows']} rows)",
        "",
        "## 1. What it refused (first, with reasons)",
    ]
    refused = [r for r in rows if r["decision"]["action"] == "ESCALATE"]
    lines += ([f"- `{r['event_id']}` — {', '.join(r['decision']['reason_codes'])}" for r in refused]
              or ["- none this run"])
    lines += ["", "## 2. What changed"]
    changed = [r for r in rows if r["decision"]["action"] in ("PUBLISH", "REVERT")]
    downstream: set[str] = set()
    for r in changed:
        a = r["artifact"] or {}
        quiz = f" · quiz {a['quiz_item']} regenerated" if a.get("quiz_path") else ""
        lines.append(f"- {r['decision']['action']} `{a.get('lesson_id')}` {a.get('previous_version')} → {a.get('new_version')} · {a.get('diff_path', '')}{quiz}")
        if r["decision"]["action"] == "PUBLISH":
            downstream.update(downstream_lessons(a.get("lesson_id", "")))
    if not changed:
        lines.append("- nothing")
    if downstream:
        lines.append(f"- downstream to revisit (not rewritten tonight): {', '.join(sorted(downstream))}")
    lines += ["", "## 3. Learners"]
    dispatches = [r for r in rows if r["decision"]["action"] == "DISPATCH"]
    consent_blocked = [r for r in rows if "consent_missing" in r["decision"]["reason_codes"]]
    notified = sum(len((r["artifact"] or {}).get("notified", [])) for r in rows)
    if tree.mode == "live":
        lines.append(f"- notifications sent: {notified} (consented cohort only, one per learner)")
    else:
        lines.append(f"- notifications staged, not sent: {notified} (mode: {tree.mode}; no mail leaves the box)")
    lines.append(f"- micro-lessons dispatched: {len(dispatches)}")
    skipped = sum(len((r["artifact"] or {}).get("notification_skips", [])) for r in rows)
    if skipped:
        lines.append(f"- notifications held by cap: {skipped} (Art. XIV.2)")
    lines.append(f"- blocked for missing consent: {len(consent_blocked)}")
    lines.append("- cohort quiz delta: unmeasured (sim run: no consented live cohort)")
    lines += ["", "## 4. Discipline"]
    used: dict[str, int] = {}
    for r in rows:
        a = r["decision"]["authority"]
        used[a] = used.get(a, 0) + 1
    ladder = ", ".join(f"{k}×{v}" for k, v in sorted(used.items())) or "none"
    lines.append(f"- authority used this run: {ladder} · promotion to PA2 needs "
                 f"{THRESHOLDS['authority']['pa2_consecutive_accepted']} consecutive accepted publishes")
    lines.append(f"- budgets: publishes {log['publishes_used']}/{THRESHOLDS['budgets']['publishes_per_day']} · tokens unmeasured (sim run) · digest ≤ {THRESHOLDS['budgets']['digest_bytes']} bytes")
    lines.append(f"- kill switch: {'ENGAGED' if log['freeze_at_end'] else 'off'}")
    lines.append(f"- cost per change: unmeasured (sim run) — no vendor prices captured yet")
    lines.append(f"- receipts: {log['receipts']} rows · chain verified at end: {log['chain_verified_at_end']}")
    lines.append("")
    lines.append("> Offline twin: same policy rules as the n8n node (parity-tested); fixtures labelled in every receipt.")
    text = "\n".join(lines) + "\n"
    if len(text.encode()) > THRESHOLDS["budgets"]["digest_bytes"]:
        text = text[: THRESHOLDS["budgets"]["digest_bytes"] - 40] + "\n[trimmed — refusals kept]\n"
    return text


def render_html(tree: Tree, log: dict) -> str:
    """The console page. Same content as the digest, same lockfile colours, no scripts."""
    t = design_tokens()
    rows = tree.rows()
    colour = {"PUBLISH": t["--status-publish"], "REVERT": t["--status-revert"],
              "ESCALATE": t["--status-revert"], "NO_CHANGE": t["--status-nochange"],
              "DISPATCH": t["--status-queue"]}
    word = {"PUBLISH": "PUBLISHED", "REVERT": "REVERTED", "ESCALATE": "REFUSED",
            "NO_CHANGE": "NO CHANGE", "DISPATCH": "SENT"}
    e = html.escape
    body = []
    for r in rows:
        action = r["decision"]["action"]
        why = e(", ".join(r["decision"]["reason_codes"]) or "—")
        artifact = r["artifact"] or {}
        detail = (f"{artifact.get('lesson_id', '')} {artifact.get('previous_version', '')} → "
                  f"{artifact.get('new_version', '')}") if artifact.get("new_version") else r.get("label", "")
        body.append(
            f'<li class="row"><span class="status" style="color:{colour[action]}">'
            f'<b>{word[action]}</b></span> <code>{e(str(r["event_id"]))}</code> '
            f'<span class="why">{why}</span>'
            f'<div class="detail">{e(str(detail))}</div></li>')
    mode_note = ("the console is reading a **sim** run: fixtures, no model calls, no mail"
                 if tree.mode != "live" else "live run")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Courserefresh console — {log['run_id']}</title>
<style>
  :root {{ {" ".join(f"{k}:{v};" for k, v in t.items())} }}
  body {{ background:var(--paper); color:var(--ink); font:15px/1.6 system-ui, sans-serif;
          max-width:var(--measure, 68ch); margin:0 auto; padding:24px; }}
  h1 {{ font-size:20px; }} code {{ font-family:ui-monospace, monospace; font-size:13px; }}
  .why {{ color:var(--ink-soft); }}
  .detail {{ color:var(--ink-soft); font-size:13px; }}
  .status {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
  ul {{ list-style:none; padding:0; }} .row {{ border-top:1px solid var(--rule); padding:10px 0; }}
  .mode {{ color:var(--ink-soft); }}
</style></head><body>
<h1>Courserefresh console</h1>
<p class="mode">run <code>{log['run_id']}</code> · mode <b>{tree.mode}</b> · chain
{'ok' if log['chain_verified_at_end'] else 'BROKEN'} ({log['chain_rows']} rows) · {mode_note}</p>
<h2>Decisions, refusals first</h2>
<ul>{"".join(sorted(body, key=lambda b: "REFUSED" not in b))}</ul>
<p class="detail">Every line is a receipt; the digest is the same content in text
(<code>app/out/digest.md</code>). Colours come from <code>specs/design/MASTER.md</code>.</p>
</body></html>"""


# --- selftest ------------------------------------------------------------------------------------

def selftest() -> int:
    sandbox = ROOT / "app" / "out" / "selftest"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    (sandbox / "course").parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "course", sandbox / "course")
    tree = Tree(sandbox / "course", sandbox / "out", mode="sim")
    checks: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        checks.append((name, ok, detail))

    events = load_events(include_seed=True)   # the selftest proves the SEEDED label too
    log = run(tree, events, label="selftest")
    rows = tree.rows()
    ok, n = tree.verify_chain()
    check("receipt chain verifies", ok and n == len(rows), f"{n} rows")
    hostile = [r for r in rows if r["event_id"] == "cr-hostile-page-01"]
    check("hostile page never publishes",
          bool(hostile) and hostile[0]["decision"]["action"] == "ESCALATE"
          and "injection_or_jailbreak" in hostile[0]["decision"]["reason_codes"],
          hostile[0]["decision"]["action"] if hostile else "missing")
    check("single source never publishes",
          all(r["decision"]["action"] != "PUBLISH" for r in rows if r["event_id"] == "cr-single-source-01"))
    consent = [r for r in rows if r["event_id"] == "cr-learner-consent-01"]
    check("consent gate: no message without consent",
          bool(consent) and consent[0]["decision"]["action"] == "NO_CHANGE"
          and "consent_missing" in consent[0]["decision"]["reason_codes"])
    stuck = [r for r in rows if r["event_id"] == "cr-learner-stuck-01"]
    check("stuck learner gets help before asking",
          bool(stuck) and stuck[0]["decision"]["action"] == "DISPATCH" and stuck[0]["artifact"])
    published = [r for r in rows if r["decision"]["action"] == "PUBLISH"]
    check("publish wrote a version + diff + gate",
          bool(published) and all(r["artifact"].get("diff_path") and r["artifact"].get("revert_gate") for r in published),
          f"{len(published)} publishes")
    reverts = [r for r in rows if r["decision"]["action"] == "REVERT"]
    reverted_body = None
    if reverts:
        p = tree.root / reverts[0]["artifact"]["body_path"]
        reverted_body = p.read_text()
    check("revert restored the previous version as a new version",
          bool(reverts) and reverted_body is not None and "Reverted." in reverted_body,
          f"{len(reverts)} reverts")
    budget = [r for r in rows if r["event_id"] == "cr-budget-01"]
    check("budget cap escalates instead of publishing",
          bool(budget) and budget[0]["decision"]["action"] == "ESCALATE"
          and "over_budget" in budget[0]["decision"]["reason_codes"])
    seeded = [r for r in rows if r["event_id"] == "cr-seeded-01"]
    check("seeded rehearsal is labelled in the decision",
          bool(seeded) and "seeded_rehearsal" in seeded[0]["decision"]["reason_codes"])
    check("receipt coverage is 100% of decisions",
          len(rows) == sum(log["decisions"].values()) + (1 if False else 0), f"{len(rows)} receipts vs {log['decisions']}")
    html_tokens = set(re.findall(r"#[0-9A-Fa-f]{6}", tree.digest_path.with_suffix(".html").read_text()))
    lockfile_tokens = set(design_tokens().values())
    check("console colours exist in the design lockfile",
          html_tokens <= lockfile_tokens, f"unknown={sorted(html_tokens - lockfile_tokens)}")
    check("digest fits the 4 KB contract",
          len(tree.digest_path.read_bytes()) <= THRESHOLDS["budgets"]["digest_bytes"],
          f"{len(tree.digest_path.read_bytes())} bytes")
    # kill switch: freeze, then run; no writes may appear in the new receipts
    before = len(tree.rows())
    tree.freeze_path.write_text("paused by selftest")
    frozen_log = run(tree, load_events(include_seed=False), label="frozen")
    new_rows = tree.rows()[before:]
    written = [r for r in new_rows if r["decision"]["action"] in ("PUBLISH", "REVERT", "DISPATCH")]
    frozen_decisions = [r for r in new_rows if "freeze_active" in r["decision"]["reason_codes"]]
    check("kill switch: no writes while frozen",
          not written and bool(frozen_decisions),
          f"{len(new_rows)} frozen decisions, 0 writes")
    tree.freeze_path.unlink()
    # tamper detection (last: it invalidates the chain on purpose)
    lines = tree.receipts_path.read_text().splitlines()
    tampered = json.loads(lines[0]); tampered["ts"] = "2026.01.01T00:00:00Z"  # any edit must be detectable
    tree.receipts_path.write_text(json.dumps(tampered, sort_keys=True) + "\n" + "\n".join(lines[1:]) + "\n")
    ok2, _ = tree.verify_chain()
    check("tampering breaks the chain", ok2 is False)

    passed = sum(1 for _, ok, _ in checks if ok)
    width = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print(f"\nselftest: {passed}/{len(checks)} checks passed · sandbox: {sandbox.relative_to(ROOT)}")
    return 0 if passed == len(checks) else 1


def load_events(include_seed: bool = False, fresh: bool = False) -> list[dict]:
    events = []
    for path in sorted((ROOT / "app" / "fixtures" / "events").glob("*.json")):
        event = json.loads(path.read_text())
        if event.get("seed") and not include_seed:
            continue
        if fresh:
            event["input"]["freeze_active"] = False
        events.append(event)
    return events


def main() -> int:
    ap = argparse.ArgumentParser(description="Courserefresh offline twin")
    ap.add_argument("--run", action="store_true", help="run the loop (default)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--pause", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--replay", metavar="RUN_ID")
    ap.add_argument("--seed-demo", action="store_true", help="include the labelled seeded rehearsal event")
    ap.add_argument("--chaos", choices=["write-fail"], default=None,
                    help="rehearse a witnessed failure: one write fails and must be reported")
    ap.add_argument("--root", metavar="DIR", help="operate on another tree root")
    ap.add_argument("--mode", default="sim")
    ap.add_argument("--token", default=None, help="required for --resume when CR_DEMO_TOKEN is set")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    root = (Path(args.root) if args.root else ROOT).resolve()
    tree = Tree(root / "course" if (root / "course").exists() else root, root / "app" / "out",
                mode=args.mode, chaos=args.chaos)
    if args.pause:
        tree.freeze_path.write_text("paused")
        tree.append_receipt({"ts": now(), "run_id": run_id(), "event_id": "op-pause", "mode": tree.mode,
                             "stream": "change", "decision": {"action": "NO_CHANGE", "reason_codes": ["freeze_active"], "authority": "PA1"},
                             "artifact": None, "cost": None, "actor": "human:operator", "label": "kill switch"})
        print("paused: writes frozen (reads continue)")
        return 0
    if args.resume:
        import os
        required = os.environ.get("CR_DEMO_TOKEN")
        if required and args.token != required:      # TM14: unauthorised resume
            print("refused: bad or missing token", file=sys.stderr)
            return 3
        if not tree.freeze_path.exists():
            print("not paused", file=sys.stderr)
            return 3
        tree.freeze_path.unlink()
        tree.append_receipt({"ts": now(), "run_id": run_id(), "event_id": "op-resume", "mode": tree.mode,
                             "stream": "change", "decision": {"action": "NO_CHANGE", "reason_codes": ["no_delta"], "authority": "PA1"},
                             "artifact": None, "cost": None, "actor": "human:operator", "label": "kill switch released"})
        print("resumed: writes enabled")
        return 0
    if args.report:
        print(tree.digest_path.read_text() if tree.digest_path.exists() else "no digest yet")
        return 0
    if args.replay:
        events = load_events(include_seed=True)
        if tree.frozen():
            print("frozen: replay refused", file=sys.stderr)
            return 4
        log = run(tree, events, label=f"replay:{args.replay}")
        ok, n = tree.verify_chain()
        print(json.dumps({"run": log["run_id"], "decisions": log["decisions"], "chain": f"{'ok' if ok else 'BROKEN'} ({n} rows)"}))
        return 0

    log = run(tree, load_events(include_seed=args.seed_demo))
    ok, n = tree.verify_chain()
    print(json.dumps({"run_id": log["run_id"], "mode": tree.mode, "decisions": log["decisions"],
                      "chain": f"{'ok' if ok else 'BROKEN'} ({n} rows)",
                      "digest": str(tree.digest_path), "receipts": str(tree.receipts_path)}, indent=2))
    if not ok:
        return 1
    if log["decisions"].get("PUBLISH", 0) and any(
            r["decision"]["action"] == "PUBLISH" and "injection_or_jailbreak" in r["decision"]["reason_codes"]
            for r in tree.rows()):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
