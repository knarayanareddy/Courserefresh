# kickoff/LEARNER-PLAN.md — how the learner loop gets real (and stays ethical)
`v0.1 (draft) · Depends on: constitution.md Art. IV, V; kickoff/CONSENT.md`

The learner loop is 25% of the "autonomy" story and all of the "problem fit" story. It is also the
part of the system that touches humans, so the plan is deliberately small, consented, and capped.

---

## 1. Targets (chosen before recruitment; reported whatever happens)

| Quantity | Target | Floor to act | If below floor |
|---|---|---|---|
| Consented learners (tracking) | 12 | 5 | cohort stats print `unmeasured` |
| Learners who have attempted lesson 4 | 8 | 3 | stuck-signal stats print `n<3` and no dispatch claim |
| Quiz completions after the publish | 6 | 3 | quiz delta `unmeasured`; gate `unmeasured` |
| Named learners (with written consent) | 0–1 | 0 | nobody is named; handles only |

## 2. Where they come from (in this order)

1. Participants at the event who are taking the course (in-person ask, printed consent).
2. People who already agreed to try the course before the weekend (written form).
3. Friends of the team — **only** if they actually use the course (a message with no practice is not
   a learner and is counted as `approached`, not `consented`).

**Not allowed:** purchased participants, bot accounts, synthetic "cohorts" presented as learners,
or populating telemetry ourselves and calling it a cohort. Fixture telemetry is always labelled
`SIM COHORT — fixture telemetry` wherever it appears.

## 3. The ask (what a learner hears, verbatim, ≤45 seconds)

> "This course is being kept up to date by a program. May I track your practice — quiz attempts and
> time — under a pseudonym, and send you at most one short message a day when something changes or
> when the program thinks you are stuck? You can stop with one click, and nothing is graded or
> shared. The details are on this page."

Then: the consent form (`CONSENT.md`) is signed or sent; the handle is generated; the record is
written with the consent version hash.

## 4. The stuck signal (what "stuck" means, before we see data)

A consented learner is stuck on a concept when, within one lesson session:

- `consecutive_wrong ≥ 2` on items tagged with that concept, **or**
- `dwell ≥ 3 × the learner's median dwell` without reaching an attempt.

A signal is **not** a failure. It is a moment; the response is help, not pressure. Signalled
learners receive one micro-lesson per concept per 7 days (cap by Art. IV.2), never a "you're
behind" message.

## 5. The micro-lesson format (fixed)

```
# <concept> — two minutes
1. What it is (3 sentences)
2. One worked example (≤10 lines, mono, from the lesson's own code)
3. One practice item (multiple choice, with the answer explained)
[Stop these messages]   [See what changed]
```

Format is checked in `test_contracts.py`; content is written by the machine but **never graded,
never scored, never reported to anyone but the learner**.

## 6. Ethics guardrails (checked by the ethics seat in reviews)

1. Consent precedes storage; refusal is a normal outcome and is reported as a count
   (`telemetry_rejected`).
2. Handles are hashed at capture; no names in logs, digests, receipts, or the video (Art. V.2–V.3).
3. Messaging caps are enforced in code, not in copy: 1/day, 3/week, 1/concept/7 days.
4. Aggregates are only shown at `n ≥ 3`; a "delta" is never shown without its `n` and window.
5. Data deleted after 14 days or at pilot end; the learner can ask for deletion at any time.
6. The learner can leave without losing the course: opting out changes nothing about access.

## 7. What the loop must never do with learners (restated because it is the risk)

No grading, no scoring adjustments, no adaptive difficulty, no profiling, no "engagement" nudges, no
sharing with third parties, no contacting anyone who has not consented — and no exceptions "for the
demo". If the demo needs a learner to be contacted, the fixture cohort is used and labelled.
