# Courserefresh — amendments (the package's own change log)
`v1.5 · Last amended D-0 · Rule (Art. XVI.4): every finding and every change to this package is a row here, and a row is `open` until its verification output is pasted into reviews/04`

Vocabulary: **open** = decided, not yet proven · **verified** = command run, output pasted in
`reviews/04` · **cut** = deliberately not done, with cause · **superseded** = replaced by a later row.

Version history of this file: v1.0 (draft) · v1.1 (F-01–F-12 reverted to `open` because no output
had been pasted — the closure rule applies to the spec's own paperwork) · **v1.2** (D-0: battery
green, `reviews/04` pastes it; F-01–F-17 verified; new D-09–D-14 from the build).

---

## 1. Findings from review 01 (the 4prd structural review)

| ID | Finding | Change made to this package | Status | Verified by (pasted in reviews/04 §3) |
|---|---|---|---|---|
| F-01 | Reference corpus asserts numbers with no receipt (invented metrics) | Art. VI + `RECEIPTS.md` (N01–N24) + `test_claims.py` (TM18) | **verified** | `test_claims.py` — 3/3, battery.txt |
| F-02 | Reference eval floors are declared then violated by its own gold sets (n=3 vs floor 40) | Art. VII + `test_gold_floor.py` (8 checks) + gold `n=59` + legal degrade line in `policy.py` | **verified** | eval report + `test_gold_floor.py` 8/8 |
| F-03 | Tasks claim Phase-0 artifacts that do not exist | `test_contracts.py` fails on a `[ ]` task naming an existing path, and on any doc path that does not resolve | **verified** | `test_contracts.py` 14/14 |
| F-04 | No traceability between stories and tests | `spec.md` §2 (36 ACs) ↔ `TRACEABILITY.md` (36 rows, checked in both directions) | **verified** | `test_contracts.py` AC checks |
| F-05 | Security material unnumbered; tests could not cite threats | `security/threat-model.md` TM01–TM18 = named checks in `test_threat_model.py` | **verified** | `test_threat_model.py` 18/18 |
| F-06 | Design system asserted in prose, not locked | `design/MASTER.md` token lockfile + banned list + `test_design.py` (5 checks) | **verified** | `test_design.py` 5/5 |
| F-07 | "Agent-operable" package assumed a human operator | root `AGENTS.md` + `app/check.sh` + `app/tools/*` + `tasks.md` TIME-NOW block + BUILD.md §4 | **verified (agent-operable)**; the human-only parts (video, sign-offs) are marked as such | battery + `checklists.md` §0 |
| F-08 | Evidence/run-log protocols absent | `EVIDENCE.md` §1–5 + `app/tools/freeze_evidence.py` + a real freeze (19 files, `MANIFEST.sha256`) | **verified** | manifest in `EVIDENCE.md` §4 |
| F-09 | Hygiene failures in the reference repo (committed build junk, dates everywhere) | `.gitignore` + `test_hygiene.py` (7 checks) + D-label convention enforced under `specs/` | **verified** | `test_hygiene.py` 7/7 |
| F-10 | Review output was narrative, not binding, and never closed | this file + `reviews/02`, `reviews/03`, and `reviews/04` (pasted output) | **verified** | `reviews/04` §2–3 |
| F-11 | Claim-lint / receipt register missing | `RECEIPTS.md` v0.3 (measured rows bold; `unmeasured` rows keep placeholders) + `test_claims.py` | **verified** | `test_claims.py` 3/3 |
| F-12 | Sim vs live confusion is not designed against | `mode` on every receipt and digest header; `cohort_source` on reverts; `SEEDED` label; TM17 | **verified** | receipts + digest + TM17 |
| F-13 | 4prd's harness loops could not be tested as written | `shared/harness.md` §11 test map + `app/check.sh` (nine stages, one exit code) | **verified** | `sh app/check.sh` → 103 PASS, exit 0 |
| F-14 | The reference's "≥2 sources" counted pages, not voices | independence is now decided **in code** from the source list's publishers (oracle + JS mirror + gold rows `cr-same-publisher-01`, `cr-three-publishers-01`) | **verified** | eval report, parity 57/57 |
| F-15 | A rehearsal could borrow the credibility of the live path | seeded events are a declared branch (`seeded_rehearsal`), only run with `--seed-demo`, and `cr-seed-02` proves a rehearsal that claims upstream sources escalates (`seeded_source_misrepresented`) | **verified** | parity + gold row + receipts |
| F-16 | Paperwork can claim closures it has not verified | F-01–F-12 reverted to `open` in v1.1 and closed here only with pasted output; the self-referential F-11 grep repaired | **verified (this file)** | `reviews/04` §3 |
| F-17 | Gold-set changes must be visible | `gold-v0.1` → `gold-v0.3`: +3 rows (independence ×2, misrepresentation ×1), version bump, hash recorded (N11b) | **verified** | `skin/gold.jsonl` header + N11b |

## 2. Decisions made during drafting and the build

| ID | Decision | Why | Status |
|---|---|---|---|
| D-01 | Subject course = *Agent Ops* (n8n + Apify), six lessons | Its sources genuinely move during a build window; the hackathon's own domain | applied |
| D-02 | PA1 = publish without notify; PA2 = publish + cohort card; breaking/deprecation requires PA2 | The ladder is about *who gets told*, not whether the write happens | applied, tested (`cr-pa1-breaking` DRAFT) |
| D-03 | Revert executes as a **new** version (never a history rewrite) | Judges can see the undo; git history stays honest | applied (`v5` restores `v3`) |
| D-04 | Micro-lesson = one concept / ≤2 min / one item; per-learner caps | "Help" that becomes noise is harm | applied |
| D-05 | No Notion mirror in the demo path | One artifact surface beats two half-synced ones | cut |
| D-06 | Column (a) of the eval is `n/a` unless a key + spend are approved at kickoff | A fabricated baseline is worse than an honest gap | applied (N05) |
| D-07 | One place for the numbers: `app/tools/metrics.py` (+ `freeze_evidence.py`) | Fewer scripts, one command per number | applied |
| D-08 | Exit codes fixed at 0/1/2/3/4 across CLI and console | The reviews and tests cite them | applied (TM14 returns 3) |
| D-09 | `design/MASTER.md` §6 names WCAG 2.2 AA; status is never colour-only | The design check asserts the floor the text states | applied |
| D-10 | AC count corrected to 36 | The table always had 36; the header said 34 — the drift Art. XVI.2 exists for | applied |
| D-11 | Receipts are **linked** (chain) *and* the run summary is declared inside the chain | A receipt row is better evidence if it is itself a signed decision; coverage stays 100% | applied (10th row, decisions ⊆ receipts) |
| D-12 | Seeded rehearsal is a policy branch, not a special case in the runner | The label must survive every path; it is now a reason code, not a comment | applied (F-15) |
| D-13 | Actor inputs are validated before the run; `ACTOR_INPUTS` at D-1 | Direct answer to criterion 3 (Apify), with the actor id and build pinned | applied (WIRING §1) |
| D-14 | Tool counts, cache size and corpus bytes are config, not claims | Keeps the live wiring honest; the numbers live where they are consumed | applied |
| D-15 | The offline twin is the demo's spine; live wiring only adds real Apify rows + real model calls | One runtime, one parity test, one evidence surface — a live failure degrades to the frozen artifacts, labelled | applied |
| D-16 | 4prd review is treated as the standard of *structure*, not of *evidence* | 3 of its 4 gold sets break its own floor; its repo tracks build artifacts | applied (reviews/01, §1) |

## 3. Warden vetoes

| ID | Veto | Lifted when | Status |
|---|---|---|---|
| W-01 | No M2+ work before M0 gate (`checklists.md` §0) is signed | all seven M0 ticks have artifacts | **partially lifted** — six of seven ticks have artifacts; the seventh (a *stranger* watching the run) needs a human, booked for the live rehearsal |

## 4. Cuts (named, with cause)

| ID | Cut | Cause | Compensating evidence |
|---|---|---|---|
| C-01 | Notion lesson mirror | Time; one artifact surface is cleaner | repo diff + staged learner notifications |
| C-02 | Email + Telegram dual channel | Extra credential for little demo value | one channel, rate-limited |
| C-03 | Personalisation of micro-lesson copy | Learner profiling; out of scope by Art. IV | one lesson for every stuck learner |
| C-04 | 30-minute cadence experiment | Apify unit budget belongs to the hero run | cadence is printed, measured when live |
| C-05 | Comparator column (a) | No key/spend approved at kickoff (D-06) | `n/a` with the reason |
| C-06 | Live console | Phase 2 (T15); the twin's `--report` renders the same digest | digest artifact + `INTERFACES` spec held for the console |

## 5. Findings from review 04 (post-build panel)

| ID | Finding (seat) | Change made | Status | Verified by |
|---|---|---|---|---|
| F-18 / K-01 | Receipts name artifacts that nothing re-verifies (staff engineer) | `app/tests/test_artifacts.py`: body/diff hashes recomputed from disk, predecessor existence, revert restoration, card contract | **verified** | §3.5 of `reviews/04`, 7/7 |
| F-19 / K-02 | Per-learner notification caps configured but not consulted on the publish path (learner seat) | caps enforced in `notify_cohort`, skips recorded on the artifact, digest prints "held by cap" | **verified** | §3.5 check 6 |
| F-20 / K-03 | Per-concept micro-lesson cap configured, not enforced (product lead) | promoted to a policy branch (`rate_limited`) consumed by oracle and node | **verified** | §3.5 check 7 + parity probe |
| F-21 / K-04 | The revert's CHANGELOG entry carried no diff and no receipt id (founder) | `revert_version` writes the diff line so stamping lands; `v5 → rcpt-11-450-008` | **verified** | §3.6 |
| F-22 / K-08 | Parity covered gold rows only; new branches could drift (staff engineer) | named probes (`probe-concept-cap`, `probe-frozen-learner`) in `test_gate_parity.py` | **verified** | §3.3 |
| F-23 / K-05 | n8n is a mirror, not the engine (judge) | named open; fallback ladder pre-registered | **open** | closes with a real execution id (T12) |
| F-24 / K-06 | No real learner has received a card (product lead) | named open; the video says "staged" unless one is delivered | **open** | closes with one delivered card (T13) |
| F-25 / K-07 | No real Apify actor run id (judge) | named open; actor pins and normaliser exist | **open** | closes with the first run id (T10) |

## 6. Findings from review 05 (the specialist debate)

| ID | Finding (seat) | Change made | Status | Verified by |
|---|---|---|---|---|
| F-26 / AP-01 | Independence counted pages, not voices (Apify) | `role` on every source; oracle + node count only non-`none` voices; gold rows `cr-mirror-only-01`, `cr-mirror-plus-two-01`; `WIRING.md` §2b | **verified** | `reviews/05` §3.2–3.3, gold-v0.3 n=59 |
| F-27 / T-01 | No objectives, prerequisites or item→objective map (teacher) | `course/agent-ops/curriculum.json`; `test_curriculum.py` (8 checks) | **verified** | `reviews/05` §3.1 |
| F-28 / T-02 | "Regenerates the quiz" was unevidenced (teacher) | `quiz_patch` → versioned item with `regenerated_by`; `reset_course.py` restores authored text; lesson-04 quiz added | **verified** | digest line + `test_curriculum.py` |
| F-29 / T-03 | Micro-lesson concept cap unenforced (teacher) | policy branch `rate_limited` + `probe-concept-cap` parity probe | **verified** | `test_artifacts.py` check 7, parity probes=2 |
| F-30 / ST-01 | Cards used engineering wording (learner) | `learner_facing` copy per event (≤240 chars), used by the notifier; `test_curriculum.py` | **verified** | `reviews/05` §3.1 |
| F-31 / UX-01 | Three locked colours fail AA (UX) | `--status-unknown` `#C5A202`→`#7A5C00`, `--ink-faint`→`#68604F`, `--rule`→`#8E8160`, `--status-queue`→`#96550A`; measured table in `MASTER.md` §1.1 | **verified** | `test_design.py` 6/6 |
| F-32 / UX-02 | AA claimed while the console did not exist (UX) | console built from lockfile tokens (`app/out/digest.html`), AC-14.1–14.3, `--selftest` token check | **verified** | `reviews/05` §3.4 |
| F-33 / SRE-01 | A failed write was reported twice (SRE) | failure returned to the loop, recorded once; `--chaos write-fail`; frozen rehearsal | **verified** | `reviews/05` §3.6, `test_artifacts.py` |
| F-34 / N8N-01…05 | No canvas contract (execute-once, error workflow, queue branch, instance pin) (n8n) | `WIRING.md` §3.1 requirements table, each row naming where it shows | **open** | closes with a real execution id (T12) |
| F-35 / AP-02 | No API-contract drift check; retry budget in prose (Apify) | `WIRING.md` §6.1 row 4 + §3.1 retry row; `source_stale` degraded receipt documented | **open** | closes with the first live actor run (T10) |
| F-36 / ST-03 | A revert on a simulated cohort read like a live one (learner) | `cohort_source: fixture (simulated)` on the receipt | **verified** | `reviews/05` §3.6 |

## 7. Decisions from the debate

| ID | Decision | Why |
|---|---|---|
| D-17 | The console is **one static page built from the lockfile tokens**, refusals first; filters are Phase 2 | the digest is the product; a half-built app would be a lie with a nicer font |
| D-18 | Source `role` is assigned per host *and path prefix* in `SOURCE-PLAN.md`, and printed on the receipt | independence has to be visible where it is decided |
| D-19 | A change regenerates the quiz item it affects and **names** downstream lessons instead of rewriting them unattended | the teacher's condition, and the smallest change that keeps a course coherent |
| D-20 | `unmeasured` beats a plausible figure, even when a judge is watching — and the video says the word out loud | Art. VI survives contact with the demo |
| D-21 | A rehearsal may never borrow the credibility of the live path: seeded events carry `seeded_rehearsal` as a reason code, reverted cohorts carry `cohort_source`, and the console shows the mode in its header | the difference between a demo and a deception is one label |

## 7b. Findings and decisions from round 3 (the build, `reviews/06`)

| ID | Finding (seat that found it) | Change made | Status | Verified by |
|---|---|---|---|---|
| F-37 / B-01 | Credentials in the process environment were never read: keys pasted as `APIFY_TOKEN=… python3 app/run_live.py` were silently inert (SRE) | three-source resolution (explicit > environment > `.env` > defaults), filtered to project prefixes; `sources` map tells you where every value came from | **verified** | `test_live_modules.py` (env precedence) |
| F-38 / B-03 | Guard helpers return `(ok, reason)` tuples; two call sites treated them as booleans, so a rejected host read as allowed (JEV) | unpack at every call site and record the reason on the refusal | **verified** | `test_live_modules.py` (`host_not_allowlisted`) |
| F-39 / B-05 | Dedupe by content hash alone collapsed two publishers' copies of one page into a single voice — corroboration would have been wrong in both directions (Apify) | dedupe per `source_id:hash`; baselines seeded with the same shape | **verified** | E8 cycle: one voice → refusal, two voices → publish |
| F-40 / B-08 | Claim clustering produced one cluster per snapshot, so the same fact published twice per cycle (JEV) | Jaccard ≥ 0.25 claim overlap, authoritative+earliest representative, one publish per cycle, extras deferred with a reason | **verified** | E8 cycle (1 publish, 1 escalate) |
| F-41 / B-11 | The judge key was never validated: a wrong key surfaced as `unknown_state` refusals on stage (JEV) | `probe_provider()` validates with one `GET {base}/models` and says whether the configured model is listed — never the key | **verified** | `--preflight --probe` |
| F-42 / B-15 | `--via-n8n` compared only the action; two different refusals looked like agreement (SRE) | `canvas_agrees()` compares action **and** sorted reason codes; a mismatch writes nothing, marks materiality `ambiguous`, and records both decisions | **verified** | `test_live_modules.py` (parity + mismatch) |
| F-43 / B-09 | The export contract test asserted a fixed count and derived workflow names from file names — it would have passed while the error workflow was missing (n8n) | per-file name↔number check, execute-once guard required, sticky-note required, count read from the export set | **verified** | `test_contracts.py` 14/14 |
| F-45 / B-17 | The live learn phase could never revert: the rulebook takes a nested `cohort {n, quiz_delta, hours_since_publish}` and the engine passed flat fields, so the branch was dead code that looked wired (SRE) | `hours_since_publish()` (receipts → CHANGELOG), nested cohort at the call site, gate arithmetic on the receipt label; sim runs still say `fixture (simulated)` | **verified** | `test_live_modules.py` (learn→revert) |
| F-44 / B-14 | Nothing stopped a number reaching a learner-facing rewrite that no quote supported (teacher) | `validate_render` refuses numerals absent from the quote spans and replacements over 400 chars | **verified** | `test_live_modules.py` (anchored render) |

| ID | Decision (round 3) | Why |
|---|---|---|
| D-22 | The canvas decides whenever it is reachable; the Python oracle polices it; agreement is on action **and** reason codes; disagreement stops the cycle | criterion 3 wants n8n to power the system, Art. XIV wants the loop to survive its platforms, and a decision two runtimes disagree about is not a decision |
| D-23 | The `file` notify channel is the default and may never claim `delivered`; a channel without credentials fails loudly | "staged" and "sent" are different words, and the difference is the whole consent story |
| D-24 | Telemetry refusal happens **before** storage, with generic error text; handles are hashed by the client, and the server refuses anything else | the smallest possible surface for learner data is none |
| D-25 | A cohort below the floor prints `unmeasured` with its reason; no revert is ever triggered by a number that does not exist | Art. VI applied to the learning loop, not just to the report |
| D-26 | `--preflight` is the release note: the four claims (`apify powers the system`, `n8n runs the decisions`, `live model calls`, `learner cards delivered`) are allowed only when their platform is wired | the video may not say a thing the preflight would contradict |
| D-27 | Six exports, not five: `wf-cr-9-errors` is attached to every workflow at import time so an unhandled throw lands as a receipt instead of silence | review 05 N8N-03, now enforced by `test_contracts.py` |
| D-28 | `units_per_run: 1` with the phrase "declared 1 run = 1 unit" written into the ledger row | `WIRING.md` §5 has no price; an approximation that names itself is honest, a number that looks measured is not (Art. VI) |
| D-30 | The learn phase measures the gate window from receipts, not a configured number: if nothing published the lesson, the gate reads `measurement_incomplete` and nothing reverts | a window that cannot be dated is not a window (Art. VI) |
| D-31 | A run is handed back through `collect_live.py`, which redacts every secret value it can see, **refuses to finish (exit 3)** if one survives, and summarises learner telemetry as counts instead of copying it | a handoff that might carry a key is not a handoff, it is a leak with a README |
| D-29 | The build is recorded as **peer-supervised**: each component has a builder seat and a supervisor seat, and the 16 findings in `reviews/06` carry the seat that found them | the user asked for the personas to build while supervising each other; the record is what makes that checkable |

## 8. The one row that will matter most

| ID | Statement | Status |
|---|---|---|
| X-01 | Every claim in this package is either measured with an artifact, configured, or written `unmeasured`. | **verified** — `reviews/04` §3 pastes `test_claims.py` (3/3) and the register's measured rows; every other value is `<placeholder>`-tagged |
| X-02 | The live wiring (Apify actors, model calls, console, cohort) is the remaining gap; the package says so wherever it matters (`reviews/04` §4, tasks `[ ]`/`[~]`, `EVIDENCE.md` E7, `RECEIPTS.md` N13/N14/N20–N22). | open by design — closes only with real run ids |
| X-03 | Round 3 closed the *build* gap: every component runs and is tested with zero credentials (`SETUP.md` §1, E8, E9), and the only input left is the keys. | **verified** — `sh app/check.sh` 179 PASS / 13 stages; `reviews/06` §5 sign-off with four named conditions |
