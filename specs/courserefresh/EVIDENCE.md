# Courserefresh — evidence protocol (how a claim becomes a fact)
`v0.4 · Last amended D-0 · Amends: AMENDMENTS.md v1.2 · Depends on: shared/eval.md; RECEIPTS.md; constitution.md Art. VI, IX`

This file is the bridge between "it ran" and "we can show it". The rule: **evidence is frozen
before it is narrated.** Figures, video, and pitch are cut from the artifacts below, never from
memory.

---

## 1. Run-log schema (`app/out/run_log.jsonl`, one line per run)

```jsonc
{ "run_id": "cr-20260926-1726-793", "mode": "sim", "started_at": "…", "ended_at": "…",
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
in its own tree (the witnessed-failure run is frozen that way). Two bundles are **shipped** under `specs/evidence/` — `app/out/` is gitignored, so a bundle that is
not copied there is not in the repository and its hashes cannot be checked by anyone:

| Bundle | Run | What it is | Files |
|---|---|---|---|
| `specs/evidence/cr-20260926-1726-793/` | offline twin (E4/E6) | the hero cycle: sources → 2 publishes → refusals → revert → dispatch, plus the gold eval report and the dispatched micro-lesson | 19 |
| `specs/evidence/cr-20260926-1726-054/` | live engine, dry (E8–E10) | `run_live.py --dry-run --once`: 4 sources scanned, 2 deltas, 1 publish, 1 refusal in the withheld queue, and the preflight transcript that names what the missing keys block | 20 |

The battery's audit stage re-hashes both on every run (`app/tools/audit_claims.py`), and `RECEIPTS.md`
§6 carries their digests. `app/out/evidence/<run_id>/` is only the local spare copy a re-run leaves
behind.

## 3. Register rows (filled as they are measured)

| Row | Claim | Status | Artifact | Command | Date |
|---|---|---|---|---|---|
| E1 | gold eval run (n≥40, hostile/unsupported counters) | **measured** — gold-v0.3, n=59, action match 1.000 | `app/out/eval/gold-v0.3/report.txt` | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` | D-0 |
| E2 | loop selftest (chain, budget, freeze, refusals) | **measured** — 14/14 checks | `app/out/selftest/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` | D-0 |
| E3 | full battery | **measured** — **288 PASS: 256 in 13 measured stages plus the 32-check claims audit**, exit 0, `ALL GREEN` (round 3 added the live-path and handoff stages; the audit re-derives the register) | `app/out/evidence/battery.log` | `sh app/check.sh` | D-0 |
| E4 | hero run (sources → publish → notify staging) | **measured (sim)** — 2 publishes, 4 refusals, 1 revert, 1 dispatch, 9 receipts, 1 quiz item regenerated | `specs/evidence/cr-20260926-1726-793/` (shipped, 19 files, hashed) | `python3 app/run_walking_skeleton.py && python3 app/tools/freeze_evidence.py --ship` | D-0 |
| E5 | revert on a satisfied gate | **measured (sim cohort, labelled)** — `revert_gate_satisfied`, `cohort_source: fixture (simulated)` | receipt `rcpt-…-008` + `course/agent-ops/lesson-04-tool-permissions/v5.md` | as E4 | D-0 |
| E6 | stuck-learner dispatch (consent + caps) | **measured (fixture cohort, labelled)** — `stuck_signals_met` → `ml-permissions-mode-k-01.md` | `app/out/micro-lessons/` | as E4 | D-0 |
| E7 | one witnessed failure handled | **measured (rehearsal)** — `--chaos write-fail` → exactly one `write_failed` refusal, chain intact, digest + console both say it (N28) | local re-run: `app/out/e7/app/out/evidence/<run_id>/` (a rehearsal is regenerated by the command on the right, not shipped) | `python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail` | D-0 |
| E7b | the same failure, unwitnessed and live | `unmeasured` — the live half is unwired (K-05, K-07) | — | live run | — |
| E8 | hostile + unsupported → publish = 0 | **measured** — 0 and 0 on 57 rows | eval report lines 8–9 | as E1 | D-0 |
| E9 | **live-engine cycle** | **measured (sim)** — run `cr-20260926-1726-054`: 4 sources scanned, 2 deltas, 1 `PUBLISH` (lesson-03 v2→v3, quiz `q1` regenerated) + 1 `ESCALATE` (`insufficient_corroboration`, one voice, kept in the withheld queue for an author), a discovery gap recorded (Tavily), chain verified at end, `mode: sim` on every receipt | `specs/evidence/cr-20260926-1726-054/` (shipped, 20 files, hashed) | `python3 app/run_live.py --root app/out/e8 --seed-baseline && python3 app/run_live.py --root app/out/e8 --dry-run --once && python3 app/tools/freeze_evidence.py --out app/out/e8/app/out --course app/out/e8/course --ship` | D-0 |
| E10 | preflight with no credentials | **measured** — `mode: sim`; `apify`/`judge` named as missing, `n8n` named, four claims blocked; no secret value printed | `specs/evidence/cr-20260926-1726-054/live/preflight.txt` (and `preflight.json`) | `python3 app/run_live.py --preflight [--probe]` | D-0 |
| E12 | handoff collector (redaction, secret scan, manifest, no-telemetry, self-verified chain) | **measured** — 15/15 checks, including a planted token that must be caught and a manifest that re-hashes | `app/tests/test_handoff.py` (stage 13/13) | `python3 app/tests/test_handoff.py` | D-0 |
| E11 | live-path battery with injected transports | **measured** — 47/47 checks (config·apify·judge·n8n·telemetry·notify·console·end-to-end), no socket, no key | `app/tests/test_live_modules.py` (stage 6/13) | `python3 app/tests/test_live_modules.py` | D-0 |

## 4. The frozen hero-run record (paste-once, never edited)

```
RUN      cr-20260926-1726-793      MODE sim (fixtures; no network, no model calls, no mail)
WINDOW   2026.09.26T16:20:48Z (one in-process run of the offline twin)
HASHES   receipts 5c020f93…  run_log b9585fe6…  digest ae1a08d6…  (full list: MANIFEST.sha256)
WHAT     sources: 11  deltas: 6  published: 2  refused: 4  reverted: 1  dispatched: 1
         notifications staged (not sent): 7   consent-blocked: 1   digest: 1705 bytes
         withheld for an author (approvable refusals): 2
PROOF    specs/evidence/cr-20260926-1726-793/MANIFEST.sha256
         specs/evidence/cr-20260926-1726-793/receipts.jsonl
         specs/evidence/cr-20260926-1726-793/digest.md
         specs/evidence/cr-20260926-1726-793/digest.html
         specs/evidence/cr-20260926-1726-793/eval/gold-v0.3/report.txt
         course/agent-ops/lesson-04-tool-permissions/{v3,v4,v5}.md + diffs/
         course/agent-ops/lesson-03-apify-inputs/{v1,v2,v3}.md + diffs/v2.diff,v3.diff
         micro-lessons/ml-permissions-mode-k-01.md
LABELS   mode: sim on every receipt and on the digest header
         revert receipt: cohort_source "fixture (simulated)"
         no seeded artifact in this run (the rehearsal needs --seed-demo and says SEEDED when used)
```

## 4b. The round-3 rehearsal record (the live engine, no credentials)

```
RUN      cr-20260926-1726-054      MODE sim (recorded datasets + recorded judge answers; dry-run)
WHAT     one cycle of app/run_live.py: 4 sources scanned from the Apify fixtures → 2 deltas
         → 1 PUBLISH (lesson-03-apify-inputs v2 → v3, quiz q1 regenerated, diff written)
         → 1 ESCALATE (insufficient_corroboration: one voice) → kept as a withheld delta
         → digest + console page + judge calls (recorded) + 6 Apify units accounted
         → 1 discovery gap (Tavily lead, recorded and not counted as a voice)
HASHES   receipts fe436241…  run_log 99dd9369…  digest d21728b3…  html c49a201f…
PROOF    specs/evidence/cr-20260926-1726-054/MANIFEST.sha256
LABELS   mode: sim on every receipt, on the digest header, on the console header
         the judge provider is `mock` and the fixture is recorded — the digest says so
         live/preflight.txt beside the receipts: what is wired, what is not, by key name only
         (4 claims blocked; `live needs: apify:APIFY_TOKEN, judge:CR_JUDGE_API_KEY`)
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
