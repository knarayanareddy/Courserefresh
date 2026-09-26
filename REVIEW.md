# Courserefresh — end-to-end review

*Reviewer: Arena agent · Scope: whole repository at `3a6491d` (branch `arena/01a0de69-courserefresh`) ·
Method: read every file, then ran every documented command from a clean checkout with no credentials.*

---

## 0. TL;DR — the six things that matter

1. **The offline core is real and green.** `sh app/check.sh` → **179 PASS · 13 stages · `ALL GREEN` · exit 0**
   on a clean checkout with no `.env`. The policy oracle, its JS mirror, the receipt chain, the gold
   eval (n=59, action/reason match 1.000, hostile→publish 0), the artifact integrity suite and the
   redaction/handoff suite all genuinely pass. This is not a slideware repo.
2. **The flagship `--via-n8n` path cannot work as shipped.** The engine POSTs to
   `/webhook/cr/triage`; the export it ships registers the webhook path `triage`. Result: `404` →
   silent fallback to the oracle — the one thing criterion 3 (n8n, 20%) is judged on. `F1`
3. **Even if the paths matched, the canvas never actually decides.** The cycle always calls
   `policy.decide()` for the operative action; the canvas decision is only compared and recorded.
   That contradicts `spec.md` AC-16.1 and amendment D-22 ("the canvas decides"). `F2`
4. **The live learn-phase is fail-open on consent and crashes on a malformed dwell row.**
   `learner_consent.json` and `stuck_signals.json` have *no writer anywhere in the codebase*, and
   consent defaults to `True`. One telemetry POST of `{"kind":"dwell"}` (no `seconds`) makes
   `cohort_window()` raise `IndexError`, killing `--learn`/`--watch`. `F3`, `F12`
5. **The evidence the package points at is not in the repo, and part of it no longer matches.**
   `app/out/` is gitignored, so the "frozen" hero run (19 files) and rehearsal (14 files) do not
   exist on a clone; the register's own hash for the frozen gold set is wrong; ~10 rows carry stale
   values (digest 1323 B vs 1484 B measured, battery "155/12" vs 179/13, gold "57 rows" vs 59).
   The claims linter cannot catch value drift. `F4`, `F5`
6. **The documented commands do not do what the docs say.** `--root app/out/e8` and
   `--root app/out/e7` crash on a clean checkout (they need a `course/` tree inside the root that no
   document mentions); `reset_course.py` — the documented step before every hero run — leaves
   `app/out/micro-lessons/` behind, so the next hero run silently loses the stuck-learner `DISPATCH`
   and stops matching `EVIDENCE.md` §4. `F6`, `F10`

Everything below is evidence-first: claim → the exact command → what it actually printed.

---

## 1. What the repo is

A three-layer product built for a weekend hackathon brief ("a course that updates as its subject
changes; spot when a learner is stuck before they ask"):

| Layer | What it is |
|---|---|
| **Law** | `specs/constitution.md` — 16 articles (authority ladder PA0–PA3, two-source rule, no publish without a revert gate, no number without a receipt, hostile input in scope, containment) plus `shared/` contracts, `security/threat-model.md` (TM01–TM18), `design/MASTER.md` (locked paper-and-ink tokens, AA-verified). |
| **Rulebook (the interesting part)** | `specs/courserefresh/skin/policy.py` (oracle) ≡ `app/n8n/policy_node.js` (production). Deterministic, first-match-wins order: safety → evidence → relevance → authority → integrity → budget → default `ESCALATE(unknown_state)`. Models answer seven closed questions; code decides. |
| **Runtime** | `app/run_walking_skeleton.py` (offline twin: notice→verify→decide→act→learn→report, writes real lesson versions + diffs + chained receipts + digest), `app/run_live.py` (Apify → judge → policy → repo → learners, with `--via-n8n`, `--learn`, `--watch`), `app/lib/*` (config, apify, judge, n8n, telemetry, notify, console, guard), `app/serve.py` (console + telemetry intake), 6 n8n workflow exports. |
| **The artifact** | `course/agent-ops/` — six lessons with front matter (sources, revert gate), versioned bodies `v1…v5`, diffs, quizzes, CHANGELOG, README. |
| **Proof machinery** | `specs/courserefresh/{EVIDENCE,RECEIPTS,TRACEABILITY,AMENDMENTS}.md`, 13-stage battery `app/check.sh`, `app/tools/{freeze_evidence,collect_live,metrics,reset_course,make_n8n_exports}.py`. |

The organising idea is genuinely good and it is enforced, not just asserted: **models propose, code
decides; a publish promises its own undo; refusals are the product.** The digest really does print
refusals first, and the receipt chain really is hash-linked and tamper-evident.

---

## 2. How I verified it

```sh
sh app/check.sh                     # 179 PASS · 13 stages · ALL GREEN · exit 0   (no keys, twice)
node app/tests/test_gate_parity.py  # PASS — 59 gold rows + 2 probes, JS mirror vs Python oracle
python3 app/run_walking_skeleton.py # hero shape reproduced: PUBLISH 2 · ESCALATE 4 · NO_CHANGE 1
                                    #   · DISPATCH 1 · REVERT 1 · 9 receipts · chain ok (9 rows)
python3 app/serve.py                # console :8080 + telemetry :8787, all GET routes 200
```

Verified by hand on the running servers: `/`, `/healthz`, `/api/preflight`, `/api/receipts`,
`/api/run_log`, `/eval`, `/lesson/{id}` all 200; `POST /telemetry` with `consent:false` → `403
consent_missing` before storage; a non-hashed handle → `handle_not_hashed`; `POST /pause` without the
token → 403. The learn→revert branch works when the window closes (I forced
`hours_since_publish=60` → `REVERT revert_gate_satisfied`, labelled `fixture (simulated)` in sim
mode). `collect_live.py`'s redaction suite really does catch a planted token (15/15).

I restored the working tree afterwards (`git status` clean) — the hero run's loop-written versions
were reverted with `git checkout -- course/`.

---

## 3. Findings, ranked

Severity is about *what breaks a judge, a learner, or the next agent* — not about line count.

### F1 — `--via-n8n` cannot work: the engine and the export disagree on the webhook path · **blocker**

| | |
|---|---|
| Evidence | `app/n8n/wf-cr-1-triage.json` → `nodes[0].parameters.path = "triage"` (n8n therefore serves `POST /webhook/triage`). `app/run_live.py:298` → `client.call_webhook("cr/triage", …)`; `app/lib/n8n.py:122` → `f"{self.base}/webhook/{path}"` ⇒ `POST /webhook/cr/triage`. |
| Docs that disagree with the export | `WIRING.md:73`, `SETUP.md:151` ("path is `cr/triage`"), `HANDOFF.md:208` — all tell the operator the path is `cr/triage`, and `SETUP.md` even lists `webhook_http_404` as an operator error. |
| Why the battery is green anyway | `test_live_modules.py:158,228` mock `POST /webhook/cr/triage` — the test encodes the *client's* assumption, never the export's registered path. Nothing cross-checks the two. |

**Impact.** With real keys, `--once --via-n8n` returns 404, records `canvas.reason =
webhook_http_404`, and falls back to the oracle. The claim "powered by n8n, not decorated with it"
is then false in the only place it can be observed — the run log.

**Fix (one of two, plus a test).** Either set `"path": "cr/triage"` in the triage export (and
`cr/act` in the act workflow, updating the internal `ATTACH_AT_IMPORT/webhook/act` HTTP nodes), or
change `call_webhook("triage")` and the docs. Then add a test that reads the `path` from
`wf-cr-1-triage.json` and asserts the string the engine posts to — that is the check whose absence
caused this.

### F2 — the canvas is consulted, never obeyed (AC-16.1 is not satisfied) · **blocker for criterion 3**

`spec.md:168` — *"`--via-n8n` posts the DecisionInput to the triage webhook and **the returned
decision, with its execution id, is the one the cycle acts on**."* Amendment `D-22` says the same.
The implementation:

```python
# app/run_live.py, --via-n8n branch
canvas = canvas_decide(cfg, twin_event["input"])      # 200 {decision, execution_id}
oracle = twin.policy.decide(twin_event["input"])      # <- always computed
if canvas_agrees(decision, oracle): twin_event["canvas"] = {..., "same_as_oracle": True}
...
log = twin.run(tree, twin_events, ...)                # <- inside: out = policy.decide(inp)  (line 367)
```

`twin.run()` re-decides with the oracle for every event; the canvas value is stored on the receipt
and otherwise unused. When the two agree the difference is invisible; when they disagree the cycle
fails closed to `ESCALATE(ambiguous_change)`. So the engine is correct *and* honest, but the
advertised split ("the canvas decides, the oracle polices") is inverted: **the oracle decides, the
canvas audits.**

**Fix.** Either (a) pass the canvas decision into `twin.run()` (e.g. `event["decision_override"]`
honoured only when `canvas_agrees` is true, with the oracle result kept on the receipt as the police
record), or (b) amend AC-16.1/D-22 to say what the code does. Do not leave the current text as is —
it is exactly the kind of claim a judge with an n8n instance can falsify in ninety seconds.

### F3 — the live learner path is fail-open on consent, and its inputs have no writer · **high**

```python
# app/run_live.py:540  — read, never written anywhere in the repo
telemetry_rows = read_json(STATE / "learner_consent.json", {})
# app/run_live.py:557  — read, never written anywhere in the repo
stuck = read_json(STATE / "stuck_signals.json", [])
# app/run_live.py:618  — absent file ⇒ consent True
"consent": bool(consent.get(signal["learner_ref"], True)),
```

`grep -rn "learner_consent\|stuck_signals" app/ specs/` finds **no producer** for either file. So the
live stuck-dispatch branch is (a) dead unless an operator hand-crafts state, and (b) if the operator
does hand-craft it, every learner is treated as consented. That inverts Art. V ("consent, privacy,
and the Named Learner rule") and Art. IV.2 (dispatch only with recorded consent) at the exact moment
they matter — the live demo. The offline twin does this correctly (`notify_cohort()` requires
`learner.consent` from the labelled fixtures), so the two runtimes disagree on the system's most
sensitive branch.

**Fix.** Write consent at intake (the telemetry endpoint already validates `consent: true` — record
`learner_ref → consented_at` there), derive stuck signals from stored telemetry in the learn phase,
and default `consent` to `False` everywhere it is read. A live learner with no consent row should get
nothing, and the digest should say `consent_missing`.

### F4 — the evidence the whole package points at is not in the repository · **high**

`EVIDENCE.md` §2: *"The frozen evidence set … is `app/out/evidence/cr-20260926-1421-001/` with its
`MANIFEST.sha256`"*; §4 lists 19 files as `PROOF`; `RECEIPTS.md` opens with the same pointer;
the committed `course/agent-ops/CHANGELOG.md` cites receipt ids (`rcpt-21-001-000`). But:

```
$ git ls-files app/out | wc -l      # 0  (.gitignore: app/out/)
$ ls app/out/evidence/              # only LAST-GREEN.txt, written by my own battery run
$ ls app/out/evidence/cr-20260926-1421-001   # No such file or directory
```

On a clean checkout **every** `app/out/evidence/...` proof pointer resolves to nothing. That is
defensible as "regenerable state" — except that the frozen runs are *not* byte-reproducible (run id
and wall-clock timestamps are embedded in receipts, digest and manifest), so the hashes in
`EVIDENCE.md`/`RECEIPTS.md` can never be checked by anyone. The committed artifacts that *are*
shipped (lesson versions v4/v5, diffs) carry receipt ids whose receipts are gone.

**Fix.** Commit a small, curated `evidence/` directory (the frozen hero + rehearsal: manifests,
receipts, digest, eval report — a few hundred KB), or drop the hash claims and state plainly that
evidence is regenerated per run. Shipping the register's hash of a file nobody can obtain is worse
than shipping no hash.

### F5 — stale numbers in the register the constitution treats as ground truth · **high**

`constitution.md` Art. VI: *"Every quantitative claim … resolves to a row in RECEIPTS.md."*
`test_claims.py` enforces only that measured rows *name* an artifact and a command — it never
re-derives a value. So value drift is invisible, and there is drift:

| Row | Register says (`measured`) | Actual, re-measured today | How |
|---|---|---|---|
| N11b | gold `sha256:7b511eb5…` | `sha256:73860b21…` | `sha256sum specs/courserefresh/skin/gold.jsonl` |
| N15 | digest `1323 bytes` | **1484 bytes** (same hero command) | `wc -c app/out/digest.md` |
| N04b | naive inclinations `34/57` | `36/59` | `policy.py --eval` |
| N08 | `unknown_state` `4/57 = 0.070` | `4/59 = 0.068` | same report |
| N11 | gold set `57` rows | **59** rows (`_meta.n = 59`) | `test_gold_floor.py` prints `n=59` |
| N32 | battery `155` checks / `12` stages | **179 / 13** | `sh app/check.sh` |
| N33 | live-path checks `39 (config 9 · apify 5 · …)` | **47/47** | `test_live_modules.py` |
| E8 | "0 and 0 on **57** rows" | 59 rows | eval report |
| T08 (tasks) | "1323 bytes" | 1484 bytes | digest |
| HANDOFF §7 | "live selftest 12/12" | **13/13** | `python3 app/lib/judge.py --selftest` |
| T32 (tasks) | `--selftest` 12/12 | 13/13 | same |

A wrong hash on the *frozen gold set* is the most serious of these: it means either the gold file
changed after the row was written (Art. VII forbids that without a new `gold_version` + amendment
row) or the row was never true. Either way, "don't touch the gold set" is currently unverifiable.

**Fix.** Add a checker to `app/check.sh` that re-derives the register's key values (gold sha, n,
digest bytes, battery counts, selftest counts) and fails on drift — `test_claims.py` is the natural
home. Then correct the rows.

### F6 — the documented reproduction commands crash on a clean checkout · **high (first-touch)**

```sh
# README.md:43-44 · EVIDENCE.md:58 (E9) · OPERATIONS.md:140-141 · RECEIPTS.md N31 · SETUP
python3 app/run_live.py --root app/out/e8 --seed-baseline   # ok
python3 app/run_live.py --root app/out/e8 --dry-run --once  # FileNotFoundError:
#   '<repo>/app/out/e8/course/agent-ops/curriculum.json'
```

```sh
# AGENTS.md:64 · EVIDENCE.md:55 (E7) · RECEIPTS.md N28 · reviews/05 §3.6
python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail
# FileNotFoundError: '<repo>/app/out/e7/agent-ops/lesson-04-tool-permissions/v3.md'   (exit 1)
```

Both commands are cited as the *proof* for evidence rows. `rebase()` makes `--root` mean "a complete
tree that already contains `course/` and `app/out/`" — which the tests know
(`test_live_modules.py:317` does `copytree(ROOT/"course", SANDBOX/"course")`) and the docs never say.
So a judge following the README gets a traceback where the repo promises a verdict.

**Fix.** Make bare `--root` bootstrap: if `<root>/course` is missing, copy the repo's authored
baseline into it (and say so on stdout), or change the docs to the two-command sequence the tests
use. Bonus: the twin's `main()` already accepts a root that *is* a course tree — the two entry points
should share one bootstrap helper.

### F7 — a crashed cycle poisons dedupe state, and the next run reports success · **high (silent)**

```
$ python3 app/run_live.py --root /tmp/e8b --seed-baseline
$ python3 app/run_live.py --root /tmp/e8b --dry-run --once     # crash (F6), exit 1 — but
                                                               # seen_snapshots.json is already written
$ python3 app/run_live.py --root /tmp/e8b --dry-run --once
{"snapshots_new": 0, "decisions": {}, "sources_due": []}       # exit 0 — "success", zero work
```

`notice()` commits `seen_snapshots.json` before `verify_and_run()` can fail. The four change events
that were mid-flight are then permanently "seen"; nothing retries them, nothing marks the run
incomplete, and the summary looks like a healthy idle cycle. This directly contradicts `harness.md`
§1 ("a failed fetch is an `unverifiable` event, not silence") and it is the failure mode most likely
to bite an unattended overnight `--watch`.

**Fix.** Write the dedupe state only after a cycle completes (or move the seen-marking to a
`pending → committed` two-phase file), and make a zero-work cycle say so loudly (`no_delta`). A
crash should leave the same snapshots eligible for the next run.

### F8 — `--preflight --probe` crashes for the n8n judge provider · **medium**

`judge.py:159` passes `json.dumps({...}).encode()` (bytes) to a transport whose first line is
`json.dumps(body)` ⇒ `TypeError: Object of type bytes is not JSON serializable`. Reproduced — the
exception is uncaught, so the preflight dies instead of printing a probe verdict:

```sh
CR_JUDGE_PROVIDER=n8n CR_JUDGE_API_KEY=dummy N8N_WEBHOOK_URL=https://n8n.example/webhook/cr/judge \
  python3 app/run_live.py --preflight --probe      # exit 1, traceback
```

`n8n` is a documented, first-class provider (`.env.example`, `SETUP.md` §2), and `--probe` is the
one screen D-1 is supposed to be read from. Fix: pass the dict. Also note `WebhookProvider` sends
`CR_DEMO_TOKEN` as the auth header while everything else uses `N8N_API_KEY`/`CR_JUDGE_API_KEY` —
worth aligning while you are in there.

### F9 — `reset_course.py` deletes committed files, and the shipped tree is not the baseline · **medium**

```
$ cp -r course /tmp/course-test && python3 app/tools/reset_course.py --course /tmp/course-test
reset: removed 6 loop-written versions, restored 1 quiz file(s)
# lesson-03 → v1 only; lesson-04 → v3 only; README table back to v1/v3; CHANGELOG reset
```

Those six files (`lesson-03/v2.md`, `lesson-04/v4.md`, `v5.md` and three diffs) are **tracked at
HEAD**. So a fresh clone is not at the "authored baseline" the tool restores — it is at the *post-hero*
state that `EVIDENCE.md` §4 documents. Consequences:

* `AGENTS.md`/`HANDOFF.md` say "run `reset_course.py` before every hero run". Do that and the hero
  run no longer produces the versions `EVIDENCE.md` §4 records (you get a different chain), *and*
  your checkout shows six deletions.
* Run the hero *without* resetting (what `README`/`EVIDENCE.md` E4 imply) and you get
  `lesson-04 v5→v6`, `REVERT v4→v7`, `lesson-03 v2→v3` — different from the recorded `v4/v5` hero.

Neither path reproduces the documented evidence. Pick one contract — "commit the hero artifact and
never reset" or "commit only the authored baseline and always reset" — and make the docs, the tool
and `EVIDENCE.md` agree.

### F10 — `reset_course.py` does not reset, so the hero run silently loses the learner dispatch · **medium**

`reset_course.py` clears `receipts.jsonl`, `run_log.jsonl`, `digest.md`, `notifications.jsonl` and
`state/` — but not `app/out/micro-lessons/`. The tutor cap reads that directory
(`concept_recently_dispatched()` → `ml-<concept>-*.md` mtime within `micro_lesson_per_concept_days`),
so a stale micro-lesson from any earlier run suppresses the next run's dispatch:

```
$ python3 app/tools/reset_course.py && python3 app/run_walking_skeleton.py
  reset: removed 3 loop-written versions … state cleared   # versions only; micro-lessons/ survives
  decisions: {"PUBLISH": 2, "ESCALATE": 4, "NO_CHANGE": 2, "REVERT": 1}   # 0 DISPATCH
  cr-learner-stuck-01 → NO_CHANGE ['rate_limited']                        # "concept cap: permissions-mode"

$ rm -rf app/out/micro-lessons && python3 app/tools/reset_course.py && python3 app/run_walking_skeleton.py
  decisions: {"PUBLISH": 2, "ESCALATE": 4, "NO_CHANGE": 1, "DISPATCH": 1, "REVERT": 1}   # == E4
```

So "the documented reset, then the hero" reproduces `EVIDENCE.md` §4's numbers **only if you also
delete a directory the reset tool does not know about** — and the failure is a *silent* difference in
the decision mix (no error, no `unmeasured`, a cap that fires because of a file from a previous day's
demo). This is the learner-facing half of the product ("spot when a learner is stuck before they
ask"), so the drift is not cosmetic.

**Fix.** Make `reset_course.py` clear everything the loop consumes and can be poisoned by:
`micro-lessons/`, `notifications_delivery.jsonl`, `delivery.jsonl`, `live/`, `snapshots/`,
`state/apify_units.jsonl`, `state/telemetry.jsonl` (optionally behind `--keep-telemetry`). Then say in
`HANDOFF.md` that reproducibility starts from a fully clean `app/out/`.

### F11 — the digest's "downstream to revisit" can name a lesson it just rewrote · **medium (report)**

In the hero digest:

```
- PUBLISH `lesson-04-tool-permissions` v5 → v6 · … · quiz q2 regenerated
- PUBLISH `lesson-03-apify-inputs` v2 → v3 · …
- downstream to revisit (not rewritten tonight): lesson-04-tool-permissions, lesson-05-…, lesson-06-…
```

`lesson-04` is downstream of `lesson-03`, and `render_digest` unions `downstream_lessons()` over every
publish without subtracting the lessons published in the same run (`run_walking_skeleton.py:449`).
The sentence is self-contradictory, and this line is one the teacher seat in `reviews/05` specifically
promised would be coherent.

**Fix.** `downstream -= {lessons whose receipt in this run is PUBLISH/REVERT}`.

### F12 — a malformed telemetry row kills the unattended loop · **medium (availability)**

`validate_payload()` accepts `{"kind":"dwell"}` with no `seconds`; `cohort_window()` then evaluates
`sorted([...seconds...])[count_of_dwell_rows // 2]` (`telemetry.py:87`) — an index into a filtered
list using an unfiltered length:

```
IndexError: list index out of range      # reproduced with a single dwell row lacking `seconds`
```

`cohort_window()` is called per lesson in `learn_phase()`, which `--watch` runs every 15 minutes. One
sloppy (or malicious, if consenting) client row ⇒ the learn phase of the unattended run dies. Fix:
require `seconds` for `dwell` in `validate_payload`, and use `statistics.median` with a guard.

### F13 — smaller correctness and hygiene issues · **low, but cheap to fix**

| # | Issue | Evidence |
|---|---|---|
| a | Delivery records go to the **repo's** `app/out/notifications_delivery.jsonl` even under `--root`, while `collect_live.py` copies `live/delivery.jsonl` — the collector and the engine disagree about where delivery lives. | `notify.py:54` (`log_path or DELIVERY_LOG`, module-level repo path); `collect_live.py:56` |
| b | `make_n8n_exports.py` has no `--check` and silently ignores unknown flags; it always rewrites. Regeneration *is* idempotent (I verified `git status` stays clean), but a drift check would be better than a rewrite. | ran `--check`, `--help` |
| c | `test_contracts.py` path-existence check skips every `app/out/…` reference — which is precisely why F4 and F6 are invisible to the battery. That skip is now load-bearing and should at least assert the *evidence pointer style* is consistent. | `test_contracts.py:117` |
| d | The revert receipt's `previous_version` is the fixture's `published_version` (`v4`), not the current head (`v6`), so `REVERT lesson-04 v4 → v7` reads oddly next to `PUBLISH … v5 → v6`. Correct, but confusing without the receipt. | `run_walking_skeleton.py:revert_version` |
| e | `metrics.py` prints `generated_at` with `datetime.utcnow()` (deprecated in 3.12) and a wall-clock date in a repo that bans dates outside pre-registration — harmless in a runtime artifact, but it will trip a naive `test_hygiene` extension. | `metrics.py` |
| f | `app/lib/apify.py` sends `payload["budget"]` to the Apify *run* endpoint; the documented spend control is `usageTotalUsd`/`maxTotalChargeUsd` (a query param on the run-sync endpoints). Worth checking against the API before the first live call. | `apify.py:run_actor` |

---

## 4. What is genuinely strong (do not rebuild these)

* **The rulebook split.** One normative rule order, two runtimes, a byte-for-byte drift test, and a
  gold set with named traps (`cr-inject-01` must escalate with the hostile string on the receipt).
  59 rows, action *and* reason parity, `hostile→publish 0`, `unsupported→publish 0`.
* **The receipt chain.** Hash-linked rows, `verify_chain()` at the end of every run, tamper detection
  asserted in the selftest, artifacts re-hashed from disk against their receipts.
* **Honesty plumbing that works.** `unmeasured` is a first-class value; the preflight prints what is
  missing *by key name* and never a value (`set(len=…, sha256=…)`); the `file` notify channel says
  `staged` and refuses to say `delivered`; `collect_live.py` redacts, re-verifies the chain and exits
  3 rather than hand over a secret — proven with a planted token.
* **The console.** No scripts, no remote assets, colours read from the design lockfile (and tested
  against it), refusals first, `/healthz` reporting `receipt_count_gap`. It loaded first try on a
  clean checkout.
* **The paper trail.** `TRACEABILITY.md` maps ACs to commands, `AMENDMENTS.md` records decisions with
  reasons (D-22…D-31), and reviews 01–06 close findings with pasted output. The self-awareness in
  this repo is unusually high — most of the findings above are things the repo's own laws would
  catch if the checks were wired to values instead of shapes.

---

## 5. If you only do five things

1. **Make the canvas path real** (F1 + F2): fix the webhook path in the export, act on the canvas
   decision when it agrees with the oracle, and add the test that reads the path *from the export*.
   This is 20% of the score and currently cannot be demonstrated live.
2. **Fail closed on learner consent** (F3): write consent at intake, read it in the learn phase,
   default `False`. Then the stuck-dispatch story survives a judge asking "where did consent come
   from?".
3. **Make the evidence reproducible or stop citing hashes** (F4 + F5): either commit a curated
   evidence bundle, or delete the hash/byte rows and keep the shape claims. Either way fix the gold
   hash and the ~10 stale rows — `Art. VI` is the repo's loudest promise.
4. **De-poison the dedupe state** (F7): commit `seen_snapshots.json` only after a cycle succeeds, so
   a crash is retried instead of becoming silence. This is the difference between an unattended loop
   that is honest and one that looks honest.
5. **Fix the documented crashes and the fake reset** (F6 + F8 + F10): bootstrap `--root`, pass a
   dict to the transport, make `reset_course.py` clear everything the loop reads (`micro-lessons/`,
   delivery logs, `snapshots/`), and re-run E7/E9 to paste real output into `EVIDENCE.md`.

---

## 6. Numbers measured in this review (re-derive with the command in the right column)

| Value | Measured | Command |
|---|---|---|
| Battery | 179 PASS · 13 stages · ALL GREEN · exit 0 | `sh app/check.sh` |
| Gold eval | gold-v0.3 · n=59 · action 1.000 · reason 1.000 · hostile→publish 0 · unsupported→publish 0 · naive inclinations 36/59 | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` |
| Parity | PASS · 59 rows + 2 probes | `node app/tests/test_gate_parity.py` |
| Policy node sha | `1885efcb791872c4…` (matches HANDOFF) | `sha256sum app/n8n/policy_node.js` |
| Hero run shape | PUBLISH 2 · ESCALATE 4 · NO_CHANGE 1 · DISPATCH 1 · REVERT 1 · 9 receipts · chain ok (9 rows) · 11 sources · 6 deltas | `python3 app/run_walking_skeleton.py` |
| Hero from a fully clean `app/out/` | identical shape / same versions as `EVIDENCE.md` §4 (`lesson-04 v3→v4`, `lesson-03 v1→v2`, revert `v4→v5`) | `rm -rf app/out/micro-lessons && python3 app/tools/reset_course.py && python3 app/run_walking_skeleton.py` |
| Hero after `reset_course.py` alone (stale `micro-lessons/`) | DISPATCH becomes `NO_CHANGE(rate_limited)` — E4's mix is not reproducible | `python3 app/tools/reset_course.py && python3 app/run_walking_skeleton.py` |
| Digest (hero rerun) | 1484 bytes · sha256 `ad8a5e0e…` | `wc -c app/out/digest.md` |
| Gold file hash | `sha256:73860b21…` | `sha256sum specs/courserefresh/skin/gold.jsonl` |
| Curriculum | 6 lessons · 13 objectives · 19 quiz items | `python3 app/tests/test_curriculum.py` |
| Live modules | 47/47 · judge selftest 13/13 · handoff 15/15 | `python3 app/tests/test_live_modules.py` etc. |
| Console | 3642 bytes · no `<script` · all routes 200 | `python3 app/serve.py` + curl |

## 7. Fix log (added after the fixes landed)

Every finding above was resolved in the session that followed this review, on the no-key path, and each
one is now held by a check that fails if it comes back. `sh app/check.sh` → **295 PASS (263 in 13
measured stages + the 32-check claims audit), `ALL GREEN`, exit 0** with no credentials; the two shipped
bundles under `specs/evidence/` are re-hashed by the battery on every run. The numbers in §6 above are
what I measured *at review time* and are left as they were found.

| Finding | Fix | Held by |
|---|---|---|
| F1 (webhook path) | `skin/wiring.json` is the one source for both the path the engine posts to and the path the export registers | `test_live_modules.py` (export path = wiring) |
| F2 (canvas consulted, never obeyed) | the canvas' decision *is* the decision (`decision_override` + `decided_by: canvas`), re-validated against the closed sets; a disagreement still fails closed; **and** an author ruling outranks both (D-32) | §5 + §13 of `test_live_modules.py` |
| F3 (consent fail-open, no writer) | `record_consent()` writes the register at intake; reads default to **not consented**; stuck signals derived from stored telemetry | `test_live_modules.py` (consent intake, default-deny) |
| F4 (evidence not in the repo) | two frozen bundles shipped under `specs/evidence/` (19 + 20 files), every hash re-derived by the audit stage | `test_claims.py` (bundle completeness) + `audit_claims.py` |
| F5 (stale register numbers) | `RECEIPTS.md` §6 is a machine-checked block re-derived from the files on every battery run | `audit_claims.py` (stage 14/14) |
| F6 (documented commands crash) | bare `--root` bootstraps the course tree (and says so); both documented commands now exit 0 from an empty root | verified by running both |
| F7 (crash poisons dedupe) | dedupe state commits after the cycle; an unfinished cycle is retried from its own snapshots and abandoned loudly after 3 attempts | `test_live_modules.py` (crash-retry) |
| F8 (`--probe` crashes for n8n) | the probe passes the body it documents; provider credentials are per-provider (`CR_JEV_*` included) | `test_live_modules.py` (probe) |
| F9/F10 (reset deletes / does not reset) | `reset_course.py` restores the authored baseline and clears *everything* the loop reads back, micro-lessons and state included | `test_artifacts.py`, `test_live_modules.py` |
| F11 (digest names a lesson it rewrote) | `downstream − rewritten` | `test_walking_skeleton.py` |
| F12 (malformed telemetry kills the loop) | `dwell` without `seconds` is refused at intake; the median is guarded | `test_live_modules.py` (telemetry) |
| F13 (small things) | delivery path is root-aware; `--check` on the export generator; frozen-run pointers under `app/out` are a build error; a revert names the version it moves from *and* the one it undoes; `utcnow()` → `datetime.now(timezone.utc)`; the Apify ceiling travels as `maxTotalChargeUsd` | `test_contracts.py` (four new checks), `test_live_modules.py` |

New surface since the review: `specs/reviews/07-author-canvas-panel.md` (the seat panel on the canvas,
Tavily and JEV, with the conditions it demanded and their status), `app/lib/{canvas,rulings,jev,tavily}.py`,
`app/tools/{audit_claims,battery_summary}.py`, and the withheld-delta queue that makes an author's
approval act on the world.

## 8. What I did not verify

* No live Apify run, no live judge call, no real n8n instance, no delivered card — no credentials
  exist in this sandbox, and the repo is designed not to need them (E11/E12 cover those paths with
  injected transports). Everything above about the live path is either static reasoning from code
  plus a mocked transport, or a reproduced crash that needs no network.
* ~~The frozen `MANIFEST.sha256` values: the artifacts are not in the repository.~~ **Resolved:** two
  bundles ship in `specs/evidence/` and the audit stage re-hashes every file on each battery run, so a
  manifest that stops matching its bundle fails the build.
* Video/pitch materials (`VIDEO-SHOTLIST.md`) — not exercised.
