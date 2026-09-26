# BUILD.md — the build constitution (read this first, then tasks.md)
`v0.1 (draft) · Audience: the autonomous build agent · Depends on: constitution.md, tasks.md`

You are building Courserefresh. This file is the order of work, the gates, the forbidden moves, and
the definition of done. If a task and this file disagree, this file wins; if this file and the
constitution disagree, the constitution wins.

---

## §0 — The Core-First Warden (veto)

One agent on the build team holds the **Core-First Warden** role. The Warden's only job is to say
*no* when the loop is not yet real:

- **Hard veto on any M2+ work until M0's gate (T09) is signed.**
- Veto on any publish path without a `revert_gate`; any decision without a receipt; any "we'll add
  the chain later"; any UI work before `--selftest` is green.
- Veto is written in `AMENDMENTS.md` (`W-xx`) with the artifact that must exist to lift it.
- The Warden may not veto the honesty rules (they are law), only premature scope.

## §1 — The order of work (not negotiable)

```
M0 walking skeleton → M0 GATE (T09) → M1 live engine → M1 GATE (T17) → M2 learn+measure → M2 GATE (T23) → M3 demo/handoff
```

Rules that follow from the order:

1. **The loop first.** No console styling, no eval table, no Notion mirror, no video editing until a
   change has actually been published and actually been reverted by the machine.
2. **One commit per decision** (in the product) and **one task per commit** (in the build). A commit
   message names the task id and, for product commits, the receipt id.
3. **Fixtures before windows.** Every path (publish, refuse, revert, dispatch, degrade) is executable
   offline against fixtures before it runs live. A live-only path is an untested path.
4. **Never widen at the end.** If the demo needs something the spec does not contain, amend the spec
   first — or cut the beat. The last hour is for rehearsal, not architecture.

## §2 — Definition of done (any task)

A task is done when all five are true:

1. The acceptance criterion it serves passes.
2. The command that proves it appears in `TRACEABILITY.md` and has been run — output pasted in
   `EVIDENCE.md` (or its artifact path recorded).
3. A receipt or log line exists for the behaviour (nothing is "done" in prose).
4. The change is reflected in the spec if it altered behaviour (spec → amendment row → code).
5. `sh app/check.sh` is green *after* the change.

## §3 — Forbidden moves (each one has burned this lineage before)

| Forbidden | Why | Instead |
|---|---|---|
| Editing a receipt | The audit trail is the product | Append a new receipt with `actor: human:<name>` |
| Publishing without a gate | No undo ⇒ no autonomy (Art. XI) | Refuse the publish; escalate |
| A threshold in prose or in a prompt | Numbers must be reviewable in one place | `skin/thresholds.json`, hashed into receipts |
| A model choosing the action | Parity dies; trust dies | Closed questions → POLICY node |
| Re-labelling gold to make a test pass | That is the eval lying (Art. VII.4) | New `gold_version` + amendment row |
| A number in the video without a receipt | Art. VI | Say `unmeasured`, or measure it |
| Silent fallback (caching, mock data, twin) | Judges punish it and it is dishonest | Label: `degraded`, `sim`, `offline-twin`, `SEEDED` |
| Deleting a task that failed | Failures are evidence | Mark `[~]` with the cause |
| Touching `main` from the bot | Least privilege (Art. XIV.4) | `bot/courserefresh`, human merges |
| Free-text reason codes | Closed set is what makes decisions measurable | `change_taxonomy.json` codes only |

## §4 — The working rhythm (what the agent does per iteration)

1. **TIME-NOW block** in `tasks.md`: update `D-label`, date, hero-run armed, freeze state.
2. Pick the **oldest unfinished task in the current milestone** (no skipping ahead; the Warden
   vetoes skips).
3. Read its AC(s) in `spec.md` and its command in `TRACEABILITY.md`.
4. Write the test or the fixture **first** where the path does not exist yet (yes, even here).
5. Implement; run `sh app/check.sh`; run the specific command; paste output into `EVIDENCE.md`.
6. Mark the task; if it degraded, say so in the task line and in `AMENDMENTS.md`.
7. If a decision was made that changes behaviour, write the amendment row **before** the code.

## §5 — Commands (memorise these six)

```sh
sh app/check.sh                                             # whole battery, must be green
python3 app/run_walking_skeleton.py --selftest              # the loop's own checks
python3 app/run_walking_skeleton.py --report                # the digest
python3 specs/courserefresh/skin/policy.py --explain cr-inject-01   # why one row decided what it did
node app/tests/test_gate_parity.py                          # the two runtimes agree
python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl
```

## §6 — When to stop and ask a human

- A publish would touch an assessment or a learner record (PA3) — stop, escalate, never override.
- A source pair turns out not to be independent (same publisher) — stop attributing corroboration;
  mark the row.
- The kill switch has fired twice in one day — stop the overnight run, write the incident in
  `OPERATIONS.md` §6.
- A claim cannot be measured and the pitch script depends on it — stop and cut the line, not the
  measurement.

## §7 — Hand-off (what the human takes at D2 15:00)

A frozen evidence folder (`app/out/evidence/`), a digest, a run log, receipts, the diff, the card,
the gate state, the eval report, and this package. The human's job is the camera and the Q&A — not
re-deriving numbers. If the human has to compute something on stage, the build failed a task.
