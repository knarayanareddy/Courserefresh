# Courserefresh — operations (runbook for a machine that acts alone)
`v1.1 · D-0 · Depends on: harness.md §7, §10; constitution.md Art. XIV; SETUP.md §2 (keys)`

The author is not watching at 03:00. This file is what the system does instead of asking, and what
the human does when they wake up.

---

## 1. Start / stop / pause (the whole control surface)

| Action | How | Effect | Receipt |
|---|---|---|---|
| Start the loop (canvas) | n8n schedules on; `POST /scan` once to warm | scans begin on cadence | run header |
| Start the loop (engine, unattended) | `python3 app/run_live.py --watch` | notices, decides, acts, learns, reports on `CR_LIVE_SCAN_MINUTES`; digests at 07:30 | `run_log.jsonl`, `last_cycle.json` |
| Serve the console + intake | `python3 app/serve.py [--root DIR]` | console on `0.0.0.0:8080`, telemetry on `0.0.0.0:8787`; serves a sandbox with `--root` | console `/healthz` |
| Pause everything | `python3 app/run_walking_skeleton.py --pause` (offline) or `POST /pause` (console) | freeze file set; **no writes** in the next iteration; reads continue | `freeze_active` on every subsequent receipt |
| Resume | `--resume --token <DEMO_TOKEN>` or `POST /resume {"confirm":"RESUME"}` | writes resume | resume receipt |
| Take the loop offline | disable the n8n schedules | nothing runs; existing artifacts stand | — |
| Undo one publish now | `POST /revert/{receipt_id}` **only** for a `revert_gate_satisfied` row; otherwise refused (exit 4) | revert version committed | revert receipt |
| Emergency: stop, then look | pause → read the last digest → `app/out/receipts.jsonl` tail | — | — |

**Freeze semantics:** the kill switch is checked at the top of every phase; a freeze that arrives
mid-iteration stops the *next* write, not the current one (stated so no one believes in sharper
guarantees than exist).

## 2. Budgets and their behaviour

| Budget | Value | When exhausted |
|---|---|---|
| Apify units / day | 25 | scan holds; digest prints `budget_hold`; resumes next day |
| Tokens / change, / day | 60 k, 500 k | `ESCALATE(over_budget)`; no publish that cycle |
| Publishes / day | 6 | `ESCALATE(over_budget)` |
| Notifications / learner / day, / week | 1, 3 | queued to the digest; a hard cap, never exceeded |
| Digest size | 4 KB | trimmed oldest-first; refusals are never trimmed |

## 3. Cadence and its honesty

Configured: 60 min (`skin/thresholds.json`). Measured jitter and gaps are reported daily
(`app/tools/metrics.py cadence`). If the measured cadence is worse than 2× configured for a day,
the digest prints `cadence_degraded` and the training material's stated cadence in lesson 2 is
updated by the loop itself — the course documents the system it is part of.

## 4. Consent and messaging rules in operation

- Consent is checked **before** any message is composed; a revoked consent takes effect on the next
  dispatch (and is recorded as `consent_revoked` on the receipt).
- Card content: what changed · why it matters · what to do if wrong · diff link · opt-out. No
  greeting, no tracking beyond a "seen" count, no second channel unless §6 permits.
- A micro-lesson is never sent twice for the same concept-signal within 7 days (`no_signal` if
  suppressed); this prevents "help" becoming noise.

## 5. Failure playbook (what the system does alone, then what you do)

| Failure | Automatic response | Human, on waking |
|---|---|---|
| Actor run fails | retry once → fall back to declared `fallback_url` → mark snapshot `stale` | check `WIRING.md` §6 for the run id; re-pin only if the actor shape changed |
| Model call fails / times out | retry once with the same prompt; then `ESCALATE(model_unavailable)` (no publish) | re-run the event from the escalation queue |
| Judge returns malformed JSON | coercion → `unknown` → `ESCALATE(unknown_state)` | read the raw answer on the receipt; adjust the prompt, not the policy |
| Git write fails | retry once; then `ESCALATE(write_failed)`; the decision stays pending | check token scope; `POST /revert` is *not* the fix here |
| Chain verification fails | exit 1, `DIGEST FAILED` banner, no further writes | treat as an incident (below) |
| Telemetry gap | gates print `unmeasured`; no revert claim | recruit the missing consent or accept `unmeasured` in the digest |
| Two freezes in one day | overnight run cancelled; digest says `paused` | read §6 |

## 6. Incidents (Sev-1 / Sev-2)

- **Sev-1:** a publish that should not have happened, a chain break, a learner-visible error, or an
  unlabelled sim artifact presented as live.
  Response: pause → freeze evidence (`app/tools/freeze_evidence.py`) → write the incident in this
  file under §7 → amend the spec if a rule was missing → re-run only after the battery is green.
- **Sev-2:** a decision without a receipt, a digest gap, a budget bypass attempt, a fallback used
  without its label.
  Response: fix before the next unattended window; note it in the digest the next morning.

## 7. Incident log

| # | Date | Sev | What happened | Root cause | Fix (spec + code) |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## 8. Retention, sunset, and the humans' exit

- Telemetry rows: **14 days**, then aggregate-only; hashed handles; no raw names ever stored (Art. V).
- Snapshots and receipts: kept for the audit window, deleted after the event ends; the *lesson* and
  its diff survive (they are the artifact).
- **Sunset:** `SUNSET` in the repo root (or `CR_SUNSET=1`) turns every decision into `DRAFT` and the
  digest into a "this course is now hand-maintained" notice. Publishing off means the course stands
  still — which is a legitimate end state.
- The bot's credentials can be revoked without touching the course: the artifact is plain markdown
  in git, readable forever.

---

## 9. The unattended runner (`app/run_live.py`)

| Mode | Command | What it touches |
|---|---|---|
| Preflight | `--preflight [--probe]` | nothing; writes `app/out/live/preflight.json`, prints names + fingerprints |
| One cycle, no writes | `--once --dry-run` | reads/writes outside `course/**`; artifacts are real, the course is untouched |
| One cycle, live | `--once [--via-n8n]` | full loop; `--via-n8n` lets the canvas decide (parity-policed) |
| Watch | `--watch` | the loop above on cadence until Ctrl-C |
| Learn only | `--learn` | telemetry → cohort gates → revert/stuck decisions |
| Digest only | `--digest-only` | re-renders the digest from existing receipts |
| Rehearse a failure | `--inject-failure` (with `--once`) | one failed write, recorded once, digest line, chain intact |
| Sandbox | `--root DIR` | rebases every path to `DIR` (needs `course/` + `app/out/`); `--seed-baseline` initialises a fresh root |

Exit codes are the contract: `0` clean · `1` cycle failed · `2` preflight blocked · `3` refused
(authority, consent, freeze) · `4` human override refused.

**Cadence, in one table.** Scan `CR_LIVE_SCAN_MINUTES` (default 60) · learn every 15 min · digest
07:30 · digests and learner cards obey the caps in §2. `CR_COMMIT=1` commits artifacts on
`CR_BOT_BRANCH` (default `bot/courserefresh`); the engine refuses to commit on any other branch, so it
can never rewrite `main`.

## 10. Canvas parity, in operation

- At least one watched cycle a day should run with `--via-n8n`, so the receipts show a canvas
  execution id (`canvas.execution_id`) — that is the evidence that n8n *decided*, not just stored.
- `canvas.ok: false` means the canvas was unreachable and the oracle decided; the run log says which
  reason, and the digest prints `canvas_degraded`. That is a degradation, not a failure — but if it
  happens twice in a row, treat it as Sev-2 (§6).
- `canvas.mismatch: true` is a **stop-and-look** event: the cycle wrote nothing, materiality is
  `ambiguous`, and the two decisions are both on the receipt. Diff `policy_node.js` against
  `skin/policy.py` (`node app/tests/test_gate_parity.py` should be green first).

## 11. Learner telemetry intake, in operation

| Concern | Behaviour |
|---|---|
| Consent | checked *before* storage; a payload without consent gets `403 consent_missing` and writes nothing |
| Identity | `learner:<8 hex>` only; anything else is refused (`handle_not_hashed`) — no names, no addresses, ever |
| Token | set `CR_TELEMETRY_TOKEN` for a public demo; unset for a closed one (localhost rehearsals) |
| Small cohorts | below `cohort_min` the gate prints `unmeasured` with `cohort_below_minimum (n<k)`; no number is invented |
| Storage | one JSONL row per event batch at `app/out/state/telemetry.jsonl`; it is the only place learner signals live |

## 12. Evidence refresh (do this before recording anything)

```bash
python3 app/tools/reset_course.py                       # restore the frozen baseline (course + quizzes)
sh app/check.sh                                         # 13 stages, must be ALL GREEN
python3 app/run_live.py --root app/out/e8 --seed-baseline
python3 app/run_live.py --root app/out/e8 --dry-run --once
python3 app/tools/freeze_evidence.py --out app/out/evidence/<run_id>
python3 app/tools/collect_live.py            # the shareable bundle: redacted, counts-only telemetry
```

`collect_live.py` exits `3` if a secret-shaped string survived its redaction; nothing leaves the
machine on that exit code. Treat a `3` as Sev-2 (§6).

Rules learned the hard way: any edit to a lesson invalidates the frozen hero (hash mismatch), any edit
to `app/n8n/policy_node.js` invalidates the exports (`make_n8n_exports.py`), and any edit to the
engine invalidates the rehearsal hashes in `EVIDENCE.md` §4. Freeze *after* the last edit, never
before.
