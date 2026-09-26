#!/usr/bin/env python3
"""Courserefresh policy oracle — the rulebook, executable.

This is the ORACLE (constitution Art. XIII.3): the production decision runs the same rules inside
the n8n POLICY node (app/n8n/policy_node.js). `app/tests/test_gate_parity.py` fails if they disagree.

Rule order (normative, harness.md §3.2): safety -> evidence -> relevance -> authority ->
integrity -> budget -> default ESCALATE(unknown_state). First match wins.

Usage:
    policy.py --eval  <gold.jsonl>     # run the gold set; exit 0 ok, 1 mismatch, 2 build-breaking
    policy.py --explain <row_id> [--gold <path>]
    policy.py --dump  [<input.json>]   # one DecisionInput from stdin/file -> one line of JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
THRESHOLDS = json.loads((HERE / "thresholds.json").read_text())
TAXONOMY = json.loads((HERE / "change_taxonomy.json").read_text())

REASON_CODES = {c for group in TAXONOMY["reason_codes"].values() for c in group}
MATERIALITIES = set(TAXONOMY["materiality"])
PUBLISHABLE = set(TAXONOMY["publishable_materialities"])
COHORT_NOTIFY = set(TAXONOMY["cohort_notify_materialities"])

EVIDENCE = THRESHOLDS["evidence"]
RELEVANCE = THRESHOLDS["relevance"]
SAFETY = THRESHOLDS["safety"]
BUDGETS = THRESHOLDS["budgets"]
LEARNER = THRESHOLDS["learner"]
REVERT = THRESHOLDS["revert"]
DIFF = THRESHOLDS["diff"]

_ACTIONS = {
    "change": set(TAXONOMY["change_actions"]),
    "learner": set(TAXONOMY["learner_actions"]),
    "revert": {"NO_CHANGE", "REVERT", "ESCALATE"},
}

# Fields every DecisionInput must carry (missing/invalid -> unknown_state, constitution Art. VIII.2)
REQUIRED = (
    "event_id", "stream", "materiality", "learner_impact", "source_agreement", "quote_supported",
    "sources_verified", "injection_or_jailbreak", "authority", "freeze_active",
)


def _num(value, lo=0.0, hi=1.0):
    """Coerce a model-supplied value to a bounded float; anything else is None (= unknown)."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):  # NaN/inf
        return None
    return number if lo <= number <= hi else None


def _decision(action: str, reasons: list[str], authority: str, notes: str = "") -> dict:
    assert action in _ACTIONS["change"] | _ACTIONS["learner"], action
    assert reasons and all(r in REASON_CODES for r in reasons), reasons
    return {"action": action, "reason_codes": reasons, "authority": authority, "notes": notes}


def independent_publishers(sources) -> int | None:
    """Count distinct *voices* in the source list (constitution Art. III.1).

    Two pages from one vendor are one voice. A source whose declared role is "none" (a mirror, a
    re-post, a scraper of the same upstream) is recorded on the receipt and never counted
    (review 05, AP-01). Returns None when the list is absent (older rows keep the legacy count).
    """
    if not isinstance(sources, list) or not sources:
        return None
    voices = {str(s.get("publisher") or s.get("source_id") or "?").lower()
              for s in sources if isinstance(s, dict) and s.get("role") != "none"}
    return len(voices)


def _malformed(inp: dict) -> str | None:
    """Return the offending field name if the input cannot be trusted at all."""
    for field in REQUIRED:
        if field not in inp or inp[field] is None:
            return field
    if inp["materiality"] not in MATERIALITIES:
        return "materiality"
    if inp["authority"] not in set(TAXONOMY["authority"]):
        return "authority"
    for field in ("learner_impact", "source_agreement", "quote_supported", "injection_or_jailbreak"):
        if _num(inp[field]) is None:
            return field
    if inp["stream"] not in ("change", "learner", "revert"):
        return "stream"
    return None


def decide_change(inp: dict) -> dict:
    authority = inp["authority"]
    materiality = inp["materiality"]
    freeze = bool(inp["freeze_active"])
    injection = _num(inp["injection_or_jailbreak"])
    agreement = _num(inp["source_agreement"])
    quote = _num(inp["quote_supported"])
    impact = _num(inp["learner_impact"])
    sources = int(inp["sources_verified"])
    budgets = inp.get("budgets") or {}

    # 1) SAFETY
    if freeze:
        return _decision("DRAFT", ["freeze_active"], authority)
    if injection >= SAFETY["injection_min"]:
        return _decision("ESCALATE", ["injection_or_jailbreak"], authority)
    if inp.get("assessment_touched"):
        return _decision("ESCALATE", ["assessment_change_requires_human"], authority)

    # 2) EVIDENCE
    if materiality == "contradictory":
        return _decision("ESCALATE", ["source_conflict"], authority)
    if materiality == "unverifiable":
        return _decision("ESCALATE", ["unverifiable"], authority)
    if materiality == "ambiguous":
        return _decision("ESCALATE", ["ambiguous_change"], authority)
    # A labelled rehearsal is its own class: it may publish without live corroboration *because*
    # every artifact says SEEDED. Claiming upstream sources while seeded is a misrepresentation.
    if inp.get("seed"):
        if inp.get("claims_upstream"):
            return _decision("ESCALATE", ["seeded_source_misrepresented"], authority,
                             "rehearsal presented as a vendor change")
        return _decision("PUBLISH", [materiality, "seeded_rehearsal"], authority,
                         "SEEDED REHEARSAL — not a vendor release")
    publishers = independent_publishers(inp.get("sources"))
    if publishers is not None and publishers < EVIDENCE["min_sources"]:
        mirrors = sum(1 for s in inp.get("sources") or [] if isinstance(s, dict) and s.get("role") == "none")
        note = f"{publishers} independent voice(s) in {sources} source(s)"
        if mirrors:
            note += f" ({mirrors} mirror/re-post source(s) not counted)"
        return _decision("ESCALATE", ["insufficient_corroboration"], authority, note)
    if sources < EVIDENCE["min_sources"] or agreement < EVIDENCE["source_agreement_min"]:
        return _decision("ESCALATE", ["insufficient_corroboration"], authority,
                         f"sources={sources} agreement={agreement}")
    if quote < EVIDENCE["quote_supported_min"]:
        return _decision("ESCALATE", ["quote_unsupported"], authority)

    # 3) RELEVANCE
    if materiality == "marketing_noise":
        return _decision("NO_CHANGE", ["immaterial_change"], authority)
    if materiality == "cosmetic" or impact < RELEVANCE["learner_impact_min"]:
        return _decision("DRAFT", ["low_learner_impact"], authority)

    # 4) AUTHORITY
    if authority == "PA0":
        return _decision("DRAFT", ["authority_insufficient"], authority, "PA0: observe only")
    if materiality in COHORT_NOTIFY and authority != "PA2":
        return _decision("DRAFT", ["authority_insufficient"], authority,
                         "cohort notification required (PA2)")

    # 5) INTEGRITY FLOOR
    if not inp.get("revert_gate_present", True):
        return _decision("ESCALATE", ["integrity_floor_missing_gate"], authority)
    if int(inp.get("diff_lines", 0)) > DIFF["max_lines"]:
        return _decision("ESCALATE", ["diff_too_wide"], authority)
    if inp.get("previous_version_available", True) is False:
        return _decision("ESCALATE", ["previous_version_missing"], authority)

    # 6) BUDGET
    if int(budgets.get("publishes_used", 0)) >= int(budgets.get("publishes_cap", BUDGETS["publishes_per_day"])):
        return _decision("ESCALATE", ["over_budget"], authority, "publishes")
    if int(budgets.get("tokens_used", 0)) >= int(budgets.get("tokens_cap", BUDGETS["tokens_per_change"])):
        return _decision("ESCALATE", ["over_budget"], authority, "tokens")

    # 7) DEFAULT: a corroborated, relevant, permitted change -> publish
    if materiality in PUBLISHABLE:
        reasons = [materiality]
        if inp.get("seed"):
            reasons.append("seeded_rehearsal")
        return _decision("PUBLISH", reasons, authority, f"lesson {inp.get('lesson_touched', '?')}")
    return _decision("ESCALATE", ["unknown_state"], authority, f"unhandled materiality {materiality}")


def decide_learner(inp: dict) -> dict:
    authority = inp["authority"]
    if inp["freeze_active"]:
        return _decision("NO_CHANGE", ["freeze_active"], authority)
    if inp.get("grade_impacting"):
        return _decision("ESCALATE", ["grade_impacting_requires_human"], authority)
    if not inp.get("consent", False):
        return _decision("NO_CHANGE", ["consent_missing"], authority)
    caps = inp.get("caps") or {}
    if int(caps.get("notifications_today", 0)) >= BUDGETS["notify_per_learner_day"]:
        return _decision("NO_CHANGE", ["rate_limited"], authority, "day cap")
    if int(caps.get("notifications_week", 0)) >= BUDGETS["notify_per_learner_week"]:
        return _decision("NO_CHANGE", ["rate_limited"], authority, "week cap")
    if inp.get("stuck") and inp.get("concept_recently_dispatched"):
        return _decision("NO_CHANGE", ["rate_limited"], authority,
                         f"concept cap: {inp.get('concept', '')}")
    if inp.get("stuck"):
        return _decision("DISPATCH", ["stuck_signals_met"], authority, inp.get("concept", ""))
    return _decision("NO_CHANGE", ["no_signal"], authority)


def decide_revert(inp: dict) -> dict:
    authority = inp["authority"]
    if inp["freeze_active"]:
        return _decision("NO_CHANGE", ["freeze_active"], authority)
    if not inp.get("revert_gate_present", False):
        return _decision("ESCALATE", ["revert_gate_absent"], authority)
    if inp.get("previous_version_available", True) is False:
        return _decision("ESCALATE", ["previous_version_missing"], authority)
    cohort = inp.get("cohort") or {}
    n, delta, hours = cohort.get("n"), cohort.get("quiz_delta"), cohort.get("hours_since_publish")
    if n is None or delta is None or hours is None:
        return _decision("NO_CHANGE", ["measurement_incomplete"], authority)
    if int(n) < REVERT["n_min"]:
        return _decision("NO_CHANGE", ["cohort_below_minimum"], authority, f"n={n}")
    if float(hours) < REVERT["window_h"]:
        return _decision("NO_CHANGE", ["gate_window_open"], authority, f"{hours}h")
    if float(delta) <= 0:
        return _decision("REVERT", ["revert_gate_satisfied"], authority,
                         f"quiz_delta {delta:+.3f} at n={n} after {hours}h")
    return _decision("NO_CHANGE", ["no_improvement_measured"], authority, f"quiz_delta {delta:+.3f}")


def decide(inp: dict) -> dict:
    """The single entry point both runtimes expose."""
    bad = _malformed(inp)
    if bad:
        return _decision("ESCALATE", ["unknown_state"], inp.get("authority", "PA0") if inp.get("authority") in set(TAXONOMY["authority"]) else "PA0",
                         f"invalid:{bad}")
    stream = inp["stream"]
    if stream == "change":
        return decide_change(inp)
    if stream == "learner":
        return decide_learner(inp)
    return decide_revert(inp)


# --------------------------------------------------------------------------------------- gold eval

META_GOLD: dict = {}


def load_gold(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "_meta" in obj:
            META_GOLD.update(obj["_meta"])
            continue
        rows.append(obj)
    return rows


def policy_decision_reasons(row: dict) -> list[str]:
    """The reasons the oracle returns for a gold row (used by the eval report's counters)."""
    return decide(row["input"])["reason_codes"]


def eval_gold(path: Path) -> int:
    rows = load_gold(path)
    n = len(rows)
    mismatches: list[str] = []
    action_bad: list[str] = []
    reason_bad: list[str] = []
    hostile_publish = 0
    unsupported_publish = 0
    escalate = 0
    per_stream: dict[str, list[int]] = {}
    for row in rows:
        out = decide(row["input"])
        exp = row["expected"]
        stream = row["input"]["stream"]
        per_stream.setdefault(stream, [0, 0])
        per_stream[stream][1] += 1
        if out["action"] == exp["action"]:
            per_stream[stream][0] += 1
        else:
            action_bad.append(f"{row['row_id']}: {out['action']} != {exp['action']}")
        if set(exp["reason_codes"]) & set(out["reason_codes"]):
            pass
        else:
            reason_bad.append(f"{row['row_id']}: reasons {out['reason_codes']} !~ {exp['reason_codes']}")
        if out["action"] == "ESCALATE":
            escalate += 1
        if out["action"] == "PUBLISH":
            if exp["action"] != "PUBLISH":
                hostile_publish += 1
            if int(row["input"]["sources_verified"]) < EVIDENCE["min_sources"]:
                unsupported_publish += 1

    print(f"gold_version: {META_GOLD.get('gold_version', '<unset>')} · n={n}")
    print(f"action match: {(n - len(action_bad)) / max(n, 1):.3f}")
    print(f"reason match: {(n - len(reason_bad)) / max(n, 1):.3f}")
    print(f"escalate rate: {escalate / max(n, 1):.3f}")
    for stream, (ok, total) in sorted(per_stream.items()):
        print(f"  {stream:<8} action match {ok / total:.3f} (n={total})")
    unknown = sum(1 for r in rows
                  if "unknown_state" in sum((policy_decision_reasons(r) for r in [r]), []))
    print(f"unknown_state rows: {unknown}")
    print(f"hostile -> publish: {hostile_publish} (must be 0)")
    print(f"unsupported -> publish: {unsupported_publish} (must be 0)")
    # Column (b), informational: what "trust the model's inclination" would publish — every row
    # whose materiality hint looks publishable, with no corroboration, authority or gate check.
    naive_publish = sum(1 for r in rows if r["input"].get("stream") == "change"
                        and r["input"].get("materiality") in PUBLISHABLE)
    print(f"column (b) informational: naive publish inclinations {naive_publish}/{n}")
    if action_bad:
        print("ACTION MISMATCHES:")
        for m in action_bad[:20]:
            print(" -", m)
    if reason_bad:
        print("REASON MISMATCHES:")
        for m in reason_bad[:20]:
            print(" -", m)
    if hostile_publish or unsupported_publish:
        print("BUILD-BREAKING: invariant violated")
        return 2
    if n < 40:
        print(f"legal degrade: n={n} < 40 — no advantage claim may be made (Art. VII.3)")
        return 1
    return 1 if (action_bad or reason_bad) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Courserefresh policy oracle")
    ap.add_argument("--eval", metavar="GOLD")
    ap.add_argument("--explain", metavar="ROW_ID")
    ap.add_argument("--dump", action="store_true", help="read one DecisionInput (stdin) and print the decision")
    ap.add_argument("--gold", default=str(HERE / "gold.jsonl"))
    args = ap.parse_args()

    if args.eval:
        return eval_gold(Path(args.eval))
    if args.dump:
        inp = json.loads(sys.stdin.read())
        print(json.dumps(decide(inp)))
        return 0
    if args.explain:
        rows = load_gold(Path(args.gold))
        row = next((r for r in rows if r["row_id"] == args.explain), None)
        if not row:
            print(f"row {args.explain} not found in {args.gold}", file=sys.stderr)
            return 3
        out = decide(row["input"])
        print(f"{row['row_id']} ({row['input']['stream']})")
        print(f"  expected: {json.dumps(row['expected'])}")
        print(f"  observed: {json.dumps(out)}")
        return 0
    ap.print_help()
    return 3


if __name__ == "__main__":
    sys.exit(main())
