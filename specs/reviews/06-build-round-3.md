# Review 06 — round 3: the build, with each other's hands on the wheel

`D-0 · seats: N8N, APIFY, JEV, UX, T (teacher), ST (student), SRE · rule: nobody ships a component
they also get to mark; every component has a builder seat and a supervisor seat, and the supervisor's
name goes on the finding rows below.`

Round 2 produced a spec seven specialists would sign. Round 3 is the part where a spec that is only
agreed-with dies: **build it**. This file is the round-3 record — who built what, who watched, what
broke, what the fix was, and which command proves the fix. It is written the way the battery reads:
an assertion with no artifact is a claim, and claims are the thing this project refuses (Art. VI).

---

## 1. Assignments and supervision pairs

| Component | Built by (seat) | Supervised by (seat) | The supervision that actually bit |
|---|---|---|---|
| `skin/sources.json` (6 sources, roles, actor pins, HTTP fallbacks) | APIFY | JEV | JEV: "a changelog and its docs are the same voice; if the JSON cannot say that, the engine will publish on one voice" → roles + `independent_publishers` closed the hole |
| `app/lib/apify.py` (run, normalise, unit ledger) | APIFY | SRE | SRE: "rejected rows must be *counted*, not dropped" → every refusal carries a reason code and a count |
| `app/lib/judge.py` (7 questions, providers, render contract) | JEV | T | T: "a rewrite the model likes is not a rewrite the lesson supports" → every replacement must be anchored to a quote span; no number may appear that is not in a quote |
| `app/lib/n8n.py` + export generator (6 exports now) | N8N | N8N-alt (SRE chairing) | N8N-alt: "an edit path that offers `PUT` when it means `POST` is how you get two workflows with one name" → upsert by name, update in place, duplicate refused |
| `app/lib/telemetry.py` (consent-first intake, cohorts) | ST | UX | UX: "the learner must never see an error that names them" → refusals are generic; the handle regex and the coarsening are the ST seat's own condition |
| `app/lib/notify.py` (channels + delivery records) | ST | UX | UX: "staged is a word, and `delivered` is a different word" → the file channel can never mark delivered |
| `app/lib/console.py` (read-only page, pause switch) | UX | T | T: "if I have to open a terminal to see why lesson 3 changed, I will not" → `/lesson/{id}` returns versions, gates and the receipt that caused each one |
| `app/run_live.py` (the loop) | SRE | JEV | JEV: "the loop is one more place a model can quietly decide" → the judge answers closed questions; the code decides; `--via-n8n` is parity-policed |
| `app/tests/test_live_modules.py` (the proof, no keys) | SRE | all seven | every seat named the check that would have caught its own component's worst day; those checks are in this file |
| `app/tools/collect_live.py` (handoff collector) | SRE | UX | UX: "a folder a human will paste into a chat must be safe to paste" → telemetry becomes counts, secrets are redacted, and exit 3 blocks the handoff |
| `SETUP.md` / `.env.example` / `OPERATIONS.md` §9–12 | UX | SRE | SRE: "a runbook that assumes the reader knows the exit codes is not a runbook" |

The pairing rule was the point: the seats that built the risky parts (a model call, a learner-facing
message, a write to `course/**`) are never the seats that signed them off.

## 2. What the builders found in each other's work

Every row below is a defect that existed in round-3 code at some point in this sitting. `Fix` names
the code; `Proof` names the check that now fails if it comes back. Nothing here is hypothetical: the
"found by" column is the seat whose component it *was*, which is why the pairs were worth the trouble.

| ID | Found by → raised against | Defect (as it behaved) | Fix | Proof |
|---|---|---|---|---|
| B-01 | SRE → all | `Config()` read defaults and `.env` but **never `os.environ`**: pasting keys with `APIFY_TOKEN=… python3 app/run_live.py` resolved to nothing, so `mode` stayed `sim` with keys present | three-source resolution, explicit > environment > `.env` > defaults, filtered to project prefixes | `test_live_modules.py` (env precedence; `PATH` excluded; `missing_for`) |
| B-02 | JEV → JEV | a walrus inside a conditional expression is a syntax error in the one place the loop picked a provider | plain assignment before the branch; `--selftest` runs the import | `run_live.py --selftest` (12/12) |
| B-03 | JEV → JEV | the guard helpers return tuples (`host_allowed(url) -> (bool, str)`); two call sites treated them as booleans, so a *rejected* host read as "allowed" | unpack `(ok, reason)` at every call site, and put the reason on the refusal row | `test_live_modules.py` (`host_not_allowlisted`) |
| B-04 | APIFY → APIFY | fixture recordings were keyed differently from the engine's decision keys, and `q7_lesson_touched` (a Choice) was missing from the recordings → every live call failed closed as `unknown_state`, which looked like "the judge is careful" rather than "the fixture is wrong" | one `_answer_key()` for both sides; recordings regenerated with all seven questions; q7 resolved from the hint to a full lesson id | `make_apify_fixtures.py` + `test_live_modules.py` (partial answer set fails closed *by design*, not by accident) |
| B-05 | APIFY → APIFY | dedupe was keyed by `content_hash` alone, so the same page collected from a changelog and its docs collapsed to one snapshot — the engine then refused a change that had two voices (and would have published a change with one) | dedupe per `source_id:hash`; baselines seeded with the same key shape | dry cycle: `cr-n8n-068a1ed5ec` = one voice → `ESCALATE(insufficient_corroboration)`; `cr-apify-n8n-5ede71b47d` = two voices → publish |
| B-06 | SRE → SRE | the twin's `apply_patch` requires `event["parent"]`; the live event builder omitted it, so the first real write died in the writer, not in the policy | parent is set from the frozen course version, and the chaos rehearsal (`--chaos write-fail`) keeps that path honest | `test_artifacts.py` (failed write reported exactly once) |
| B-07 | N8N → N8N | `quiz_patch.lesson_id` must be the short form `lesson-NN`; the live engine sent the long id and the bare number, both of which the twin refuses | one conversion, in one place, with the long id kept in the receipt | `test_curriculum.py` (regenerated item traceable) |
| B-08 | JEV → SRE | claim clustering made one cluster per snapshot, so the same fact published twice in a cycle and the second publish was a duplicate of the first | cluster by claim overlap (Jaccard ≥ 0.25), representative = authoritative + earliest, one publish per cycle, extras deferred with a reason | dry cycle: exactly 1 publish, 1 escalate, `deferred_publishes` empty |
| B-09 | N8N → N8N | the export contract test asserted "five exports" and derived the workflow name from the file name — both wrong the moment the error workflow arrived | name↔number check per file, execute-once guard required in every export, sticky-note required, count read from the exported set | `test_contracts.py` (14/14) |
| B-10 | SRE → SRE | the preflight wrote `preflight.json` before ensuring the directory existed, so a preflight on a fresh clone failed with `FileNotFoundError` — the one command the user must run first | `mkdir(parents=True, exist_ok=True)` before the write | `run_live.py --preflight` on a clean tree |
| B-11 | JEV → JEV | the judge key was never *validated*: the probe checked Apify and n8n, so a wrong model key would only surface as `unknown_state` refusals on stage | `probe_provider()` — one `GET {base}/models`, prints status + whether the configured model is listed, never the key | `--preflight --probe` (judge_probe line) |
| B-12 | T → T | the export test would have passed with a *renamed* workflow whose jobs did not match its nodes; a lesson the system updates is only trustworthy if the workflow that changed it declares the same vocabulary as the course | export checks now bind name↔number and the triage export's embedded rulebook to the file byte-for-byte | `test_contracts.py` (policy drift) |
| B-13 | UX → ST | a test file contained a literal email-shaped string as a "bad handle" example; the hygiene test caught it (the repository is scanned for addresses) | the probe value is now `"alice dot example"` | `test_hygiene.py` (7/7) |
| B-14 | ST → JEV | nothing prevented a *number* appearing in a learner-facing rewrite that no quote supported — the exact failure mode the teacher seat spent round 2 arguing about | `validate_render` refuses a replacement containing a numeral absent from the quote spans, and refuses > 400 chars replaced | `test_live_modules.py` (anchored render passes, unanchored refused) |
| B-15 | SRE → N8N | `--via-n8n` compared only the *action*: `ESCALATE` for a missing voice and `ESCALATE` for a hostile page would have looked like agreement | `canvas_agrees()` compares action **and** sorted reason codes; mismatch fails closed and records both decisions | `test_live_modules.py` (`canvas_agrees` + mismatch detection) |
| B-16 | N8N → SRE | the canvas path had no defined behaviour when the webhook answered nothing usable | `canvas_decide()` returns typed failures (`not_configured`, `webhook_http_…`, `payload_invalid`); the cycle degrades to the oracle and writes `canvas.reason` into the run log | `test_live_modules.py` (unreachable canvas degrades; AC-16.2) |

| B-17 | SRE → JEV | the live learn phase could **never** revert: it handed `decide_revert` flat fields (`cohort_n`, `window_h`) while the rulebook takes the nested `cohort {n, quiz_delta, hours_since_publish}` — the same shape the fixtures and the gold set use. The path looked implemented and was dead | `hours_since_publish()` measured from receipts (falling back to the CHANGELOG), the nested cohort built at the call site, and the gate's own arithmetic written onto the receipt label | `test_live_modules.py` (measured cohort + closed window ⇒ `REVERT(revert_gate_satisfied)`, restored version on disk); `--learn` on the demo |

Two of these (B-01, B-05) were the kind that would have cost the hackathon run rather than the score:
one made credentials silently inert, the other made corroboration silently wrong. Both were found by
the seat that did **not** write the line, which is the only reason they were found before the video.

## 3. The debate that decided the shape of the loop

**JEV** argued the engine should let the canvas decide everything (`--via-n8n` as the default), because
criterion 3 rewards n8n *powering* the system and a canvas that only stores decisions is decoration.
**SRE** refused: a default network hop that can fail closed would make the unattended run depend on an
instance being awake, and the spec's own containment rules (Art. XIV) say the loop must survive its
platforms. **N8N** proposed the resolution that shipped: **the canvas decides whenever it is reachable,
the oracle polices it, and disagreement stops the cycle** — with `canvas.ok`, `canvas.same_as_oracle`
and `canvas.execution_id` on the receipt so a judge can see which machine decided and whether the two
runtimes agreed. **T** added the condition that the *learner-facing* consequence of a mismatch is
silence, not a message: a change nobody can reproduce is not sent to a student. All four signed.

**ST** and **UX** then pushed the other way on the learner side: if telemetry is unavailable (cohorts
below the floor), the system must not say "no change needed" — that sentence would be a claim. Hence
`unmeasured` with its reason, printed on the digest and the console, and no revert ever triggered from a
number that does not exist. **T** signed this one too; it is the seat's own round-2 condition, now in code.

## 4. Open conditions (agreed, not yet met)

| # | Condition | Holder | Unblocks when |
|---|---|---|---|
| 1 | one watched live cycle with `--via-n8n` and a canvas execution id in the run log | N8N, JEV | keys pasted at the end (`SETUP.md` §3–4) |
| 2 | one delivered learner card through telegram or webhook (not `staged`) | ST, UX | a bot token + chat id, or a webhook URL |
| 3 | `WIRING.md` §4/§5/§6 rows filled from real runs (instance version, prices, run ids) | SRE | the same session that pastes keys |
| 4 | the live instance's export drift check (canvas edited by hand vs file edited in git) | N8N | first `--import` on the real instance |

## 5. Sign-off

| Seat | Verdict | Condition |
|---|---|---|
| APIFY | **sign** | condition 1 (an actor run id from the real account) |
| N8N | **sign** | conditions 1 and 4 |
| JEV | **sign** | condition 1 |
| UX | **sign** | condition 2 |
| T | **sign** | none — learner-safety conditions are in code and tested |
| ST | **sign** | condition 2 |
| SRE | **sign** | conditions 3 and 4 |

The seven seats agree on the built system the way they agreed on the spec: *the parts that can be
proven without credentials are proven by the battery (13 stages, 179 checks), and the parts that need
the real world are named, gated and listed above rather than asserted.* What remains is pasting keys —
and the preflight that will tell you, in one screen, exactly what that unlocks.
