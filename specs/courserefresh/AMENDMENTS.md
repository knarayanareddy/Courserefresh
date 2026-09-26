# Courserefresh — amendments (the package's own change log)
`v1.3 · Last amended D-0 · Rule (Art. XVI.4): every finding and every change to this package is a row here, and a row is `open` until its verification output is pasted into reviews/04`

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
| F-02 | Reference eval floors are declared then violated by its own gold sets (n=3 vs floor 40) | Art. VII + `test_gold_floor.py` (8 checks) + gold `n=57` + legal degrade line in `policy.py` | **verified** | eval report + `test_gold_floor.py` 8/8 |
| F-03 | Tasks claim Phase-0 artifacts that do not exist | `test_contracts.py` fails on a `[ ]` task naming an existing path, and on any doc path that does not resolve | **verified** | `test_contracts.py` 13/13 |
| F-04 | No traceability between stories and tests | `spec.md` §2 (36 ACs) ↔ `TRACEABILITY.md` (36 rows, checked in both directions) | **verified** | `test_contracts.py` AC checks |
| F-05 | Security material unnumbered; tests could not cite threats | `security/threat-model.md` TM01–TM18 = named checks in `test_threat_model.py` | **verified** | `test_threat_model.py` 18/18 |
| F-06 | Design system asserted in prose, not locked | `design/MASTER.md` token lockfile + banned list + `test_design.py` (5 checks) | **verified** | `test_design.py` 5/5 |
| F-07 | "Agent-operable" package assumed a human operator | root `AGENTS.md` + `app/check.sh` + `app/tools/*` + `tasks.md` TIME-NOW block + BUILD.md §4 | **verified (agent-operable)**; the human-only parts (video, sign-offs) are marked as such | battery + `checklists.md` §0 |
| F-08 | Evidence/run-log protocols absent | `EVIDENCE.md` §1–5 + `app/tools/freeze_evidence.py` + a real freeze (18 files, `MANIFEST.sha256`) | **verified** | manifest in `EVIDENCE.md` §4 |
| F-09 | Hygiene failures in the reference repo (committed build junk, dates everywhere) | `.gitignore` + `test_hygiene.py` (7 checks) + D-label convention enforced under `specs/` | **verified** | `test_hygiene.py` 7/7 |
| F-10 | Review output was narrative, not binding, and never closed | this file + `reviews/02`, `reviews/03`, and `reviews/04` (pasted output) | **verified** | `reviews/04` §2–3 |
| F-11 | Claim-lint / receipt register missing | `RECEIPTS.md` v0.3 (measured rows bold; `unmeasured` rows keep placeholders) + `test_claims.py` | **verified** | `test_claims.py` 3/3 |
| F-12 | Sim vs live confusion is not designed against | `mode` on every receipt and digest header; `cohort_source` on reverts; `SEEDED` label; TM17 | **verified** | receipts + digest + TM17 |
| F-13 | 4prd's harness loops could not be tested as written | `shared/harness.md` §11 test map + `app/check.sh` (nine stages, one exit code) | **verified** | `sh app/check.sh` → 92 PASS, exit 0 |
| F-14 | The reference's "≥2 sources" counted pages, not voices | independence is now decided **in code** from the source list's publishers (oracle + JS mirror + gold rows `cr-same-publisher-01`, `cr-three-publishers-01`) | **verified** | eval report, parity 57/57 |
| F-15 | A rehearsal could borrow the credibility of the live path | seeded events are a declared branch (`seeded_rehearsal`), only run with `--seed-demo`, and `cr-seed-02` proves a rehearsal that claims upstream sources escalates (`seeded_source_misrepresented`) | **verified** | parity + gold row + receipts |
| F-16 | Paperwork can claim closures it has not verified | F-01–F-12 reverted to `open` in v1.1 and closed here only with pasted output; the self-referential F-11 grep repaired | **verified (this file)** | `reviews/04` §3 |
| F-17 | Gold-set changes must be visible | `gold-v0.1` → `gold-v0.2`: +3 rows (independence ×2, misrepresentation ×1), version bump, hash recorded (N11b) | **verified** | `skin/gold.jsonl` header + N11b |

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

## 6. The one row that will matter most

| ID | Statement | Status |
|---|---|---|
| X-01 | Every claim in this package is either measured with an artifact, configured, or written `unmeasured`. | **verified** — `reviews/04` §3 pastes `test_claims.py` (3/3) and the register's measured rows; every other value is `<placeholder>`-tagged |
| X-02 | The live wiring (Apify actors, model calls, console, cohort) is the remaining gap; the package says so wherever it matters (`reviews/04` §4, tasks `[ ]`/`[~]`, `EVIDENCE.md` E7, `RECEIPTS.md` N13/N14/N20–N22). | open by design — closes only with real run ids |
