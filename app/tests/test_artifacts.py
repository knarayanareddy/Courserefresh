#!/usr/bin/env python3
"""Artifact-integrity and learner-contract checks (constitution Art. IX, XIV; AC-9.1–9.3, AC-11.2).

The receipts chain proves the ledger; this file proves the *artifacts the ledger names* — that every
published version still hashes to its receipt, that a revert really restored the version it claims,
that a learner card carries the contract and nothing raw, and that the per-learner / per-concept caps
are enforced in code rather than promised in a table.

Run: python3 app/tests/test_artifacts.py
"""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)

SANDBOX = ROOT / "app" / "out" / "artifacts-test"
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


def sha_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_text().encode()).hexdigest()


if SANDBOX.exists():
    shutil.rmtree(SANDBOX)
shutil.copytree(ROOT / "course", SANDBOX / "course")
out = SANDBOX / "app" / "out"
out.mkdir(parents=True, exist_ok=True)
tree = twin.Tree(SANDBOX / "course", out, mode="sim")
twin.run(tree, twin.load_events(include_seed=False), label="artifacts-test")
rows = tree.rows()

artifacts = [r for r in rows if r["artifact"] and r["artifact"].get("body_path")]
reverts = [r for r in rows if r["decision"]["action"] == "REVERT" and r["artifact"]]

# 1. every receipted body still hashes to the receipt, and its predecessor exists and differs
bad_hash, bad_prev = [], []
for r in artifacts:
    a = r["artifact"]
    body = tree.root / a["body_path"]
    prev = (tree.root / a["body_path"]).parent / f"{a['previous_version']}.md"
    if not body.exists() or sha_file(body) != a["payload_hash"]:
        bad_hash.append(a["body_path"])
    if not prev.exists() or prev.read_text() == body.read_text():
        bad_prev.append(a["body_path"])
check("every artifact still hashes to its receipt", not bad_hash, f"mismatched={bad_hash[:2]}")
check("every publish names a predecessor that exists and differs", not bad_prev, f"bad={bad_prev[:2]}")

# 2. every diff still hashes to the receipt (the receipt stores the diff without a trailing newline)
bad_diff = []
for r in artifacts:
    a = r["artifact"]
    diff_path = tree.root / a["diff_path"]
    if not diff_path.exists():
        bad_diff.append(a["diff_path"])
        continue
    digest = "sha256:" + hashlib.sha256(diff_path.read_text().rstrip("\n").encode()).hexdigest()
    if digest != a["diff_hash"]:
        bad_diff.append(a["diff_path"])
check("every diff still hashes to its receipt", not bad_diff, f"mismatched={bad_diff[:2]}")

# 3. a revert names the version it restores and keeps that version's text
target = json.loads((ROOT / "app" / "fixtures" / "events" / "09-revert.json").read_text())["target"]
restore = tree.root / "agent-ops" / target["lesson_id"] / f"{target['restore_version']}.md"
revert_body = tree.root / reverts[0]["artifact"]["body_path"] if reverts else None
restored_text = restore.read_text() if restore.exists() else ""
distinctive = [l for l in restored_text.splitlines() if l.startswith("1.") or l.startswith("- ")]
kept = bool(revert_body and revert_body.exists() and
            any(line in revert_body.read_text() for line in distinctive[:3]))
marker = bool(revert_body and revert_body.exists() and "**Reverted.**" in revert_body.read_text())
check("a revert restores the version it names (text kept, marker written)",
      bool(reverts) and kept and marker, f"reverts={len(reverts)} marker={marker}")

# 4. learner cards carry the contract and nothing raw
notes = [json.loads(l) for l in (out / "notifications.jsonl").read_text().splitlines() if l.strip()]
required = {"learner_ref", "lesson_id", "from", "to", "what_changed", "opt_out", "diff_path"}
consented = {json.loads(p.read_text())["learner_ref"]
             for p in (ROOT / "app" / "fixtures" / "telemetry").glob("*.json") if json.loads(p.read_text())["consent"]}
raw_markers = ("diff --git", "@@ ", "```")
bad_cards = [n["learner_ref"] for n in notes
             if required - set(n) or len(n["what_changed"]) > 240
             or any(m in n["what_changed"] for m in raw_markers)
             or n["learner_ref"] not in consented]
check("learner cards carry the contract, no raw diff, consented refs only",
      not bad_cards and len(notes) == len(consented), f"cards={len(notes)} bad={bad_cards[:2]}")

# 5. the per-learner notification cap is enforced in code (second same-day publish notifies nobody)
publish_event = next(e for e in twin.load_events(include_seed=False) if e["event_id"] == "cr-n8n-rename-01")
again = twin.notify_cohort(tree, publish_event, {"lesson_id": "lesson-04-tool-permissions",
                                                 "previous_version": "v3", "new_version": "v4"})
check("notification caps are enforced in code (day cap skips every consented learner)",
      again["notified"] == [] and len(again["skipped"]) == len(consented),
      f"notified={len(again['notified'])} skipped={len(again['skipped'])}")

# 6. the per-concept micro-lesson cap is enforced (second stuck signal in the window is rate-limited)
stuck_event = next(e for e in twin.load_events(include_seed=False) if e["event_id"] == "cr-learner-stuck-01")
before = {p.name for p in (out / "micro-lessons").glob("*.md")}
twin.run(tree, [stuck_event], label="artifacts-test-cap")
after = {p.name for p in (out / "micro-lessons").glob("*.md")}
last = tree.rows()[-1]
check("per-concept micro-lesson cap holds (second dispatch in the window is rate-limited)",
      last["decision"]["action"] == "NO_CHANGE" and last["decision"]["reason_codes"] == ["rate_limited"]
      and before == after, f"{last['decision']['action']} {last['decision']['reason_codes']} new={after - before}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_artifacts: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
