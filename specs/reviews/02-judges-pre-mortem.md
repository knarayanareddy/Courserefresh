# Sitting 02 — the judges' pre-mortem on the *built* Courserefresh package
`Version 1.0 · Last amended D-0 · Amends: AMENDMENTS.md 1.1 (J-rows)`

The package exists and its battery is green. This sitting is the adversarial dry run before the
video: five seats score the build against the actual criteria, a hostile reviewer reads every
claim, and the panel binds each finding to a file. Findings are `open` until `reviews/04` pastes
an output (Art. XVI.4).

## 0. Panel and mandates

| Seat | Persona | Mandate in this sitting |
|---|---|---|
| **A** | Hackathon judge — autonomy (25%) | Find any action that was actually approved by a human, or any "learning" with no receipt |
| **B** | Hackathon judge — proven in real use (25%) | Separate what ran on real data from what ran on fixtures; check the logs are real |
| **C** | Hackathon judge — n8n & Apify (20%) | Ask whether n8n *made the decision* or is decoration; whether Apify data actually entered the loop |
| **D** | Potential user (course author, ~600 learners) | Would I let this touch my course? What breaks my trust first? |
| **E** | Hostile reviewer (engineer) | Assume everything measurable is inflated; follow the weakest number to its source |
| **F** | Ethics / consent seat | Consent path, learner data, the word "personalised", the notification budget |

## 1. Openings (what each seat sees in ten minutes)

- **A:** "It notices, decides, acts, learns and reports — and I can watch it refuse. The revert is
  the strongest thing in the room. But the autonomy is running on *fixtures*; show me the clock."
- **B:** "The receipts chain, the diff, the digest, the `unmeasured` — this is the most honest
  evidence surface I have seen today. The one thing missing is a real Apify run id."
- **C:** "`app/n8n/policy_node.js` proves the decision is code. There is no exported workflow the
  canvas can run yet. Today n8n is a mirror, not the engine — that is 20% at risk."
- **D:** "Seven 'learners' got a card. Those handles are hashed fixtures. Say so out loud and I
  trust you more, not less."
- **E:** "I will try to break three things: the 4 KB digest claim, the `PA2 earned` claim, and the
  cohort delta that triggered the revert."
- **F:** "Consent gates the card; the declined learner is untouched; no learner record is written.
  Keep the phrase 'fixture cohort' in the digest and this is clean."

## 2. Findings

| # | Severity | Finding (one line) | Bound to |
|---|---|---|---|
| **J-01** | **MUST-FIX before recording** | The whole `app/` layer runs in **sim mode** (fixtures, no network, no model calls, no Apify). Judges scoring "proven in real use" may reasonably read the receipts as a live run unless every surface says otherwise. | `run_walking_skeleton.py` stamps `mode: sim` on receipts and the digest (done); **the live M1 run (Apify + n8n + a real cohort) is Phase 2 and is the only thing that closes this** |
| **J-02** | SHOULD-FIX | The hero change is a *rename* of a settings toggle. It is genuinely breaking for anyone following lesson 04, but the lesson text does not yet say what breaks; a judge may call it a "docs typo". | `course/agent-ops/lesson-04-tool-permissions/v3.md` §Practical notes — **carried into J-02b**: add one operational line *before* the hero run (do not re-anchor fixtures mid-run) |
| **J-03** | MUST-FIX (labelling) | The "notifications sent: 7" line and the revert's cohort delta are fixture-driven. Presenting them without a label is the exact wound the constitution names. | Done: the revert fixture carries `sim_cohort: true` → receipt `cohort_source: fixture (simulated)` + label; digest header carries the sim banner; `EVIDENCE.md` §4 row is labelled **sim** |
| **J-04** | **MUST-FIX for the 20% criterion** | `app/n8n/wf-cr-{0..4}` exports were claimed in `plan.md` §3 and are not in the repo. n8n must *run* the workflow and Apify must *pull* the data for the criterion to score. | Phase 2 (T16–T20); until they exist, `task.md` Phase 2 stays `[ ]` and `plan.md` is read as intent |
| **J-05** | SHOULD-FIX | "≤4 KB digest" was an unenforced claim (Art. VI). | Fixed: `test_walking_skeleton.py::test_digest_fits_the_4kb_contract` |
| **J-06** | SHOULD-FIX | `authority_pa2_earned` appears on publish receipts while the earning rule (3 consecutive accepts) is nowhere measured; the digest prints `current: unmeasured`. | Acceptable as-is (`unmeasured` is legal) — **but the pitch may not claim PA2 was "earned"**; the video says "the ladder is configured; the history prints `unmeasured`" |
| **J-07** | SHOULD-FIX | `input_hash` covers the fixture/judge payload, not the fetched source bytes. In sim that is fine; live, the snapshot hash must be the input hash. | `plan.md` §2 already requires `content_hash` per snapshot; the live wiring (Phase 2) must feed it into the receipt — noted in `WIRING.md` checklist |
| **J-08** | KNOWN LIMIT | `test_gate_parity.py` proves the two implementations agree on the frozen gold set — it cannot prove the n8n canvas embeds the same code. | Live canvas check belongs to T18; the test's docstring says exactly this |
| **J-09** | SHOULD-FIX | `app/prices.json` has every value `null` → cost talk is `unmeasured`. Correct per Art. VI, thin per judging. | Capture two real vendor prices during Phase 2 (T43); the register row N10 stays `pending capture` until then |
| **J-10** | FIXED | The revert that fires on night 2 looked like real learner telemetry. | Now `cohort_source: fixture (simulated)` + `SIMULATED COHORT` label on the receipt (see J-03) |
| **J-11** | FIXED | No single command a judge could run. | `sh app/check.sh` — whole battery, exit ≠ 0 on any failure |
| **J-12** | **MUST-FIX (honesty)** | `tasks.md` T06 claimed `AGENTS.md` + `AGENT_BOOTSTRAP_PROMPT.md` existed; only `BUILD.md` did. That is an invented-done claim of the lineage's exact wound (review 01 H3). | Fixed: `AGENTS.md` written; T06 marked `[~]` with the cut named; the task-hygiene check (`test_contracts.py`) now fails the build when a `[ ]` task names a path that already exists |

## 3. Named clashes (and how they resolved)

- **A × E — "the sim receipts are honest" vs "the sim receipts are a liability".** Resolved:
  receipts stay, but every sim surface carries the banner and the video's first spoken line
  separates *"what you are watching is the machine on fixtures"* from *"here is the live run"*.
- **C × B — "n8n is decoration" vs "the loop is real".** Resolved: both are true at different
  layers. The decision layer is real and tested (parity, gold, 13/13 selftest); the n8n canvas is
  unbuilt. The 20% criterion is only earned when T16–T20 run live.
- **D × F — "show the notifications" vs "protect the cohort".** Resolved: show the rendered card
  layout with hashed handles and the opt-out line; never show names, never claim real recipients
  until a real cohort exists.
- **E × A — "the revert proves autonomy" vs "the revert used a fake delta".** Resolved: the revert
  *mechanism* is proven (gate recorded → evaluated → undone, with its own diff and receipt); the
  delta is labelled simulated. The pitch says "rehearsed with a fixture cohort" in one breath.

## 4. Bindings

**MUST-FIX before the video:** J-01 (live run or explicit sim framing), J-04 (n8n/Apify live), J-03/J-10 (labels — done), J-12 (done).
**SHOULD-FIX:** J-05 (done) · J-09 (prices) · J-02b (one operational line in lesson 04 before the hero run).
**CUT, explicitly:** J-06 (do not claim PA2 "earned"), J-08 (canvas-embedding proof), `AGENT_BOOTSTRAP_PROMPT.md`, M4 items (replay cache, cost measurement, exhibit export) at loop expense.

## 5. Vote

- A: *continue* — "the machine earns the autonomy 25%, but not on fixtures alone; run it live."
- B: *continue* — "the evidence surface is real; the Apify run id is missing."
- C: *conditional* — "20% is at risk until workflows execute on the canvas."
- D: *continue* — "labelled and reversible; I would pilot it on my own course."
- E: *conditional* — "fix J-01, J-04, J-12; then I will believe the rest."
- F: *continue* — "consent-first; keep the fixture labels on screen."

**Verdict:** proceed to the live phase; re-convene (`reviews/04`) after the battery is re-run and
the J-rows are closed with pasted output.
