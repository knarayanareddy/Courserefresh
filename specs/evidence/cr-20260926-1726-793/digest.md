# Courserefresh digest — 2026.09.26T17:26:16Z

mode: **sim** · run `cr-20260926-1726-793` · chain: ok (9 rows)

## 1. What it refused (first, with reasons)
- `cr-hostile-page-01` — injection_or_jailbreak
- `cr-single-source-01` — insufficient_corroboration
- `cr-conflict-01` — source_conflict
- `cr-budget-01` — over_budget

## 2. What changed
- PUBLISH `lesson-04-tool-permissions` v3 → v4 · agent-ops/lesson-04-tool-permissions/diffs/v4.diff · quiz q2 regenerated
- PUBLISH `lesson-03-apify-inputs` v1 → v2 · agent-ops/lesson-03-apify-inputs/diffs/v2.diff
- REVERT `lesson-04-tool-permissions` v4 → v5 · agent-ops/lesson-04-tool-permissions/diffs/v5.diff
- downstream to revisit (not rewritten tonight): lesson-05-receipts-and-reverts, lesson-06-evals-that-survive

## 3. Learners
- notifications staged, not sent: 7 (mode: sim; no mail leaves the box)
- micro-lessons dispatched: 1
- blocked for missing consent: 1
- cohort quiz delta: unmeasured (sim run: no consented live cohort)
- decisions wanting a human (2): rcpt-26-793-003 ESCALATE — a second independent publisher carrying the same fact would unblock it; rcpt-26-793-004 ESCALATE — a decision about which publisher to believe is a human's call → app/out/canvas.html

## 4. Discipline
- authority used this run: PA1×4, PA2×5 · promotion to PA2 needs 3 consecutive accepted publishes
- budgets: publishes 2/6 · tokens unmeasured (sim run) · digest ≤ 4096 bytes
- kill switch: off
- cost per change: unmeasured (sim run) — no vendor prices captured yet
- receipts: 9 rows · chain verified at end: True

> Offline twin: same policy rules as the n8n node (parity-tested); fixtures labelled in every receipt.
