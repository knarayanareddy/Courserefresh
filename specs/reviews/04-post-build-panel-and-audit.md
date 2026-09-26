# Sitting 04 — post-build panel, and the closing audit
`Version 1.0 · Last amended D-0 · Amends: AMENDMENTS.md v1.3 (K-rows) · Rule: a finding is closed only by pasted output, below`

Six seats review the **built** package — the thing that exists in this repository, not the idea of it.
Then the audit pastes the commands. The finding rows (K-01…K-08) are answered in §5 with a file and a
command; anything still open is named in §4 with an owner and the condition that closes it.

> **Superseded for current numbers by `reviews/05` (this file is a dated record and is not edited).**
> Where the two disagree, the later sitting is right — it re-ran everything and pasted the output.

## 0. Verification path, run in front of the panel

```
sh app/check.sh                         → 92 PASS · exit 0 · ALL GREEN   (§3.1)
python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl
                                        → action 1.000 · reason 1.000 · hostile→publish 0 (§3.2)
node app/tests/test_gate_parity.py      → rows=57 probes=2 · PASS      (§3.3)
python3 app/run_walking_skeleton.py --selftest
                                        → 13/13 · 10 receipts = 10 decisions (§3.4)
python3 app/tests/test_artifacts.py     → 7/7 (this sitting's new gate) (§3.5)
```

## 1. Openings (ten minutes each, no coaching)

- **Product lead (course platforms).** "The loop is legible, the digest is the product, and the
  refusal list first is the best decision in the file. My worry is the learner side: the cards are
  *staged*. Until a human receives one, 'learning' is a claim."
- **Staff engineer.** "Receipts chain, parity holds, the twin is deterministic. But the ledger only
  proves itself: nothing re-hashes the lesson files it names. A corrupted or hand-edited artifact
  would pass every test you have."
- **Founder (seed-stage).** "Cost and cadence are `unmeasured`, which I respect, and the revert is
  the only moat in this category. The audit trail has a hole exactly where the demo's best story is:
  the revert entry had no diff and no receipt line in the changelog."
- **Curriculum lead (potential user).** "I would let it touch my course *after* one change I can
  read, and one change it refused. Both are in the run. My condition: it must never touch an
  assessment without a human — that is written down and tested."
- **Potential learner.** "Seven cards, one opt-out link, no raw diff, no jargon dump. If a second
  lesson lands the same day, do I get spammed? The cap is configured — is it enforced?"
- **Hackathon judge.** "Autonomy, refusal, revert, receipts: strong. But 45% of the score is
  proven-in-use and n8n/Apify powering the system. Right now n8n is a mirrored rulebook and Apify is
  a pinned table. I need a real execution id before the live round, or the video has to say the word
  'staged' on screen."

## 2. Findings

| ID | Seat | Finding | Severity | Status |
|---|---|---|---|---|
| K-01 | engineer | Receipts name artifacts that nothing re-verifies — no post-publish integrity check on body/diff hashes or on the predecessor version | **MUST-FIX** | **fixed** — `test_artifacts.py` 7/7 (F-18) |
| K-02 | learner | The per-learner notification caps exist in `thresholds.json` but the publish-notification path never consults them | **MUST-FIX** | **fixed** — caps enforced in code, skips recorded, digest line (F-19) |
| K-03 | product lead | The per-concept micro-lesson cap (`micro_lesson_per_concept_days`) was configured, not enforced: a learner could receive the same concept twice in a week | **MUST-FIX** | **fixed** — a policy branch (`rate_limited`) consumed by both deciders, parity-probed (F-20) |
| K-04 | founder | The revert's CHANGELOG entry carried no `- diff:` and no receipt id — the audit trail's best story had a hole | **MUST-FIX** | **fixed** — revert entries now carry both; stamped id = `rcpt-11-450-008` (F-21) |
| K-05 | judge | n8n is still a mirror, not the engine: no execution id, no canvas run | MUST-FIX before the live round | **open** — T10–T17, WIRING §6; fallback wording pre-registered (`EVIDENCE.md` §5) |
| K-06 | product lead | No real learner has received a card; notifications are staged in the twin | MUST-FIX before the video | **open** — T13; the video either shows a delivered card or says "staged" on screen |
| K-07 | judge | Apify rows are pinned and normalised but no actor run id exists yet | MUST-FIX before the live round | **open** — T10, `SOURCE-PLAN.md` §3 |
| K-08 | engineer | Parity checked gold rows only; a new policy branch could drift between the oracle and the n8n node unnoticed | SHOULD-FIX | **fixed** — parity now also checks named probes (`probe-concept-cap`, `probe-frozen-learner`) (F-22) |

No seat raised a problem with the spec's **shape**: constitution → shared contracts → product spec →
gates → evidence → review sits, with the claim register and traceability as first-class files.

## 3. Closing audit — pasted output

### 3.1 The battery (`sh app/check.sh`, tail)

```
== 8/10 contracts =========================================
test_contracts: 13/13 checks passed

== 9/10 claims ============================================
test_claims: 3/3 checks passed

== 10/10 hygiene + design =================================
test_hygiene: 7/7 checks passed
test_design: 5/5 checks passed

ALL GREEN
```

`92 PASS · exit 0`. Archived at `app/out/evidence/battery.log` (the file is overwritten by every
battery run, so the number here is the panel's own run, not a claim about the current one).

### 3.2 Decision eval (`policy.py --eval specs/courserefresh/skin/gold.jsonl`)

```
gold_version: gold-v0.2 · n=57
action match: 1.000
reason match: 1.000
escalate rate: 0.421
  change   action match 1.000 (n=40)
  learner  action match 1.000 (n=9)
  revert   action match 1.000 (n=8)
unknown_state rows: 4
hostile -> publish: 0 (must be 0)
unsupported -> publish: 0 (must be 0)
column (b) informational: naive publish inclinations 34/57
```

### 3.3 Parity (`node app/tests/test_gate_parity.py`)

```
gate parity — rows=57 probes=2 checked against the Python oracle
PASS
```

### 3.4 Loop selftest (`--selftest`, tail)

```
  PASS  receipt coverage is 100% of decisions     10 receipts vs {'PUBLISH': 3, 'ESCALATE': 4, …}
  PASS  digest fits the 4 KB contract             1480 bytes
  PASS  kill switch: no writes while frozen       3 frozen decisions, 0 writes
  PASS  tampering breaks the chain

selftest: 13/13 checks passed · sandbox: app/out/selftest
```

### 3.5 The new gate (`python3 app/tests/test_artifacts.py`)

```
  PASS  every artifact still hashes to its receipt                                 mismatched=[]
  PASS  every publish names a predecessor that exists and differs                  bad=[]
  PASS  every diff still hashes to its receipt                                     mismatched=[]
  PASS  a revert restores the version it names (text kept, marker written)         reverts=1 marker=True
  PASS  learner cards carry the contract, no raw diff, consented refs only         cards=7 bad=[]
  PASS  notification caps are enforced in code (day cap skips every consented learner)  notified=0 skipped=7
  PASS  per-concept micro-lesson cap holds (second dispatch in the window is rate-limited)  NO_CHANGE ['rate_limited']

test_artifacts: 7/7 checks passed
```

### 3.6 Frozen run `cr-20260926-1411-450` (sim)

```
run_log   {"decisions": {"PUBLISH": 2, "ESCALATE": 4, "NO_CHANGE": 1, "DISPATCH": 1,
           "REVERT": 1}, "chain_rows": 9, "chain_verified_at_end": true, "sources_scanned": 11,
           "publishes_used": 2}
hashes    receipts   120badecdf8693ff2c5f3c6fc58e84317bc786a1962124ecf721d39cc4ebff1b
          run_log    ed839f621e5712c5309c4b24705fa46b961116b5617daa159c96b2959524c698
          digest     9526096f93d85340ec808fecb825b905f9a1bf3ca23a772e1110b0753ae76e2b  (1323 bytes)
          eval       3253c387791866a325c2005f433c8a8d4bc2e5eae68fcba23e5458ea21e9c3df
          cards      3823f61d178538081b5f209db2dede4c22a6456ece968a908a5b130ee9e56b0a  (7 rows)
manifest  app/out/evidence/cr-20260926-1411-450/MANIFEST.sha256 — 18 files
```

The CHANGELOG now carries exactly one diff line and one receipt line per entry
(`v4 → rcpt-11-450-000`, `v2 → rcpt-11-450-001`, `v5 → rcpt-11-450-008`), and every artifact hash in
the manifest is the one the receipts name — that was K-01, and it is the difference between a log and
an audit.

## 4. What remains open (named, not rounded up)

| # | Open item | Closes when | Owner |
|---|---|---|---|
| K-05 / J-04 | n8n runs the decision, with an execution id | a real execution appears in `WIRING.md` §6 | live phase (T12) |
| K-06 | a real learner receives a real card | one delivered notification (or the on-screen word "staged") | live phase (T13) |
| K-07 | a real Apify actor run feeds a snapshot | actor run id in `WIRING.md` §1 | live phase (T10) |
| E7 | one witnessed failure handled live | a degraded-mode receipt from the live run | live phase (T16) |
| C-06 / T15 | the console | Phase 2, after the live loop | stretch — the digest is the product surface |

These are the rows that keep 25% (proven in real use) and 20% (Apify & n8n) at risk; every other
criterion is now backed by an artifact in this repository.

## 5. Feedback → implementation (the builder agents' answer)

| Finding | Change made | File | Verified by |
|---|---|---|---|
| K-01 | artifact/diff hashes re-computed from disk; predecessor existence; revert restoration; card contract | `app/tests/test_artifacts.py` (new) | `test_artifacts` 7/7 |
| K-02 | per-learner caps enforced on the publish-notification path; skipped learners recorded on the artifact; digest line "held by cap" | `app/run_walking_skeleton.py` (`notify_cohort`) | §3.5 check 6 |
| K-03 | the per-concept cap became a policy branch — `rate_limited` — instead of a runner special case | `skin/policy.py`, `app/n8n/policy_node.js`, `app/run_walking_skeleton.py` | §3.5 check 7 + probe |
| K-04 | revert CHANGELOG entries write their diff line, so the receipt stamping lands | `app/run_walking_skeleton.py` (`revert_version`) | §3.6 CHANGELOG |
| K-08 | parity now verifies gold rows **and** named probes for branches gold does not exercise | `app/tests/test_gate_parity.py` | §3.3 |
| — | the battery grew a tenth stage (artifact integrity) so this class of hole cannot return silently | `app/check.sh` | §3.1 |

## 6. Verdict

**Conditional pass.** The package is buildable from its own documents, refusals are proven, the undo
is proven, and every number on screen has a row. The panel's condition is the live phase: one real
Apify run, one real n8n execution, one delivered learner card — or the on-screen words that say
otherwise. Re-verdict belongs to the next sitting, and it starts from §4.
