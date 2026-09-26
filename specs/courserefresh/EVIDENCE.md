# Courserefresh — evidence protocol (how a claim becomes a fact)
`v0.4 · Last amended D-0 · Amends: AMENDMENTS.md v1.2 · Depends on: shared/eval.md; RECEIPTS.md; constitution.md Art. VI, IX`

This file is the bridge between "it ran" and "we can show it". The rule: **evidence is frozen
before it is narrated.** Figures, video, and pitch are cut from the artifacts below, never from
memory.

---

## 1. Run-log schema (`app/out/run_log.jsonl`, one line per run)

```jsonc
{ "run_id": "cr-20260926-1421-001", "mode": "sim", "started_at": "…", "ended_at": "…",
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
| Run log | `app/out/run_log.jsonl` | `sha256` (`85e5428d…`) |
| Receipts (chained) | `app/out/receipts.jsonl` | `sha256` (`69606627…`) + `verify_chain()` output |
| Digest | `app/out/digest.md` | `sha256` (`10976626…`), 1323 bytes |
| Changed lesson + diff | `course/**/v<n>.md`, `diffs/v<n>.diff` | copied into the freeze; `git hash-object` once committed |
| Learner notifications (staged or sent) | `app/out/notifications.jsonl` | `sha256` (`685a88bd…`) |
| Micro-lesson | `app/out/micro-lessons/<id>.md` | `sha256` (`f2de7227…`) |
| Eval report | `app/out/eval/<gold_version>/report.txt` | `sha256` (`d816f4d4…`) |
| Snapshot raws | `app/out/snapshots/<snap_id>.*` | live mode only; matches receipt `snapshot_hash` |
| Apify run ids | console links recorded in `WIRING.md` §6 | live mode only |
| Console screenshots | `app/out/ui/<run_id>/*.png` | live mode only |

`app/tools/freeze_evidence.py` copies the set to `app/out/evidence/<run_id>/`, writes
`MANIFEST.sha256`, and prints the manifest for pasting into §4. `--out DIR` freezes a rehearsal run
in its own tree (the witnessed-failure run is frozen that way). The current freeze is
`app/out/evidence/cr-20260926-1421-001/` (19 files, the hero) and
`app/out/evidence/cr-20260926-1441-130/` (14 files, the round-3 live-engine rehearsal, E9).

## 3. Register rows (filled as they are measured)

| Row | Claim | Status | Artifact | Command | Date |
|---|---|---|---|---|---|
| E1 | gold eval run (n≥40, hostile/unsupported counters) | **measured** — gold-v0.3, n=59, action match 1.000 | `app/out/eval/gold-v0.3/report.txt` | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` | D-0 |
| E2 | loop selftest (chain, budget, freeze, refusals) | **measured** — 14/14 checks | `app/out/selftest/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` | D-0 |
| E3 | full battery | **measured** — **179 PASS across 13 stages**, exit 0, `ALL GREEN` (round 3 added the live-path and handoff stages) | `app/out/evidence/battery.txt` | `sh app/check.sh` | D-0 |
| E4 | hero run (sources → publish → notify staging) | **measured (sim)** — 2 publishes, 4 refusals, 1 revert, 1 dispatch, 9 receipts, 1 quiz item regenerated | `app/out/evidence/cr-20260926-1421-001/` | `python3 app/run_walking_skeleton.py && python3 app/tools/freeze_evidence.py` | D-0 |
| E5 | revert on a satisfied gate | **measured (sim cohort, labelled)** — `revert_gate_satisfied`, `cohort_source: fixture (simulated)` | receipt `rcpt-…-008` + `course/agent-ops/lesson-04-tool-permissions/v5.md` | as E4 | D-0 |
| E6 | stuck-learner dispatch (consent + caps) | **measured (fixture cohort, labelled)** — `stuck_signals_met` → `ml-permissions-mode-k-01.md` | `app/out/micro-lessons/` | as E4 | D-0 |
| E7 | one witnessed failure handled | **measured (rehearsal)** — `--chaos write-fail` → exactly one `write_failed` refusal, chain intact, digest + console both say it (N28) | `app/out/e7/app/out/evidence/cr-20260926-1420-924/` | `python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail` | D-0 |
| E7b | the same failure, unwitnessed and live | `unmeasured` — the live half is unwired (K-05, K-07) | — | live run | — |
| E8 | hostile + unsupported → publish = 0 | **measured** — 0 and 0 on 57 rows | eval report lines 8–9 | as E1 | D-0 |
| E9 | **live-engine cycle (round 3 build)** | **measured (sim)** — run `cr-20260926-1441-130`: 1 `PUBLISH` (lesson-03 v2→v3, quiz `q1` regenerated) + 1 `ESCALATE` (`insufficient_corroboration`, one voice), chain verified at end, 2 judge calls on recorded answers, `mode: sim` on every receipt | `app/out/evidence/cr-20260926-1441-130/` (14 files) | `python3 app/run_live.py --root app/out/e8 --seed-baseline && python3 app/run_live.py --root app/out/e8 --dry-run --once` | D-0 |
| E10 | preflight with no credentials | **measured** — `mode: sim`; `apify`/`judge` named as missing, `n8n` named, four claims blocked; no secret value printed | `app/out/evidence/cr-20260926-1441-130/preflight-nokeys.txt` | `python3 app/run_live.py --preflight [--probe]` | D-0 |
| E12 | handoff collector (redaction, secret scan, manifest, no-telemetry, self-verified chain) | **measured** — 15/15 checks, including a planted token that must be caught and a manifest that re-hashes | `app/tests/test_handoff.py` (stage 13/13) | `python3 app/tests/test_handoff.py` | D-0 |
| E11 | live-path battery with injected transports | **measured** — 47/47 checks (config·apify·judge·n8n·telemetry·notify·console·end-to-end), no socket, no key | `app/tests/test_live_modules.py` (stage 6/12) | `python3 app/tests/test_live_modules.py` | D-0 |

## 4. The frozen hero-run record (paste-once, never edited)

```
RUN      cr-20260926-1421-001      MODE sim (fixtures; no network, no model calls, no mail)
WINDOW   2026.09.26T14:21:39Z (one in-process run of the offline twin)
HASHES   receipts 69606627…  run_log 85e5428d…  digest 10976626…  (full list: MANIFEST.sha256)
WHAT     sources: 11  deltas: 6  published: 2  refused: 4  reverted: 1  dispatched: 1
         notifications staged (not sent): 7   consent-blocked: 1   digest: 1323 bytes
PROOF    app/out/evidence/cr-20260926-1421-001/MANIFEST.sha256
         app/out/evidence/cr-20260926-1421-001/receipts.jsonl
         app/out/evidence/cr-20260926-1421-001/digest.md
         app/out/evidence/cr-20260926-1421-001/digest.html
         app/out/evidence/cr-20260926-1421-001/eval/gold-v0.3/report.txt
         course/agent-ops/lesson-04-tool-permissions/{v4,v5}.md + diffs/
         course/agent-ops/lesson-03-apify-inputs/{v1,v2}.md + diffs/v2.diff
LABELS   mode: sim on every receipt and on the digest header
         revert receipt: cohort_source "fixture (simulated)"
         no seeded artifact in this run (the rehearsal needs --seed-demo and says SEEDED when used)
```

## 4b. The round-3 rehearsal record (the live engine, no credentials)

```
RUN      cr-20260926-1441-130      MODE sim (recorded datasets + recorded judge answers; dry-run)
WHAT     one cycle of app/run_live.py: snapshots from the Apify fixtures → 2 claims clustered
         → 1 PUBLISH (lesson-03-apify-inputs v2 → v3, quiz q1 regenerated, diff written)
         → 1 ESCALATE (insufficient_corroboration: two publishers, one voice)
         → digest + console page + 2 judge calls (recorded) + 6 Apify units accounted
HASHES   receipts 0bd5f131…  run_log ad215f20…  digest 92aab48e…  html f52fbc78…
PROOF    app/out/evidence/cr-20260926-1441-130/MANIFEST.sha256
LABELS   mode: sim on every receipt, on the digest header, on the console header
         the judge provider is `mock` and the fixture is recorded — the digest says so
         preflight-nokeys.txt next to the run: what is wired, what is not, by key name only
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
