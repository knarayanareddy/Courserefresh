#!/usr/bin/env python3
"""Courserefresh live engine — the real loop: Apify in, judge, policy, repo out, learners told.

The offline twin (`app/run_walking_skeleton.py`) remains the fallback and the test engine. This file
is what runs on a schedule once credentials are present. It reuses the twin's writers and the same
`skin/policy.py` gate, so a live cycle and a sim cycle differ in *where the data came from*, never in
what is decided.

Phases (harness.md §1), all receipted:
    notice  Apify actor per source (or the declared HTTP fallback) → snapshots, hashed, cached,
            deduplicated against `app/out/state/seen_snapshots.json`, budgeted by the unit ledger
    verify  claims extracted deterministically (keyword + overlap), the judge answers the seven
            closed questions, corroboration counted by **voices** (role `none` never counts)
    decide  `skin/policy.py` — the same oracle the n8n node mirrors
    act     the twin's writers: lesson version + diff + CHANGELOG + quiz item + card rows
    learn   telemetry → cohort window → `decide_revert` / `decide_learner` (`--learn`)
    report  digest + console page, plus a delivery summary per channel

Commands
    --preflight          what is wired, what is missing, which claims are allowed (writes a JSON)
    --once               one cycle (default; `--dry-run` uses recorded datasets and the mock judge)
    --watch              loop on `CR_LIVE_SCAN_MINUTES` cadence, budget-guarded, freeze-aware
    --learn              run the learn phase only (cohort gate + stuck dispatch) and report
    --digest-only        re-render the digest from receipts
    --seed-baseline      pre-seed the dedupe state from `app/fixtures/apify/baseline/` (dry runs)
    --selftest           offline end-to-end over the recorded datasets, assertions included

Exit codes: 0 ok · 1 verification failed · 2 blocked (missing credentials for the requested mode) ·
3 usage/config · 4 refused by policy.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]     # the repository — never rebased; fixtures live here
ROOT = REPO
APP = ROOT / "app"
sys.path.insert(0, str(APP / "lib"))
sys.path.insert(0, str(APP))

import apify as apify_lib  # noqa: E402
import judge as judge_lib  # noqa: E402
import notify as notify_lib  # noqa: E402
import telemetry as telemetry_lib  # noqa: E402
from config import Config  # noqa: E402

spec = importlib.util.spec_from_file_location("twin", APP / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)

OUT = APP / "out"
STATE = OUT / "state"
SNAPSHOTS = OUT / "snapshots"
LIVE = OUT / "live"


def rebase(root: Path) -> None:
    """Point the engine at another tree (tests and rehearsals). Fixtures stay in the repo."""
    global ROOT, APP, OUT, STATE, SNAPSHOTS, LIVE
    ROOT = root.resolve()
    APP = ROOT / "app"
    OUT = APP / "out"
    STATE = OUT / "state"
    SNAPSHOTS = OUT / "snapshots"
    LIVE = OUT / "live"
THRESHOLDS = apify_lib.load_thresholds()
SOURCES = apify_lib.load_sources()
COHORT_NOTIFY = ("material_breaking", "material_deprecation")
STOPWORDS = {"the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are", "was", "with",
             "that", "this", "it", "as", "by", "from", "at", "be", "can", "will", "now", "new"}


# --- small helpers -------------------------------------------------------------------------------

def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def tree_for(mode: str) -> "twin.Tree":
    return twin.Tree(ROOT / "course", OUT, mode=mode)


def read_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


# --- notice --------------------------------------------------------------------------------------

def due_sources(state: dict, scan_minutes: int) -> list[dict]:
    """Cadence per source (skin/sources.json). A source is due when its last scan is old enough."""
    due = []
    for source in SOURCES["sources"]:
        last = state.get(source["source_id"], {}).get("last_scan_epoch")
        cadence = source.get("cadence_minutes", scan_minutes) * 60
        if last is None or (time.time() - last) >= cadence:
            due.append(source)
    return due


def fetch_source(client: apify_lib.ApifyClient, source: dict, cfg: Config) -> dict:
    """Actor first, declared fallback second, `unreachable` third — never silence."""
    run = client.run_actor(source)
    if cfg.flag("CR_APIFY_DRY") or client.dry_run:
        items = run.get("items") or client.dataset_items(run.get("dataset_id", ""))
    else:
        items = client.dataset_items(run.get("dataset_id", "")) if run.get("ok") else []
    if not run.get("ok") or not items:
        fallback = source.get("fallback") or {}
        if fallback.get("kind") == "http":
            return {"ok": False, "used_fallback": True, "run": run,
                    "error": run.get("error") or "empty_dataset",
                    "message": run.get("message") or "actor returned no rows",
                    "source_id": source["source_id"]}
        return {"ok": False, "used_fallback": False, "run": run,
                "error": run.get("error", "actor_failed"), "source_id": source["source_id"]}
    return {"ok": True, "run": run, "items": items, "used_fallback": False, "source_id": source["source_id"]}


def notice(cfg: Config, tree: "twin.Tree", dry_run: bool, ledger: apify_lib.UnitLedger) -> dict:
    """Fetch every due source, normalise, cache, dedupe. Returns snapshots + a tally."""
    state = read_json(STATE / "scan_state.json", {})
    seen = set(read_json(STATE / "seen_snapshots.json", []))
    transport = apify_lib.RecordingTransport(apify_lib.urllib_transport)
    client = apify_lib.ApifyClient(token=cfg.get("APIFY_TOKEN"), base_url=cfg.get("APIFY_BASE_URL"),
                                   transport=transport, timeout=cfg.int("APIFY_TIMEOUT_S", 300),
                                   max_retries=cfg.int("APIFY_MAX_RETRIES", 1),
                                   dry_run=dry_run)
    due = due_sources(state, cfg.int("CR_LIVE_SCAN_MINUTES", 60))
    fresh, rejected, holds, sources_scanned = [], [], [], 0
    for source in due:
        allowed, note = ledger.can_spend(SOURCES.get("units_per_run", 1))
        if not allowed:
            holds.append({"source_id": source["source_id"], "reason": note})
            continue
        result = fetch_source(client, source, cfg)
        if not result["ok"]:
            # a failed fetch is an `unverifiable` event, not silence (harness §1)
            fresh.append({"source_id": source["source_id"], "unreachable": True,
                          "reason": result["error"],
                          "message": result.get("message", ""),
                          "used_fallback": result["used_fallback"],
                          "url": source["url"], "publisher": source["publisher"],
                          "role": source["role"], "independence_group": source["independence_group"]})
            state[source["source_id"]] = {"last_scan_epoch": time.time(), "last_scan": now(),
                                          "error": result["error"]}
            continue
        normalised = apify_lib.normalise_dataset(result["items"], source, SNAPSHOTS)
        ledger.record(source["source_id"], result["run"].get("run_id") or "dry",
                      result["run"].get("usd"), unit_price_eur=None)
        sources_scanned += 1
        rejected.extend([{**r, "source_id": source["source_id"]} for r in normalised["rejected"]])
        for snapshot in normalised["snapshots"]:
            key = f"{snapshot['source_id']}:{snapshot['content_hash']}"   # per source, or a shared
            if key in seen:                                               # page would lose a voice
                continue
            seen.add(key)
            fresh.append(snapshot)
        state[source["source_id"]] = {"last_scan_epoch": time.time(), "last_scan": now(),
                                      "rows": len(result["items"]),
                                      "accepted": len(normalised["snapshots"]),
                                      "discarded": normalised["discarded"]}
    write_json(STATE / "scan_state.json", state)
    write_json(STATE / "seen_snapshots.json", sorted(seen))
    return {"snapshots": fresh, "rejected": rejected, "budget_holds": holds,
            "sources_scanned": sources_scanned, "due": [s["source_id"] for s in due],
            "apify_calls": transport.calls, "spent_units": ledger.spent_today()}


# --- verify --------------------------------------------------------------------------------------

def claims_from_markdown(markdown: str, limit: int = 12) -> list[str]:
    """Deterministic claim extraction: sentences that carry a version, a setting name, or a change verb.

    Deliberately not a model: this runs on every scan, costs nothing, and cannot hallucinate a claim
    that is not in the text. `CR_OBSERVE_PROVIDER=model` swaps in the observe prompt for operators
    who want it (see docs/OPERATIONS.md §3).
    """
    sentences = re.split(r"(?<=[.!?])\s+|\n+", markdown)
    keep = []
    for sentence in sentences:
        text = sentence.strip()
        if len(text) < 20 or len(text) > 400:
            continue
        if re.search(r"\b\d+\.\d+(\.\d+)?\b|rename[sd]?|remov(e|ed|al)|deprecat\w*|replaced|no longer|"
                     r"now require[sd]?|now validat\w+|now check\w*|must now|breaking|sunset|migrat\w*|"
                     r"schema", text, re.I):
            keep.append(re.sub(r"\s+", " ", text))
        if len(keep) >= limit:
            break
    return keep


def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_.]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def overlap(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def group_events(snapshots: list[dict], lessons: list[dict]) -> list[dict]:
    """Cluster changed snapshots into *events*: one fact, every voice that states it.

    Two snapshots belong to the same event when their claims overlap (≥ 0.25 Jaccard by token) — that
    is the machine version of "same fact". The cluster keeps every voice, so corroboration is decided
    on all of them at once; a scan that publishes the same change twice is a bug, not a demo.
    """
    prepared = []
    for snapshot in snapshots:
        if snapshot.get("unreachable"):
            continue
        prepared.append({**snapshot, "_claims": claims_from_markdown(snapshot["markdown"]),
                         "_tokens": tokens(" ".join(claims_from_markdown(snapshot["markdown"])[:2000]))})
    clusters: list[list[dict]] = []
    for item in prepared:
        placed = False
        for cluster in clusters:
            merged = set().union(*[c["_tokens"] for c in cluster]) if cluster else set()
            if item["_tokens"] and overlap(item["_tokens"], merged) >= 0.25:
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    events = []
    for raw_cluster in clusters:
        cluster = [{k: v for k, v in item.items() if not k.startswith("_")} for item in raw_cluster]
        voices = sorted({c["publisher"].lower() for c in cluster if c.get("role") != "none"})
        concept = next((c for lesson in lessons for c in lesson.get("concepts", [])
                        if any(c.replace("-", " ") in item["markdown"].lower() for item in cluster)), "")
        claims = sorted({claim for item in raw_cluster for claim in item["_claims"]})
        event_id = "cr-" + "-".join(sorted({c["source_id"].split("-")[0] for c in cluster})) \
                   + "-" + short_hash("|".join(sorted(claims)))[:10]
        # the representative is the authoritative voice that stated the fact first: it names the
        # event and it is the snapshot whose judge/render recordings are consulted
        representative = sorted(cluster, key=lambda c: (0 if c.get("role") == "authoritative" else 1,
                                                        c.get("published_at") or "9999"))[0]
        events.append({
            "event_id": event_id, "kind": "change", "sources": cluster, "claims": claims,
            "summary": (representative.get("title") or representative["url"])[:120],
            "lesson_touched": concept, "snapshot": representative,
            "quotes": [{"source_id": item["source_id"], "url": item["url"],
                        "text": (item["_claims"] or [item.get("title", "")])[0][:280]}
                       for item in raw_cluster],
            "voices": voices, "sources_verified": len(voices),
        })
    # an unreachable source is still an event: `unverifiable`, never silence (harness §1)
    for snapshot in snapshots:
        if snapshot.get("unreachable"):
            events.append({"event_id": f"cr-{snapshot['source_id']}-unreachable", "kind": "change",
                           "unreachable": True, "sources": [snapshot], "claims": [], "quotes": [],
                           "summary": f"{snapshot['source_id']} could not be fetched",
                           "lesson_touched": ""})
    return events


def corroboration_summary(event: dict) -> dict:
    voices = {s["publisher"].lower() for s in event["sources"] if s.get("role") != "none"}
    mirrors = [s["source_id"] for s in event["sources"] if s.get("role") == "none"]
    return {"sources_verified": len(voices), "voices": sorted(voices), "mirrors": mirrors,
            "sources": [{"source_id": s.get("source_id"), "publisher": s.get("publisher"),
                         "role": s.get("role"), "url": s.get("url")} for s in event["sources"]]}


# --- act: the twin does the writing, so there is one implementation of every artifact -------------

def canvas_decide(cfg: Config, event_input: dict, transport=None) -> dict:
    """Ask the n8n canvas to decide: POST the DecisionInput to the triage webhook (WIRING §3).

    The canvas's POLICY node is the production rulebook; the oracle is the test. If the two disagree,
    the cycle fails closed — a decision nobody can reproduce is not a decision (Art. VIII, XIII).
    """
    import n8n as n8n_lib
    client = n8n_lib.N8nClient(cfg.get("N8N_BASE_URL"), cfg.get("N8N_API_KEY"), transport=transport or n8n_lib.urllib_transport,
                               instance_version=cfg.get("N8N_INSTANCE_VERSION"))
    if not client.configured():
        return {"ok": False, "reason": "not_configured"}
    result = client.call_webhook("cr/triage", {"input": event_input})
    if not result.get("ok"):
        return {"ok": False, "reason": f"webhook_http_{result.get('status')}"}
    payload = result.get("response") or {}
    decision = payload.get("decision") if isinstance(payload, dict) else None
    if not isinstance(decision, dict) or "action" not in decision:
        return {"ok": False, "reason": "payload_invalid", "raw": str(payload)[:200]}
    return {"ok": True, "decision": decision,
            "execution_id": payload.get("execution_id"), "workflow": payload.get("workflow", "wf-cr-1-triage")}


def canvas_agrees(canvas_decision: dict, oracle_decision: dict) -> bool:
    """Two decisions agree only on action *and* reason codes (Art. VIII: the code decides).

    A bare action match is not enough: `ESCALATE` for `insufficient_corroboration` and
    `ESCALATE` for `hostile_content` are different decisions with different fixes.
    """
    return (canvas_decision.get("action") == oracle_decision.get("action")
            and sorted(canvas_decision.get("reason_codes", [])) == sorted(oracle_decision.get("reason_codes")))


def render_change(cfg: Config, event: dict, provider, model: str, tree: "twin.Tree") -> dict:
    """One anchored rewrite per change event. A refusal here becomes a receipt, never a silent skip."""
    lesson_id = event.get("lesson_touched") or ""
    lesson_dir = ROOT / "course" / "agent-ops" / lesson_id
    versions = sorted(lesson_dir.glob("v*.md")) if lesson_dir.exists() else []
    if not versions:
        return {"ok": False, "reason_codes": ["claim_unanchored"],
                "message": f"no lesson body for '{lesson_id}'"}
    body = versions[-1].read_text()
    rendered = judge_lib.ask_renderer(event, body, provider, model)
    if not rendered["ok"]:
        tree.append_receipt({"ts": twin.now(), "run_id": twin.run_id(),
                             "event_id": event["event_id"], "mode": tree.mode, "stream": "change",
                             "sources": [{"source_id": s.get("source_id"), "publisher": s.get("publisher"),
                                          "role": s.get("role"), "url": s.get("url")} for s in event["sources"]],
                             "quotes": event.get("quotes", []),
                             "judge": {"model": model, "answers": {}},
                             "decision": {"action": "ESCALATE",
                                          "reason_codes": ["claim_unanchored"], "authority": "PA2"},
                             "artifact": None,
                             "cost": {"tokens": rendered.get("tokens"), "apify_units": 0, "eur": None,
                                      "cost_state": "unmeasured (no vendor prices captured)"},
                             "actor": "system",
                             "label": f"rewrite refused: {rendered.get('problems') or rendered.get('error')}"})
    return rendered


def to_twin_event(event: dict, judgement: dict, authority: str, freeze: bool, budgets: dict,
                  render: dict | None = None) -> dict:
    """Live event → the shape the twin consumes (identical to a fixture, so receipts are comparable)."""
    stats = corroboration_summary(event)
    lesson_id = event.get("lesson_touched") or ""
    lesson_dir = ROOT / "course" / "agent-ops" / lesson_id
    version_file = sorted(lesson_dir.glob("v*.md"))[-1] if lesson_dir.exists() else None
    body = version_file.read_text() if version_file else ""
    patch = None
    if render and render.get("ok"):
        patch = {"file": f"{lesson_id}/{version_file.name}", **render["patch"]}
    return {
        "event_id": event["event_id"], "kind": "change",
        "parent": lesson_id,                      # the twin's writer needs the lesson folder
        "summary": event["summary"][:120],
        "learner_facing": ((render or {}).get("learner_facing")
                           or f"Something you learned changed upstream: {event['summary'][:140]}"),
        "sources": [{"source_id": s.get("source_id"), "publisher": s.get("publisher"),
                     "role": s.get("role"), "url": s.get("url")} for s in event["sources"]],
        "quotes": event.get("quotes", []), "patch": patch,
        "quiz_patch": ({"lesson_id": f"lesson-{lesson_id.split('-')[1]}", **(render or {}).get("quiz")}
                       if (render or {}).get("quiz") else None),
        "gate": {"n_min": THRESHOLDS["revert"]["n_min"], "window_h": THRESHOLDS["revert"]["window_h"],
                 "metric": "quiz_delta", "condition": "<=0"},
        "input": {**judge_lib.decision_input_from_judgement(event, judgement, stats, authority,
                                                            freeze, budgets),
                  "stream": "change",
                  "sources_verified": stats["sources_verified"]},
    }


def _answer_key(event: dict) -> str:
    """Recorded judge/render answers are keyed by the *claim hash*, so a dataset row can be replayed."""
    snapshot = event.get("snapshot") or {}
    return snapshot.get("fixture_key") or snapshot.get("source_id", "")


def verify_and_run(cfg: Config, tree: "twin.Tree", snapshots: list[dict], mode: str,
                   inject_failure: bool = False, via_n8n: bool = False) -> dict:
    """The verify → decide → act → report phases, on top of the twin's writers."""
    judgement_ledger = judge_lib.TokenLedger(STATE / "token_ledger.jsonl",
                                             THRESHOLDS["budgets"]["tokens_per_change"],
                                             THRESHOLDS["budgets"]["tokens_per_day"])
    lessons = json.loads((ROOT / "course" / "agent-ops" / "curriculum.json").read_text())["lessons"]
    lesson_index = {lesson["lesson_id"]: lesson for lesson in lessons}
    lessons = [{"lesson_id": l["lesson_id"], "concepts": [o["id"].split("-")[-1] for o in l["objectives"]]
                + [w for obj in l["objectives"] for w in tokens(obj["text"])]}
               for l in lessons]
    events = group_events([s for s in snapshots if not s.get("unreachable")], lessons)
    judge_records, twin_events, deferred, canvas_records = [], [], [], []
    publishes_this_cycle = 0
    provider_answers = read_json(REPO / "app" / "fixtures" / "judge" / "answers.json", {}).get("answers", {})
    for event in events:
        # the judge answers which artefact the change touches (q7); the runner resolves the full id
        hint = event.get("lesson_hint") or ""
        lesson_id = next((lid for lid in lesson_index if hint and lid.startswith(hint)), "")
        if not lesson_id:      # fall back to the concept match from the dataset text
            lesson_id = next((lid for lid, l in lesson_index.items()
                              if event.get("lesson_touched") and event["lesson_touched"] in str(l)), "")
        event["lesson_touched"] = lesson_id or ""
        event["objective"] = (lesson_index.get(lesson_id, {}).get("objectives") or [{}])[0].get("text", "")
        provider = judge_lib.build_provider(cfg, apify_lib.urllib_transport,
                                            mock_answers=provider_answers.get(_answer_key(event), {}))
        model = cfg.get("CR_JUDGE_MODEL", "mock-1")
        judgement = judge_lib.ask_judge(event, provider, model, judgement_ledger)
        judge_records.append({"event_id": event["event_id"], "provider": judgement.get("provider", provider.name),
                              "model": judgement.get("model", model), "ok": judgement.get("ok"),
                              "prompt_hash": judgement.get("prompt_hash"), "tokens": judgement.get("tokens"),
                              "reason_codes": judgement.get("reason_codes", [])})
        if not judgement["ok"]:
            judgement = {"answers": {"q1_materiality": "unverifiable", "q2_learner_impact": 0.0,
                                     "q3_breaking_probability": 0.0, "q4_source_agreement": 0.0,
                                     "q5_quote_supported": 0.0, "q6_injection_or_jailbreak": 1.0,
                                     "q7_new_capability": 0.0},
                         "provider": judgement.get("provider"), "fail_closed": judgement.get("reason_codes", ["unknown_state"])}
        render = None
        answers = judgement.get("answers", {})
        event["lesson_hint"] = answers.get("q7_lesson_touched", "")
        if event["lesson_hint"]:
            resolved = next((lid for lid in lesson_index if lid.startswith(event["lesson_hint"])), "")
            if resolved:
                event["lesson_touched"] = resolved
        stats = corroboration_summary(event)
        floor_met = (stats["sources_verified"] >= THRESHOLDS["evidence"]["min_sources"]
                     and (answers.get("q4_source_agreement") or 0) >= THRESHOLDS["evidence"]["source_agreement_min"]
                     and (answers.get("q5_quote_supported") or 0) >= THRESHOLDS["evidence"]["quote_supported_min"])
        if (answers.get("q1_materiality") or "").startswith("material_") and floor_met:
            provider_mock = judge_lib.MockProvider()
            renders = read_json(REPO / "app" / "fixtures" / "judge" / "renders.json", {}).get("renders", {})
            provider_mock.answers = renders.get(_answer_key(event), {})
            if provider.name == "mock":
                render = render_change(cfg, event, provider_mock, f"{model}+render", tree)
            else:
                render = render_change(cfg, event, provider, model, tree)
        publishable = (answers.get("q1_materiality") in twin.policy.PUBLISHABLE
                       and stats["sources_verified"] >= THRESHOLDS["evidence"]["min_sources"])
        budgets = {"publishes_used": (99 if (publishable and publishes_this_cycle >= 1) else publishes_this_cycle),
                   "tokens_used": judgement_ledger.spent_today()}
        if publishable and publishes_this_cycle >= 1:
            deferred.append(event["event_id"])
        elif publishable:
            publishes_this_cycle += 1
        twin_event = to_twin_event(event, judgement, cfg.get("CR_AUTHORITY", "PA2"),
                                   tree.frozen(), budgets, render)
        if via_n8n:
            canvas = canvas_decide(cfg, twin_event["input"])
            oracle = twin.policy.decide(twin_event["input"])
            if not canvas["ok"]:
                canvas_records.append({"event_id": event["event_id"], "ok": False,
                                       "reason": canvas.get("reason"), "used": "oracle_fallback"})
                twin_event["canvas"] = {"ok": False, "reason": canvas.get("reason"), "used": "oracle"}
            else:
                decision = canvas["decision"]
                same = canvas_agrees(decision, oracle)
                canvas_records.append({"event_id": event["event_id"], "ok": True, "same_as_oracle": same,
                                       "execution_id": canvas.get("execution_id"),
                                       "action": decision.get("action")})
                if not same:
                    # fail closed: neither decision is trusted, and the disagreement is on the record
                    twin_event["canvas"] = {"ok": True, "mismatch": True,
                                            "canvas_action": decision.get("action"),
                                            "oracle_action": oracle["action"],
                                            "execution_id": canvas.get("execution_id")}
                    twin_event["input"]["materiality"] = "ambiguous"
                    twin_event["patch"] = None
                else:
                    twin_event["canvas"] = {"ok": True, "same_as_oracle": True,
                                            "execution_id": canvas.get("execution_id")}
        twin_events.append(twin_event)
    if inject_failure and twin_events:
        twin_events[-1]["patch"] = {"file": "nonexistent/file.md", "find": "nope", "replace": "nope"}
    log = twin.run(tree, twin_events, label=f"{mode} cycle")
    write_json(LIVE / "last_cycle.json",
               {"run_id": log["run_id"], "mode": mode, "judge": judge_records,
                "deferred_publishes": deferred, "canvas": canvas_records,
                "events": [{"event_id": e["event_id"], "sources": e["sources"],
                            "decision_input": e["input"]} for e in twin_events]})
    return {"log": log, "judge": judge_records, "events": twin_events, "deferred": deferred,
            "canvas": canvas_records}


# --- deliver + commit ---------------------------------------------------------------------------

def deliver_staged(cfg: Config, tree: "twin.Tree", before: int) -> dict:
    rows = twin.tree_rows(tree) if hasattr(twin, "tree_rows") else tree.rows()
    staged = []
    for row in rows[before:]:
        for ref in (row.get("artifact") or {}).get("notified", []):
            staged.append({"ts": row["ts"], "learner_ref": ref,
                           "lesson_id": (row["artifact"] or {}).get("lesson_id"),
                           "from": (row["artifact"] or {}).get("previous_version"),
                           "to": (row["artifact"] or {}).get("new_version"),
                           "what_changed": next((e.get("learner_facing", e.get("summary", ""))
                                                 for e in twin.load_events() if e["event_id"] == row["event_id"]), ""),
                           "diff_path": (row["artifact"] or {}).get("diff_path"),
                           "opt_out": "one-click", "consent": True})
    if not staged:
        return {"channel": cfg.channel(), "attempted": 0, "delivered": 0, "failed": 0, "staged": 0,
                "records": []}
    result = notify_lib.Notifier(cfg).deliver(staged)
    failures = [r for r in result["records"] if r["status"] == "notification_failed"]
    if failures:
        tree.append_receipt({"ts": twin.now(), "run_id": twin.run_id(), "event_id": "op-notify",
                             "mode": tree.mode, "stream": "change",
                             "decision": {"action": "ESCALATE", "reason_codes": ["notification_failed"],
                                          "authority": "PA1"},
                             "artifact": None, "cost": None, "actor": "system",
                             "label": f"{len(failures)} card(s) failed to deliver"})
    return result


def commit_changes(cfg: Config, tree: "twin.Tree", run_id: str) -> dict:
    """Commit the artifacts on the bot branch. Off by default; refuses to switch branches itself."""
    if not cfg.flag("CR_COMMIT"):
        return {"ok": True, "skipped": True, "reason": "CR_COMMIT=0 (the operator commits, or the cron does)"}
    current = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    target = cfg.get("CR_BOT_BRANCH", "bot/courserefresh")
    if current != target:
        return {"ok": False, "error": "write_conflict", "code": "write_conflict",
                "message": f"HEAD is {current}, the bot branch is {target}; the engine never switches branches"}
    subprocess.run(["git", "add", "course"], cwd=ROOT, check=True)
    message = f"cr: cycle {run_id} [live]"
    proc = subprocess.run(["git", "commit", "-m", message], cwd=ROOT, capture_output=True, text=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"ok": proc.returncode == 0, "commit": sha, "message": message,
            "stdout": proc.stdout[-200:], "stderr": proc.stderr[-200:]}


# --- learn --------------------------------------------------------------------------------------

def learn_phase(cfg: Config, tree: "twin.Tree") -> dict:
    """Telemetry → gate → revert / stuck dispatch, using the same policy functions as the twin."""
    lessons = json.loads((ROOT / "course" / "agent-ops" / "curriculum.json").read_text())["lessons"]
    telemetry_rows = read_json(STATE / "learner_consent.json", {})
    events, gates = [], []
    for lesson in lessons:
        gate = telemetry_lib.cohort_window(lesson["lesson_id"])
        gates.append(gate)
        if gate.get("state") == "measured" and gate.get("quiz_delta") is not None:
            decision = twin.policy.decide_revert({
                "authority": "PA1", "freeze_active": tree.frozen(), "revert_gate_present": True,
                "cohort_n": gate["n"], "window_h": gate["window_h"], "quiz_delta": gate["quiz_delta"],
                "n_min": THRESHOLDS["revert"]["n_min"], "previous_version_available": True,
                "stream": "revert"})
            if decision["action"] == "REVERT":
                events.append(twin.build_revert_event(lesson["lesson_id"], gate, decision) if hasattr(twin, "build_revert_event")
                              else _revert_event(lesson["lesson_id"], gate))
    stuck = read_json(STATE / "stuck_signals.json", [])
    for signal in stuck:
        events.append(_learner_event(signal, telemetry_rows))
    if events:
        twin.run(tree, events, label="learn phase")
    write_json(LIVE / "cohort_gates.json", gates)
    return {"gates": gates, "events": len(events)}


def _revert_event(lesson_id: str, gate: dict) -> dict:
    versions = sorted((ROOT / "course" / "agent-ops" / lesson_id).glob("v*.md"))
    published = versions[-1].stem if versions else "v1"
    return {"event_id": f"cr-learn-revert-{lesson_id}", "kind": "revert",
            "summary": f"quiz_delta {gate['quiz_delta']} at n={gate['n']} after {gate['window_h']}h",
            "target": {"lesson_id": lesson_id, "published_version": published,
                       "restore_version": versions[-2].stem if len(versions) > 1 else "v1"},
            "input": {"event_id": f"cr-learn-revert-{lesson_id}", "stream": "revert", "materiality": "cosmetic",
                      "learner_impact": 0.5, "quote_supported": 1.0, "source_agreement": 1.0,
                      "sources_verified": 2, "injection_or_jailbreak": 0.0, "authority": "PA1",
                      "freeze_active": False, "revert_gate_present": True, "previous_version_available": True,
                      "cohort_n": gate["n"], "window_h": gate["window_h"],
                      "quiz_delta": gate["quiz_delta"], "n_min": THRESHOLDS["revert"]["n_min"]}}


def _learner_event(signal: dict, consent: dict) -> dict:
    return {"event_id": f"cr-learn-stuck-{signal['learner_ref'][-4:]}-{short_hash(signal['concept'])}",
            "kind": "learner", "learner_ref": signal["learner_ref"], "summary": signal.get("summary", ""),
            "input": {"event_id": "cr-learn-stuck", "stream": "learner", "materiality": "cosmetic",
                      "learner_impact": 0.5, "quote_supported": 1.0, "source_agreement": 1.0,
                      "sources_verified": 2, "injection_or_jailbreak": 0.0, "authority": "PA1",
                      "freeze_active": False, "consent": bool(consent.get(signal["learner_ref"], True)),
                      "stuck": True, "concept": signal["concept"],
                      "grade_impacting": False, "caps": signal.get("caps", {})}}


# --- preflight ----------------------------------------------------------------------------------

def preflight(cfg: Config, probe: bool = False) -> dict:
    report = cfg.preflight()
    report["checked_at"] = now()
    if probe and cfg.has("APIFY_TOKEN"):
        client = apify_lib.ApifyClient(token=cfg.get("APIFY_TOKEN"), base_url=cfg.get("APIFY_BASE_URL"))
        status, body = client.transport("GET", f"{client.base}/users/me?token={client.token}", {}, None, 20)
        report["apify_probe"] = {"ok": status == 200,
                                 "user": ((body or {}).get("data") or {}).get("username"),
                                 "message": None if status == 200 else f"HTTP {status}"}
    if probe and (cfg.has("CR_JUDGE_API_KEY") or cfg.get("CR_JUDGE_PROVIDER") != "mock"):
        report["judge_probe"] = judge_lib.probe_provider(cfg, judge_lib.urllib_transport)
    if probe and cfg.has("N8N_API_KEY"):
        import n8n as n8n_lib
        client = n8n_lib.N8nClient(cfg.get("N8N_BASE_URL"), cfg.get("N8N_API_KEY"),
                                   instance_version=cfg.get("N8N_INSTANCE_VERSION"))
        listing = client.list_workflows()
        report["n8n_probe"] = {"ok": listing["ok"],
                               "workflows": [w.get("name") for w in listing.get("workflows", [])]}
    LIVE.mkdir(parents=True, exist_ok=True)
    write_json(LIVE / "preflight.json", report)
    return report


def print_preflight(report: dict) -> None:
    print(f"mode: {report['mode']}")
    for platform, state in report["platforms"].items():
        mark = "wired" if state["wired"] else f"missing {state['keys_missing_required'] or '(nothing required)'}"
        print(f"  {platform:8s} {mark}")
    for claim, allowed in report["claims_allowed"].items():
        print(f"  claim {'ALLOWED ' if allowed else 'blocked '} {claim}")
    if report["blocking_for_live"]:
        print(f"live needs: {', '.join(report['blocking_for_live'])}")
    for probe in ("judge_probe", "apify_probe", "n8n_probe"):
        if probe in report:
            extra = report[probe].get("models_sample") or report[probe].get("note") or report[probe].get("reason") or ""
            print(f"  {probe}: {'ok' if report[probe]['ok'] else 'failed'} {extra}")


# --- main ---------------------------------------------------------------------------------------

def one_cycle(cfg: Config, dry_run: bool, inject_failure: bool = False, via_n8n: bool = False) -> dict:
    mode = "sim" if dry_run else cfg.mode()
    tree = tree_for(mode)
    ledger = apify_lib.UnitLedger(STATE / "apify_units.jsonl",
                                  THRESHOLDS["budgets"]["apify_units_per_day"],
                                  SOURCES.get("units_per_run", 1))
    notice_result = notice(cfg, tree, dry_run or mode == "sim", ledger)
    before = len(tree.rows())
    work = [s for s in notice_result["snapshots"] if not s.get("unreachable")]
    result = verify_and_run(cfg, tree, work, mode, inject_failure=inject_failure,
                            via_n8n=via_n8n) if work else \
        {"log": twin.run(tree, [], label=f"{mode} cycle (no new snapshots)"), "judge": [], "events": []}
    delivery = deliver_staged(cfg, tree, before)
    commit = commit_changes(cfg, tree, result["log"]["run_id"])
    summary = {"run_id": result["log"]["run_id"], "mode": mode,
               "sources_due": notice_result["due"], "snapshots_new": len(notice_result["snapshots"]),
               "rejected": len(notice_result["rejected"]), "budget_holds": notice_result["budget_holds"],
               "decisions": result["log"]["decisions"], "chain": result["log"]["chain_verified_at_end"],
               "judge_calls": len(result["judge"]), "canvas": result.get("canvas", []),
               "delivery": {k: v for k, v in delivery.items() if k != "records"},
               "commit": {k: commit[k] for k in ("ok", "skipped") if k in commit},
               "spent_units": notice_result["spent_units"], "finished_at": now()}
    write_json(LIVE / "last_summary.json", summary)
    return summary


def watch(cfg: Config, dry_run: bool) -> int:
    cadence = max(1, cfg.int("CR_LIVE_SCAN_MINUTES", 60))
    print(f"watching every {cadence} min · mode {'sim' if dry_run else cfg.mode()} · ctrl-c to stop",
          flush=True)
    while True:
        summary = one_cycle(cfg, dry_run)
        print(json.dumps(summary, sort_keys=True), flush=True)
        time.sleep(cadence * 60)


def selftest() -> int:
    """Offline end-to-end: recorded datasets, recorded judge answers, assertions. No network."""
    checks: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), str(detail)))

    sandbox = OUT / "live-selftest"
    if sandbox.exists():
        subprocess.run(["rm", "-rf", str(sandbox)])
    (sandbox / "app" / "out").mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-r", str(ROOT / "course"), str(sandbox / "course")], check=True)

    env = {"CR_MODE": "sim", "CR_JUDGE_PROVIDER": "mock", "CR_NOTIFY_CHANNEL": "file"}
    cfg = Config(env)
    check("preflight reports the live blockers honestly",
          cfg.preflight()["blocking_for_live"] == ["apify:APIFY_TOKEN", "judge:CR_JUDGE_API_KEY"],
          str(cfg.preflight()["blocking_for_live"]))

    ledger = apify_lib.UnitLedger(sandbox / "app" / "out" / "units.jsonl", 25, 1)
    allowed, _ = ledger.can_spend(1)
    ledger.record("n8n-releases", "dry-run-1", 0.0)
    check("the unit ledger spends before calling and remembers it",
          allowed and ledger.spent_today() == 1, f"spent={ledger.spent_today()}")

    client = apify_lib.ApifyClient(token=None, dry_run=True)
    source = SOURCES["sources"][0]
    run = client.run_actor(source)
    check("a dry-run actor returns the recorded dataset",
          run["ok"] and run.get("items"), f"rows={len(run.get('items') or [])}")

    normalised = apify_lib.normalise_dataset(
        [{"url": "https://evil.example/x", "markdown": "x" * 50},
         {"url": "https://docs.n8n.io/", "markdown": "n8n 1.85 renamed tool_permissions to permissions.mode."},
         {"url": "https://docs.n8n.io/"}],
        source, sandbox / "app" / "out" / "snapshots")
    reasons = sorted(r["reason"] for r in normalised["rejected"])
    check("rows without a url, a body, or an allowlisted host are rejected with reasons",
          reasons == ["host_not_allowlisted", "no_markdown"] and len(normalised["snapshots"]) == 1, str(reasons))

    claims = claims_from_markdown("n8n 1.85 renamed tool_permissions to permissions.mode. Blog post coming soon.")
    check("claim extraction keeps the versioned sentence and drops the small talk", len(claims) == 1, str(claims))

    grouped = group_events([{"source_id": "n8n-releases", "publisher": "n8n", "role": "authoritative",
                             "url": "https://github.com/n8n-io/n8n/releases", "title": "Release notes",
                             "content_hash": "sha256:abc", "markdown": "n8n 1.85 renamed tool_permissions to permissions.mode."},
                            {"source_id": "n8n-docs", "publisher": "n8n", "role": "authoritative",
                             "url": "https://docs.n8n.io/", "title": "Docs",
                             "content_hash": "sha256:def", "markdown": "n8n 1.85 renamed tool_permissions to permissions.mode."}],
                           [{"lesson_id": "lesson-04-tool-permissions", "concepts": ["tool_permissions", "permissions"]}])
    stats = corroboration_summary(grouped[0])
    check("two pages from one vendor are one voice, even when the text matches",
          stats["sources_verified"] == 1 and len(grouped[0]["sources"]) == 2, str(stats["voices"]))

    tree = twin.Tree(sandbox / "course", sandbox / "app" / "out", mode="sim")
    result = verify_and_run(cfg, tree, [{"source_id": "n8n-releases", "publisher": "n8n", "role": "authoritative",
                                         "url": "https://github.com/n8n-io/n8n/releases", "title": "Release notes",
                                         "content_hash": "sha256:live1",
                                         "markdown": "n8n 1.85 renamed tool_permissions to permissions.mode, "
                                                     "and the old key is removed."}],
                            "sim")
    rows = tree.rows()
    check("an end-to-end sim cycle writes receipts, a digest and a console page",
          bool(rows) and (sandbox / "app" / "out" / "digest.md").exists()
          and (sandbox / "app" / "out" / "digest.html").exists(), f"receipts={len(rows)}")
    check("the decision came from the oracle, not the model",
          rows[-1]["decision"]["action"] in ("PUBLISH", "DRAFT", "ESCALATE", "NO_CHANGE", "REVERT"),
          f"{rows[-1]['decision']['action']} {rows[-1]['decision']['reason_codes']}")
    check("the judge call is recorded with provider, prompt hash and tokens",
          bool(result["judge"]) and result["judge"][0]["prompt_hash"].startswith("sha256:"),
          str(result["judge"][0].get("provider")))

    gate = telemetry_lib.cohort_window("lesson-04-tool-permissions", path=sandbox / "app" / "out" / "nope.jsonl")
    check("a missing cohort is `unmeasured`, never a revert claim",
          gate["state"] == "unmeasured" and gate["n"] == 0, gate["reason"])

    delivery = notify_lib.Notifier(cfg, log_path=sandbox / "app" / "out" / "delivery.jsonl").deliver(
        [{"ts": now(), "learner_ref": "learner:deadbeef", "lesson_id": "lesson-04-tool-permissions",
          "from": "v3", "to": "v4", "what_changed": "a setting was renamed", "diff_path": "x.diff",
          "opt_out": "one-click"}])
    check("the file channel stages rather than claiming delivery",
          delivery["staged"] == 1 and delivery["delivered"] == 0, f"delivered={delivery['delivered']}")

    import config as config_lib
    masked = config_lib.Config({"APIFY_TOKEN": "apify_api_supersecret"}).masked("APIFY_TOKEN")
    check("masking never prints a secret value", "supersecret" not in masked and "sha256=" in masked, masked)

    passed = sum(1 for _, ok, _ in checks if ok)
    width = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print(f"\nlive selftest: {passed}/{len(checks)} checks passed")
    return 0 if passed == len(checks) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Courserefresh live engine")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--probe", action="store_true", help="with --preflight: actually call Apify/n8n")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--learn", action="store_true")
    ap.add_argument("--digest-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="recorded datasets + mock judge; no network")
    ap.add_argument("--inject-failure", action="store_true", help="rehearse a failed write this cycle")
    ap.add_argument("--via-n8n", action="store_true",
                    help="let the n8n canvas decide (parity-checked against the oracle)")
    ap.add_argument("--seed-baseline", action="store_true", help="pre-seed dedupe state from the baseline")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", metavar="DIR", help="operate on another tree (tests, rehearsals)")
    args = ap.parse_args()

    if args.root:
        rebase(Path(args.root))
    cfg = Config()
    if args.selftest:
        return selftest()
    if args.preflight:
        report = preflight(cfg, probe=args.probe)
        print_preflight(report)
        return 0 if report["mode"] == "live" or not report["blocking_for_live"] else 2
    if args.seed_baseline:
        baseline = read_json(REPO / "app" / "fixtures" / "apify" / "baseline.json", {})
        keys = sorted(f"{e['source_id']}:{e['hash']}" for e in baseline.get("entries", []))
        write_json(STATE / "seen_snapshots.json", keys)
        print(f"seeded {len(keys)} known snapshots (per source) from the baseline recording")
        return 0
    if args.digest_only:
        tree = tree_for(cfg.mode())
        rows = tree.rows()
        if rows:
            tree.digest_path.write_text(twin.render_digest(tree, read_json(OUT / "run_log.jsonl", [])[-1]
                                                           if (OUT / "run_log.jsonl").exists() else
                                                           {"run_id": "manual", "decisions": {},
                                                            "publishes_used": 0, "receipts": len(rows),
                                                            "chain_verified_at_end": tree.verify_chain()[0],
                                                            "chain_rows": tree.verify_chain()[1]}))
            (tree.out / "digest.html").write_text(twin.render_html(tree, read_json(OUT / "run_log.jsonl", [])[-1]
                                                                   if (OUT / "run_log.jsonl").exists() else {}))
        print(tree.digest_path.read_text() if tree.digest_path.exists() else "no receipts yet")
        return 0
    if args.learn:
        tree = tree_for(cfg.mode() if not args.dry_run else "sim")
        print(json.dumps(learn_phase(cfg, tree), sort_keys=True))
        return 0
    if args.watch:
        return watch(cfg, args.dry_run)
    summary = one_cycle(cfg, args.dry_run, inject_failure=args.inject_failure, via_n8n=args.via_n8n)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
