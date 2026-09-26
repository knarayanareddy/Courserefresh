# Courserefresh — tasks (the TODO, in gated order)
`v0.5 · Last amended D-0 · Executor: the build agent (see BUILD.md §0) · Depends on: spec.md, plan.md`

**Done-done** = the acceptance criterion passes **and** the command in `TRACEABILITY.md` has been
run **and** its output/link is in `EVIDENCE.md`. Nothing else counts as done. State vocabulary:
`[ ]` todo · `[x]` done-done · `[~]` cut/degraded (say what, in the task) · `[!]` blocked (say who).

**TIME-NOW block.** `D-label: D-0 · mode: sim green · hero run: cr-20260926-1421-001 (offline twin) · live engine: built, dry-run green (cr-20260926-1436-436; E8) · credentials: the only input left`

---

## M0 — Walking skeleton (the loop, ugly, end to end)

| ID | Task | Done when | Status |
|---|---|---|---|
| T01 | Real course artifact: six lessons (v1/v3 bodies), quizzes, CHANGELOG | front matter parses; the twin reads and rewrites it | `[x]` |
| T02 | `app/run_walking_skeleton.py`: notice→verify→decide→act→learn→report over fixtures | `--selftest` 14/14; `--report` renders | `[x]` |
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
| T10 | Apify actors pinned (id+build) and called from `wf-cr-0-scan`; dataset → snapshot normaliser | one real actor run id in `WIRING.md` §6; snapshots cached | `[~]` — **built**: `skin/sources.json` pins + `app/lib/apify.py` (run, normalise with reason codes, unit ledger, retries) + `wf-cr-0-scan`; one real run id still needs `APIFY_TOKEN` (E8 ran on recorded datasets) |
| T11 | Scan schedule with dedupe (content hash) and zero-new = `no_delta` | two consecutive runs behave | `[~]` — **built**: per-source `source_id:hash` dedupe + baselines, `no_delta` path, cadence config, `ONCE` execute-once guard in the export; the live schedule needs an activated canvas |
| T12 | Triage live: observe + judge calls, quote anchoring, POLICY node, receipt | receipts with judge answers and `input_hash` | `[~]` — **built**: 7-question judge with 4 providers, closed-set fail-closed validation, anchored render contract, POLICY node parity-checked, `--via-n8n` canvas decisions; live model calls need a key (E8 used recorded answers, labelled) |
| T13 | Act live: commit to `bot/courserefresh`, card to consented cohort, receipt | `git log` shows the `cr:` commit; card artifact exists | `[~]` — **built**: version+diff+CHANGELOG+card, `CR_COMMIT=1` commits on `bot/courserefresh` and refuses any other branch, notify channels with per-attempt records; a real push/delivery needs the git remote + a channel token |
| T14 | Telemetry endpoint + learn workflow: consent gate, cohort window | no-consent POST rejected; window row produced | `[x]` — `app/lib/telemetry.py` (POST /telemetry: consent checked before storage → 403; hashed handles only; cohort below floor → `unmeasured` with reason) + `wf-cr-3-learn`; proven by `test_live_modules.py` (E8) |
| T15 | Digest delivery (07:30) + console read routes | digest delivered; console renders a receipt | `[~]` — **built**: `app/lib/console.py` serves the page, `/healthz`, `/api/preflight|receipts|run_log`, `/lesson/{id}`, `/receipt/{id}`, `/eval` + gated POST `/pause|/resume`; `app/serve.py` runs console + telemetry on `0.0.0.0`; delivery at 07:30 is `--watch`'s job and needs the loop running |
| T16 | One witnessed failure handled: degraded receipt + digest line | receipt shows failure and mode | `[~]` — rehearsed offline (E7 `--chaos write-fail`) and in the live engine (`--inject-failure`), once-only reporting; `wf-cr-9-errors` turns an unhandled canvas throw into a receipt + digest line; the live equivalent on the real instance is pending |
| T17 | **M1 GATE:** preflight green with `mode: live`; hero run armed | sign-off; preflight artifact | `[!]` — needs live credentials |
| T21b | n8n exports embedding the rulebook, drift-checked | `test_contracts.py` compares the embedded code to the node file | `[x]` (pulled forward to answer review 02 seat C) |

## M2 — Learn, and measure

| ID | Task | Done when | Status |
|---|---|---|---|
| T18 | Gate evaluation (n≥5, 48 h, `quiz_delta ≤ 0`) → revert queue, `unmeasured` when n<floor | gate row in the run log; `unmeasured` branch | `[~]` — implemented and proven offline (`cr-revert-*` gold rows, `09-revert.json`); live cohort absent |
| T19 | Stuck detection + micro-lesson dispatch (consent + caps) | dispatch artifact + receipt; rate-limit rows | `[x]` |
| T20 | Eval harness: three columns on the frozen gold set, report archived | `policy.py --eval` exits 0; report in `app/out/eval/` | `[x]` — columns (b)/(c) offline; (a) is `n/a` (D-06) |
| T21 | All test files green | `sh app/check.sh` exit 0 | `[x]` — **164 PASS** across 12 stages |
| T22 | `RECEIPTS.md` + `EVIDENCE.md` filled from real outputs (or `unmeasured`) | claims lint green; no orphan numbers | `[x]` |
| T23 | **M2 GATE:** hostile→publish = 0 and unsupported→publish = 0 on the archived report | excerpt pasted in `reviews/04` §3 | `[x]` |

## M3 — Demo, honesty, handoff

| ID | Task | Done when | Status |
|---|---|---|---|
| T24 | Evidence freeze: run log, receipts, diffs, notifications, digest, eval report | `MANIFEST.sha256` in `EVIDENCE.md` §4 | `[x]` — 19 files frozen |
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

## M5 — Round 3: the build (what round 3 added, and what is left for the keys)

| ID | Task | Done when | Status |
|---|---|---|---|
| T32 | Live engine `app/run_live.py` over the twin's writers (notice→verify→decide→act→learn→report) | `--selftest` 12/12; one dry cycle publishes, refuses and digests | `[x]` — `cr-20260926-1436-436` (sim) and E8; `--watch`, `--learn`, `--digest-only`, `--inject-failure`, `--via-n8n` all exist |
| T33 | n8n build requirements: execute-once guard, error workflow `wf-cr-9-errors`, contract notes, `--import` | `test_contracts.py` green on 6 exports; import prints ids | `[x]` — import is credential-gated (`N8N_BASE_URL`+`N8N_API_KEY`), proven through an injected transport |
| T34 | Judge with four providers + key probe | probe prints status, never the key; `unknown_state` fails closed | `[x]` — `probe_provider()`; `--preflight --probe` |
| T35 | Telemetry + console servers, and a demo launcher | console serves a sandbox with `--root`; intake refuses no-consent | `[x]` — `app/serve.py`; see the LIVE preview in this session |
| T36 | Notify channels (file/telegram/webhook) with delivery records | staged ≠ delivered; missing keys fail loudly | `[x]` — `app/lib/notify.py` |
| T37 | Preflight, `.env.example`, `SETUP.md`, `OPERATIONS.md` §9–12 | a stranger can paste keys from one page | `[x]` — `--preflight [--probe]` |
| T38 | Live-path battery (`test_live_modules.py`, 47 checks) with injected transports | green inside `check.sh`, no keys, no sockets | `[x]` — 12 stages, 164 PASS |
| T39 | Peer-supervised build log (`reviews/06`) | 16 findings, each with a check that fails if it returns | `[x]` — `specs/reviews/06-build-round-3.md` |

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
