# Courserefresh — tasks (the TODO, in gated order)
`v0.4 · Last amended D-0 · Executor: the build agent (see BUILD.md §0) · Depends on: spec.md, plan.md`

**Done-done** = the acceptance criterion passes **and** the command in `TRACEABILITY.md` has been
run **and** its output/link is in `EVIDENCE.md`. Nothing else counts as done. State vocabulary:
`[ ]` todo · `[x]` done-done · `[~]` cut/degraded (say what, in the task) · `[!]` blocked (say who).

**TIME-NOW block.** `D-label: D-0 · mode: sim green · hero run: cr-20260926-1411-450 (offline twin) · live wiring: not yet · freeze: off`

---

## M0 — Walking skeleton (the loop, ugly, end to end)

| ID | Task | Done when | Status |
|---|---|---|---|
| T01 | Real course artifact: six lessons (v1/v3 bodies), quizzes, CHANGELOG | front matter parses; the twin reads and rewrites it | `[x]` |
| T02 | `app/run_walking_skeleton.py`: notice→verify→decide→act→learn→report over fixtures | `--selftest` 13/13; `--report` renders | `[x]` |
| T03 | Receipts: append-only JSONL, linked chain, 100% coverage, `verify_chain()` | selftest chain+coverage checks; TM15 tamper check | `[x]` |
| T04 | Publish path: `v<n>.md`, diff, CHANGELOG line, gate recorded | `lesson-04` v3→v4 in the hero run; receipt names it | `[x]` |
| T05 | Refusal path: hostile event escalates, quote preserved, publish = 0 | receipt `injection_or_jailbreak`; TM01 | `[x]` |
| T06 | Revert path: gate recorded at publish; satisfied gate restores as a new version | `lesson-04` v4→v5 (v5 = v3 body + revert note); receipt `revert_gate_satisfied` | `[~]` — proven on the fixture cohort (labelled `fixture (simulated)`); a *live* gate needs the live cohort |
| T07 | Kill switch: `--pause`/`--resume`, freeze visible on receipts, token gate | selftest "no writes while frozen"; TM14 (exit 3) | `[x]` |
| T08 | Digest v0 from receipts, refusals first, ≤4 KB, mode header | digest check; 1323 bytes; 4 KB contract test | `[x]` |
| T09 | **M0 GATE:** a stranger watching the run says *"it changed the lesson by itself, and it refused this one"* | sign-off in `reviews/04` §0 | `[!]` — six of seven ticks have artifacts; the *stranger* tick needs a human (booked for the live rehearsal) |

## M1 — Live engine (Apify + n8n really move the course)

| ID | Task | Done when | Status |
|---|---|---|---|
| T10 | Apify actors pinned (id+build) and called from `wf-cr-0-scan`; dataset → snapshot normaliser | one real actor run id in `WIRING.md` §6; snapshots cached | `[~]` — the pin contract and the normaliser exist (`app/n8n/wf-cr-0-scan.json`); no real run id yet (no credentials) |
| T11 | Scan schedule with dedupe (content hash) and zero-new = `no_delta` | two consecutive runs behave | `[~]` — dedupe proven offline (second run: 0 publishes); no schedule yet |
| T12 | Triage live: observe + judge calls, quote anchoring, POLICY node, receipt | receipts with judge answers and `input_hash` | `[~]` — logic + parity 57/57; model calls are fixture-fed (no keys) |
| T13 | Act live: commit to `bot/courserefresh`, card to consented cohort, receipt | `git log` shows the `cr:` commit; card artifact exists | `[~]` — body/diff/notify staged and receipted; the push to the bot branch is unwired |
| T14 | Telemetry endpoint + learn workflow: consent gate, cohort window | no-consent POST rejected; window row produced | `[~]` — consent gate and window computation exist (fixtures); no HTTP endpoint |
| T15 | Digest delivery (07:30) + console read routes | digest delivered; console renders a receipt | `[~]` — digest render and `--report`; delivery and console are Phase 2 |
| T16 | One witnessed failure handled: degraded receipt + digest line | receipt shows failure and mode | `[ ]` |
| T17 | **M1 GATE:** preflight green with `mode: live`; hero run armed | sign-off; preflight artifact | `[!]` — needs live credentials |
| T21b | n8n exports embedding the rulebook, drift-checked | `test_contracts.py` compares the embedded code to the node file | `[x]` (pulled forward to answer review 02 seat C) |

## M2 — Learn, and measure

| ID | Task | Done when | Status |
|---|---|---|---|
| T18 | Gate evaluation (n≥5, 48 h, `quiz_delta ≤ 0`) → revert queue, `unmeasured` when n<floor | gate row in the run log; `unmeasured` branch | `[~]` — implemented and proven offline (`cr-revert-*` gold rows, `09-revert.json`); live cohort absent |
| T19 | Stuck detection + micro-lesson dispatch (consent + caps) | dispatch artifact + receipt; rate-limit rows | `[x]` |
| T20 | Eval harness: three columns on the frozen gold set, report archived | `policy.py --eval` exits 0; report in `app/out/eval/` | `[x]` — columns (b)/(c) offline; (a) is `n/a` (D-06) |
| T21 | All test files green | `sh app/check.sh` exit 0 | `[x]` — 92 PASS |
| T22 | `RECEIPTS.md` + `EVIDENCE.md` filled from real outputs (or `unmeasured`) | claims lint green; no orphan numbers | `[x]` |
| T23 | **M2 GATE:** hostile→publish = 0 and unsupported→publish = 0 on the archived report | excerpt pasted in `reviews/04` §3 | `[x]` |

## M3 — Demo, honesty, handoff

| ID | Task | Done when | Status |
|---|---|---|---|
| T24 | Evidence freeze: run log, receipts, diffs, notifications, digest, eval report | `MANIFEST.sha256` in `EVIDENCE.md` §4 | `[x]` — 18 files frozen |
| T25 | Video shot per the shot list; refusals and labels on screen | checklist §4 signed | `[!]` — human time |
| T26 | Live final dry run (3 min + Q&A) | checklist §5 signed | `[!]` — human time |
| T27 | `AMENDMENTS.md` current; `reviews/04` with pasted outputs; findings closed or open | closure rule satisfied | `[~]` — closed except the live rows named in `reviews/04` §4 |

## M4 — Stretch (each is a cut candidate; none blocks the demo)

| ID | Task | Why it is last |
|---|---|---|
| T28 | Notion mirror of the changed lesson | needs a token + API patience |
| T29 | Digest email in addition to Telegram | second channel, small win |
| T30 | Eval column (a) via a proprietary model, prompt frozen | needs a key and a spend decision |
| T31 | Cadence experiment: 60 → 30 min, measured | more Apify units for a nicer number |

## Blocked list

| ID | Blocked by | Unblocked by |
|---|---|---|
| T10 | Apify credentials + actor choice | kickoff (`SOURCE-PLAN.md` §3) |
| T17 | live credentials + one green preflight | the same kickoff |
| T09 | a human observer | the live rehearsal (booked) |
| T25, T26 | human time on D2 | the shooting schedule |
| T30 | comparator API key | the budget decision at kickoff |

*Last updated: D-0. Every `[x]` above has its command output in `EVIDENCE.md` or `reviews/04`, or it
is a lie (Art. VI.2, Art. XVI.3).*
