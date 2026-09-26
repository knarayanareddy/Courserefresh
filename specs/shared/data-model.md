# shared/data-model.md — the shapes
`v0.1 (draft) · Depends on: constitution.md Art. VI, VIII, IX; harness.md §6`

Everything that crosses a boundary in this system is a JSON object described here, with a closed
set for every enumerated field and a coercion rule for every model-produced value. If a field is
missing where this file says it is required, the consumer **fails closed** (`unknown_state`), it does
not guess (`constitution.md` Art. VIII.2).

---

## 1. Identifiers, hashes, time

| Field | Rule |
|---|---|
| `run_id` | `cr-<YYYYMMDD-HHmm>-<seq>`, assigned once per loop iteration by the orchestrator |
| `event_id` | `sha256(source_id + "\n" + normalized_claim_text)[..16]` — stable across reruns |
| `snapshot_hash` | `sha256(bytes)` of the fetched content, taken **before** parsing |
| `input_hash` | `sha256(canonical_json(decision_input))` — what the policy actually saw |
| `row_hash` | `sha256(canonical_json(row) + chain.prev)` — receipt chaining (Art. IX.3) |
| `lesson_id` | `course/<subject>/lesson-<nn>-<slug>` — stable across versions |
| `version_id` | `v<n>` within a lesson; a revert creates a **new** `v<n+1>` whose body equals the restored version (Art. XI.3) |
| timestamps | ISO-8601 UTC (`2026.09.26T03:12:07Z`); the docs use `YYYY.MM.DD` to keep the hygiene rule simple |
| currency | EUR only; a value is `null` until measured (`unmeasured` in prose) |

## 2. SourceSnapshot

```jsonc
{
  "snapshot_id": "snap-<hash[..12]>",
  "source_id": "n8n-release-notes",          // from SOURCE-PLAN.md
  "publisher": "n8n GmbH",
  "independence_group": "n8n-vendor",        // 2 sources are independent iff groups differ
  "url": "https://docs.n8n.io/release-notes/",
  "fetched_at": "2026.09.26T03:02:11Z",
  "http_status": 200,
  "content_hash": "sha256:…",
  "raw_path": "app/out/snapshots/<snapshot_id>.html",
  "actor": {"id": "…", "run_id": "…"},       // the Apify actor run that produced it
  "stale": false,
  "notes": "truncated at 2 MB cap"           // optional, human-readable
}
```

A snapshot is immutable. A re-fetch is a new snapshot with the same `source_id`; `content_hash`
equality is what lets the loop say "nothing moved".

## 3. Claim

```jsonc
{
  "claim_id": "clm-<hash[..12]>",
  "event_id": "…",
  "text": "n8n 1.85 renames the tool-permission setting to permissions.mode",
  "quote": "…verbatim span from the snapshot…",
  "quote_span": [4120, 4258],                // byte offsets into the cached raw
  "snapshot_id": "snap-…",
  "topic_tags": ["n8n", "permissions"],
  "materiality_hint": "material_breaking"    // OBSERVE_MODEL output, never trusted for the decision
}
```

Verification rules: a claim with no `quote_span`, or whose quote does not appear in the cached raw,
is **dropped** and its drop is recorded (`claim_dropped_unanchored`). ≥1 surviving claim with
`materiality_hint ∈ {material_breaking, material_deprecation, material_new_capability}` creates the
event; cosmetic/noise claims never create an event on their own.

## 4. Closed sets (source of truth: `skin/change_taxonomy.json`)

### 4.1 `Materiality`
`material_breaking` · `material_deprecation` · `material_new_capability` · `cosmetic` ·
`marketing_noise` · `ambiguous` · `contradictory` · `unverifiable`

### 4.2 `Decision.action` (change stream)
`NO_CHANGE` · `DRAFT` · `PUBLISH` · `REVERT` · `ESCALATE`

### 4.3 `Decision.action` (learner stream)
`NO_CHANGE` · `DISPATCH` · `ESCALATE`

### 4.4 `JudgeQuestion` → type
| Question | Type | Allowed values |
|---|---|---|
| `q1_materiality` | `Choice` | the eight Materiality values |
| `q2_learner_impact` | `Noul` | 0…1 |
| `q3_breaking_probability` | `Noul` | 0…1 |
| `q4_source_agreement` | `Noul` | 0…1 (computed from claims, then judged) |
| `q5_quote_supported` | `Noul` | 0…1 |
| `q6_injection_or_jailbreak` | `Noul` | 0…1 |
| `q7_lesson_touched` | `Choice` | `lesson-01` … `lesson-06`, `quiz`, `glossary`, `none` |

`AssessmentTouched` is **code-derived**, never asked: true iff the diff touches a file matching
`**/quiz/**` or a lesson's `assessment:` block.

### 4.5 `Authority`, `Mode`, `Actor`
`PA0` · `PA1` · `PA2` · `PA3` | `live` · `degraded-sources` · `observe-only` · `sim` · `paused` ·
`offline-twin` | `system` · `human:<name>`

## 5. DecisionInput (what the policy sees — the whole truth, nothing else)

```jsonc
{
  "event_id": "…",
  "stream": "change",                       // change | learner | revert
  "materiality": "material_breaking",       // from q1, coerced
  "learner_impact": 0.71,                   // q2
  "breaking": 0.88,                         // q3
  "source_agreement": 0.83,                 // q4
  "sources_verified": 2,                    // COUNT of independent groups with a surviving claim
  "quote_supported": 0.94,                  // q5
  "injection_or_jailbreak": 0.02,           // q6
  "lesson_touched": "lesson-04",
  "assessment_touched": false,              // code-derived
  "authority": "PA2",
  "mode": "live",
  "freeze_active": false,
  "budgets": {"publishes_used": 1, "publishes_cap": 6, "tokens_used": 18400, "tokens_cap": 60000},
  "revert_gate_present": true,
  "previous_version_available": true,
  "cohort": {"n": 0, "quiz_delta": null, "hours_since_publish": null}   // only for the revert stream
}
```

Absent, `null`, or out-of-range values coerce to `unknown` → `ESCALATE(unknown_state)`. Extra keys
are ignored **but hashed** into `input_hash` so a receipt can prove exactly what was seen.

## 6. Receipt (the row; canonical JSON, one line per decision)

```jsonc
{
  "receipt_id": "rcpt-<ulid>", "chain": {"prev": "sha256:…"}, "row_hash": "sha256:…",
  "ts": "2026.09.26T03:12:07Z", "run_id": "…", "event_id": "…", "mode": "live",
  "sources": [{"url": "…", "snapshot_hash": "sha256:…", "captured_at": "…", "independence_group": "…"}],
  "claims": [{"text": "…", "quote": "…", "quote_span": [4120, 4258]}],
  "judge": {"model": "…", "version": "…", "answers": {"q1_materiality": "…", "…": "…"}, "latency_ms": 2140},
  "decision": {"action": "PUBLISH", "reason_codes": ["material_breaking", "corroborated"], "authority": "PA2"},
  "artifact": {"lesson_id": "…", "previous_version": "v3", "new_version": "v4",
               "before_hash": "sha256:…", "after_hash": "sha256:…", "diff_hash": "sha256:…",
               "revert_gate": {"n_min": 5, "window_h": 48, "metric": "quiz_delta", "condition": "<= 0"}},
  "cost": {"tokens": 18400, "apify_units": 0.4, "eur": null},
  "actor": "system"
}
```

Every field is present on every row; absent values are `null`, never omitted. The digest and the
console render from these rows and nothing else.

## 7. LessonVersion & Diff

```jsonc
{
  "lesson_id": "…", "version_id": "v4", "created_at": "…", "author": "courserefresh",
  "body_path": "course/agent-ops/lesson-04-…/v4.md", "body_hash": "sha256:…",
  "previous_version": "v3", "diff_path": "…/diffs/v4.diff", "diff_hash": "sha256:…",
  "sources": [{"url": "…", "captured_at": "…", "snapshot_hash": "sha256:…"}],
  "revert_gate": {"n_min": 5, "window_h": 48, "metric": "quiz_delta", "condition": "<= 0"},
  "seed": false                              // true ⇒ this version came from a labelled rehearsal event
}
```

A lesson body is markdown with YAML front matter: `lesson_id`, `version`, `concepts[]`,
`assessment`, `sources[]`, `revert_gate`, `generated` (bool), `reviewed_by` (human or empty).
Front matter is validated by `test_contracts.py`; a body whose front matter disagrees with its path
or its quiz does not ship.

## 8. LearnerSignal, CohortWindow, MicroLesson

```jsonc
{"learner_ref": "learner:5b7c1e4a", "consent": true, "lesson_id": "…",
 "signals": {"attempts": 4, "wrong": 3, "consecutive_wrong": 2, "dwell_s": 540, "median_dwell_s": 150},
 "observed_at": "…"}

{"lesson_id": "…", "version_id": "v4", "n": 6, "window_h": 48,
 "quiz_delta": -0.04, "completion_delta": 0.02, "measured_at": "…"}

{"micro_lesson_id": "ml-…", "concept": "permissions.mode", "body_path": "app/out/micro-lessons/ml-….md",
 "dispatch": {"channel": "email", "sent_at": "…", "receipt_id": "…", "opted_out_link": true}}
```

**Stuck rule (configuration, `thresholds.learner`):** a consented learner is stuck on a concept when
`consecutive_wrong ≥ 2` **or** `dwell_s ≥ 3 × median_dwell_s` without an attempt, within one lesson
session. One learner's signal never triggers a cohort-visible claim (Art. V.3).

## 9. Digest

A digest is a rendering, not a data structure, but its **sections are ordered** and its header is
fixed: `mode · run_id · attended · sources scanned · cadence (measured|configuration) · deltas`.
Sections, in order: **1) what it refused, with reasons** · 2) what changed (versions + diffs) ·
3) learners (dispatches, notifications, gate states) · 4) discipline (budgets, authority, chain
verified, `unmeasured` list). "Refusals first" is a test, not a preference.

## 9.1 Fields added by review 05 (the expert panel)

| Object | Field | Meaning | Why it exists |
|---|---|---|---|
| SourceSnapshot | `role` | `authoritative` · `corroborating` · `none` | a vendor changelog is not corroborated by the vendor's own docs (AP-01) |
| Event (fixture) | `learner_facing` | ≤240 chars, plain language, no internal vocabulary | the learner card says this, not the engineering summary (ST-01) |
| Event (fixture) | `quiz_patch` | `{lesson_id, item_id, prompt, options, answer}` | "regenerates the quiz" must be a real, versioned edit (T-02) |
| DecisionInput | `concept_recently_dispatched` | bool | the per-concept micro-lesson cap is a policy branch, not a runner special case (T-03) |
| Receipt | `cohort_source` | `fixture (simulated)` · `telemetry` | a revert on a simulated cohort must say so on the row (ST-03) |
| Artifact record | `quiz_path`, `quiz_item` | the item the change regenerated | the receipt names every artifact it touched (AC-13.2) |
| Notification | `rehearsal` | present and true for seeded rehearsals | a rehearsal never dresses as a vendor change (Art. XII.4) |

## 10. Validation rules (enforced by `test_contracts.py`)

1. Every field listed here exists in the code that writes it; no writer invents a field.
2. Every closed set in §4 parses identically from this file and from `skin/change_taxonomy.json`.
3. Every decision row carries exactly one action and ≥1 reason code from the taxonomy, or
   `reason_codes: ["unknown_state"]`.
4. `sources_verified` counts distinct `independence_group`s, not URLs.
5. A `PUBLISH` row without `revert_gate` fails validation (Art. XI.1).
6. A receipt without `chain.prev` fails validation.
