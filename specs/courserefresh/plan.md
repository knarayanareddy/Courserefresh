# Courserefresh — plan (the HOW)
`v0.1 (draft) · Depends on: spec.md; shared/interfaces.md; security/threat-model.md`

This is how the spec is built: the architecture, the five n8n workflows, the stack, the run
protocol, the money, the fallbacks, and the order of work. It narrows the spec; it may not widen it.

---

## 1. Architecture (one picture, no boxes unaccounted for)

```
  SOURCES (independent groups)                    COURSE (the artifact)
  ┌────────────────────────┐                      ┌──────────────────────────┐
  │ n8n releases/docs      │──┐                   │ course/agent-ops/         │
  │ Apify changelog        │  │  Apify actors     │   lesson-0N-*/v<n>.md     │
  │ MCP spec repo (3rd)    │  ├─(crawler+RSS)──┐   │   lesson-0N-*/quiz/*.json │
  └────────────────────────┘  │                │   │   lesson-0N-*/diffs/      │
                              ▼                │   └──────────────────────────┘
                        snapshots/            ▼        ▲            │
                    (hashed, cached)     wf-cr-0-scan │            │ commit (bot/courserefresh)
                              │                    │  │            ▼
                              ▼                    ▼  │      git history + CHANGELOG
                        wf-cr-1-triage ──► POLICY node (deterministic)
                              │                      │
                 ┌────────────┴───────────┐          │
                 ▼                        ▼          │
           ESCALATE/DRAFT            PUBLISH/REVERT ──► wf-cr-2-act ──► card + micro-lesson
                                                          │
   LEARNERS ── /telemetry ──► wf-cr-3-learn ──(stuck)─────┘
        ▲                         │
        └──── digest + console ◄── wf-cr-4-digest ◄── receipts (chained JSONL)
```

Everything that decides is in the POLICY node; everything that talks is n8n; every input is Apify
or the learner client; the artifact is the repo.

## 2. The five workflows (node-level contracts in `WIRING.md`)

| Workflow | Trigger | Nodes (essential) | Writes |
|---|---|---|---|
| `wf-cr-0-scan` | Schedule (60 min) + manual webhook | THRESHOLDS → Apify actor runs (×N) → Normalize → Dedupe (`state/seen.json`) → HTTP to triage | `snapshots/`, receipts |
| `wf-cr-1-triage` | Webhook from scan | BuildPrompt → OBSERVE call → Anchor quotes → JUDGE call (closed Qs) → **POLICY** → Receipt → Branch (act / escalate) | receipts, escalation queue |
| `wf-cr-2-act` | Webhook for approved decisions | RenderBody → RenderDiff → UpdateQuiz? → Git commit (bot branch) → Card email? → Receipt | `course/**`, `CHANGELOG.md`, cards |
| `wf-cr-3-learn` | Schedule (15 min) | ReadTelemetry → CohortWindow → GateEval → decide_revert → Queue → stuck check → decide_learner → Dispatch | micro-lessons, dispatch receipts |
| `wf-cr-4-digest` | Schedule 07:30 + webhook | ReadReceipts(window) → OrderSections → RenderText ≤4 KB → Send (Telegram/email) → VerifyChain | digest artifact, run_log |

Every workflow ends with a receipt call; a workflow that ends without one is detected by the
receipt-gap check and reported as `DIGEST FAILED` (exit 1).

## 3. Stack and why

| Layer | Choice | Why this, not the other thing |
|---|---|---|
| Ingestion | **Apify actors** (pinned id+build) | The criterion rewards Apify powering the system; actors give retries, proxies, and a run history that *is* the evidence |
| Orchestration + decisions | **n8n** (cloud or self-hosted) | Decisions must be inspectable on a canvas at 3am; the execution log is the audit trail; the POLICY node answers "where are the rules?" |
| Policy | `app/n8n/policy_node.js` + `skin/policy.py` | JS runs in production, Python is the oracle for tests and the offline twin; parity is a test |
| Models | `OBSERVE_MODEL` (cheap, fast) + `JUDGE_MODEL` (strong, pinned) | Separation keeps the judge honest and the cost low; the judge never sees the rulebook |
| Artifact | Git repo `course/**`, branch `bot/courserefresh` | Versioning, diffs, revertability and provenance come free; the judge can read the history |
| Learner surface | Email card + Notion mirror (P1) + the repo | Consent-respecting, no new platform accounts, works in the demo |
| Telemetry | SQLite (or Sheets) + `POST /telemetry` | Small, local, hash-only; enough to compute cohort windows honestly |
| Console | FastAPI + Jinja + one CSS file, server-rendered | Read-mostly instrument; no SPA build step in a 2-day window |
| Human channel | Telegram + email digest | The morning report is the product's face |

**Forbidden in the live loop:** any component that decides outside the POLICY node; any LLM call
that sets a threshold; any scraper that is not an Apify actor (n8n HTTP is a *fallback*, labelled
in the digest when used); any write outside `course/**`.

## 4. Determinism, parity, and the offline twin

- The two policy runtimes are compared row-by-row on the gold set (59 rows + 2 named probes → 0 disagreements).
- The offline twin (`app/run_walking_skeleton.py`) executes the *same* rules for the demo and the
  tests; its receipts carry `mode: sim` or `offline-twin`.
- Deterministic replay: given the same snapshots and telemetry, the digest and the decisions must be
  byte-identical (`--replay`), because the judge may ask "show me that again".

## 5. Run protocol (what a "hero run" is)

**D-1, before midnight:** preflight green (config, allowlist, budgets, credentials, chain empty),
fixtures replayed, then the live loop is armed to run unattended overnight.

**Overnight:** scan every 60 min; decisions as they come; a publish only on corroborated evidence;
cohort cards sent within minutes of a publish; the digest at 07:30. Nobody watches.

**D2, the harvest:** the run log, the receipts, the diff, the card, the gate state and the digest are
frozen as evidence (`EVIDENCE.md`) *before* any video is edited. Whatever the night produced is what
the video says — including "no live change arrived".

## 6. The ladder in practice (what the demo will exercise)

| Level | What runs | How it is earned |
|---|---|---|
| PA0 | draft everything, notify nobody | default at first run |
| PA1 | auto-publish to `course/**` | after the first clean preflight; the demo's hero change runs here if no history |
| PA2 | auto-publish **+ cohort card** | 3 consecutive accepted publishes, 0 rollbacks (from receipts) |
| PA3 | human-only | assessment/quiz, learner records, money, non-consented contact — permanently |

If the overnight history yields PA2, the card is real; if not, the video says PA1 and shows the
*rule* that would promote it. No narrative upgrade of the ladder (Art. VI).

## 7. Budgets, cost, and the cut list

| Item | Budget | Notes |
|---|---|---|
| Apify units | `budgets.apify_units_per_day` = 25 | Actor call capped per run |
| Tokens | 60 k per change, 500 k per day | Observe ≪ judge; measured per receipt |
| Publishes | 6 per day | `over_budget` beyond |
| Notifications | 1/learner/day, 3/learner/week | hard caps in code |
| Digest | 4 KB | trims oldest sections, never refusals |

**Cuts, in order (first to go, with the reason recorded):**
1. Notion mirror → the repo + card is the honest artifact surface.
2. Eval column (a) → keep (b) and (c); column (a) becomes `n/a` with the reason.
3. Micro-lesson channel switching (email only).
4. Scan cadence 60 → 120 min (still measured, printed).
**Never cut:** receipts, chain, revert gate, refusal path, hostile fixture, the labels.

## 8. Shape of the two days (the plan on one screen)

| When | Work | Gate |
|---|---|---|
| **D-3** | Ratify constitution; freeze thresholds; author gold ≥40; write the two policy runtimes; walking skeleton green | `sh app/check.sh` |
| **D-2** | n8n workflow skeleton on real webhooks (fixtures); console read routes; telemetry endpoint | M0 done-done (§`tasks.md`) |
| **D-1** | Live actors pinned; credentials wired; dry run with `mode: live`; arm the hero run before midnight | preflight green; warden sign-off |
| **D1** | Overnight unattended; morning: harvest; fix what broke; second run if needed | digest + ≥1 receipt set |
| **D2** | Freeze evidence → film → **submit 15:00** → live final 16:15 | checklist §4 signed |

## 9. What we will not build (even if there is time)

- A conversational UI, a mobile app, a SaaS landing page, a vector DB, a fine-tune, an "agent
  swarm", a second subject course, a billing page, a Notion two-way sync, a recommendation engine.
- Any feature whose absence is described in this plan as a cut but which the demo script leans on.
