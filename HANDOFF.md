# HANDOFF — continuing the Courserefresh session

`Branch: arena/01a0de69-courserefresh · Written at the end of the review-fix session, D1 (Sat 2026-09-26) · Deadline: video 15:00, live final 16:15, Sun 2026-09-27`

**Read this file first, then `AGENTS.md`.** This is the operating handoff: where the project stands,
what is genuinely left, and the exact commands. It is written for the agent (or human) who picks this
up next — no prior context assumed.

---

## 0. Where the last session stopped (read this before §1)

Two commits on this branch, green, pushed:

| Commit | What it contains |
|---|---|
| `85e3ce6` | `REVIEW.md` F1–F13 resolved on the no-key path; the author's round (D-32) built end to end; Tavily and JEV integrated; two evidence bundles shipped under `specs/evidence/`; registers re-derived |
| `e2bfbc5` | the canvas queue ordered by learner consequence (C-05), row anchors, and JV-04's JEV fixture replay |

**Verified at this tip:** `sh app/check.sh` → **295 PASS (263 PASS lines in 13 measured stages + the
32-check claims audit) · `ALL GREEN` · exit 0**, with no credentials and no sockets. A live form ruling
was exercised against the served console end to end: `GET /canvas` → form POST → `303` → the next cycle
published at `authority: PA3 · decided_by: human:author · reason human_signoff`) — the digest line reads
`- author ruling rcpt-… (approve, human_signoff): applied`).

**`app/out/` does not survive a session boundary.** It is gitignored *and* it is runtime state (runs,
receipts, digest, `state/`, `evidence/`, `eval/`); on a fresh clone, or after this sandbox is reset, it
is simply not there. Nothing is lost — it is derived. The first three commands of any session:

```bash
sh app/check.sh                       # regenerates app/out/{evidence,selftest,eval,…}; expect ALL GREEN
python3 app/run_walking_skeleton.py   # the hero run: receipts, run_log, digest, notifications, canvas rows
python3 app/lib/canvas.py             # writes app/out/canvas.{json,html} (the console also renders on demand)
python3 app/serve.py                  # console 0.0.0.0:8080 · telemetry 0.0.0.0:8787 (LIVE preview)
```

The *durable* evidence is what is shipped: `specs/evidence/cr-20260926-1726-793/` (offline twin, 19
files) and `specs/evidence/cr-20260926-1726-054/` (live engine dry cycle, 20 files incl.
`live/preflight.txt`) — every hash re-derived by the audit stage on each battery run.

Git: the branch is `arena/01a0de69-courserefresh`; if the local branch pointer ever looks older than the
work, the pushed tip is the truth:

```bash
git fetch origin "refs/heads/arena/01a0de69-courserefresh:refs/remotes/origin/arena/01a0de69-courserefresh"
git reset --mixed origin/arena/01a0de69-courserefresh      # worktree-keeping; then git status
```

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
| Battery | `sh app/check.sh` → **295 PASS (13 measured stages + the 32-check claims audit) · `ALL GREEN` · exit 0**, **with zero credentials** |
| Live path | Built and exercised end-to-end through injected transports (127/127, `test_live_modules.py`, including the Tavily, JEV-fixture, canvas and author-ruling paths); **never called a real API** — that is deliberate |
| Blocking input | **keys only.** `python3 app/run_live.py --preflight` prints exactly what is missing, by name |
| Author rulings | built and exercised (D-32): a ruling binds the next cycle at `authority: PA3` / `decided_by: human:author` / `reason human_signoff`, and expires the moment the evidence it was made about changes |
| Round status | Rounds 1–3 (package → panel → specialist debate → peer-supervised build) are complete and recorded in `specs/reviews/01…06`; the seat panel on the canvas / Tavily / JEV is `specs/reviews/07` (C-01…C-08, TV-01…TV-04, JV-01…JV-05, 8 ranked complements, each with its status) |
| Today | **D1.** Keys → first live cycle → `--watch` overnight → harvest in the morning → film → submit 15:00 |

The single sentence that describes this repo's design: *every claim is either measured and receipted,
or it is written `unmeasured`; and the system runs, refuses, records and renders before it has a
single credential.*

## 3. The critical path (in order, with commands)

### Step 0 — prove the wiring before any key (2 min)

```bash
sh app/check.sh                       # expect: ALL GREEN (295 PASS: 13 measured stages + the claims audit), no network, no keys
python3 app/run_live.py --preflight   # expect: mode: sim, apify/judge/n8n "missing", 4 claims blocked
```

### Step 1 — paste the keys (5 min, names only; never commit, never paste into chat)

```bash
cp .env.example .env                  # .env is gitignored; the file is the checklist
```

The authoritative table (where each value comes from, what it unlocks, what happens without it) is
`specs/courserefresh/SETUP.md` §2. Minimum set for "live": `APIFY_TOKEN` (Apify console → Settings →
Integrations), `N8N_BASE_URL` + `N8N_API_KEY` (n8n → Settings → API), `CR_JUDGE_PROVIDER` /
`CR_JUDGE_BASE_URL` / `CR_JUDGE_API_KEY` / `CR_JUDGE_MODEL` (any OpenAI-compatible endpoint; the typed-decision
provider is its own switch — `CR_JUDGE_PROVIDER=jev` + `CR_JEV_BASE_URL`/`CR_JEV_API_KEY`/`CR_JEV_MODEL`),
`TAVILY_API_KEY` (the second discovery source; optional if Apify alone is enough),
`CR_NOTIFY_CHANNEL` + `CR_TELEGRAM_BOT_TOKEN`/`CR_TELEGRAM_CHAT_ID` (or
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

### Step 4b — the author's round (no keys needed; do this before filming)

The loop keeps the refusals a person may lift as *withheld deltas*, and the canvas is where the ruling
happens. It is worth 60 seconds on camera because it is the difference between a report and a control:

```bash
python3 app/run_walking_skeleton.py     # hero run → receipts, digest, state/pending.jsonl (the queue)
python3 app/lib/canvas.py               # writes app/out/canvas.{json,html} (read-only copy of the page)
python3 app/serve.py                    # then open /canvas (append ?token=… if CR_CONSOLE_TOKEN is set)
```

Read a queued row (diff, sources with the "is this a voice?" column, the plain-language reason, how close
the call was), submit Approve or Reject **without JavaScript**, then re-run the loop: the receipt shows
`decided_by: human:author`, `authority: PA3`, reason `human_signoff`, and the digest lists the ruling.
Run it again with the evidence changed and the same ruling is reported `stale` — the machine decides and
the row comes back. Runbook: `OPERATIONS.md` §9b. Law: `AMENDMENTS.md` D-32.

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
   occurrences, including backticked ones: `295 PASS`, `13 stages + audit`, `59 rows + 2 probes`, per-suite numbers).
7. Commit on this branch and push (`git push origin arena/01a0ddea-courserefresh`).

### Step 7 — film

`specs/courserefresh/VIDEO-SHOTLIST.md` is the shot-by-shot sheet; every visual in it already exists as
a frozen artifact. Two words must be said out loud if they are true: **`staged`** (no learner actually
received a card) and **`sim`** (no live Apify/n8n execution). The console header prints both.

## 4. What is already done — do not rebuild it

- **Spec corpus**: `specs/constitution.md` (16 articles), `shared/{harness,data-model,interfaces,eval}.md`,
  `security/threat-model.md` (TM01–TM18), `design/MASTER.md` (paper-and-ink lockfile),
  `courserefresh/spec.md` (US-1…US-19, 59 ACs) → `plan.md` → `tasks.md` → `BUILD.md` → `TRACEABILITY.md`
  (every AC → the command that proves it) → `JUDGING-MAP.md`; kickoff pre-registration docs; six reviews.
- **Policy**: `specs/courserefresh/skin/policy.py` (oracle) ≡ `app/n8n/policy_node.js` (production);
  `node app/tests/test_gate_parity.py` → PASS over 59 gold rows + 2 named probes. Gold is `gold-v0.3`,
  n=59, frozen (`app/out/eval/gold-v0.3/report.txt`: action/reason 1.000, hostile→publish 0,
  unsupported→publish 0).
- **Offline twin**: `app/run_walking_skeleton.py` (writes real artifacts into `course/**`), frozen hero
  run shipped in `specs/evidence/cr-20260926-1726-793/` (19 files, hashed); the live engine's dry cycle
  is `specs/evidence/cr-20260926-1726-054/` (20 files, incl. `live/preflight.txt`). The witnessed-failure
  rehearsal `cr-20260926-1420-924` regenerates locally.
- **The author's round (D-32)**: refusals a person could lift are kept as *withheld deltas*
  (`app/out/state/pending.jsonl`) and the canvas at `GET /canvas` is where a teacher approves or
  rejects them. A ruling binds the next cycle (`authority: PA3`, `decided_by: human:author`,
  `human_signoff`) and expires when the evidence it was made about changes — see `OPERATIONS.md` §9b
  for the runbook and `specs/reviews/07` for the panel that demanded it.
- **Live engine**: `app/run_live.py` + `app/lib/{config,apify,judge,n8n,notify,telemetry,console,jev,tavily,rulings,canvas}.py`,
  `app/tools/make_apify_fixtures.py`; the dry cycle is shipped as `specs/evidence/cr-20260926-1726-054/`
  (20 files: receipts, digest, the preflight transcript that names what the missing keys block).
- **n8n**: 6 exports with the rulebook embedded byte-for-byte, an execute-once `ONCE` guard after every
  trigger, contract sticky notes, `wf-cr-9-errors` attached to all five, `--import` upserts in place.
- **Surfaces**: read-only console (+ gated pause/resume), telemetry intake, digest, learner card,
  micro-lesson, `app/serve.py`.
- **Handoff safety**: `app/tools/collect_live.py` — one command packs a run, redacts every secret value
  it can see, summarises telemetry as counts, re-verifies the receipt chain itself, and **exits 3**
  rather than hand over anything containing a key-shaped string.
- **The registers are machine-checked**: `app/tools/audit_claims.py` (stage 14) re-derives every number
  in `RECEIPTS.md` §6 from the files it names — battery totals, per-suite counts, per-bundle digest sizes,
  shipped-bundle completeness — and `test_contracts.py` fails if a spec still points at a frozen run under
  `app/out/`. If you change a suite, the register must change in the same commit.

## 5. The complete leftover list (what to do next, with the check that closes each)

Status of every REVIEW.md finding is in `REVIEW.md` §7 (all F1–F13 closed, each held by a check).
Status of every panel condition is in `specs/reviews/07` — the rows below are what is *left*.

### 5a. No credentials needed — start here

| ID | What is left | Closes with (exact check) |
|---|---|---|
| **C-08 / complement 6** | **Revert from the canvas.** The teacher's most common intervention has no verb: `approve` and `reject` exist, `revert` does not. Add it to the closed ruling set (`app/lib/rulings.py`), render a third button on the canvas row, and have the engine act on it as a human REVERT (`authority: PA3`, `decided_by: human:author`, cohort gate bypassed because a person decided) | §13 of `test_live_modules.py`: a `revert` ruling on a published row produces a REVERT receipt at PA3 naming `restore_version`, and a *single* ruling on a quiz-touching row stays queued (see complement 4) |
| **complement 4** | **Two-key for assessment changes** (Art. IV): a quiz rewrite that one author approved is the highest-consequence row in the product; it should need a second ruling (or a second author) before it publishes | same §13: assessment diff + single `approve` → the row stays queued with `needs_second_key` |
| **TV-02 (action half)** | A discovery lead that is allowlisted but untracked is surfaced in the digest and dies there. Write it to `app/out/state/source_proposals.jsonl` and render it as a canvas queue row ("proposed source — add to the watchlist?"). The **add itself stays a PA3 human edit** of `skin/sources.json` (Art. XIV.1 — a model never edits the allowlist) | §11 check: a fixture lead → a proposal row → a PA3 add; `state/source_proposals.jsonl` has one row per lead |
| **JV-03 (record half)** | The page says `Judge confidence (predicted) · calibration: unmeasured`. That stays until a calibration record exists: **n ≥ 20 published decisions with an observed outcome**, written by a tool (extend `app/tools/metrics.py`), with a register row | the canvas prints a measured rate instead of `unmeasured`, and `RECEIPTS.md` has the row with artifact + command |
| **complement 7** | **Queue-only / run-scoped view + the boundary measured** (SRE): 9 rows render in well under a second; nobody has measured 100 or 1000 | a timing check at n = 100/1000 receipts, reported as a number (or `unmeasured`) |
| **complement 8** | **Time-to-decision receipt**: "the queue is short" is a claim. `median time from queue to ruling`, derived from ruling timestamps; `unmeasured` until n ≥ 20 rulings | a register row; the number comes from the timestamps, never a guess |
| **hardening (small, do it with C-08)** | `run_walking_skeleton.revert_version()` reads `target["restore_version"]` with `[]`. A hand-made or canvas-made revert event without that key raises `KeyError` instead of escalating `previous_version_missing`, which is how every other missing precondition behaves | a test that feeds a revert event with no `restore_version` and asserts an ESCALATE, not a traceback |
| **housekeeping** | `test_live_modules.py` is 127 checks; if you add checks, re-derive the register block (§6 of `RECEIPTS.md`) — the audit fails **both** ways (stale register, undocumented check) | `sh app/check.sh` → `ALL GREEN` with the new counts |

### 5b. Blocked on the user's keys (the only input left)

| ID | What is left | Closes when |
|---|---|---|
| T17 / M1 gate | `--preflight --probe` green with `mode: live` and zero `claim blocked` lines | keys |
| T10 / K-07 | a **real** Apify actor run id in `WIRING.md` §1/§6, snapshots hashed | `APIFY_TOKEN` |
| T12 / K-05 | a real n8n execution of `wf-cr-1-triage` deciding a cycle (`--via-n8n`), execution id on the receipt | `N8N_BASE_URL` + `N8N_API_KEY` + activated canvas |
| T13 / K-06 | one delivered learner card — or the word `staged` said out loud | a channel token |
| T15 | the digest delivered by `--watch` at 07:30 | a running loop |
| T16 / E7b | one **live** failure handled: degraded receipt + digest line, no crash | an unattended window |
| T18 | a live cohort gate fires (n ≥ 5 for ≥ 48 h). If the window is shorter this stays `unmeasured` — legal, and it must be said out loud | a live cohort |
| X-02 | the "live wiring is the remaining gap" row closes only with real run ids | the above |

### 5c. Human-only (no agent can close these)

| ID | What |
|---|---|
| T09 / M0 gate | a stranger watching the run says *"it changed the lesson by itself, and it refused this one"* |
| T25 | the video, per `VIDEO-SHOTLIST.md` (two words out loud if true: `staged`, `sim`) |
| T26 | the live-final rehearsal, per `checklists.md` §5 |

### 5d. Stretch (explicitly optional)

| ID | What |
|---|---|
| T28 | Notion mirror of the changed lesson (token + API patience) |
| T29 | digest by email as a second channel (small win) |
| T30 | eval column (a) with a proprietary comparator (needs a key + a spend decision) |
| T31 | cadence experiment 60 → 30 min, measured |

### 5e. Refused on purpose — do not "fix" these

* **JV-05**: a JEV `score` question for materiality. The seven questions are closed on purpose; the
  materiality decision belongs to the rulebook, not to a probability-weighted average (Art. III).
* **Auto-approval after a timeout** — a silence is not a decision.
* **Learner-level detail on the canvas** — aggregate counts only (C-07).

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
  Current: 295 PASS (13 stages + 32 audit checks) · contracts 16/16 · live modules 127/127 · handoff 15/15 · live selftest
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
- **A session boundary deletes `app/out/`.** It is gitignored runtime state and the sandbox prunes
  output directories, so a handoff can arrive with no `app/out/` at all. Run `sh app/check.sh` first;
  everything in it is regenerable. The shipped bundles in `specs/evidence/` are the durable copies.
- **Count-sweep ritual.** After any change to a suite, re-derive `RECEIPTS.md` §6 — the register block's
  keys are `stages_before_audit`, `pass_lines_before_audit`, `parity`, `audit_checks`, `suites`,
  `evidence{run_id,bundles,digests}` and the audit fails *both* ways (stale register, undocumented
  check). Then grep **every** prose count (`295 PASS`, per-suite numbers, `13 stages`) — backticks get
  missed. Historical docs (`reviews/01…06`, `REVIEW.md` §6) keep their own numbers on purpose.
- **Do not name a runnable file under `app/out/evidence/` in a spec** (F13c lint: frozen evidence
  belongs in `specs/evidence/`). Prose mentions of the directory, or `app/out/evidence/<run_id>/`
  placeholders, are fine; N28's rehearsal path survives because it does not end in a file extension.
- **The canvas queue order is `canvas.review_key` → `verdict.queue`**, and the page renders that list.
  A queued row's proposed file lives on the withheld delta (`review.proposed_path`), not on the receipt —
  that is what the consequence ordering reads.
- **The canvas interval sentence only renders for a row with no `flip_drivers`** (and no provider
  confidences). A test that wants the ±interval case must clear both, or the drivers sentence prints.
- **JEV fixture drift guard**: `app/fixtures/jev/systemone-response.json` must keep its option keys equal
  to the closed sets in `specs/courserefresh/skin/questions.json`; §10 of the live tests fails otherwise.
- **Replay merge replaces a fixture event with the same `event_id`** (an append-only guard silently
  drops replays), and `apply_patch` requires `event["parent"]`.
- **Course tree**: HEAD carries the hero run's written versions (`lesson-03/v2`, `lesson-04/v4,v5`); that
  is the delivered state. `reset_course.py` deliberately diffs against it, and a fresh hero run writes
  *new* version files that are untracked — so the full restore after any local loop run is:

  ```bash
  python3 app/tools/reset_course.py >/dev/null; git checkout -- course/; git clean -f course/
  ```

  (`git clean -f` there removes only the loop's new `v*.md` / `diffs/v*.diff`; `.baseline/` is tracked.)

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

**First, with no keys** (all of it verifiable in this repo):

0. `sh app/check.sh` → `ALL GREEN`; `python3 app/run_walking_skeleton.py`; `python3 app/serve.py` and
   `/canvas` serves the queue with the ruling form (the console builds the document on demand). Then close what §5a names: **C-08 + complement 4** (revert from the canvas, two-key
   for assessment rows — do the `restore_version` hardening in the same change), **TV-02's action half**
   (leads → `source_proposals.jsonl` → a PA3 add), and whichever of complements 7/8 you can measure
   honestly. Each one ships with its check, and the register block is re-derived in the same commit.

**Then, when the keys arrive:**

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
