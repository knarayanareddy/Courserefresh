# Courserefresh — evidence protocol (how a claim becomes a fact)
`v0.3 · Last amended D-0 · Amends: AMENDMENTS.md v1.2 · Depends on: shared/eval.md; RECEIPTS.md; constitution.md Art. VI, IX`

This file is the bridge between "it ran" and "we can show it". The rule: **evidence is frozen
before it is narrated.** Figures, video, and pitch are cut from the artifacts below, never from
memory.

---

## 1. Run-log schema (`app/out/run_log.jsonl`, one line per run)

```jsonc
{ "run_id": "cr-20260926-1411-450", "mode": "sim", "started_at": "…", "ended_at": "…",
  "label": "", "sources_scanned": 11, "deltas": 6,
  "decisions": {"PUBLISH": 2, "ESCALATE": 4, "NO_CHANGE": 1, "DISPATCH": 1, "REVERT": 1},
  "publishes_used": 2, "receipts": 9, "chain_verified_at_end": true, "chain_rows": 9,
  "freeze_at_end": false }
```

`deltas` counts change events that produced a decision; `sources_scanned` counts the source rows the
run read (fixtures here; Apify dataset rows in the live mode). `receipts` must equal the number of
decisions — coverage is asserted by `--selftest`.

## 2. The evidence set (what gets frozen, and its hash)

| Artifact | Path | Hash how |
|---|---|---|
| Run log | `app/out/run_log.jsonl` | `sha256` (`ed839f62…`) |
| Receipts (chained) | `app/out/receipts.jsonl` | `sha256` (`120badec…`) + `verify_chain()` output |
| Digest | `app/out/digest.md` | `sha256` (`9526096f…`), 1323 bytes |
| Changed lesson + diff | `course/**/v<n>.md`, `diffs/v<n>.diff` | copied into the freeze; `git hash-object` once committed |
| Learner notifications (staged or sent) | `app/out/notifications.jsonl` | `sha256` (`3823f61d…`) |
| Micro-lesson | `app/out/micro-lessons/<id>.md` | `sha256` (`f2de7227…`) |
| Eval report | `app/out/eval/<gold_version>/report.txt` | `sha256` (`3253c387…`) |
| Snapshot raws | `app/out/snapshots/<snap_id>.*` | live mode only; matches receipt `snapshot_hash` |
| Apify run ids | console links recorded in `WIRING.md` §6 | live mode only |
| Console screenshots | `app/out/ui/<run_id>/*.png` | live mode only |

`app/tools/freeze_evidence.py` copies the set to `app/out/evidence/<run_id>/`, writes
`MANIFEST.sha256`, and prints the manifest for pasting into §4. The current freeze is
`app/out/evidence/cr-20260926-1411-450/` (18 files).

## 3. Register rows (filled as they are measured)

| Row | Claim | Status | Artifact | Command | Date |
|---|---|---|---|---|---|
| E1 | gold eval run (n≥40, hostile/unsupported counters) | **measured** — gold-v0.2, n=57, action match 1.000 | `app/out/eval/gold-v0.2/report.txt` | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` | D-0 |
| E2 | loop selftest (chain, budget, freeze, refusals) | **measured** — 13/13 checks | `app/out/selftest/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` | D-0 |
| E3 | full battery | **measured** — 92 PASS, exit 0, `ALL GREEN` | `app/out/evidence/battery.txt` | `sh app/check.sh` | D-0 |
| E4 | hero run (sources → publish → notify staging) | **measured (sim)** — 2 publishes, 4 refusals, 1 revert, 1 dispatch, 9 receipts | `app/out/evidence/cr-20260926-1411-450/` | `python3 app/run_walking_skeleton.py && python3 app/tools/freeze_evidence.py` | D-0 |
| E5 | revert on a satisfied gate | **measured (sim cohort, labelled)** — `revert_gate_satisfied`, `cohort_source: fixture (simulated)` | receipt `rcpt-…-008` + `course/agent-ops/lesson-04-tool-permissions/v5.md` | as E4 | D-0 |
| E6 | stuck-learner dispatch (consent + caps) | **measured (fixture cohort, labelled)** — `stuck_signals_met` → `ml-permissions-mode-k-01.md` | `app/out/micro-lessons/` | as E4 | D-0 |
| E7 | one witnessed failure handled live | `unmeasured` — the degraded paths exist (`over_budget` escalation, `write_failed`/`source_stale` codes) but no live incident has been witnessed | — | live run | — |
| E8 | hostile + unsupported → publish = 0 | **measured** — 0 and 0 on 57 rows | eval report lines 8–9 | as E1 | D-0 |

## 4. The frozen hero-run record (paste-once, never edited)

```
RUN      cr-20260926-1411-450      MODE sim (fixtures; no network, no model calls, no mail)
WINDOW   2026.09.26T14:11:25Z (one in-process run of the offline twin)
HASHES   receipts 120badec…  run_log ed839f62…  digest 9526096f…  (full list: MANIFEST.sha256)
WHAT     sources: 11  deltas: 6  published: 2  refused: 4  reverted: 1  dispatched: 1
         notifications staged (not sent): 7   consent-blocked: 1   digest: 1323 bytes
PROOF    app/out/evidence/cr-20260926-1411-450/MANIFEST.sha256
         app/out/evidence/cr-20260926-1411-450/receipts.jsonl
         app/out/evidence/cr-20260926-1411-450/digest.md
         app/out/evidence/cr-20260926-1411-450/eval/gold-v0.2/report.txt
         course/agent-ops/lesson-04-tool-permissions/{v4,v5}.md + diffs/
         course/agent-ops/lesson-03-apify-inputs/{v1,v2}.md + diffs/v2.diff
LABELS   mode: sim on every receipt and on the digest header
         revert receipt: cohort_source "fixture (simulated)"
         no seeded artifact in this run (the rehearsal needs --seed-demo and says SEEDED when used)
```

## 5. Replay ladder (what to show when something is down)

1. **Live** — the running system (preferred; not yet wired — see reviews/04 §4).
2. **Replay** — `python3 app/run_walking_skeleton.py --replay <run_id>` re-executes the recorded
   inputs in the offline twin; on screen: `REPLAY — run <run_id>`.
3. **Frozen artifacts** — the digest, receipts, and diff from the hero run, shown as images; on
   screen: `RECORDED <date> · mode: sim`.
4. **Labelled rehearsal** — `--seed-demo` adds the seeded event; on screen: `SEEDED SOURCE — not a
   vendor release`.

Every rung except (1) carries its label on screen, in the same typography as the rest of the
overlay (`design/MASTER.md` §2). A fallback that is not labelled is a lie (Art. VI.3).
