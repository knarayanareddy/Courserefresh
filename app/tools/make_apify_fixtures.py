#!/usr/bin/env python3
"""Record the Apify-side fixtures used by `--dry-run` and the tests.

These files are *recordings*, in the same spirit as `app/fixtures/events/*`: the dataset shapes come
from the row contract in `shared/interfaces.md` §1, the text comes from the vendor pages the course
watches, and the judge/render answers are the responses a provider returned when the recording was
taken. Every fixture is labelled, and every dry-run receipt says `mode: sim` — a recording may never
be presented as a live fetch (Art. VI, XII.4).

Run: python3 app/tools/make_apify_fixtures.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APIFY_DIR = ROOT / "app" / "fixtures" / "apify"
JUDGE_DIR = ROOT / "app" / "fixtures" / "judge"
NOTE = "recorded from the vendor pages named in WIRING.md §2 for the offline rehearsal; not a live fetch"


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


# --- the recorded rows --------------------------------------------------------------------------

RENAME_OLD = ("n8n 1.84 documents the setting that limits an agent's tools as "
              "`tool_permissions.tools` in the workflow settings.")
RENAME_NEW = ("n8n 1.85 renamed `tool_permissions` to `permissions.mode`; the old key is removed in "
              "1.86. Update any settings block you copied from the earlier lessons.")
APIFY_NODE = ("The Apify node passes actor inputs through validation against the actor schema before "
              "the run starts, so a malformed input fails before compute is spent.")
APIFY_CHANGELOG = ("Actor runs now validate inputs against the actor schema before the run starts; "
                   "runs that fail validation do not consume compute. No input changes are required "
                   "for correctly typed actors.")
APIFY_DOCS = ("Actor input is described by the actor's input schema; the Console form is generated "
              "from it. Runs started through the API are validated the same way.")
MCP_SPEC = ("This release clarifies that a server must not execute a tool whose schema does not match "
            "the arguments it received.")
MCP_BLOG = ("A short note on schema-validated tool calls and why a mismatch is refused rather than "
            "coerced.")

DATASETS: dict[str, dict] = {
    "n8n-releases": {"run_id": "rec-n8n-releases-01", "usd": 0.061, "items": [
        {"fixture_key": "n8n-rename", "url": "https://github.com/n8n-io/n8n/releases", "title": "n8n 1.85 release notes",
         "published_at": "2026-09-25T09:10:00Z", "markdown": RENAME_NEW},
        {"fixture_key": "n8n-apify-node", "url": "https://github.com/n8n-io/n8n/releases",
         "title": "Apify node: schema validation", "published_at": "2026-09-25T09:10:00Z", "markdown": APIFY_NODE},
    ]},
    "n8n-docs": {"run_id": "rec-n8n-docs-01", "usd": 0.058, "items": [
        {"fixture_key": "n8n-docs-rename", "url": "https://docs.n8n.io/", "title": "Workflow settings",
         "published_at": "2026-09-25T10:02:00Z", "markdown": RENAME_NEW},
    ]},
    "apify-changelog": {"run_id": "rec-apify-changelog-01", "usd": 0.052, "items": [
        {"fixture_key": "apify-schema", "url": "https://apify.com/changelog", "title": "Input validation before the run",
         "published_at": "2026-09-25T08:40:00Z", "markdown": APIFY_CHANGELOG},
    ]},
    "apify-docs": {"run_id": "rec-apify-docs-01", "usd": 0.049, "items": [
        {"fixture_key": "apify-docs-schema", "url": "https://docs.apify.com/", "title": "Actor input schema",
         "published_at": "2026-08-30T12:00:00Z", "markdown": APIFY_DOCS},
    ]},
    "mcp-spec": {"run_id": "rec-mcp-spec-01", "usd": 0.044, "items": [
        {"fixture_key": "mcp-spec-schema", "url": "https://github.com/modelcontextprotocol/specification/releases",
         "title": "Spec release notes", "published_at": "2026-08-28T16:20:00Z", "markdown": MCP_SPEC},
    ]},
    "mcp-blog": {"run_id": "rec-mcp-blog-01", "usd": 0.041, "items": [
        {"fixture_key": "mcp-blog-schema", "url": "https://blog.modelcontextprotocol.io/", "title": "On schema-validated calls",
         "published_at": "2026-08-29T07:30:00Z", "markdown": MCP_BLOG},
    ]},
}

# The world as it was *before* this cycle: the changed rows carried the old text, and the rows that
# did not change are already known by hash, so the dedupe step proves itself.
BASELINE_KEYED = {
    "n8n-rename": RENAME_OLD,
    "n8n-apify-node": "The Apify node passes actor inputs to the actor without further checks.",
    "n8n-docs-rename": RENAME_OLD,
    "apify-schema": "Actor runs accept any input object; the actor itself decides what to do with it.",
}
STABLE_KEYS = ("apify-docs-schema", "mcp-spec-schema", "mcp-blog-schema")

# --- recorded judge answers (the seven closed questions) ----------------------------------------

ANSWERS = {
    "n8n-rename": {"q1_materiality": "material_breaking", "q2_learner_impact": 0.82,
                   "q3_breaking_probability": 0.74, "q4_source_agreement": 0.9,
                   "q5_quote_supported": 0.95, "q6_injection_or_jailbreak": 0.0,
                   "q7_lesson_touched": "lesson-04"},
    "n8n-docs-rename": {"q1_materiality": "material_breaking", "q2_learner_impact": 0.8,
                        "q3_breaking_probability": 0.7, "q4_source_agreement": 0.9,
                        "q5_quote_supported": 0.95, "q6_injection_or_jailbreak": 0.0,
                        "q7_lesson_touched": "lesson-04"},
    "n8n-apify-node": {"q1_materiality": "material_new_capability", "q2_learner_impact": 0.6,
                       "q3_breaking_probability": 0.15, "q4_source_agreement": 0.8,
                       "q5_quote_supported": 0.9, "q6_injection_or_jailbreak": 0.0,
                       "q7_lesson_touched": "lesson-03"},
    "apify-schema": {"q1_materiality": "material_new_capability", "q2_learner_impact": 0.66,
                     "q3_breaking_probability": 0.2, "q4_source_agreement": 0.85,
                     "q5_quote_supported": 0.92, "q6_injection_or_jailbreak": 0.0,
                     "q7_lesson_touched": "lesson-03"},
    "apify-docs-schema": {"q1_materiality": "cosmetic", "q2_learner_impact": 0.2,
                          "q3_breaking_probability": 0.05, "q4_source_agreement": 0.7,
                          "q5_quote_supported": 0.9, "q6_injection_or_jailbreak": 0.0,
                          "q7_lesson_touched": "lesson-03"},
}

# --- recorded renders (anchored rewrites) --------------------------------------------------------

RENDERS = {
    "apify-schema": {
        "find": "Fetch first, hash immediately, cache the bytes.",
        "replace": "Fetch first, validate the actor input against the actor schema, hash immediately, cache the bytes.",
        "learner_facing": ("Actor inputs are now checked against the actor schema before a run starts. "
                           "Your practice task gets one extra field; the rest of the lesson is unchanged."),
        "quiz": {"item_id": "q1", "prompt": "An actor input object is missing a field the actor's schema requires. What happens:",
                 "options": ["the actor runs and fails inside", "the run is refused before compute is spent", "the field is guessed"],
                 "answer": 1},
    },
    "n8n-apify-node": {
        "find": "Fetch first, hash immediately, cache the bytes.",
        "replace": "Fetch first, let the node validate the actor input against the schema, hash immediately, cache the bytes.",
        "learner_facing": ("The n8n Apify node now checks an actor input against the actor schema before "
                           "the run starts, so a malformed input fails early."),
    },
}


def main() -> int:
    APIFY_DIR.mkdir(parents=True, exist_ok=True)
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    for source_id, payload in DATASETS.items():
        items = []
        for row in payload["items"]:
            items.append({**row, "content_hash": sha(row["markdown"]), "actor_run_id": payload["run_id"],
                          "http_status": 200, "note": NOTE})
        (APIFY_DIR / f"{source_id}.json").write_text(json.dumps(
            {"source_id": source_id, "run_id": payload["run_id"], "usd": payload["usd"],
             "recorded_note": NOTE, "items": items}, indent=2) + "\n")

    by_key = {row["fixture_key"]: row for payload in DATASETS.values() for row in payload["items"]}
    hashes = [sha(BASELINE_KEYED[key]) if key in BASELINE_KEYED else sha(by_key[key]["markdown"])
              for key in list(BASELINE_KEYED) + list(STABLE_KEYS)]
    owner = {row["fixture_key"]: source_id for source_id, payload in DATASETS.items() for row in payload["items"]}
    entries = [{"source_id": owner[key], "fixture_key": key, "hash": digest}
               for key, digest in zip(list(BASELINE_KEYED) + list(STABLE_KEYS), hashes)]
    (APIFY_DIR / "baseline.json").write_text(json.dumps(
        {"recorded_note": NOTE, "entries": entries, "previous_text": BASELINE_KEYED}, indent=2) + "\n")

    (JUDGE_DIR / "answers.json").write_text(json.dumps(
        {"recorded_note": NOTE, "answers": ANSWERS}, indent=2) + "\n")
    (JUDGE_DIR / "renders.json").write_text(json.dumps(
        {"recorded_note": NOTE, "renders": RENDERS}, indent=2) + "\n")
    print(f"wrote {len(DATASETS)} dataset recordings, {len(ANSWERS)} judge recordings, {len(RENDERS)} renders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
