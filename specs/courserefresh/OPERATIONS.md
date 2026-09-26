# Courserefresh — operations (runbook for a machine that acts alone)
`v0.1 (draft) · Depends on: harness.md §7, §10; constitution.md Art. XIV`

The author is not watching at 03:00. This file is what the system does instead of asking, and what
the human does when they wake up.

---

## 1. Start / stop / pause (the whole control surface)

| Action | How | Effect | Receipt |
|---|---|---|---|
| Start the loop | n8n schedules on; `POST /scan` once to warm | scans begin on cadence | run header |
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
