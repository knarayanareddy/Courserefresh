# shared/harness.md — the runtime contract
`v0.1 (draft) · Depends on: constitution.md Art. II, III, VIII, IX, XIII, XIV`

This file is what every other file assumes about *how the machine runs*. It names the phases, the
knobs, the budgets, the latency doctrine, and the degraded modes. The product spec may narrow these;
it may not widen them (Art. XVI.1).

---

## 1. The six phases (one loop)

| Phase | Owner | Input | Output | Failure behaviour |
|---|---|---|---|---|
| **Notice** | Apify actor → `wf-cr-0-scan` | Scheduled actor runs + RSS/API fallbacks | `SourceSnapshot[]` + `ChangeEvent[]` (deduped) | fetch fails → retry once; still failing → `Snapshot(unreachable)` and the event is `unverifiable`, never silent |
| **Verify** | `wf-cr-1-triage` | Snapshots + event | `Claim[]` (quote-anchored) + `source_agreement`, `sources_verified` | a claim with no resolvable quote span is dropped; if none survive → `ESCALATE(no_verifiable_claim)` |
| **Decide** | `wf-cr-1-triage` POLICY node (deterministic) | Claims + state | `Decision{action, reason_codes[], authority}` | unknown/malformed/out-of-range input → `ESCALATE(unknown_state)` (fail closed) |
| **Act** | `wf-cr-2-act` | Decision + artifact plan | versioned lesson + quiz + diff + commit + card | write fails → receipt `publish_failed`, retry once, then `ESCALATE(write_failed)`; no partial publishes |
| **Learn** | `wf-cr-3-learn` (cron) | Consented telemetry + gates | revert decisions, stuck-learner dispatches, gate states | telemetry missing → `unmeasured` gate, no revert claim (Art. XI.4) |
| **Report** | `wf-cr-4-digest` (cron 07:30) | Receipts (last run window) | digest (refusals first) + console | render fails → digest shows `DIGEST FAILED` with the exception, exit non-zero; never a silent empty digest |

An iteration is one scan cycle: **the same scan may publish at most once**; the loop never sleeps
inside a cycle.

## 2. Model knobs (two, never one)

| Knob | Default | Used for | Rules |
|---|---|---|---|
| `OBSERVE_MODEL` | small, fast, cheap | Claim extraction, topic matching, tag normalisation | May hallucinate; output is always re-anchored to a quote span or dropped |
| `JUDGE_MODEL` | strongest available, pinned version | The closed-question call (`Choice` / `Noul`) | Temperature 0; strict JSON; the model never sees the policy thresholds or the expected action |
| `COMPARATOR_MODEL` | a named proprietary model + date | Eval column (a) only; never in the live loop | Named in `RECEIPTS.md` when the run happens; its prompt is frozen in `shared/eval.md` |

The judge is **not** shown the rulebook: it answers questions about the world, not about what the
system should do. That separation is what makes the parity test meaningful.

## 3. The policy node

3.1 Input: a single JSON object (see `data-model.md` §5). Output: exactly one line of JSON:
`{"action": …, "reason_codes": […], "authority": "PA0|PA1|PA2|PA3", "notes": "…"}`.
3.2 Rule order is normative and machine-checked: **safety** → **evidence** → **relevance** → **authority** → **integrity** → **budget** → default **ESCALATE(unknown_state)**.
authority → integrity floor → budget → default `ESCALATE(unknown_state)`**.
3.3 First matching rule wins; every rule that fires appends its reason code(s) to the receipt.
3.4 No clocks, no randomness, no network, no environment reads inside the node. Time and state are
passed in.
3.5 `notes` may explain; it may not introduce a reason code outside `change_taxonomy.json`.

## 4. Budgets (enforced before spending)

| Budget | Cap | On exhaustion |
|---|---|---|
| Apify units | `budgets.apify_units_per_day` (thresholds) | Stop scanning; digest says `budget_hold` |
| Model tokens | `budgets.tokens_per_change`, `budgets.tokens_per_day` | `ESCALATE(over_budget)`; no publish that cycle |
| Publishes | `budgets.publishes_per_day` | `ESCALATE(over_budget)` |
| Notifications | `budgets.notify_per_learner_day` = 1, `…_week` = 3 | Queue to the digest; never exceed |
| Digest size | `budgets.digest_bytes` = 4096 | Digest trims the *oldest* sections, never the refusals; prints `trimmed: n lines` |

Costs are recorded per receipt as `cost{tokens, apify_units, eur}`; `eur` is `unmeasured` until the
prices in `WIRING.md` §5 are captured.

## 5. Latency doctrine (honesty rule)

The honest unit of this system is the **scheduled scan cycle**, not a websocket. What is measured
and claimed:

- **cadence**: the configured interval, and its measured jitter across ≥5 runs (`RECEIPTS.md`);
- **decision latency**: from `event.ingested_at` to `receipt.ts` — p50 and p95 across the run;
- **change latency**: from `snapshot.captured_at` of the earliest source to `publish.ts` — this is
  the number in the video, whatever it is;
- **nothing else**. "Real-time", "instant", and "live" are banned words for this loop. The lesson
  states the cadence it uses, honestly, for its own readers.

## 6. State and idempotency

6.1 `event_id = sha256(source_id + normalized_claim_text)[..16]`; a seen-ledger (`state/seen.json`)
makes scanning idempotent. An event already decided is not re-decided, but a **new snapshot for the
same event** re-opens verification with the new evidence attached.
6.2 Writes are idempotent by construction: a publish is keyed by `(lesson_id, from_version)`; a
retry that finds the target version already written emits `noop_already_applied` instead of a
second version.
6.3 Every run has a `run_id`; every receipt and artifact names it. A digest only ever renders the
current run window (no reprinting yesterday's refusals as today's).

## 7. Mods / degraded modes (declared, printed, never silent)

| Mode | Trigger | What still works | What the surfaces say |
|---|---|---|---|
| `live` | n8n + Apify reachable | Everything | — |
| `degraded-sources` | An actor fails but a cache exists | Verify + decide on cached snapshots, capped at `thresholds.stale_hours` | `source_stale: true` on receipts; digest banner |
| `observe-only` | Sources stale beyond cap, or budget `budget_hold` | Notice, verify, draft | `PA0` stamped on every decision |
| `sim` | Fixtures, offline, no model calls | The whole loop, on fixtures | `mode: sim` on receipts and the digest header |
| `paused` | Kill switch | Reads only | `freeze_active` on every receipt; digest says PAUSED |
| `offline-twin` | n8n/Apify unreachable during the demo | The same rules in `app/run_walking_skeleton.py`, parity-tested | Banner: `OFFLINE TWIN — same policy node (parity-tested)` |

## 8. Sources and cadence (subject-dependent defaults)

Default cadence: `scan.every_min = 60` (configurable, printed), `jitter_max_s = 300`;
the pre-registration may tighten it. Sources are declared per subject in
`courserefresh/kickoff/SOURCE-PLAN.md`: each with `source_id`, `publisher`, `independence_group`,
`apify_actor`, `fallback_url`, `topic_tags`. Two sources are independent only if their
`independence_group`s differ.

## 9. The run's shape (what "a run" means in receipts)

```
run_id: cr-<YYYYMMDD-HHmm>-<seq>
  00. preflight   — config loaded, thresholds hashed, allowlist loaded, budget counters read
  01. notice      — actor runs OR cached snapshots; snapshots content-hashed and stored verbatim
  02. verify      — claims extracted and anchored; independence groups resolved
  03. decide      — one policy call per event; receipts written
  04. act         — ordered: reverts before publishes (undoing is never blocked by new work)
  05. learn       — gates evaluated; dispatches queued (rate-limited); nothing sent without consent
  06. report      — digest + console; chain verified; `exit 0` only if every phase reported
```

## 10. Exit codes and the one command

`0` ok · `1` verification failed (chain, digest, or a built-in check) · `2` build-breaking invariant
violated (hostile→publish ≠ 0, unsupported→publish ≠ 0) · `3` usage/config error (unknown flag,
missing file, unallowlisted host) · `4` refused (a human override attempted against a PA3 decision).

```sh
sh app/check.sh          # the battery; any non-zero exit is a stop-the-line
python3 app/run_walking_skeleton.py --report     # the digest, from receipts
```

## 11. Where this contract is tested

| Contract | Test |
|---|---|
| Phase order & receipt fields | `app/tests/test_walking_skeleton.py`, `--selftest` |
| Rule order & closed sets | `app/tests/test_contracts.py` (parses this file, `data-model.md`, `skin/*.json`) |
| Parity of the two runtimes | `node app/tests/test_gate_parity.py` |
| Budget caps, kill switch, containment | `--selftest` checks + `app/tests/test_threat_model.py` |
| Sim vs live labelling | `test_claims.py` + digest header check |
