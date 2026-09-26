# Courserefresh — receipts register (every number, and where it came from)
`v0.4 · Last amended D-0 · Amends: AMENDMENTS.md v1.0 · Rule (Art. VI): a number with no row here may not appear in any other file or on screen`

Status vocabulary: **measured** (value + date + artifact + command) · **configuration** (a chosen
value, not a measurement — the word "measured" may not be used) · **n/a** (deliberately not
applicable, with the reason) · **unmeasured** (not yet known; printed as `unmeasured` everywhere,
including on screen).

The frozen evidence set for the run quoted below is shipped in `specs/evidence/` with its
`MANIFEST.sha256` (the audit stage re-hashes it; `app/out/evidence/<run_id>/` is cast aside because
`app/out/` is gitignored). Re-generate anything with the commands in the rows; nothing here is copied
from memory.

---

## 1. Decision-quality numbers (gold eval)

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N01 | hostile → publish (build-breaking) | `0` | **measured** (gold-v0.3) | `app/out/eval/gold-v0.3/report.txt` | `python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl` |
| N02 | unsupported → publish (build-breaking) | `0` | **measured** (gold-v0.3) | same report | same |
| N03 | action match, ours (column c) | `1.000` (n=59) | **measured** (gold-v0.3) | same report | same |
| N04 | action match, vanilla no-policy (column b, scored) | `<x.xxx>` | **unmeasured** — column (b) runs live model calls; the offline report prints only the informational inclination count below | `app/out/eval/gold-v0.3/report.txt` | same |
| N04b | naive publish inclinations (informational proxy for b) | `36/59` | **measured** (gold-v0.3) | same report | same |
| N05 | proprietary one-shot (column a) | `n/a` — no key or spend approved (D-06) | **n/a** | `app/out/eval/a/` (empty) | frozen prompt runner (not run) |
| N06 | reason-code match | `1.000` (n=59) | **measured** (gold-v0.3) | same report | as N01 |
| N07 | over-escalation rate | `<x.xxx>` | **unmeasured** — needs a scored column (b) to define "over" | — | as N01 once (b) runs |
| N08 | `unknown_state` rate | `4/59 = 0.068` | **measured** (gold-v0.3) | same report (`unknown_state rows: 4`) | as N01 |
| N09 | p50 / p95 decision latency | `<ms>` | **unmeasured** — the offline twin is in-process; no timer harness yet | — | `python3 app/tools/metrics.py` (prints `null`) |
| N10 | cost per change (tokens · apify units · €) | `unmeasured (no vendor prices captured)` | **unmeasured** — `app/prices.json` is all nulls by design | receipts `cost.cost_state` | `python3 app/tools/metrics.py` |
| N11 | gold set size / version | `59` rows · `gold-v0.3` | **measured** | `specs/courserefresh/skin/gold.jsonl` | `python3 app/tests/test_gold_floor.py` |
| N11b | gold set hash | `sha256:73860b210baec7f380ced2ee4f31cb0313a7a8338b54e0c096e9479a08d6a49a` | **measured** (re-derived D-1; the row above was written against an earlier revision, and `audit_claims.py` now fails the build on any drift) | `skin/gold.jsonl` | `sha256sum specs/courserefresh/skin/gold.jsonl` |

## 2. Loop / engine numbers

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N12 | scan cadence (configured) | `60 min` | **configuration** | `skin/thresholds.json` | `cat specs/courserefresh/skin/thresholds.json` |
| N13 | scan cadence (measured, ≥5 live runs) | `<min ± x>` | **unmeasured** — no live runs yet | run log | `python3 app/tools/metrics.py` |
| N14 | unattended window | `<h>` | **unmeasured** — the twin run is in-process; the live hero run is the test | run log | `python3 app/tools/metrics.py` |
| N15 | digest size | `1705 bytes` (cap 4096); the live-engine bundle's digest is `1411 bytes` | **measured** (shipped run `cr-20260926-1726-793`) | `specs/evidence/cr-20260926-1726-793/digest.md` | `wc -c specs/evidence/*/digest.md` |
| N16 | receipt coverage | `100%` (9 receipts / 9 decisions) | **measured** | `app/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` |
| N17 | chain integrity | `true` (`ok (9 rows)`) | **measured** | `app/out/receipts.jsonl` | `python3 app/run_walking_skeleton.py --selftest` |
| N18 | Apify units per run / per day | `<n>` | **unmeasured** — no actor called yet | actor run history | Apify console export |
| N19 | publishes / notifications in the run | `2 publishes · 7 notifications staged (not sent, sim)` | **measured** (sim) | `app/out/notifications.jsonl` | `wc -l app/out/notifications.jsonl` |
| N19b | staged notifications dropped for missing consent | `1 learner` (`consent_missing`) | **measured** (sim) | receipt `cr-learner-consent-01` | `python3 app/tools/metrics.py` |
| N19c | second same-night publish notifying nobody (caps) | `0 notified · 7 held by cap` | **measured** | `app/tests/test_artifacts.py` check 6 | `python3 app/tests/test_artifacts.py` |

| N25 | console page size (the built surface) | `3642 bytes`, no scripts, no remote assets | **measured** (shipped run `cr-20260926-1726-793`) | `specs/evidence/cr-20260926-1726-793/digest.html` | `wc -c specs/evidence/*/digest.html` |
| N26 | curriculum size (what the agent is allowed to edit) | `6 lessons · 13 objectives · 19 quiz items`, all mapped | **measured** | `course/agent-ops/curriculum.json` | `python3 app/tests/test_curriculum.py` |
| N27 | worst measured colour contrast in the lockfile | `4.61:1` (`--status-queue` on `--paper-2`); three tokens were darkened this sitting | **measured** | `specs/design/MASTER.md` §1.1 | `python3 app/tests/test_design.py` |
| N28 | witnessed failure, rehearsed offline | `1 write_failed receipt · 9 receipts · chain ok` | **measured (rehearsal)** | `app/out/e7/app/out/evidence/cr-20260926-1420-924/` | `python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail` |

## 3. Learner numbers (small n, said out loud)

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N20 | cohort n for gate evaluation | `<n>` | **unmeasured** — the run's cohort is a labelled fixture (`cohort_source: fixture (simulated)`) | cohort window row | `python3 app/tools/metrics.py` |
| N21 | quiz delta post-change | `unmeasured` | **unmeasured** — no live cohort yet; the revert fixture carries `-0.04` and is labelled | fixture `09-revert.json` | `cat app/fixtures/events/09-revert.json` |
| N22 | time from stuck signal → dispatch | `<min>` | **unmeasured** — same run, one dispatch, no clock model | dispatch receipt | `python3 app/tools/metrics.py` |
| N23 | micro-lessons dispatched | `1` (`ml-permissions-mode-k-01.md`) | **measured** (sim) | `app/out/micro-lessons/` | `ls app/out/micro-lessons/` |
| N24 | consented learners / total in fixtures | `7 / 8` (one declined-by-design fixture) | **measured** (fixtures) | `kickoff/LEARNER-PLAN.md` §1 | `python3 app/tools/metrics.py` |

| N29 | live-engine dry cycle: decisions | `PUBLISH 1` · `ESCALATE 1` · `NO_CHANGE 0` (run `cr-20260926-1726-054`, shipped) | **measured** (sim) | `specs/evidence/cr-20260926-1726-054/receipts.jsonl` | E9 command |
| N30 | judge calls on the live path | `2` (recorded answers, provider `mock`, fixture printed on the digest) | **measured** (sim) | E9 receipts (`judge.provider`) | E9 command |
| N31 | Apify units accounted in a live cycle | `6` units, ledger row carries the declared approximation `1 run = 1 unit` | **measured** (sim) | `app/out/e8/app/out/state/apify_units.jsonl` | E9 command |
| N32 | battery, after the review fixes | `256` PASS lines across the `13` measured stages, plus stage 14 (the claims audit: see the block in §6), exit 0 | **measured** | `app/out/evidence/battery.log` + `battery-summary.json` | `sh app/check.sh` |
| N33 | live-path checks that run with no credentials | `120` (47 at round 3 + 73 review-fix checks: canvas path, canvas-decides, crash-retry, consent, probe, dwell, bootstrap, JEV, Tavily, canvas, author rulings) | **measured** | `app/tests/test_live_modules.py` | E11 command |

| N34 | handoff collector checks | `15` (redaction, secret scan, self-verified chain + session totals, manifest re-hash, canvas/Apify ids, telemetry counts-only, archive, empty-tree refusal) | **measured** | `app/tests/test_handoff.py` | stage 13/13 |

## 3b. Review-fix rows (`REVIEW.md`, D-1 review pass)

| ID | Claim | Value | Status | Artifact | Command |
|---|---|---|---|---|---|
| N35 | the canvas path the engine posts to is the path the export registers | `cr/triage` in both, read from `skin/wiring.json` | **measured** | `specs/courserefresh/skin/wiring.json` · `app/n8n/wf-cr-1-triage.json` | `python3 app/tests/test_live_modules.py` |
| N36 | with `--via-n8n` the canvas' decision is the one acted on | `decided_by: canvas` on the receipt; the oracle stays as the police record | **measured** | `app/tests/test_live_modules.py` (canvas-decides checks) | E11 command |
| N37 | a crashed cycle does not consume its snapshots | dedupe set unchanged after the crash; the next run processes the parked 4 snapshots (`PUBLISH 1 · ESCALATE 1`) | **measured** | `app/out/live-test/f7-root/app/out/state/` | `python3 app/tests/test_live_modules.py` |
| N38 | the live learner branch is fail-closed on consent | a learner with no consent row is `consent: false`; a refusal is recorded as a revocation | **measured** | `app/lib/telemetry.py` (`record_consent`, `load_consent`) | E11 command |
| N39 | the shipped evidence bundles re-hash | `19` files (offline twin) + `20` (live engine), README included, every hash re-derived by the audit on each battery run | **measured** | `specs/evidence/*/MANIFEST.sha256` | `python3 app/tools/audit_claims.py` |
| N40 | the battery stops the line on a failing stage | `run_stage` preserves the exit status (the old `\| tee` masked a failing gold eval) | **measured** | `app/check.sh` | `sh app/check.sh` |

## 4. Configuration (chosen, not measured — the word "measured" is banned here)

| Item | Value | File |
|---|---|---|
| Thresholds (authority, evidence, learner, budgets) | see file | `skin/thresholds.json` |
| Closed sets (materiality, actions, reason codes, questions) | see file | `skin/change_taxonomy.json` |
| Budgets | Apify 25 units/day · tokens 60 k/change & 500 k/day · 6 publishes/day · 1 notify/learner/day & 3/week · digest 4 KB | `skin/thresholds.json` |
| Revert gate template | `n_min=5 · window_h=48 · metric=quiz_delta · condition≤0` | `skin/thresholds.json` |
| Authority ladder | PA0–PA3; PA1 = publish without notify, PA2 = publish + cohort card, PA3 = human only; promotion = 3 consecutive accepted publishes, 0 rollbacks | `constitution.md` Art. II |
| Subject | *Agent Ops* (n8n + Apify agents in production), six lessons, objectives + prereqs in `curriculum.json` | `spec.md` §1 |
| Source roles | `authoritative` · `corroborating` · `none` (a mirror is recorded, never counted) | `WIRING.md` §2b |
| Comparator (a) | name + version + date recorded **when it runs**; today `n/a` (D-06) | `shared/eval.md` §1 |
| Mode of the quoted run | `sim` (fixtures; no network, no model calls, no mail) | `app/out/receipts.jsonl` |

## 5. What the video may say (and nothing else)

1. "Two changes shipped and one was reverted by the machine — run `cr-20260926-1726-793`." (N19, N17)
2. "Four refusals, with reasons: hostile, single source, contradiction, over budget." (digest §1)
3. "hostile → publish is zero on a 59-row frozen set; so is unsupported → publish." (N01, N02)
4. "The digest is 1.7 KB, refusals first." (N15)
5. "Cost, latency, cadence, the live cohort: `unmeasured` until the live run exists — here is the
   row that says so." (N07, N09, N10, N13, N14, N20–N22)
6. "Every colour on screen is a locked token with a measured contrast — the worst is 4.61:1." (N27)
7. "A failed write is refused once, with its reason, in the digest and on the console." (N28)
8. "It runs a full cycle with no credentials at all: one change published, one refused, both
   labelled `sim` — and the preflight names the four claims the missing keys still block." (N29, N32,
   E9/E10)

Any other number — including in the pitch, the video, or a judge's question — is answered by the
matching register row or by the words `unmeasured` (Art. VI, TM18).

## 6. Machine-checked counts (`app/tools/audit_claims.py`, battery stage 14)

Everything below is re-derived from the files on every `sh app/check.sh`, and a mismatch stops the
line. This block exists because the register used to be prose: the numbers could drift while the
battery stayed green (review F5 — a wrong sha256 for the frozen gold set sat here unnoticed).

<!-- claims-audit:begin -->
```json
{
  "gold": {
    "n": 59,
    "sha256": "73860b210baec7f380ced2ee4f31cb0313a7a8338b54e0c096e9479a08d6a49a",
    "gold_version": "gold-v0.3",
    "action_match": "1.000",
    "reason_match": "1.000",
    "unknown_state": 4,
    "naive_inclinations": "36/59"
  },
  "battery": {
    "stages_before_audit": 13,
    "pass_lines_before_audit": 256,
    "parity": [
      59,
      2
    ],
    "audit_checks": 32
  },
  "suites": {
    "judge_selftest": [
      13,
      13
    ],
    "selftest": [
      14,
      14
    ],
    "test_artifacts": [
      8,
      8
    ],
    "test_claims": [
      5,
      5
    ],
    "test_contracts": [
      16,
      16
    ],
    "test_curriculum": [
      8,
      8
    ],
    "test_design": [
      6,
      6
    ],
    "test_gold_floor": [
      8,
      8
    ],
    "test_handoff": [
      15,
      15
    ],
    "test_hygiene": [
      7,
      7
    ],
    "test_live_modules": [
      120,
      120
    ],
    "test_policy": [
      18,
      18
    ]
  },
  "evidence": {
    "run_id": "cr-20260926-1726-793",
    "bundles": {
      "cr-20260926-1726-793": 19,
      "cr-20260926-1726-054": 20
    },
    "digests": {
      "cr-20260926-1726-793": 1705,
      "cr-20260926-1726-054": 1411
    }
  }
}
```
<!-- claims-audit:end -->

`stages_before_audit` and `pass_lines_before_audit` count the thirteen measured stages that run ahead
of the audit; the audit's own checks are counted by `audit_checks` (it verifies that number against
itself, so adding a check forces a row here). `evidence` points at the **shipped** bundles under
`specs/evidence/` (two: the offline twin's hero run and the live engine's dry cycle), never at `app/out/`: a per-run number compared against mutable state would break
the next time anybody ran the loop, and a number nobody can check is what this section exists to
prevent. `bundles` is the manifest's file count per shipped run, so a bundle that loses a file to a
stray `rm` is caught rather than quietly trusted.
