# Courserefresh — receipts register (every number, and where it came from)
`v0.3 · Last amended D-0 · Amends: AMENDMENTS.md v1.0 · Rule (Art. VI): a number with no row here may not appear in any other file or on screen`

Status vocabulary: **measured** (value + date + artifact + command) · **configuration** (a chosen
value, not a measurement — the word "measured" may not be used) · **n/a** (deliberately not
applicable, with the reason) · **unmeasured** (not yet known; printed as `unmeasured` everywhere,
including on screen).

The frozen evidence set for the run quoted below is `app/out/evidence/cr-20260926-1411-450/` with
its `MANIFEST.sha256`. Re-generate anything with the commands in the rows; nothing here is copied
from memory.

---

## 1. Decision-quality numbers (gold eval)

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N01 | hostile → publish (build-breaking) | `0` | **measured** (gold-v0.2) | `app/out/eval/gold-v0.2/report.txt` | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` |
| N02 | unsupported → publish (build-breaking) | `0` | **measured** (gold-v0.2) | same report | same |
| N03 | action match, ours (column c) | `1.000` (n=57) | **measured** (gold-v0.2) | same report | same |
| N04 | action match, vanilla no-policy (column b, scored) | `<x.xxx>` | **unmeasured** — column (b) runs live model calls; the offline report prints only the informational inclination count below | `app/out/eval/gold-v0.2/report.txt` | same |
| N04b | naive publish inclinations (informational proxy for b) | `34/57` | **measured** (gold-v0.2) | same report | same |
| N05 | proprietary one-shot (column a) | `n/a` — no key or spend approved (D-06) | **n/a** | `app/out/eval/a/` (empty) | frozen prompt runner (not run) |
| N06 | reason-code match | `1.000` (n=57) | **measured** (gold-v0.2) | same report | as N01 |
| N07 | over-escalation rate | `<x.xxx>` | **unmeasured** — needs a scored column (b) to define "over" | — | as N01 once (b) runs |
| N08 | `unknown_state` rate | `4/57 = 0.070` | **measured** (gold-v0.2) | same report (`unknown_state rows: 4`) | as N01 |
| N09 | p50 / p95 decision latency | `<ms>` | **unmeasured** — the offline twin is in-process; no timer harness yet | — | `python3 app/tools/metrics.py` (prints `null`) |
| N10 | cost per change (tokens · apify units · €) | `unmeasured (no vendor prices captured)` | **unmeasured** — `app/prices.json` is all nulls by design | receipts `cost.cost_state` | `python3 app/tools/metrics.py` |
| N11 | gold set size / version | `57` rows · `gold-v0.2` | **measured** | `specs/courserefresh/skin/gold.jsonl` | `python3 app/tests/test_gold_floor.py` |
| N11b | gold set hash | `sha256:7b511eb57a1013050d33fd22e3cb443bca349812b984951931da2cdc367fa4f0` | **measured** | `skin/gold.jsonl` | `sha256sum specs/courserefresh/skin/gold.jsonl` |

## 2. Loop / engine numbers

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N12 | scan cadence (configured) | `60 min` | **configuration** | `skin/thresholds.json` | `cat specs/courserefresh/skin/thresholds.json` |
| N13 | scan cadence (measured, ≥5 live runs) | `<min ± x>` | **unmeasured** — no live runs yet | run log | `python3 app/tools/metrics.py` |
| N14 | unattended window | `<h>` | **unmeasured** — the twin run is in-process; the live hero run is the test | run log | `python3 app/tools/metrics.py` |
| N15 | digest size | `1323 bytes` (cap 4096) | **measured** (run `cr-20260926-1411-450`) | `app/out/digest.md` | `wc -c app/out/digest.md` |
| N16 | receipt coverage | `100%` (9 receipts / 9 decisions) | **measured** | `app/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` |
| N17 | chain integrity | `true` (`ok (9 rows)`) | **measured** | `app/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` |
| N18 | Apify units per run / per day | `<n>` | **unmeasured** — no actor called yet | actor run history | Apify console export |
| N19 | publishes / notifications in the run | `2 publishes · 7 notifications staged (not sent, sim)` | **measured** (sim) | `app/out/notifications.jsonl` | `wc -l app/out/notifications.jsonl` |
| N19b | staged notifications dropped for missing consent | `1 learner` (`consent_missing`) | **measured** (sim) | receipt `cr-learner-consent-01` | `python3 app/tools/metrics.py` |

## 3. Learner numbers (small n, said out loud)

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N20 | cohort n for gate evaluation | `<n>` | **unmeasured** — the run's cohort is a labelled fixture (`cohort_source: fixture (simulated)`) | cohort window row | `python3 app/tools/metrics.py` |
| N21 | quiz delta post-change | `unmeasured` | **unmeasured** — no live cohort yet; the revert fixture carries `-0.04` and is labelled | fixture `09-revert.json` | `cat app/fixtures/events/09-revert.json` |
| N22 | time from stuck signal → dispatch | `<min>` | **unmeasured** — same run, one dispatch, no clock model | dispatch receipt | `python3 app/tools/metrics.py` |
| N23 | micro-lessons dispatched | `1` (`ml-permissions-mode-k-01.md`) | **measured** (sim) | `app/out/micro-lessons/` | `ls app/out/micro-lessons/` |
| N24 | consented learners / total in fixtures | `7 / 8` (one declined-by-design fixture) | **measured** (fixtures) | `kickoff/LEARNER-PLAN.md` §1 | `python3 app/tools/metrics.py` |

## 4. Configuration (chosen, not measured — the word "measured" is banned here)

| Item | Value | File |
|---|---|---|
| Thresholds (authority, evidence, learner, budgets) | see file | `skin/thresholds.json` |
| Closed sets (materiality, actions, reason codes, questions) | see file | `skin/change_taxonomy.json` |
| Budgets | Apify 25 units/day · tokens 60 k/change & 500 k/day · 6 publishes/day · 1 notify/learner/day & 3/week · digest 4 KB | `skin/thresholds.json` |
| Revert gate template | `n_min=5 · window_h=48 · metric=quiz_delta · condition≤0` | `skin/thresholds.json` |
| Authority ladder | PA0–PA3; PA1 = publish without notify, PA2 = publish + cohort card, PA3 = human only; promotion = 3 consecutive accepted publishes, 0 rollbacks | `constitution.md` Art. II |
| Subject | *Agent Ops* (n8n + Apify agents in production), six lessons | `spec.md` §1 |
| Comparator (a) | name + version + date recorded **when it runs**; today `n/a` (D-06) | `shared/eval.md` §1 |
| Mode of the quoted run | `sim` (fixtures; no network, no model calls, no mail) | `app/out/receipts.jsonl` |

## 5. What the video may say (and nothing else)

1. "Two changes shipped and one was reverted by the machine — run `cr-20260926-1411-450`." (N19, N17)
2. "Four refusals, with reasons: hostile, single source, contradiction, over budget." (digest §1)
3. "hostile → publish is zero on a 57-row frozen set; so is unsupported → publish." (N01, N02)
4. "The digest is 1.3 KB, refusals first." (N15)
5. "Cost, latency, cadence, the live cohort: `unmeasured` until the live run exists — here is the
   row that says so." (N07, N09, N10, N13, N14, N20–N22)

Any other number — including in the pitch, the video, or a judge's question — is answered by the
matching register row or by the words `unmeasured` (Art. VI, TM18).
