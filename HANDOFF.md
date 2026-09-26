# HANDOFF — continuing the Courserefresh session

`Branch: arena/01a0ddea-courserefresh · Written D1 (Sat 2026-09-26) · Deadline: video 15:00, live final 16:15, Sun 2026-09-27`

**Read this file first, then `AGENTS.md`.** This is the operating handoff: where the project stands,
what is genuinely left, and the exact commands. It is written for the agent (or human) who picks this
up next — no prior context assumed.

---

## 1. The project in five lines

Courserefresh keeps **one course true** (`course/agent-ops/`, six lessons) while its subject — the
n8n / Apify / agent tooling world — keeps moving. The loop **notices** upstream changes (Apify),
**verifies** them with a deterministic policy (`skin/policy.py` ≡ `app/n8n/policy_node.js`, parity-
tested), **decides** (`PUBLISH` / `ESCALATE` / `REVERT` / `DISPATCH` / `NO_CHANGE`), **acts** (rewrites
the lesson, regenerates the quiz item affected, commits on `bot/courserefresh`, cards the consented
cohort), **learns** (cohort gate → reverts its own bad publish), and **reports** (07:30 digest,
refusals first). It never publishes on one source, never publishes hostile input, and it says
`unmeasured` when it has not measured something.

It serves the Build Weekend brief *"build a course that updates as its subject changes; spot when a
learner is stuck before they ask"* and is judged: **Autonomy 25 · Proven in real use 25 · Apify & n8n
20 · Problem fit 15 · Product & presentation 15** (`specs/courserefresh/JUDGING-MAP.md` holds the
criterion → evidence → sentence mapping).

## 2. State right now

| | |
|---|---|
| Battery | `sh app/check.sh` → **179 PASS · 13 stages · `ALL GREEN` · exit 0**, **with zero credentials** |
| Live path | Built and exercised end-to-end through injected transports (47/47, `test_live_modules.py`); **never called a real API** — that is deliberate |
| Blocking input | **keys only.** `python3 app/run_live.py --preflight` prints exactly what is missing, by name |
| Round status | Rounds 1–3 (package → panel → specialist debate → peer-supervised build) are complete and recorded in `specs/reviews/01…06` |
| Today | **D1.** Keys → first live cycle → `--watch` overnight → harvest in the morning → film → submit 15:00 |

The single sentence that describes this repo's design: *every claim is either measured and receipted,
or it is written `unmeasured`; and the system runs, refuses, records and renders before it has a
single credential.*

## 3. The critical path (in order, with commands)

### Step 0 — prove the wiring before any key (2 min)

```bash
sh app/check.sh                       # expect: ALL GREEN (179 PASS, 13 stages), no network, no keys
python3 app/run_live.py --preflight   # expect: mode: sim, apify/judge/n8n "missing", 4 claims blocked
```

### Step 1 — paste the keys (5 min, names only; never commit, never paste into chat)

```bash
cp .env.example .env                  # .env is gitignored; the file is the checklist
```

The authoritative table (where each value comes from, what it unlocks, what happens without it) is
`specs/courserefresh/SETUP.md` §2. Minimum set for "live": `APIFY_TOKEN` (Apify console → Settings →
Integrations), `N8N_BASE_URL` + `N8N_API_KEY` (n8n → Settings → API), `CR_JUDGE_PROVIDER` /
`CR_JUDGE_BASE_URL` / `CR_JUDGE_API_KEY` / `CR_JUDGE_MODEL` (any OpenAI-compatible endpoint, including
a "jev"-style one), `CR_NOTIFY_CHANNEL` + `CR_TELEGRAM_BOT_TOKEN`/`CR_TELEGRAM_CHAT_ID` (or
`CR_NOTIFY_WEBHOOK_URL`). `CR_COMMIT=1` turns artifacts into commits on `CR_BOT_BRANCH`
(`bot/courserefresh`). Optional: `CR_DEMO_TOKEN`, `CR_TELEMETRY_TOKEN`, `CR_CONSOLE_TOKEN`,
`N8N_INSTANCE_VERSION`.

### Step 2 — the one screen that says what is now real

```bash
python3 app/run_live.py --preflight --probe
```

`--probe` makes exactly three cheap calls (`GET /users/me` Apify, `GET {base}/models` judge,
`GET /api/v1/workflows` n8n) and prints `ok`/`failed` with HTTP status — **never a value**, only
`set(len=…, sha256=…)` fingerprints. Expect `mode: live` and no `claim blocked` lines. Failure
recipes are in `SETUP.md` §6 (judge 401 → wrong base URL; `model_listed: false` → pick a listed
model; n8n 404 → base URL includes `/api/v1`; etc.).

### Step 3 — put the canvas up (once)

```bash
python3 app/tools/make_n8n_exports.py            # regen 6 exports from source (in-repo, no network)
python3 app/tools/make_n8n_exports.py --import   # upsert into your n8n, prints workflow ids
```

Then in the n8n UI: check every node marked `ATTACH_AT_IMPORT` (credentials, telegram thread) and
**activate all six workflows** (five `wf-cr-0…4` + `wf-cr-9-errors`). Record the instance version in
`WIRING.md` §4 and the first execution id in §6.

### Step 4 — first real cycles

```bash
python3 app/run_live.py --once --dry-run      # everything real except writes to course/**
python3 app/run_live.py --once --via-n8n      # the canvas decides; the oracle polices
```

Success = a run id, labelled decisions, `canvas.execution_id` on the decision, digest ≤ 4096 B, and
`app/out/live/` holding `preflight.json`, `last_cycle.json`, `last_summary.json`. Exit codes:
`0` fine · `1` cycle failed · `2` preflight blocked · `3` refused (authority/consent/freeze) ·
`4` human override refused. **Exit 3 is the system working**, not a crash.

### Step 5 — let it run while nobody watches (the 25% criterion)

```bash
python3 app/run_live.py --watch      # scans on CR_LIVE_SCAN_MINUTES, learns every 15 min, digests 07:30
python3 app/serve.py                 # console 0.0.0.0:8080 · telemetry intake 0.0.0.0:8787
```

Real learners POST telemetry (consent first; handles must be exactly 8 hex chars, e.g.
`learner:deadbeef`; no read routes exist). The cohort gate needs **n≥5 for ≥48 h** after a publish to
fire a revert — if the window is shorter, that row stays `unmeasured` and the receipt says why. That
is legal (Art. VI) and should be said out loud; do not round it up.

### Step 6 — harvest (Sunday morning, before filming)

```bash
python3 app/tools/freeze_evidence.py --out app/out/evidence/<run_id>   # ALWAYS pass --out
python3 app/tools/collect_live.py                                      # the shareable, redacted bundle
```

Then the paperwork — it is part of the build, not an afterthought:

1. `EVIDENCE.md` — add the live run to §4b/§5 and flip the rows it measures (`E7b` first).
2. `RECEIPTS.md` — `unmeasured` → measured, each with artifact + command; **every number needs a row**.
3. `WIRING.md` §1/§4/§6 — real Apify run id, instance version, n8n execution id, bot commit, digest id.
4. `tasks.md` — T10/T11/T12/T13/T15/T16/T17 move from `[~]`/`[!]` when the artifact exists; T09/T25/T26 are human.
5. `AMENDMENTS.md` — one row per change; a finding is `open` until its output is pasted.
6. `sh app/check.sh` again (the counts will not move unless files changed — if they do, sweep **all**
   occurrences, including backticked ones: `179 PASS`, `13 stages`, `59 rows + 2 probes`, per-suite numbers).
7. Commit on this branch and push (`git push origin arena/01a0ddea-courserefresh`).

### Step 7 — film

`specs/courserefresh/VIDEO-SHOTLIST.md` is the shot-by-shot sheet; every visual in it already exists as
a frozen artifact. Two words must be said out loud if they are true: **`staged`** (no learner actually
received a card) and **`sim`** (no live Apify/n8n execution). The console header prints both.

## 4. What is already done — do not rebuild it

- **Spec corpus**: `specs/constitution.md` (16 articles), `shared/{harness,data-model,interfaces,eval}.md`,
  `security/threat-model.md` (TM01–TM18), `design/MASTER.md` (paper-and-ink lockfile),
  `courserefresh/spec.md` (US-1…US-19, 57 ACs) → `plan.md` → `tasks.md` → `BUILD.md` → `TRACEABILITY.md`
  (every AC → the command that proves it) → `JUDGING-MAP.md`; kickoff pre-registration docs; six reviews.
- **Policy**: `specs/courserefresh/skin/policy.py` (oracle) ≡ `app/n8n/policy_node.js` (production);
  `node app/tests/test_gate_parity.py` → PASS over 59 gold rows + 2 named probes. Gold is `gold-v0.3`,
  n=59, frozen (`app/out/eval/gold-v0.3/report.txt`: action/reason 1.000, hostile→publish 0,
  unsupported→publish 0).
- **Offline twin**: `app/run_walking_skeleton.py` (writes real artifacts into `course/**`), frozen hero
  run `cr-20260926-1421-001` (19 files), witnessed-failure run `cr-20260926-1420-924`.
- **Live engine**: `app/run_live.py` + `app/lib/{config,apify,judge,n8n,notify,telemetry,console}.py`,
  `app/tools/make_apify_fixtures.py`; round-3 rehearsal `cr-20260926-1441-130` (14 files).
- **n8n**: 6 exports with the rulebook embedded byte-for-byte, an execute-once `ONCE` guard after every
  trigger, contract sticky notes, `wf-cr-9-errors` attached to all five, `--import` upserts in place.
- **Surfaces**: read-only console (+ gated pause/resume), telemetry intake, digest, learner card,
  micro-lesson, `app/serve.py`.
- **Handoff safety**: `app/tools/collect_live.py` — one command packs a run, redacts every secret value
  it can see, summarises telemetry as counts, re-verifies the receipt chain itself, and **exits 3**
  rather than hand over anything containing a key-shaped string.

## 5. What is genuinely open (named, not rounded up)

| Item | Closes when | Owner |
|---|---|---|
| T10 / K-07 | a real Apify actor run id lands in `WIRING.md` §6 | keys |
| T12 / K-05 | a real n8n execution of `wf-cr-1-triage` decides a cycle (`--via-n8n`) | keys + activated canvas |
| T13 / K-06 | one delivered learner card (or the word `staged` on screen) | keys + channel |
| T15 | the digest is delivered by `--watch` at 07:30 | a running loop |
| T16 / E7b | one live failure handled: degraded receipt + digest line, no crash | an unattended window |
| T17 | `--preflight --probe` green with `mode: live` | keys |
| T18 | a live cohort gate fires (n≥5, 48 h) | a live cohort — may not fit the window; then `unmeasured` |
| T09 | a stranger watching says *"it changed the lesson by itself, and it refused this one"* | a human |
| T25 / T26 | the video and the live final rehearsal | human time |
| T28–T31 | stretch (Notion mirror, email digest, eval column (a), cadence experiment) | optional |

## 6. The laws that will bite (each has a test that enforces it)

1. **Models propose, code decides.** Never let model output choose an action; change `policy.py` and
   `policy_node.js` in the same commit, regen the exports (`make_n8n_exports.py`) and re-run
   `node app/tests/test_gate_parity.py`. Node sha: `1885efcb791872c4…`.
2. **Never invent a number.** `unmeasured` is legal; a plausible guess is a violation. Measured values
   belong in `RECEIPTS.md` with artifact + command (`test_claims.py`).
3. **No publish without a `revert_gate`**; a revert writes its own diff line and restores as a *new*
   version.
4. **Don't touch the frozen gold set** to make a test pass; relabel only with a new `gold_version` and
   an `AMENDMENTS.md` row.
5. **Curriculum coherence**: every lesson has objectives/prereqs in `course/agent-ops/curriculum.json`;
   a change regenerates the quiz item it affects and *names* downstream lessons — never rewrites them
   unattended (`test_curriculum.py`).
6. **Never read `os.environ` by hand** — use `app/lib/config.py` (`test_live_modules.py` fails if the
   old bug returns).
7. **`app/out/**` is gitignored state**; the repo carries machinery + specs, and everything in
   `app/out/` is regenerable by the documented commands. Never commit build junk (`test_hygiene.py`).
8. **A receipt must still describe the file** — after any change that writes artifacts, run
   `python3 app/tests/test_artifacts.py`.
9. **Nothing leaves the machine with a key in it** — `collect_live.py` (exit 3 = refuse).

## 7. Traps distilled (from the build's own error log)

- **Count sweeps**: after a battery change, grep *every* count reference (backticks get missed).
  Current: 179 PASS · 13 stages · contracts 14/14 · live modules 47/47 · handoff 15/15 · live selftest
  12/12 · skeleton selftest 14/14 · policy 18/18 · threats 18/18 · artifacts 8/8 · curriculum 8/8 ·
  gold floor 8/8 · claims 3/3 · hygiene 7/7 · design 6/6 · parity 59 rows + 2 probes.
- **Hygiene**: no wall-clock dates outside `kickoff/PREREGISTRATION.md` (use `D-0`); no email-shaped
  literals anywhere (write "alice dot example"); key-shaped test literals must be assembled at runtime.
- **Evidence**: `reset_course.py` before every hero run; `freeze_evidence.py` **always** with `--out`.
- **Telemetry**: consent before storage (else 403); handles exactly 8 hex; no read routes; the cohort
  gate reads `<root>/app/out/state/telemetry.jsonl`.
- **Judge failures fail closed** → `ESCALATE`/`unknown_state`. That is correct behaviour, not a bug.
- **`--via-n8n` says `webhook_http_404`** → `wf-cr-1-triage` is not activated, or the path is not
  `cr/triage`.
- **Collector exit 3** → a secret survived its redaction; nothing leaves the machine. Fix and rerun.
- **Never run two servers on the same ports** — `CR_CONSOLE_PORT=8081 python3 app/serve.py` to move one.

## 8. Where everything lives

| Path | What |
|---|---|
| `specs/` | source of truth — constitution, contracts, threat model, design, product spec, receipts, evidence, wiring, ops, reviews 01–06 |
| `specs/courserefresh/SETUP.md` | the only page needed to go live (keys, canvas, cycles, handoff, troubleshooting) |
| `specs/courserefresh/tasks.md` | `[x]` done · `[~]` degraded · `[!]` blocked · `[ ]` todo |
| `specs/courserefresh/skin/` | executable policy, thresholds, closed sets, gold `gold-v0.3`, sources `sources-v1.1` |
| `app/run_live.py` · `app/lib/` · `app/serve.py` | the live engine, its clients, the two servers |
| `app/n8n/` | `policy_node.js` + the 6 generated workflow exports |
| `app/tools/` | `make_n8n_exports.py` · `make_apify_fixtures.py` · `freeze_evidence.py` · `reset_course.py` · `metrics.py` · `collect_live.py` |
| `app/tests/` | the battery's suites; `app/check.sh` runs all 13 stages |
| `course/agent-ops/` | the artifact: six lessons, versions, diffs, quizzes, CHANGELOG |
| `app/out/` | gitignored state: runs, receipts, digest, live/, state/, evidence/, eval/ |

## 9. Definition of done for the next session

1. `--preflight --probe` green, `mode: live`, zero `claim blocked` lines.
2. Canvas imported and activated; a real execution id in `WIRING.md` §6.
3. A real Apify run id in `WIRING.md` §1/§6; snapshots hashed.
4. One cycle decided via `--via-n8n` with `canvas.execution_id` on the receipt.
5. An unattended window (≥3 h) with at least one **degraded-mode receipt** and its digest line.
6. One delivered card — or `staged` said out loud.
7. Evidence frozen, `collect_live.py` handed over, `RECEIPTS.md`/`EVIDENCE.md`/`tasks.md` honest
   (measured where measured, `unmeasured` where not), battery re-run green, committed + pushed.
8. Video shot per `VIDEO-SHOTLIST.md`; the live final rehearsed per `checklists.md` §5.

**If the keys never arrive**: the system is designed to be honest about that. Use the replay ladder
(`EVIDENCE.md` §5), label every fallback on screen, and the submission still stands on the offline
proof — but say `sim` and `staged` out loud. Do not claim live.

*Every number in this file has a row in `RECEIPTS.md` or is regenerable by the command named next to
it. If you cannot find the row, write `unmeasured` — never a guess.*
