# kickoff/ — pre-registration (promises made before the window opens)
`v0.1 (draft) · Signed by: the build team at kickoff · This is the only file in specs/ allowed to contain wall-clock dates`

Pre-registration means: the things we will measure, the thresholds we will use, and the fallbacks we
will accept are written down **before** we see the results, so that no number in the final pitch is
chosen after the fact.

---

## 1. Calendar (fill at kickoff; `D2` is submission day)

| Label | Date | Milestone |
|---|---|---|
| D-3 | `<date>` | Constitution ratified; thresholds frozen; gold ≥40 authored; skeleton green |
| D-2 | `<date>` | M0 gate signed (walking skeleton end-to-end) |
| D-1 | `<date>` | Live actors pinned; dry run `mode: live`; **hero run armed before midnight** |
| D1 | `<date>` | Unattended overnight run; harvest at 07:30; gates evaluated |
| D2 | `<date>` | Evidence freeze; film; **submit 15:00**; live final 16:15 |

## 2. Hypotheses (learning is falsifiable or it is decoration)

- **H1 — Corroboration matters.** With the policy enabled, `unsupported → publish` is 0 on the gold
  set; with the same models and the policy disabled, it is > 0. (Measured by the eval's columns b/c.)
- **H2 — The gate catches at least one bad publish.** Over the window, at least one published change
  has its gate satisfied and is reverted (or the gate is `unmeasured` and that is stated).
- **H3 — Help before asking is real.** At least one consented learner receives a micro-lesson within
  one scan cycle of the stuck signal; they do not have to ask a question first.

Each hypothesis is scored in `RECEIPTS.md` (N01, N02, N05, N09, N10, N20–N23) and reported in the
digest, whatever the outcome.

## 3. Frozen thresholds (chosen now; changing any of these is an `AMENDMENTS.md` row)

| Threshold | Value | Rationale written at kickoff |
|---|---|---|
| `min_sources` | 2 | One source is an anecdote; the cost of a wrong publish is a confused cohort |
| `source_agreement` floor | 0.5 | Below half agreement the sources are fighting, not confirming |
| `quote_supported` floor | 0.8 | A claim that is not mostly a quote is an interpretation |
| `learner_impact` floor for publishing | 0.4 | Below that, a draft is enough; do not churn learners |
| `injection` escate threshold | 0.5 | Deliberately low: the cost of a false alarm is a receipt, the cost of a miss is a poisoned lesson |
| PA2 promotion | 3 consecutive accepted publishes, 0 rollbacks | Earned authority, cheap to lose |
| Revert gate | `n ≥ 5 · 48 h · quiz_delta ≤ 0` | Waiting 48 h avoids reverting on one bad afternoon |
| Publishes/day | 6 | A course that changes 10 times in a day is not a course |
| Notifications | 1/learner/day · 3/week | Above this, updates become noise and consent erodes |
| Digest | ≤ 4 KB | One minute of reading, by construction |

## 4. What will be called success (before we know the result)

| Outcome | Verdict |
|---|---|
| Loop ran unattended ≥ 3 h; ≥1 real corroborated publish; ≥1 refusal with reason; chain intact | **success** |
| Same, but the revert gate was `unmeasured` (n < 5) | **success with a named unknown** |
| No real source moved; the labelled rehearsal ran and is labelled everywhere | **success with the fallback exercised** |
| Loop ran but every decision was `ESCALATE` | **partial** — honest in the digest, weak in the video |
| Any unlabelled sim artifact presented as live; any number without a receipt | **failure**, regardless of the rest |

## 5. Fallbacks accepted in advance

As `plan.md` §7 and `EVIDENCE.md` §5: cached sources → degraded; canvas down → offline twin;
no change → labelled rehearsal; no consented learner → labelled sim cohort. Every fallback carries
its on-screen label; none is silently substituted.

## 6. Freeze and stop rules confirmed at kickoff

- The kill switch is tested **before** the overnight run, in live mode.
- Two freezes in one day cancel the overnight run (`OPERATIONS.md` §5).
- Any Sev-1 incident (`OPERATIONS.md` §6) pauses the loop until the battery is green again.

## 7. Signatures

| Role | Agent/human | Signed at |
|---|---|---|
| Builder | `<name>` | `<D-3>` |
| Core-First Warden | `<name>` | `<D-3>` |
| Design lock | `<name>` | `<D-3>` |
| Consent/ethics check | `<name>` | `<D-3>` |
