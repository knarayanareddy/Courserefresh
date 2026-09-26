#!/usr/bin/env python3
"""The Teacher/Author canvas — what changed, on whose word, and how sure the system is (Art. VI, IX).

The loop already refuses to publish on one voice, writes a receipt for every decision and chains
them. What a teacher could not see, until this file existed, is the part they are actually asked to
trust: *the lesson somebody changed for them*, the sources that carried each change, the reason codes
in plain language, and — the honest part nobody usually ships — where the decision was fragile.

Three sources of "how sure", none of them invented:

  1. **JEV's own confidences.** When the decision came from a typed-decision provider
     (`CR_JUDGE_PROVIDER=jev`), every answer arrives with its probability or its choice confidence and
     it is printed per question. A chat model reports nothing, and the canvas says `unmeasured`
     instead of faking a number (Art. VI: no number without a receipt).
  2. **The flip analysis.** The answers are replayed through the *oracle itself*, nudged one question
     at a time (± `CANVAS.flip_delta`). If a nudge changes the action or the reason codes, the canvas
     names the direction and the value where the decision turns over: "at q3 ≥ 0.62 this would have
     been `ESCALATE(quote_unsupported)`". That is a fact about the rulebook, not a model's opinion of
     its own work, and it is the same computation for every provider.
  3. **The disagreement record.** A canvas/oracle mismatch (`canvas.mismatch`), a fail-closed
     judgement (`unknown_state`), a budget refusal, or an off-allowlist host: each is a reason to look,
     and each is already on a receipt.

`needs_review` is deliberately *not* "below 0.7". It is: the decision is fragile, or the provider was
unsure, or the two rulebooks disagreed, or the loop could not verify something. A teacher's queue
should be short and each entry should be arguable.

Output surfaces: `app/out/canvas.json` (the machine view), `app/out/canvas.html` (the reading view,
served by `app/lib/console.py` at `/canvas`), and a line in the digest so the queue is not a silo.

Run: python3 app/lib/canvas.py [--root DIR] [--receipts PATH] [--course PATH] [--out PATH] [--json]
Defaults are the run in `app/out/` (`--receipts app/out/receipts.jsonl`, `--course course/`), which is
what the console serves; pass `--root` to read a different run (the tests do). `--json` prints the
machine view to stdout instead of writing `canvas.json` next to `--out`.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIN = ROOT / "specs" / "courserefresh" / "skin"
if str(SKIN) not in sys.path:
    sys.path.insert(0, str(SKIN))
import policy  # noqa: E402  (the closed sets the ruling form offers)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rulings as rulings_lib  # noqa: E402  (D-32: is the ruling still describing the world?)
SKIN = ROOT / "specs" / "courserefresh" / "skin"
sys.path.insert(0, str(SKIN))
import policy  # noqa: E402  (the oracle — the flip analysis must use the same rulebook as the loop)

THRESHOLDS = json.loads((SKIN / "thresholds.json").read_text())
EVIDENCE = THRESHOLDS["evidence"]

# The questions the oracle actually reads as numbers, and the input field each one lands in.
# Only these can be nudged: a flip analysis on a field the oracle ignores would be theatre.
NUMERIC_INPUTS = {"q2_learner_impact": "learner_impact", "q3_breaking_probability": "breaking_probability",
                  "q4_source_agreement": "source_agreement", "q5_quote_supported": "quote_supported",
                  "q6_injection_or_jailbreak": "injection_or_jailbreak"}

# Every reason code in `skin/policy.py` → the sentence a teacher reads. The set is closed; a code
# that is not in this table renders as the identifier itself rather than a made-up explanation, and
# `test_live_modules.py` fails if the rulebook gains a code this table does not cover.
STR_STALE = " stale"

REASON_PLAIN = {
    # why a change was published
    "material_breaking": "a breaking change the lesson still teaches as current",
    "material_deprecation": "a deprecation with a deadline the lesson does not mention",
    "material_new_capability": "a new capability that changes what the lesson should recommend",
    # why a person published it (D-32: an author may lift an evidence-class refusal; nothing else)
    "human_signoff": "an author reviewed the evidence and approved this change themselves",
    # why a change was refused
    "insufficient_corroboration": "fewer than two independent publishers carry the same fact",
    "quote_unsupported": "the claim is not fully supported by the verbatim quotes supplied",
    "source_conflict": "the publishers disagree about the same fact",
    "source_stale": "the source returned something other than what it promised",
    "unverifiable": "the change could not be verified against the sources",
    "ambiguous_change": "it is not clear what kind of change this is",
    "fallback_used": "only the declared fallback answered, not the primary source",
    "injection_or_jailbreak": "the text tried to instruct the system instead of informing it",
    "immaterial_change": "real, but it changes nothing the lesson teaches",
    "low_learner_impact": "too little risk of a learner acting on something now wrong",
    "no_signal": "nothing in the telemetry rises to a signal",
    "no_delta": "nothing new since the last scan",
    "noop_already_applied": "the lesson already says this",
    "diff_too_wide": "the rewrite changes more of the lesson than the change justifies",
    "previous_version_missing": "the version this would revert to is not in the tree",
    # budgets, cadence, freeze
    "budget_hold": "a daily budget was reached before this could be acted on",
    "over_budget": "a token budget was reached before the decision",
    "rate_limited": "a cadence or credit cap held this back",
    "cadence_degraded": "the source was scanned later than its cadence promises",
    "freeze_active": "the kill switch was engaged",
    "write_failed": "a write failed mid-cycle; the run did not pretend it succeeded",
    # learners
    "consent_missing": "no consent on record, so nothing was sent",
    "consent_revoked": "the learner withdrew consent",
    "stuck_signals_met": "the learner's own telemetry says they are stuck",
    "assessment_change_requires_human": "this changes what is assessed: a human's call by rule",
    "grade_impacting_requires_human": "this affects grades: a human's call by rule",
    "authority_insufficient": "the run's authority level does not cover this action",
    # reverts and measurement
    "revert_gate_satisfied": "the cohort's measured quiz delta says the rewrite did not help",
    "revert_gate_absent": "no revert gate was declared for this version",
    "cohort_below_minimum": "too few learners to measure the rewrite yet",
    "gate_window_open": "the measurement window has not closed: too early to judge the rewrite",
    "measurement_incomplete": "the measurement is incomplete",
    "no_improvement_measured": "the measured effect is not an improvement",
    "integrity_floor_missing_gate": "a lesson with no measurement gate cannot be reverted",
    # the judge itself
    "unknown_state": "the judge did not answer inside the closed question set — refused, never guessed",
    # labelled rehearsals
    "seeded_rehearsal": "a labelled rehearsal, not a vendor release",
    "seeded_source_misrepresented": "a rehearsal that claimed upstream sources — refused",
}

# Which refusals a teacher can actually unblock, and which the rulebook has already assigned to a
# human. The distinction is the difference between a queue someone reads and a queue someone closes.
REVIEW_BECAUSE_MISSING = {
    "insufficient_corroboration": "a second independent publisher carrying the same fact would unblock it",
    "quote_unsupported": "a verbatim quote that states the new behaviour would unblock it",
    "source_conflict": "a decision about which publisher to believe is a human's call",
    "source_stale": "the source has to return what it promises before this can be decided",
    "unverifiable": "the claim needs a verifiable source",
    "ambiguous_change": "a human has to say what kind of change this is",
    "fallback_used": "the primary source has to answer, not the fallback",
    "measurement_incomplete": "the measurement has to complete",
    "revert_gate_absent": "a revert gate has to be declared for the version",
    "cohort_below_minimum": "the cohort has to reach the minimum size",
    "gate_window_open": "the window has to close before the rewrite can be judged",
    "previous_version_missing": "the version to revert to has to be in the tree",
    "no_signal": "no learner action is needed until the telemetry says otherwise",
}
REVIEW_BECAUSE_HUMAN = {
    "assessment_change_requires_human": "this changes what is assessed, which is a human's call",
    "grade_impacting_requires_human": "this affects grades, which is a human's call",
    "authority_insufficient": "the run's authority level needs raising for this action",
}


def _plain(reason: str) -> str:
    return REASON_PLAIN.get(reason, reason.replace("_", " "))


def _stamp() -> str:
    """Wall-clock stamp for the page's provenance line (a runtime artifact, never a receipt field)."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y.%m.%dT%H:%M:%SZ")


def flip_analysis(inputs: dict, delta: float = 0.1, scan: float = 0.5,
                  step: float = 0.01) -> dict:
    """Which single answer would have changed the decision, how far away it is, and to what.

    The answers are replayed through `policy.decide` — the same rulebook the loop used — walking each
    numeric input outward until the action or the reason codes change. The distance to that turn-over
    is the margin: a decision that flips at 0.02 is a decision nobody should trust, and a decision
    that does not flip within 0.5 is robust at this resolution. `sources_verified` is walked as a
    count (±1, ±2), because "one more independent voice would have published this" is the single most
    useful sentence in a refusal queue.

    Returns {"baseline": {...}, "drivers": [...], "margin": float|None, "fragile": bool,
    "measured": bool}. Nothing here is a guess: no flip found inside the scan is reported as no flip.
    """
    required = ("event_id", "stream", "materiality", "learner_impact", "source_agreement",
                "quote_supported", "sources_verified", "injection_or_jailbreak", "authority",
                "freeze_active")
    missing = [f for f in required if f not in inputs]
    if missing:
        # an old receipt may predate a field; replaying a half-input would answer a different
        # question and call it confidence, so the canvas reports `unmeasured` instead (Art. VI)
        return {"baseline": {}, "drivers": [], "margin": None, "fragile": False,
                "measured": False, "missing": missing}
    baseline = policy.decide(inputs)
    drivers, margins = [], []
    steps = int(round(scan / step))
    for question, field in NUMERIC_INPUTS.items():
        value = inputs.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        found = None
        for sign in (1, -1):
            for i in range(1, steps + 1):
                nudge = round(min(1.0, max(0.0, value + sign * i * step)), 4)
                if nudge == value:
                    break
                verdict = policy.decide({**inputs, field: nudge})
                if (verdict["action"] != baseline["action"]
                        or sorted(verdict["reason_codes"]) != sorted(baseline["reason_codes"])):
                    found = {"question": question, "field": field, "from": value, "to": nudge,
                             "delta": round(i * step, 3), "direction": "up" if sign > 0 else "down",
                             "becomes": verdict["action"], "reason_codes": verdict["reason_codes"],
                             "note": f"{field} {value}→{nudge} (Δ{round(i * step, 3)}): "
                                     f"{verdict['action']}({', '.join(verdict['reason_codes'])})"}
                    break
            if found:
                break
        if found:
            drivers.append(found)
            margins.append(found["delta"])
    count = inputs.get("sources_verified")
    if isinstance(count, int) and not isinstance(count, bool):
        for nudge in (count + 1, count - 1, count + 2):
            if nudge < 0:
                continue
            verdict = policy.decide({**inputs, "sources_verified": nudge})
            if (verdict["action"] != baseline["action"]
                    or sorted(verdict["reason_codes"]) != sorted(baseline["reason_codes"])):
                delta_count = abs(nudge - count)
                drivers.append({"question": "sources_verified", "field": "sources_verified",
                                "kind": "answer_perturbation",
                                "from": count, "to": nudge, "delta": delta_count,
                                "direction": "up" if nudge > count else "down",
                                "becomes": verdict["action"], "reason_codes": verdict["reason_codes"],
                                "note": f"{count}→{nudge} independent voice(s): "
                                        f"{verdict['action']}({', '.join(verdict['reason_codes'])})"})
                margins.append(float(delta_count))
                break
    # The counterfactual a refusal queue actually needs: the oracle counts *voices* from the source
    # list, so "what if a second independent publisher carried the same fact?" is answerable exactly.
    # The synthetic publisher is generated, labelled and never written anywhere — it is a question
    # about the rulebook ("what does this rule need?"), not a claim about the world.
    if "insufficient_corroboration" in baseline["reason_codes"]:
        existing = list(inputs.get("sources") or [])
        publishers = {str(s.get("publisher", "")).lower() for s in existing}
        for candidate in ("counterfactual-second-voice", "counterfactual-third-voice"):
            if candidate in publishers:
                continue
            trial_sources = existing + [{"publisher": candidate, "role": "corroborating",
                                         "url": "counterfactual://not-a-real-source"}]
            verdict = policy.decide({**inputs, "sources": trial_sources,
                                     "sources_verified": max(2, int(count or 0) + len(trial_sources) - len(existing))})
            if (verdict["action"] != baseline["action"]
                    or sorted(verdict["reason_codes"]) != sorted(baseline["reason_codes"])):
                drivers.append({"question": "sources", "field": "sources",
                                "kind": "counterfactual_evidence",
                                "from": len(existing), "to": len(trial_sources), "delta": 1.0,
                                "direction": "add", "becomes": verdict["action"],
                                "reason_codes": verdict["reason_codes"],
                                "note": "with one more independent publisher carrying the same fact: "
                                        f"{verdict['action']}({', '.join(verdict['reason_codes'])})"})
                break
    margin = min(margins) if margins else None
    drivers.sort(key=lambda d: d["delta"])
    return {"baseline": {"action": baseline["action"], "reason_codes": baseline["reason_codes"],
                         "authority": baseline["authority"]},
            "drivers": drivers, "margin": margin,
            # the interval every numeric answer was walked over, both directions, and the step: "no
            # flip found" is only a claim about *this* range, and the page prints it (panel C-06)
            "scan_low": round(max(0.0, min(margins) if False else scan), 3) if False else None,
            "scan_span": scan, "flip_step": step,
            "fragile": margin is not None and margin <= delta, "measured": True}


def confidence_for(row: dict) -> dict:
    """The row's confidence verdict: what the provider said, what the rulebook says, what is unknown.

    `needs_review` is not "below 0.7". It is: the decision turns over within a rounding error of the
    answers given, or the provider was unsure, or the two rulebooks disagreed, or the loop could not
    verify something. A queue that is short and arguable is the only kind anyone reads.
    """
    inputs = row.get("inputs") or {}
    confidences = (row.get("judge") or {}).get("confidences") or {}
    flip = flip_analysis(inputs)
    reasons = row["decision"].get("reason_codes") or []
    fail_closed = "unknown_state" in reasons
    mismatch = bool((row.get("canvas") or {}).get("mismatch"))
    numeric = [v for k, v in confidences.items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    provider_floor = min(numeric) if numeric else None
    # A refusal that hinges on missing evidence is the most actionable row a teacher can be shown:
    # the sentence is "go and get the second voice", not "the model was unsure". Those rows ask for a
    # human regardless of how wide the numeric margin is.
    missing_info = [r for r in reasons if r in REVIEW_BECAUSE_MISSING]
    human_class = [r for r in reasons if r in REVIEW_BECAUSE_HUMAN]
    review_because = []
    if fail_closed:
        review_because.append("the judge did not answer inside the closed question set")
    if mismatch:
        review_because.append("the canvas and the oracle disagreed on this event")
    review_because += [REVIEW_BECAUSE_MISSING[r] for r in missing_info]
    review_because += [REVIEW_BECAUSE_HUMAN[r] for r in human_class]
    if any(d.get("kind") == "counterfactual_evidence" for d in flip["drivers"]):
        review_because.append("a second independent publisher carrying the same fact would publish it")
    margin = flip["margin"]
    level = "high"
    if fail_closed or mismatch:
        level = "low"
    elif margin is not None and margin <= 0.02:
        level = "low"
    elif margin is not None and margin <= 0.10:
        level = "medium"
    if provider_floor is not None and provider_floor < 0.6:
        level = "low"
    if (missing_info or human_class) and level == "high":
        level = "medium"                       # a question for a human, not a fragile decision
    return {"level": level, "margin": margin, "provider_floor": provider_floor,
            "scan_span": flip.get("scan_span"), "flip_step": flip.get("flip_step"),
            "unmeasured_reason": ("receipt predates the recorded inputs: " +
                                  ", ".join(flip.get("missing", []))) if not flip.get("measured") and
                                 flip.get("missing") else None,
            "provider_confidences": confidences or None,
            "fragile": flip["fragile"], "flip_measured": flip["measured"],
            "flip_drivers": flip["drivers"], "baseline": flip["baseline"],
            "fail_closed": fail_closed, "canvas_mismatch": mismatch,
            "review_because": review_because,
            "needs_review": level != "high"}


def build(root: Path | None = None, receipts_path: Path | None = None,
          course: Path | None = None) -> dict:
    """One JSON document: every decision, its evidence, its plain-language reasons, its confidence."""
    root = (root or ROOT).resolve()
    receipts_path = receipts_path or (root / "app" / "out" / "receipts.jsonl")
    course = course or (root / "course")
    rows = [json.loads(l) for l in receipts_path.read_text().splitlines() if l.strip()] \
        if receipts_path.exists() else []
    decisions = []
    for row in rows:
        if row.get("event_id", "").startswith("op-"):
            continue                                  # console/kill-switch rows are operations, not lessons
        artifact = row.get("artifact") or {}
        judgement = row.get("judge") or {}
        answers = judgement.get("answers") or {}
        # the receipt carries the inputs the oracle actually read (`inputs`); the judge's answers are
        # a different shape (question ids) and are shown as evidence, never substituted for them
        inputs = dict(row.get("inputs") or {})
        inputs["sources"] = row.get("sources") or []
        sources = row.get("sources") or []
        voices = sorted({s.get("publisher") for s in sources
                         if s.get("role") not in set(EVIDENCE.get("discovery_roles", ["none"]))})
        item = {
            "receipt_id": row.get("receipt_id"), "ts": row.get("ts"), "run_id": row.get("run_id"),
            "event_id": row.get("event_id"), "label": row.get("label"),
            "mode": row.get("mode"), "stream": row.get("stream"),
            "decision": {"action": row["decision"].get("action"),
                         "reason_codes": row["decision"].get("reason_codes") or [],
                         "reasons_plain": [_plain(r) for r in (row["decision"].get("reason_codes") or [])],
                         "authority": row["decision"].get("authority"),
                         "decided_by": row["decision"].get("decided_by") or "oracle"},
            "actor": row.get("actor"),
            "lesson": {"lesson_id": artifact.get("lesson_id"),
                       "previous_version": artifact.get("previous_version"),
                       "new_version": artifact.get("new_version"),
                       "body_path": artifact.get("body_path"), "diff_path": artifact.get("diff_path"),
                       "quiz_item": artifact.get("quiz_item")},
            "sources": [{"publisher": s.get("publisher"), "role": s.get("role"),
                         "url": s.get("url"),
                         "counts_as_independent": s.get("role") not in
                         set(EVIDENCE.get("discovery_roles", ["none"]))} for s in sources],
            "voices": voices,
            "quotes": (row.get("quotes") or [])[:8],
            "inputs": inputs, "answers": answers,
            "judge": {"provider": judgement.get("provider"), "model": judgement.get("model"),
                      "fail_closed": judgement.get("fail_closed", False),
                      "confidences": judgement.get("confidences")},
            "canvas": row.get("canvas") or None,
            "cohort_source": row.get("cohort_source"),
            "ruling_basis": {"stream": row.get("stream"), "event_id": row.get("event_id"),
                             "inputs": row.get("inputs"), "sources": row.get("sources"),
                             "quotes": row.get("quotes")},
        }
        item["confidence"] = confidence_for(item)
        decisions.append(item)
    # the author's own rulings, read back: a queue that forgets what a person decided is a queue
    # somebody has to keep re-reading
    rulings: dict = {}
    by_event: dict = {}
    rulings_path = root / "app" / "out" / "state" / "author_decisions.jsonl"
    if rulings_path.exists():
        for line in rulings_path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rulings.setdefault(row.get("receipt_id"), []).append(row)
                if row.get("event_id"):
                    by_event.setdefault(row["event_id"], []).append(row)
    # A ruling has to be actionable to be worth offering: an evidence-class refusal whose withheld
    # delta still carries a proposed change can be approved (D-32); one that never had a patch (a
    # conflict is "we do not know which version to write") can only be closed. The form says so
    # rather than showing a button that would come back as an error.
    withheld = {row.get("event_id"): row for row in rulings_lib.load_pending(root / "app" / "out")}
    for item in decisions:
        codes = item["decision"]["reason_codes"]
        withheld_row = withheld.get(item["event_id"]) or {}
        item["review"] = {
            "approve": bool(codes) and all(c in rulings_lib.APPROVABLE for c in codes)
                       and bool(withheld_row.get("patch")),
            "reject": True,
            "why": ("there is nothing to publish: the refusal was about which publisher to believe, so "
                    "the loop never wrote a proposed change — close it, or add a second source"
                    if all(c in rulings_lib.APPROVABLE for c in codes) and withheld_row and
                    not withheld_row.get("patch") else
                    "" if all(c in rulings_lib.APPROVABLE for c in codes) else
                    "this refusal is not a judgement call: " + ", ".join(codes or ["(no codes)"])),
        }
    for item in decisions:
        # A ruling is about an *event*, not about the receipt that happened to record it: when the
        # loop re-decides the same event (an approval, a rescan), the person's call still shows, and
        # it shows as expired if the evidence moved underneath it.
        mine = rulings.get(item["receipt_id"]) or by_event.get(item["event_id"], [])
        item["author_decisions"] = [dict(r) for r in mine]
        # A ruling stops deciding anything the moment the evidence moves (D-32). The canvas says so
        # rather than leaving a settled-looking row the loop has already stopped honouring.
        for ruling in item["author_decisions"]:
            expired = rulings_lib.expired(ruling, item["ruling_basis"])
            ruling["expired"] = bool(expired)
            if expired:
                ruling["expired_why"] = expired["why"]

    verdict = {"total": len(decisions),
               "ruled_by_author": sum(1 for d in decisions if d.get("author_decisions")),
               "publishes": sum(1 for d in decisions if d["decision"]["action"] == "PUBLISH"),
               "refusals": sum(1 for d in decisions if d["decision"]["action"] == "ESCALATE"),
               "needs_review": [d["receipt_id"] for d in decisions
                                if d["confidence"]["needs_review"] and not d.get("author_decisions")]}
    # the diff is read here, not stored on the receipt: the course tree is where the truth lives.
    # The read cap is the page's budget, so the *size* of what was cut is recorded with it.
    for item in decisions:
        path = item["lesson"].get("diff_path")
        candidates = [Path(course) / path, Path(course) / "agent-ops" / path] if path else []
        found = next((c for c in candidates if c.exists()), None)
        item["diff"] = found.read_text()[:20000] if found else None
        item["diff_bytes"] = found.stat().st_size if found else None
        item["diff_path_shown"] = str(item["lesson"].get("diff_path") or "")
    runs = [json.loads(l) for l in (root / "app" / "out" / "run_log.jsonl").read_text().splitlines()
            if l.strip()] if (root / "app" / "out" / "run_log.jsonl").exists() else []
    provenance = {"run_id": (runs[-1].get("run_id") if runs else None),
                  "receipts": len(rows), "policy": policy.THRESHOLDS.get("version"),
                  "built_at": _stamp(), "mode": (runs[-1].get("mode") if runs else None)}
    return {"root": str(root), "decisions": decisions, "verdict": verdict, "provenance": provenance,
            # Art. VI: the provider's number is a prediction until a calibration record exists. The
            # canvas says `unmeasured` out loud rather than letting a reader assume it is accuracy.
            "calibration": "unmeasured",
            "unmeasured": [k for k in ("flip_analysis",) if not any(d["inputs"] for d in decisions)]}


def review_queue(receipts_path: Path, course: Path) -> list[dict]:
    """The rows a human should look at, with the sentence explaining why. Never raises.

    Used by the digest (so the queue is not a silo somebody has to remember to open) and by the
    console (which serves the full canvas page).
    """
    try:
        doc = build(root=receipts_path.parents[2] if len(receipts_path.parents) > 2 else receipts_path.parent,
                    receipts_path=receipts_path, course=course)
    except Exception:  # noqa: BLE001 - the digest must render even if the canvas cannot be built
        return []
    return [{"receipt_id": row["receipt_id"], "action": row["decision"]["action"],
             "lesson_id": row["lesson"].get("lesson_id"),
             "level": row["confidence"]["level"], "why": row["confidence"]["review_because"],
             "undecided": row["decision"].get("decided_by") != "author"}
            for row in doc["decisions"]
            if row["confidence"]["needs_review"]
            and not any(not d.get("expired") for d in row.get("author_decisions") or [])]


def render_html(doc: dict, action_url: str | None = None, token: str | None = None) -> str:
    """The reading view. No scripts, no external assets, refusals and review rows first.

    `action_url` turns the review rows into a form (D-32/C-02): the same surface a teacher reads is
    the surface they rule on, with `approve`/`reject`, the closed reason set, and an optional note —
    posted as a plain HTML form, so the page stays script-free. `token` is embedded only when the
    caller already proved it has one (the console decides that), and is omitted entirely for the
    read-only copy the CLI writes.
    """
    reason_options = "".join(f"<option value='{html.escape(c)}'>{html.escape(c)} — "
                             f"{html.escape(_plain(c))}</option>" for c in sorted(policy.REASON_CODES))
    css = """
    body{font-family:ui-sans-serif,system-ui,sans-serif;margin:2rem;color:#1c2130;max-width:78rem}
    h1{font-size:1.4rem} h2{font-size:1.05rem;margin-top:1.6rem}
    .row{border:1px solid #d7dbe6;border-radius:6px;padding:.8rem 1rem;margin:.7rem 0}
    .PUBLISH{border-left:5px solid #2f7d4f} .ESCALATE{border-left:5px solid #b4531f}
    .DISPATCH{border-left:5px solid #2b5fa8} .REVERT{border-left:5px solid #8a2f8a}
    .NO_CHANGE{border-left:5px solid #9aa2b1}
    .pill{display:inline-block;padding:.05rem .45rem;border-radius:999px;background:#eef1f7;
          margin-right:.3rem;font-size:.78rem}
    .review{background:#fff6e8;border-color:#e0a75e}
    code,pre{font-family:ui-monospace,monospace;font-size:.82rem;white-space:pre-wrap}
    table{border-collapse:collapse;width:100%} td,th{border-bottom:1px solid #e6e9f0;padding:.25rem .4rem;
          text-align:left;vertical-align:top;font-size:.87rem}
    .muted{color:#5b6376;font-size:.85rem} .why{margin:.35rem 0 .2rem}
    form.ruling{margin:.5rem 0 0;padding:.5rem .6rem;background:#f4f6fb;border:1px solid #ccd3e2;
                border-radius:5px;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
    form.ruling select,form.ruling input{font:inherit;font-size:.85rem;padding:.15rem .3rem}
    form.ruling button{font:inherit;font-size:.85rem;padding:.25rem .7rem;cursor:pointer}
    form.ruling button.reject{background:#fdeaea}
    .stale{background:#fdf0f0;border-color:#d98a8a}
    """
    prov = doc.get("provenance") or {}
    lines = ["<!doctype html>", "<html><head><meta charset='utf-8'>",
             "<title>Courserefresh — Teacher/Author canvas</title>", f"<style>{css}</style></head><body>",
             "<h1>Teacher/Author canvas</h1>",
             f"<p class='muted'>{doc['verdict']['total']} decisions · "
             f"{doc['verdict']['publishes']} published · {doc['verdict']['refusals']} refused · "
             f"{len(doc['verdict']['needs_review'])} want a human</p>",
             f"<p class='muted'>run {html.escape(str(prov.get('run_id')))} · "
             f"{prov.get('receipts')} receipts · policy {html.escape(str(prov.get('policy')))} · "
             f"built {html.escape(str(prov.get('built_at')))}</p>"]
    ordered = sorted(doc["decisions"], key=lambda d: (not d["confidence"]["needs_review"],
                                                      d["decision"]["action"] != "ESCALATE"))
    for item in ordered:
        d = item["decision"]
        klass = "row " + str(d["action"]) + (" review" if item["confidence"]["needs_review"] else "")
        lines.append(f"<div class='{klass}'>")
        lines.append(f"<b>{html.escape(str(d['action']))}</b> "
                     f"<span class='pill'>{html.escape(str(item['lesson'].get('lesson_id') or '—'))}</span>"
                     f"<span class='pill'>{html.escape(str(d['decided_by']))} · "
                     f"{html.escape(str(d['authority']))}</span>"
                     f"<span class='pill'>confidence: {html.escape(item['confidence']['level'])}</span>"
                     f"<div class='muted'>{html.escape(str(item['label'] or ''))} — "
                     f"{html.escape(str(item['ts'] or ''))} · {html.escape(str(item['receipt_id'] or ''))}</div>")
        lines.append("<div class='why'><b>Why:</b> " +
                     html.escape("; ".join(d["reasons_plain"]) or "no reason codes") + "</div>")
        if item["lesson"].get("new_version"):
            lines.append(f"<div class='why'><b>Change:</b> "
                         f"{html.escape(str(item['lesson']['previous_version']))} → "
                         f"{html.escape(str(item['lesson']['new_version']))} "
                         f"(<code>{html.escape(str(item['lesson'].get('diff_path') or ''))}</code>)</div>")
        if item["sources"]:
            rows = "".join(f"<tr><td>{html.escape(str(s['publisher']))}</td><td>{html.escape(str(s['role']))}</td>"
                           f"<td>{'counted' if s['counts_as_independent'] else 'not counted'}</td>"
                           f"<td><code>{html.escape(str(s['url'] or ''))}</code></td></tr>"
                           for s in item["sources"])
            lines.append(f"<table><tr><th>publisher</th><th>role</th><th>voice?</th><th>url</th></tr>{rows}</table>")
        if item["quotes"]:
            def quote_line(quote) -> str:
                if isinstance(quote, dict):
                    body, origin = quote.get("text", ""), quote.get("source_id") or ""
                else:
                    body, origin = str(quote), ""
                return (f"<li><code>{html.escape(str(body)[:220])}</code> "
                        f"<span class='muted'>{html.escape(str(origin))}</span></li>")
            lines.append("<div class='why'><b>Quotes:</b><ul>" + "".join(
                quote_line(q) for q in item["quotes"]) + "</ul></div>")
        conf = item["confidence"]
        if conf["flip_drivers"]:
            first = conf["flip_drivers"][0]
            lines.append(f"<div class='why'><b>Would have flipped:</b> "
                         f"{html.escape(first['note'])}<br><span class='muted'>"
                         f"margin {conf['margin']} — the decision turns over that close to the answers "
                         f"({len(conf['flip_drivers'])} way(s) found)</span></div>")
        elif conf["provider_confidences"]:
            shown = ", ".join(f"{k}={v}" for k, v in list(conf["provider_confidences"].items())[:7])
            lines.append(f"<div class='why'><b>Judge confidence (predicted):</b> "
                         f"<code>{html.escape(shown)}</code><br><span class='muted'>the model's own "
                         f"number — calibration: {html.escape(str(doc.get('calibration', 'unmeasured')))}"
                         "</span></div>")
        else:
            span = (f"in either direction, up to ±{conf.get('scan_span')} (step {conf.get('flip_step')})"
                    if conf.get("scan_span") is not None else "inside the scan")
            lines.append(f"<div class='why muted'><b>No flip found {html.escape(span)}:</b> no single "
                         "answer moved this decision at that resolution — outside the interval nothing "
                         "is claimed; judge confidence unmeasured (a chat model reports none)</div>")
        for ruling in item.get("author_decisions") or []:
            stale = ruling.get("expired")
            lines.append(f"<div class='why{STR_STALE if stale else ''}'><b>Author "
                         f"({html.escape(str(ruling.get('actor')))}, {html.escape(str(ruling.get('ts')))}):</b> "
                         f"{html.escape(str(ruling.get('ruling')))} — "
                         f"{html.escape(_plain(str(ruling.get('reason_code'))))}"
                         + (f" · {html.escape(str(ruling.get('note')))}" if ruling.get("note") else "")
                         + (f"<br><span class='muted'>{html.escape(str(ruling.get('expired_why')))}</span>"
                            if stale else "")
                         + "</div>")
        if action_url and item["confidence"]["needs_review"] \
                and not any(not d.get("expired") for d in item.get("author_decisions") or []):
            lines.append(
                f"<form class='ruling' method='post' action='{html.escape(action_url)}'>"
                f"<input type='hidden' name='receipt_id' value='{html.escape(str(item['receipt_id']))}'>"
                + (f"<input type='hidden' name='token' value='{html.escape(str(token))}'>"
                   if token else "")
                + "<label>reason <select name='reason_code'>"
                + f"<option value=''>(use the default for this ruling)</option>{reason_options}"
                + "</select></label>"
                + "<label>note <input name='note' size='28' placeholder='what you checked'></label>"
                + ("<button name='ruling' value='approve'>Approve</button>"
                   if item.get("review", {}).get("approve") else
                   f"<span class='muted'>approve unavailable — {html.escape(str(item.get('review', {}).get('why')))}</span>")
                + "<button class='reject' name='ruling' value='reject'>Reject</button>"
                + "</form>")
        if item.get("diff"):
            body = item["diff"] if item["confidence"]["needs_review"] else item["diff"][:1500]
            showing = f"<span class='muted'>showing {len(body)} of {item.get('diff_bytes', len(body))} " \
                      f"bytes (the file is {item.get('diff_path_shown', 'in the course tree')})</span>" \
                if item.get("diff_bytes", 0) > len(body) else ""
            lines.append(f"<pre>{html.escape(body)}</pre>")
            if showing:
                lines.append(f"<div class='why'>{showing}</div>")
        lines.append("</div>")
    lines.append("<p class='muted'>Every line above is a receipt. Nothing here is generated: the diffs come "
                 "from the course tree, the reasons from the decision log, the fragility from replaying "
                 "the answers through the same rulebook that made the decision.</p>")
    lines.append("</body></html>")
    return "\n".join(lines)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="build the Teacher/Author canvas")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--receipts")
    ap.add_argument("--course")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true", help="print the document instead of writing files")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    doc = build(root, Path(args.receipts) if args.receipts else None,
                Path(args.course) if args.course else None)
    if args.json:
        print(json.dumps(doc, indent=2, default=str))
        return 0
    out = Path(args.out) if args.out else root / "app" / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "canvas.json").write_text(json.dumps(doc, indent=2, default=str) + "\n")
    (out / "canvas.html").write_text(render_html(doc))
    print(json.dumps({"canvas": str(out / "canvas.html"), "decisions": doc["verdict"]["total"],
                      "needs_review": doc["verdict"]["needs_review"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
