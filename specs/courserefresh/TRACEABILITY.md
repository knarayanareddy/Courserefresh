# Courserefresh — traceability (every acceptance criterion, its proof, its evidence)
`v0.1 (draft) · Rule: an AC is closed only when the command has run and the artifact exists (Art. XVI.4)`

`spec.md` carries the AC text; this file carries the binding to a command and to the artifact that
lands in `EVIDENCE.md`. `test_contracts.py` parses both files and fails if they disagree in either
direction (an AC with no row, a row with no AC). **Nothing is "verified" until the artifact exists.**

| AC | Command / test | Evidence artifact | Video beat |
|---|---|---|---|
| AC-1.1 | `--selftest` notice check; live run log | `app/out/run_log.jsonl` (snapshots, no_delta) | 0:12 proof |
| AC-1.2 | `test_walking_skeleton.py::test_dedupe_*` | run log dedupe rows | — |
| AC-1.3 | digest header check | `app/out/digest.md` header | 0:12 |
| AC-2.1 | `TM03` + `cr-ambiguous-01` | eval report row; receipt quote | 0:30 refusal |
| AC-2.2 | `cr-single-01`, `cr-conflict-01` gold rows | eval report; receipts | 0:30 |
| AC-2.3 | `test_policy.py::test_independence_groups` | test output | — |
| AC-3.1 | `node app/tests/test_gate_parity.py` | parity output (42 rows) | 1:40 canvas |
| AC-3.2 | `test_contracts.py` taxonomy parse + receipt validation | test output | 1:40 |
| AC-3.3 | `test_policy.py::test_coercion_*` | test output | — |
| AC-4.1 | `--selftest` publish check | `course/**/v4.md`, `diffs/v4.diff`, `git log` | 0:45 action |
| AC-4.2 | front-matter validation | `sources:` + `revert_gate` blocks in the version | 0:45 / 1:20 |
| AC-4.3 | `--selftest` revert check | night-2 log, `v5.md` = restored body | 1:20 undo |
| AC-5.1 | five trap rows | eval report + five receipt excerpts | 0:30 refusal |
| AC-5.2 | `--selftest` human-override refusal | selftest output (exit 4) | — |
| AC-5.3 | `test_walking_skeleton.py` digest check | digest, refusals first | 0:12 |
| AC-6.1 | `test_digest_fits_the_4kb_contract` | digest artifact + byte count | 0:12 |
| AC-6.2 | `test_claims.py` + digest spot-check | claim register rows | — |
| AC-6.3 | digest header | `mode:` line | 0:12 first line |
| AC-7.1 | `test_policy.py` no-gate publish row | test output | — |
| AC-7.2 | night-2 run log | receipt `revert_gate_satisfied` | 1:20 |
| AC-7.3 | gate `unmeasured` row | digest learner section | 1:20 |
| AC-8.1 | telemetry fixture run + caps check | dispatch receipt | 1:05 learner |
| AC-8.2 | fixture `learner:07` (consent false) | run log `NO_CHANGE(consent_missing)` | 1:05 |
| AC-8.3 | micro-lesson format check | `app/out/micro-lessons/*.md` | 1:05 |
| AC-9.1 | `policy.py --dump` + ladder check | receipt history; digest authority line | 1:35 |
| AC-9.2 | `--selftest` PA3 override refusal | selftest output | 1:35 |
| AC-9.3 | digest authority line | digest | 1:35 |
| AC-10.1 | `--selftest` freeze check | receipts with `freeze_active` | — |
| AC-10.2 | `cr-budget-01` + budget check | eval report; selftest output | — |
| AC-10.3 | `TM04`, `TM16` | test output | — |
| AC-11.1 | `--selftest` chain checks | run log `chain_verified_at_end: true` | 1:40 |
| AC-11.2 | `policy.py --eval …/gold.jsonl` | `app/out/eval/<version>/report.txt` | 0:12 proof |
| AC-11.3 | `test_claims.py` | register rows | — |
| AC-12.1 | checklist §4 | video file + shot-list ticks | whole video |
| AC-12.2 | checklist §4 | labelled fallbacks on screen | as used |
| AC-12.3 | checklist §5 | live-final rehearsal notes | 16:15 |

**Closing rule.** Before the video is submitted, every row above must be either `verified`
(artifact path recorded in `EVIDENCE.md` §3) or explicitly `[~] cut` with its cause. There is no
third state. Any row still open at 14:00 on D2 is a line the video may not say.
