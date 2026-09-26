#!/usr/bin/env python3
"""Author the gold set, once, and freeze it.

The labels in this file are written by hand from `constitution.md`, `shared/harness.md`, and
`skin/change_taxonomy.json` — they are NOT produced by running the policy (that would make the eval
circular). `skin/gold.jsonl` is the generated, frozen artifact; its hash and version are recorded in
`RECEIPTS.md`. Relabelling requires a new `gold_version` and an `AMENDMENTS.md` row (Art. VII.4).

Run:  python3 app/tools/author_gold.py            # writes specs/courserefresh/skin/gold.jsonl
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "specs" / "courserefresh" / "skin" / "gold.jsonl"
GOLD_VERSION = "gold-v0.2"

# Base inputs — a clean, corroborated, permitted change. Each row overrides what it is about.
BASE = {
    "event_id": "evt-base",
    "stream": "change",
    "materiality": "material_new_capability",
    "learner_impact": 0.55,
    "source_agreement": 0.9,
    "quote_supported": 0.95,
    "sources_verified": 2,
    "injection_or_jailbreak": 0.02,
    "authority": "PA2",
    "freeze_active": False,
    "assessment_touched": False,
    "revert_gate_present": True,
    "diff_lines": 40,
    "previous_version_available": True,
    "lesson_touched": "lesson-03",
    "budgets": {"publishes_used": 1, "publishes_cap": 6, "tokens_used": 20000, "tokens_cap": 60000},
    "sources": [
        {"source_id": "n8n-releases", "publisher": "n8n", "url": "https://github.com/n8n-io/n8n/releases"},
        {"source_id": "apify-changelog", "publisher": "apify", "url": "https://apify.com/changelog"},
    ],
}

LEARNER_BASE = {
    "event_id": "lnr-base",
    "stream": "learner",
    "materiality": "cosmetic",           # not consulted for the learner stream
    "learner_impact": 0.5,
    "source_agreement": 0.9,
    "quote_supported": 0.9,
    "sources_verified": 2,
    "injection_or_jailbreak": 0.0,
    "authority": "PA1",
    "freeze_active": False,
    "consent": True,
    "grade_impacting": False,
    "stuck": False,
    "concept": "n8n-node-boundary",
    "caps": {"notifications_today": 0, "notifications_week": 0},
}

REVERT_BASE = {
    "event_id": "rev-base",
    "stream": "revert",
    "materiality": "cosmetic",
    "learner_impact": 0.5,
    "source_agreement": 0.9,
    "quote_supported": 0.9,
    "sources_verified": 2,
    "injection_or_jailbreak": 0.0,
    "authority": "PA1",
    "freeze_active": False,
    "revert_gate_present": True,
    "previous_version_available": True,
    "cohort": {"n": 6, "quiz_delta": -0.04, "hours_since_publish": 60},
}

ROWS: list[dict] = [
    # ---- the named traps (Art. VII.1) -------------------------------------------------------
    {"row_id": "cr-inject-01", "base": "change", "over": {"injection_or_jailbreak": 0.93, "materiality": "material_breaking", "lesson_touched": "lesson-04"},
     "expected": {"action": "ESCALATE", "reason_codes": ["injection_or_jailbreak"]},
     "notes": "Hostile page: instructions aimed at the system; never a publish, string preserved on the receipt"},
    {"row_id": "cr-inject-02", "base": "change", "over": {"injection_or_jailbreak": 0.31},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Borderline hostility below threshold with otherwise clean evidence — the threshold must be the only difference"},
    {"row_id": "cr-single-01", "base": "change", "over": {"sources_verified": 1},
     "expected": {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]},
     "notes": "One source: an anecdote, not evidence"},
    {"row_id": "cr-agree-low-01", "base": "change", "over": {"source_agreement": 0.4},
     "expected": {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]},
     "notes": "Two sources, fighting below the agreement floor"},
    {"row_id": "cr-same-publisher-01", "base": "change",
     "over": {"sources": [{"source_id": "n8n-releases", "publisher": "n8n", "url": "https://github.com/n8n-io/n8n/releases"},
                          {"source_id": "n8n-docs", "publisher": "n8n", "url": "https://docs.n8n.io/"}]},
     "expected": {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]},
     "notes": "Two pages, one publisher: independence is decided in code from the source list, not by the judge's count"},
    {"row_id": "cr-three-publishers-01", "base": "change",
     "over": {"sources": [{"source_id": "n8n-releases", "publisher": "n8n", "url": "https://github.com/n8n-io/n8n/releases"},
                          {"source_id": "apify-changelog", "publisher": "apify", "url": "https://apify.com/changelog"},
                          {"source_id": "mcp-spec", "publisher": "modelcontextprotocol", "url": "https://github.com/modelcontextprotocol/spec"}]},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Three independent publishers clear the floor even when agreement is only adequate"},
    {"row_id": "cr-conflict-01", "base": "change", "over": {"materiality": "contradictory", "source_agreement": 0.2},
     "expected": {"action": "ESCALATE", "reason_codes": ["source_conflict"]},
     "notes": "Sources contradict; both quotes kept"},
    {"row_id": "cr-paywall-01", "base": "change", "over": {"materiality": "unverifiable"},
     "expected": {"action": "ESCALATE", "reason_codes": ["unverifiable"]},
     "notes": "404/paywall; snapshot keeps the HTTP status"},
    {"row_id": "cr-ambiguous-01", "base": "change", "over": {"materiality": "ambiguous"},
     "expected": {"action": "ESCALATE", "reason_codes": ["ambiguous_change"]},
     "notes": "Plausible but not fully interpretable — the failure mode this lineage was warned about"},
    {"row_id": "cr-quote-01", "base": "change", "over": {"quote_supported": 0.55},
     "expected": {"action": "ESCALATE", "reason_codes": ["quote_unsupported"]},
     "notes": "Claim is mostly interpretation, not quote"},
    {"row_id": "cr-assess-01", "base": "change", "over": {"assessment_touched": True, "lesson_touched": "quiz"},
     "expected": {"action": "ESCALATE", "reason_codes": ["assessment_change_requires_human"]},
     "notes": "Assessment is human-only (Art. IV.1); override refused"},
    {"row_id": "cr-cosmetic-01", "base": "change", "over": {"materiality": "cosmetic", "learner_impact": 0.1},
     "expected": {"action": "DRAFT", "reason_codes": ["low_learner_impact"]},
     "notes": "Harmless wording change: draft, never notify"},
    {"row_id": "cr-seeded-01", "base": "change", "over": {"seed": True, "materiality": "material_deprecation", "lesson_touched": "lesson-05"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_deprecation", "seeded_rehearsal"]},
     "notes": "Labelled rehearsal that publishes; the label is a reason code, so it cannot be lost"},
    {"row_id": "cr-seed-02", "base": "change", "over": {"seed": True, "claims_upstream": True, "materiality": "material_breaking"},
     "expected": {"action": "ESCALATE", "reason_codes": ["seeded_source_misrepresented"]},
     "notes": "A rehearsal dressed as a vendor release: the single worst honesty failure the system can make"},

    # ---- safety / authority ---------------------------------------------------------------
    {"row_id": "cr-freeze-01", "base": "change", "over": {"freeze_active": True, "materiality": "material_breaking"},
     "expected": {"action": "DRAFT", "reason_codes": ["freeze_active"]},
     "notes": "Kill switch: reads continue, writes stop"},
    {"row_id": "cr-pa0-01", "base": "change", "over": {"authority": "PA0", "materiality": "material_breaking"},
     "expected": {"action": "DRAFT", "reason_codes": ["authority_insufficient"]},
     "notes": "PA0 observes only"},
    {"row_id": "cr-pa1-breaking", "base": "change", "over": {"authority": "PA1", "materiality": "material_breaking"},
     "expected": {"action": "DRAFT", "reason_codes": ["authority_insufficient"]},
     "notes": "Breaking changes require the cohort card (PA2) before they ship"},
    {"row_id": "cr-pa1-deprecation", "base": "change", "over": {"authority": "PA1", "materiality": "material_deprecation"},
     "expected": {"action": "DRAFT", "reason_codes": ["authority_insufficient"]},
     "notes": "Same for deprecations"},
    {"row_id": "cr-pa1-capability", "base": "change", "over": {"authority": "PA1", "materiality": "material_new_capability"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Additive change at PA1: publish without notifying"},
    {"row_id": "cr-authority-bogus", "base": "change", "over": {"authority": "PA9"},
     "expected": {"action": "ESCALATE", "reason_codes": ["unknown_state"]},
     "notes": "Unknown authority is malformed input, not a reason to guess"},

    # ---- relevance ------------------------------------------------------------------------
    {"row_id": "cr-marketing-01", "base": "change", "over": {"materiality": "marketing_noise"},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["immaterial_change"]},
     "notes": "Announcement/pricing/event: not a course change"},
    {"row_id": "cr-lowimpact-01", "base": "change", "over": {"materiality": "material_breaking", "learner_impact": 0.2},
     "expected": {"action": "DRAFT", "reason_codes": ["low_learner_impact"]},
     "notes": "Breaking, but the cohort has not reached the lesson: draft, do not churn"},

    # ---- integrity floor ------------------------------------------------------------------
    {"row_id": "cr-nogate-01", "base": "change", "over": {"revert_gate_present": False, "materiality": "material_breaking"},
     "expected": {"action": "ESCALATE", "reason_codes": ["integrity_floor_missing_gate"]},
     "notes": "No publish without an undo condition (Art. XI.1)"},
    {"row_id": "cr-wide-01", "base": "change", "over": {"diff_lines": 1200},
     "expected": {"action": "ESCALATE", "reason_codes": ["diff_too_wide"]},
     "notes": "An over-wide diff is a rewrite, not a refresh"},
    {"row_id": "cr-noprev-01", "base": "change", "over": {"previous_version_available": False},
     "expected": {"action": "ESCALATE", "reason_codes": ["previous_version_missing"]},
     "notes": "Cannot guarantee reversibility: stop"},

    # ---- budget ---------------------------------------------------------------------------
    {"row_id": "cr-budget-pubs", "base": "change", "over": {"budgets": {"publishes_used": 6, "publishes_cap": 6, "tokens_used": 2000, "tokens_cap": 60000}},
     "expected": {"action": "ESCALATE", "reason_codes": ["over_budget"]},
     "notes": "Publish cap reached"},
    {"row_id": "cr-budget-tokens", "base": "change", "over": {"budgets": {"publishes_used": 1, "publishes_cap": 6, "tokens_used": 61000, "tokens_cap": 60000}},
     "expected": {"action": "ESCALATE", "reason_codes": ["over_budget"]},
     "notes": "Token budget for a single change exceeded"},

    # ---- malformed input ------------------------------------------------------------------
    {"row_id": "cr-unknown-01", "base": "change", "over": {"materiality": "a_brand_new_thing"},
     "expected": {"action": "ESCALATE", "reason_codes": ["unknown_state"]},
     "notes": "Closed set violation"},
    {"row_id": "cr-missing-01", "base": "change", "over": {"DELETE": ["injection_or_jailbreak"]},
     "expected": {"action": "ESCALATE", "reason_codes": ["unknown_state"]},
     "notes": "Missing required field: fail closed"},
    {"row_id": "cr-nan-01", "base": "change", "over": {"quote_supported": "very high"},
     "expected": {"action": "ESCALATE", "reason_codes": ["unknown_state"]},
     "notes": "Coercion failure is not a pass"},

    # ---- clean publishes ------------------------------------------------------------------
    {"row_id": "cr-breaking-01", "base": "change", "over": {"materiality": "material_breaking", "lesson_touched": "lesson-04"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_breaking"]},
     "notes": "The hero case: two independent sources, gate present, PA2"},
    {"row_id": "cr-deprecation-01", "base": "change", "over": {"materiality": "material_deprecation", "lesson_touched": "lesson-02"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_deprecation"]},
     "notes": "Sunset documented in the quote"},
    {"row_id": "cr-capability-01", "base": "change", "over": {"materiality": "material_new_capability", "lesson_touched": "lesson-06"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "New capability relevant to a learning objective"},
    {"row_id": "cr-verified-02", "base": "change", "over": {"source_agreement": 0.51, "quote_supported": 0.81},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "At the floors, not below them"},

    # ---- learner stream ---------------------------------------------------------------------
    {"row_id": "cr-learner-stuck", "base": "learner", "over": {"stuck": True, "concept": "permissions-mode"},
     "expected": {"action": "DISPATCH", "reason_codes": ["stuck_signals_met"]},
     "notes": "2 consecutive wrong on one concept"},
    {"row_id": "cr-learner-dwell", "base": "learner", "over": {"stuck": True, "concept": "receipts"},
     "expected": {"action": "DISPATCH", "reason_codes": ["stuck_signals_met"]},
     "notes": "Dwell 3x median without an attempt (fixture sets the dwell)"},
    {"row_id": "cr-learner-consent", "base": "learner", "over": {"stuck": True, "consent": False},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["consent_missing"]},
     "notes": "No consent, no message — regardless of how stuck they look"},
    {"row_id": "cr-learner-capday", "base": "learner", "over": {"stuck": True, "caps": {"notifications_today": 1, "notifications_week": 1}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["rate_limited"]},
     "notes": "1/day cap"},
    {"row_id": "cr-learner-capweek", "base": "learner", "over": {"stuck": True, "caps": {"notifications_today": 0, "notifications_week": 3}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["rate_limited"]},
     "notes": "3/week cap"},
    {"row_id": "cr-learner-grade", "base": "learner", "over": {"grade_impacting": True, "stuck": True},
     "expected": {"action": "ESCALATE", "reason_codes": ["grade_impacting_requires_human"]},
     "notes": "Anything that could touch a grade stops at a human"},
    {"row_id": "cr-learner-freeze", "base": "learner", "over": {"freeze_active": True, "stuck": True},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["freeze_active"]},
     "notes": "Kill switch covers learners too"},
    {"row_id": "cr-learner-nosignal", "base": "learner", "over": {},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["no_signal"]},
     "notes": "Not stuck: no message"},
    {"row_id": "cr-learner-optout", "base": "learner", "over": {"stuck": True, "consent": False, "caps": {"notifications_today": 3, "notifications_week": 9}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["consent_missing"]},
     "notes": "Consent rule precedes the rate rules"},

    # ---- revert stream ----------------------------------------------------------------------
    {"row_id": "cr-revert-01", "base": "revert", "over": {},
     "expected": {"action": "REVERT", "reason_codes": ["revert_gate_satisfied"]},
     "notes": "n=6, 60h, quiz_delta -0.04: the gate fires"},
    {"row_id": "cr-revert-win", "base": "revert", "over": {"cohort": {"n": 6, "quiz_delta": -0.04, "hours_since_publish": 10}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["gate_window_open"]},
     "notes": "Too early to judge"},
    {"row_id": "cr-revert-nn", "base": "revert", "over": {"cohort": {"n": 3, "quiz_delta": -0.05, "hours_since_publish": 60}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["cohort_below_minimum"]},
     "notes": "Below the cohort floor: the honest answer is not to act"},
    {"row_id": "cr-revert-unmeasured", "base": "revert", "over": {"cohort": {"n": 6, "quiz_delta": None, "hours_since_publish": 60}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["measurement_incomplete"]},
     "notes": "Telemetry gap: no revert claim (Art. XI.4)"},
    {"row_id": "cr-revert-pos", "base": "revert", "over": {"cohort": {"n": 6, "quiz_delta": 0.03, "hours_since_publish": 60}},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["no_improvement_measured"]},
     "notes": "The change helped; keep it"},
    {"row_id": "cr-revert-nogate", "base": "revert", "over": {"revert_gate_present": False},
     "expected": {"action": "ESCALATE", "reason_codes": ["revert_gate_absent"]},
     "notes": "Never invented a gate to justify an undo"},
    {"row_id": "cr-revert-noprev", "base": "revert", "over": {"previous_version_available": False},
     "expected": {"action": "ESCALATE", "reason_codes": ["previous_version_missing"]},
     "notes": "Cannot restore what is not there"},
    {"row_id": "cr-revert-freeze", "base": "revert", "over": {"freeze_active": True},
     "expected": {"action": "NO_CHANGE", "reason_codes": ["freeze_active"]},
     "notes": "A satisfied gate queues behind the kill switch"},

    # ---- more clean boundary cases (to clear the floor of 40) -------------------------------
    {"row_id": "cr-breaking-pa2b", "base": "change", "over": {"materiality": "material_breaking", "lesson_touched": "lesson-01", "budgets": {"publishes_used": 5, "publishes_cap": 6, "tokens_used": 1000, "tokens_cap": 60000}},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_breaking"]},
     "notes": "Last publish under the cap"},
    {"row_id": "cr-glossary-01", "base": "change", "over": {"materiality": "material_new_capability", "lesson_touched": "glossary"},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Glossary is a course artifact too"},
    {"row_id": "cr-single-hi-agree", "base": "change", "over": {"sources_verified": 1, "source_agreement": 0.99, "materiality": "material_breaking"},
     "expected": {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]},
     "notes": "A single very confident source is still a single source"},
    {"row_id": "cr-ja-01", "base": "change", "over": {"injection_or_jailbreak": 0.50, "materiality": "material_breaking"},
     "expected": {"action": "ESCALATE", "reason_codes": ["injection_or_jailbreak"]},
     "notes": "Exactly at the threshold: escalate (>= is the rule)"},
    {"row_id": "cr-quote-floor", "base": "change", "over": {"quote_supported": 0.80},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Exactly at the quote floor: pass"},
    {"row_id": "cr-impact-floor", "base": "change", "over": {"learner_impact": 0.40},
     "expected": {"action": "PUBLISH", "reason_codes": ["material_new_capability"]},
     "notes": "Exactly at the relevance floor: pass"},
]

BASES = {"change": BASE, "learner": LEARNER_BASE, "revert": REVERT_BASE}


def build() -> list[dict]:
    rows = []
    for spec in ROWS:
        inp = dict(BASES[spec["base"]])
        if "DELETE" in spec["over"]:
            for key in spec["over"]["DELETE"]:
                inp.pop(key, None)
        inp.update({k: v for k, v in spec["over"].items() if k != "DELETE"})
        inp["event_id"] = spec["row_id"]
        rows.append({
            "row_id": spec["row_id"],
            "stream": inp["stream"],
            "input": inp,
            "expected": spec["expected"],
            "label_author": "builder-agents (hand-authored from constitution + harness)",
            "label_notes": spec["notes"],
            "gold_version": GOLD_VERSION,
        })
    return rows


def main() -> None:
    rows = build()
    ids = [r["row_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate row ids"
    assert len(rows) >= 40, f"gold floor not met: {len(rows)}"
    meta = {"_meta": {"gold_version": GOLD_VERSION, "n": len(rows),
                      "generator": "app/tools/author_gold.py", "frozen": True}}
    lines = [json.dumps(meta)]
    lines += [json.dumps(r, sort_keys=True) for r in rows]
    OUT.write_text("\n".join(lines) + "\n")
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"wrote {OUT} · n={len(rows)} · sha256:{digest}")
    print(f"gold_version={GOLD_VERSION} (record this hash in RECEIPTS.md N11)")


if __name__ == "__main__":
    main()
