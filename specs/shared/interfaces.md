# shared/interfaces.md — contracts at every seam
`v0.1 (draft) · Depends on: harness.md, data-model.md, constitution.md Art. XIII, XIV`

Six seams: **Apify → n8n**, **n8n workflow → workflow**, **n8n → policy node**, **n8n → repo/Notion**,
**telemetry → learner learner flow**, **console → human**. Each seam has a payload shape, an error
policy, and an idempotency key. Nothing crosses a seam without one of each.

---

## 1. Apify → n8n (scan inputs)

**Actor call** (made by `wf-cr-0-scan` via the Apify node):

```jsonc
{ "actor_id": "<pinned id>", "build": "<pinned build tag>", "run_mode": "single",
  "input": { "startUrls": [{"url": "…"}], "maxPages": 5, "proxy": {"useApifyProxy": true} },
  "budget": {"max_total_charge_usd": 0.25} }
```

**Dataset row contract** (what the normaliser accepts — anything else is discarded noisily):

```jsonc
{ "url": "https://…", "title": "…", "markdown": "…", "published_at": "2026-…-…T…Z",
  "content_hash": "sha256:…", "actor_run_id": "…" }
```

- `content_hash` missing ⇒ compute from `markdown`. Row without `url` or `markdown` ⇒ discarded,
  counted in the run's `discarded` tally, printed in the digest's discipline section.
- The normaliser converts each row to a `SourceSnapshot` (`data-model.md` §2) and writes the raw
  bytes under `app/out/snapshots/`.
- **Allowlist:** only exact hosts from `WIRING.md` §2 are fetched; a row for any other host is
  rejected with `host_not_allowlisted` (TM04) and the rejection is receipted.

## 2. n8n workflow → workflow

| From | To | Trigger | Payload | Idempotency |
|---|---|---|---|---|
| `wf-cr-0-scan` | `wf-cr-1-triage` | HTTP (per snapshot batch ≤5) | `{run_id, snapshots:[…], discarded:int}` | `event_id` + `input_hash`; triage dedupes |
| `wf-cr-1-triage` | `wf-cr-2-act` | HTTP (approved only) | `{receipt_id, decision, artifact_plan}` | `(lesson_id, from_version)` |
| `wf-cr-2-act` | `wf-cr-9-receipt` (sub-workflow) | every terminal step | the receipt row (§`data-model.md` §6) | `receipt_id` |
| `wf-cr-3-learn` | `wf-cr-2-act` | revert queue drain | `{receipt_id, decision: REVERT, artifact_plan}` | `(lesson_id, from_version)` |
| any | `wf-cr-4-digest` | cron 07:30 or `POST /digest` | `{run_id?}` | rendering is idempotent per window |

Every workflow returns `{ok:true, …}` or `{ok:false, error:{code, message, receipt_id}}`; a workflow
that crashes without a receipt is a Sev-2 (the digest detects the gap between `notice` count and
receipt count and prints `DIGEST FAILED: receipt gap n`).

**Error codes** (closed set, shared with the console and the tests):
`host_not_allowlisted` · `size_cap_exceeded` · `fetch_timeout` · `actor_failed` · `payload_invalid` ·
`claim_unanchored` · `insufficient_corroboration` · `source_conflict` · `assessment_touched` ·
`injection_detected` · `over_budget` · `write_conflict` · `write_failed` · `chain_broken` ·
`consent_missing` · `cohort_below_minimum` · `unknown_state` · `freeze_active`.

## 3. n8n → policy node

```jsonc
// input: DecisionInput (data-model.md §5). Output: exactly one line of JSON.
{ "action": "ESCALATE", "reason_codes": ["insufficient_corroboration"],
  "authority": "PA0", "notes": "single source: n8n release notes" }
```

Rules: the node only reads its input; it writes nothing; it never throws (malformed input →
`ESCALATE(unknown_state)` with the offending key named in `notes`); it must fit on one canvas
screen when rendered (`design/MASTER.md` §5) because it is the answer to "where are the rules?".

## 4. n8n → repo, and the human channel

- **Write target:** `course/<subject>/**` on branch `bot/courserefresh` only. The commit message
  starts `cr: <action> <lesson_id> <from>→<to> [<receipt_id>]`. The actor never merges to `main`;
  the human does that, and the digest links the comparison URL.
- **Commit content:** the new `v<n>.md`, its `diffs/v<n>.diff`, updated `CHANGELOG.md`, updated
  quiz if regenerated, and the lesson's `sources:` block. One commit per decision — never a batch.
- **Notion mirror (P1, may be cut):** the lesson page is replaced with the new body and a
  "what changed" block. If it fails: `notification_failed` receipt, commit stands, digest says so.
- **Learner card (P0):** three lines — *what changed · why it matters to you · what to do if it is
  wrong* — plus a link to the diff and a one-click opt-out. Sent to consented handles only, through
  the digest's channel (§`harness.md` §1 Learn), rate-limited per Art. IV.2.
- **Micro-lesson dispatch:** one concept, ≤2 minutes of reading, one practice item. Same channel,
  same rate limit, consent-gated, opt-out in every message.

## 5. Telemetry → learner flow

```jsonc
// POST /telemetry (learner client) — consent is checked BEFORE storage
{ "learner_ref": "learner:<hash8>", "consent": true, "lesson_id": "…",
  "events": [{"t": "…", "kind": "attempt", "item": "q2", "correct": false},
             {"t": "…", "kind": "dwell", "seconds": 540}] }
```

- Rejected (`403`) when `consent` is false or missing: not stored, not counted, digest reports
  `telemetry_rejected: n`.
- Stored as one append-only JSONL row per event; hashed handles only (Art. V.2).
- A cohort window is computed by `wf-cr-3-learn` per published version (Art. XI); a cohort with
  `n < thresholds.learner.cohort_min` yields `unmeasured` gate state, never a revert claim.

## 6. Console → human (author instrument, read-mostly)

| Route | Method | Contract |
|---|---|---|
| `/` | GET | Latest digest, rendered from receipts (refusals first) |
| `/lesson/{lesson_id}` | GET | Version list, current body, sources block, gate state |
| `/lesson/{lesson_id}/diff/{version_id}` | GET | Unified diff, `−`/`+` markers, no colour-only signalling |
| `/receipt/{receipt_id}` | GET | The full receipt row, pretty-printed; `chain.verify` result |
| `/eval` | GET | Last eval run: three columns, per-class table, floor status, `gold_version` |
| `/healthz` | GET | `{mode, freeze, chain_ok, last_run, receipt_count_gap}` |
| `/pause` | POST | Sets the freeze; one iteration to take effect; receipted |
| `/resume` | POST | Requires `{"confirm": "RESUME"}`; receipted |
| `/revert/{receipt_id}` | POST | Only for a `revert_gate_satisfied` receipt; refuses otherwise (exit 4) |

A human override (accept/override/reject an escalated decision) writes a **new** receipt with
`actor: human:<name>`; the original is never edited. `POST /resume` and overrides require the
`DEMO_TOKEN` when set; a wrong token is `403` + exit 3 (TM14).

## 7. Exit codes (shared by CLI and console actions)

`0` ok · `1` verification failed · `2` build-breaking invariant violated · `3` usage/config/authorisation ·
`4` refused (PA3 guard). The offline twin (`app/run_walking_skeleton.py`) implements all five; the
console maps them to HTTP 200/500/500/400/409.

## 8. Configuration surface (env vars, all optional except tokens)

| Var | Default | Meaning |
|---|---|---|
| `CR_MODE` | `sim` | `sim` \| `live` |
| `CR_THRESHOLDS` | `skin/thresholds.json` | Path; hashed into every receipt's run header |
| `CR_ALLOWLIST` | `WIRING.md` §2, mirrored in `app/out/state/allowlist.json` | Exact hosts |
| `CR_DEMO_TOKEN` | unset | When set, resume/override require it |
| `CR_FREEZE` | unset | Path of the freeze file (kill switch) |
| `OBSERVE_MODEL`, `JUDGE_MODEL`, `COMPARATOR_MODEL` | per `WIRING.md` §4 | Model ids, pinned versions |
| `APIFY_TOKEN`, `N8N_WEBHOOK_BASE`, `GITHUB_TOKEN`, `NOTION_TOKEN`, `SMTP_DSN` | — | Credentials; never logged, never in receipts |

Secrets are read from the environment only. A receipt containing a secret-shaped string fails
`test_hygiene.py` (TM12): the tests grep receipts and snapshots for token prefixes, emails, and
`20\d\d-` dates outside the pre-registration.
