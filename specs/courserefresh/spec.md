# Courserefresh — spec (the WHAT)
`v0.1 (draft) · Depends on: constitution.md; shared/{harness,data-model,interfaces,eval}.md`

**One sentence.** Courserefresh keeps a course true to a moving subject: it notices when the world
a lesson describes has changed, decides — by rulebook, on corroborated evidence — whether the
lesson is now wrong, rewrites the lesson and its quiz when it is, tells the humans who opted in,
watches whether the change helped, and **reverts its own edit** when it did not.

**The subject taught.** *Agent Ops* — a six-lesson course (n8n + Apify + agents in production).
The subject is chosen because its sources move during any build window: n8n and Apify ship
releases on a weekly cadence, and their docs/changelogs are public, fetchable, and independent of
each other. The course lives at `course/agent-ops/`; learners read it there and in Notion.

**Who it serves.** Course authors with fast-moving technical material (primary), and their learners
(secondary). The author gets a morning report and every edit reversible; the learner gets an honest
"this lesson changed, here's why" card and help *before* they have to ask.

---

## 1. The loop, in the product's words

| Phase | Observable behaviour | Cadence |
|---|---|---|
| **Notice** | Scheduled Apify runs fetch the declared sources; snapshots are hashed and cached; duplicate events are skipped | every `scan.every_min` (default 60; measured, never called "real-time") |
| **Verify** | Claims are extracted with verbatim quotes; independence groups are resolved; uncorroborated or contradictory claims get no publish | per event |
| **Decide** | The `POLICY` node (deterministic, one screen) returns one action + reason codes under the current authority level | per event, seconds |
| **Act** | A versioned lesson body + diff + quiz + CHANGELOG commit on `bot/courserefresh`; consented learners get a card | ≤ one publish per scan cycle |
| **Learn** | A cohort window is evaluated against the publish's revert gate; stuck signals dispatch micro-lessons; a satisfied gate reverts | every 15 min, gates at 48 h |
| **Report** | The digest (refusals first) at 07:30 and on demand; the console shows the same receipts | daily |

## 2. User stories & acceptance criteria (42 ACs)

Priority: **P0** = the demo dies without it · **P1** = proves the "learns" clause · **P2** = stretch.

### US-1 (P0) — As the author, I want the system to notice real changes without me.
- **AC-1.1** A scheduled n8n run executes the pinned Apify actor(s) and turns dataset rows into
  `SourceSnapshot`s with `content_hash`; a run with zero new snapshots writes a receipt and prints
  `no_delta`. *Proof:* `python3 app/run_walking_skeleton.py --selftest` (notice phase) and the
  live run's `app/out/run_log.jsonl`.
- **AC-1.2** A re-fetched unchanged source produces no change event (`content_hash` equality).
  *Proof:* `test_walking_skeleton.py::test_dedupe_*`.
- **AC-1.3** The measured cadence (not the configured one) appears in the digest's run header.
  *Proof:* digest header line, `RECEIPTS.md` N03.

### US-2 (P0) — As the author, I want only corroborated changes to move my course.
- **AC-2.1** A claim survives only with a verbatim quote anchored in the cached snapshot.
  *Proof:* `test_threat_model.py::TM03`, `cr-ambiguous-01` gold row.
- **AC-2.2** `PUBLISH` requires `sources_verified ≥ 2` from distinct independence groups.
  *Proof:* `cr-single-01`, `cr-conflict-01` gold rows; `policy.py --explain`.
- **AC-2.3** Two pages from one publisher count as one source. *Proof:* `SOURCE-PLAN.md` §2 +
  `test_policy.py` (group logic).

### US-3 (P0) — As the judge, I want to see where the rules live.
- **AC-3.1** One executable rulebook exists in two parity-tested runtimes.
  *Proof:* `node app/tests/test_gate_parity.py` — 42/42 rows agree; `POLICY` node visible on canvas.
- **AC-3.2** Every decision carries ≥1 reason code from the closed taxonomy, or `unknown_state`.
  *Proof:* `test_contracts.py` (taxonomy parse), `--selftest` receipt validation.
- **AC-3.3** Malformed/out-of-range input escalates; the node never throws.
  *Proof:* `test_policy.py::test_coercion_*`.

### US-4 (P0) — As the author, I want a change to be a real, inspectable edit.
- **AC-4.1** A `PUBLISH` writes `v<n+1>.md`, `diffs/v<n+1>.diff`, a `CHANGELOG.md` entry, and a
  commit whose message names the receipt. *Proof:* `--selftest` publish check + `git log` excerpt in
  `EVIDENCE.md`.
- **AC-4.2** Every version carries its `sources[]` block and a `revert_gate`.
  *Proof:* front-matter validation in `test_contracts.py`; `cr-cosmetic-01` gold row shows the gate.
- **AC-4.3** A revert is a new version, never a rewrite of history.
  *Proof:* `--selftest` revert check; night-2 run log.

### US-5 (P0) — As the author, I want the system to refuse clearly.
- **AC-5.1** Single-source, contradictory, hostile, unreachable, and assessment-touching changes
  each produce a visible escalation with a reason code and a preserved quote.
  *Proof:* `cr-inject-01`, `cr-single-01`, `cr-conflict-01`, `cr-paywall-01`, `cr-assess-01` gold
  rows and their `receipt` excerpts in `EVIDENCE.md`.
- **AC-5.2** A refusal is never rewritten into an action by a human override for the PA3 classes.
  *Proof:* `--selftest` "human override refused" check (exit 4).
- **AC-5.3** The digest lists refusals **first**. *Proof:* `test_walking_skeleton.py` digest check.

### US-6 (P0) — As the author, I want a morning report I can read in one minute.
- **AC-6.1** The digest renders from receipts only, with sections in the fixed order, ≤ 4096 bytes.
  *Proof:* `test_walking_skeleton.py::test_digest_fits_the_4kb_contract`; digest artifact.
- **AC-6.2** Every number in the digest resolves to a receipt or says `unmeasured`.
  *Proof:* `test_claims.py` + digest spot-check in the eval report.
- **AC-6.3** The digest names the run's mode (`live`/`sim`/`degraded`) — always.

### US-7 (P0) — As the author, I want the system to undo its own mistakes.
- **AC-7.1** A publish without a `revert_gate` is impossible (policy refuses). *Proof:* `TM08`-style
  negative row in `test_policy.py`.
- **AC-7.2** When the gate is satisfied (n≥5, 48 h, `quiz_delta ≤ 0`), the revert executes without
  a human and announces itself to the same cohort. *Proof:* night-2 run log + receipt with
  `revert_gate_satisfied`.
- **AC-7.3** When the gate is unmeasurable, the digest says `unmeasured` and no revert claim is made.
  *Proof:* `unmeasured` row in `RECEIPTS.md` N07; digest line.

### US-8 (P1) — As a learner, I want help before I ask for it.
- **AC-8.1** The stuck rule (`consecutive_wrong ≥ 2` or `dwell ≥ 3 × median`) dispatches a
  micro-lesson only with consent and within the messaging caps. *Proof:* telemetry fixture run +
  rate-limit checks in `--selftest`/`test_policy.py`.
- **AC-8.2** A refused/absent consent produces `NO_CHANGE(consent_missing)` and nothing is sent.
  *Proof:* fixture learner `learner:07` (consent false) in the run log.
- **AC-8.3** The micro-lesson is one concept, ≤2 min reading, one practice item, with opt-out.
  *Proof:* artifact in `app/out/micro-lessons/`, format check in `test_contracts.py`.

### US-9 (P1) — As the judge, I want to see autonomy that is earned.
- **AC-9.1** The ladder state is derived from receipts (3 consecutive accepted publishes ⇒ PA2;
  one rollback ⇒ PA0 for that lesson), never asserted. *Proof:* `policy.py --dump` + `--selftest`
  ladder check; digest prints the state.
- **AC-9.2** PA3 decisions are refused for overrides (exit 4 / HTTP 409). *Proof:* `--selftest`
  refusal check.
- **AC-9.3** The digest prints the current authority and how it was earned.

### US-10 (P0) — As an operator, I want the system's limits enforced in code.
- **AC-10.1** The kill switch freezes all writes within one iteration and is visible on subsequent
  receipts and the digest. *Proof:* `--selftest` freeze check.
- **AC-10.2** Budgets are checked before spending; exhaustion escalates (`over_budget`), never
  silently bypasses. *Proof:* `cr-budget-01` gold row + `--selftest` budget check.
- **AC-10.3** The write path cannot leave `course/**`; hosts must be allowlisted, HTTPS only.
  *Proof:* `test_threat_model.py::TM04/TM16`.

### US-11 (P0) — As the judge, I want proof rather than adjectives.
- **AC-11.1** Receipts are chained; `verify_chain()` passes at run end; coverage is 100%.
  *Proof:* `--selftest` chain checks; `run_log.jsonl`.
- **AC-11.2** The decision eval runs on the frozen gold set (n ≥ 40) with the three columns and the
  two build-breaking invariants. *Proof:* `python3 specs/courserefresh/skin/policy.py --eval
  specs/courserefresh/skin/gold.jsonl`; report under `app/out/eval/`.
- **AC-11.3** Claims in this package carry a register row with value, status, artifact, command.
  *Proof:* `test_claims.py`.

### US-12 (P0) — As the team, we want the video and the live demo to be honest and rehearsed.
- **AC-12.1** The 2-minute video follows the shot list and shows: a refusal, a real change, a stuck
  learner, a revert, and the logs behind all four. *Proof:* `VIDEO-SHOTLIST.md` checklist.
- **AC-12.2** Every fallback shown is the pre-registered one; the offline twin is labelled on
  screen. *Proof:* `checklists.md` §4.
- **AC-12.3** The live final demos the same loop against the running system (or the labelled twin),
  and the Q&A answers come from `JUDGING-MAP.md`. *Proof:* checklist sign-off.

### US-13 (P0) — As the teacher, I want the course to still make sense after the agent edits it.
- **AC-13.1** Every lesson carries objectives and prerequisites; every quiz item maps to one of them;
  the mapping is a file, not a convention. *Proof:* `python3 app/tests/test_curriculum.py`;
  `course/agent-ops/curriculum.json`.
- **AC-13.2** A change that claims to affect an item regenerates that item — versioned, traceable to
  the event that did it, and restored by `reset_course.py`. *Proof:* `test_curriculum.py`
  (regenerated item is well-formed and traceable).
- **AC-13.3** A change names the downstream lessons to revisit and never rewrites them in the same
  unattended pass. *Proof:* digest line `downstream to revisit`; `test_curriculum.py`.

### US-14 (P1) — As the person reading the console, I want it to obey the same rules as the receipts.
- **AC-14.1** The console page is generated from the design lockfile tokens, contains no scripts and
  no remote resources, and lists refusals first, like the digest. *Proof:* `--selftest` (colours exist
  in the lockfile) + `TM11`.
- **AC-14.2** Every locked colour is measured for contrast and passes AA on both papers; hairlines
  pass the 3:1 non-text floor. *Proof:* `python3 app/tests/test_design.py`.
- **AC-14.3** Hostile text that reaches a receipt is escaped in the console, never rendered.
  *Proof:* `TM11` (escapes a `<script>` probe).

## 3. Non-goals (things this spec refuses to be)

1. **No grading, no learner records, no scores** — the machine never touches an assessment or a
   learner's record (Art. IV.1).
2. **No chat interface** — there is no "ask the course anything" box; the loop runs without prompts.
3. **No new course authoring** — Courserefresh edits the course it has (six lessons), it does not
   invent lessons.
4. **No "personalisation"** — learner data triggers help, never a different syllabus for different
   people.
5. **No platform sprawl** — n8n + Apify are the engine; every additional tool must replace one of
   them, not sit beside them (Art. XIII).
6. **No claim of real-time** — this loop's honest unit is the scan cycle (`harness.md` §5).
7. **No LMS integration in v1** — the course is a folder in a repo; "sync to the platform" is a
   documented export step, not a claim (`plan.md` §7). Saying "it updates your course" while writing
   to a repository would be the kind of rounding this spec exists to prevent.

## 4. Success metrics (measured, not asserted — `RECEIPTS.md`)

| Metric | Target | Where it is proven |
|---|---|---|
| hostile → publish | 0 (build-breaking) | gold eval report |
| unsupported → publish | 0 (build-breaking) | gold eval report |
| receipt coverage | 100% | run log |
| chain integrity | true, every run | run log |
| real, corroborated change detected live | ≥1 during D1 (or the honest fallback, labelled) | run log + `EVIDENCE.md` |
| unattended window | ≥ 3 h with the loop running and the digest written | run log timestamps |
| learner dispatches | ≥1 consented micro-lesson (live or labelled sim) | dispatch receipts |
| reverts | ≥1 executed on a satisfied gate (live or labelled rehearsal) | receipt `revert_gate_satisfied` |
| digest size | ≤ 4096 bytes | contract test |
| cost per change | reported; `unmeasured` until prices captured | `RECEIPTS.md` N10 |

## 5. Risks & what would make us stop

| Risk | Signal | Pre-registered response |
|---|---|---|
| No source moves during the window | 0 events over 12 h | run the labelled rehearsal event (`cr-seeded-01`); say so on screen |
| n8n/Apify unavailable | preflight failure | offline twin + recorded canvas; the video says which |
| Actor output shape drifts | discarded rows > 0 | degrade to observe-only; digest names the actor |
| A publish proves wrong on night 2 | gate satisfied | revert (that is the product working) |
| A judge reads the sim receipts as live | — | the digest header and the video's first line say `mode`; Art. VI.3 |

## 6. Open questions (resolved at kickoff; see `AMENDMENTS.md`)

1. Which exact actor versions for the two source families? → `WIRING.md` §1, pinned at D-1.
2. Does the real cohort reach n≥5 for gate evaluation? → `LEARNER-PLAN.md` target; if not, gates are
   `unmeasured` and the video says so.
3. Is a Notion mirror affordable inside the window? → P1 cut candidate #1 (`plan.md` §7).
