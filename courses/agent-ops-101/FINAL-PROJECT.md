# Final Project — run the loop on your own subject

**Weight:** 30% of the grade · **Format:** solo or pairs · **Deliverable:** a repository
with the loop running on a subject you choose, plus the artifacts it produced.

The capstone is the whole course in one move: pick a subject that moves, build the
six-phase loop around it with n8n and Apify, and ship the receipts that let a skeptic
argue with every action the system took. Lecture 24 is the walkthrough; this document
is the contract you are graded against.

## 1. Choose a subject (the choice is graded)

Your subject must have **public, fetchable, independent sources that move during the
project window**. Good subjects: a fast-moving open-source tool, a protocol spec, a
regulation tracker, a weather-dependent field. Bad subjects: anything behind a
login, anything with one authoritative voice only, anything static.

You must be able to name, before you build: your authoritative sources, your
corroborating sources, and at least one pair of URLs that look independent but are
not (same publisher, mirror, or syndication) — and show how your system counts them
as one voice.

## 2. Build the loop

| Phase | Requirement |
|-------|-------------|
| NOTICE | A scheduled Apify actor fetch per source, pinned build, snapshots hashed and cached, dedupe on content hash |
| VERIFY | Two independent voices before any claim moves on; verbatim quotes anchored to the snapshot |
| DECIDE | A Code-node policy with ordered rules, first match wins; no model call inside the decision |
| ACT | A versioned artifact write (lesson, page or dataset) with a diff and a changelog |
| LEARN | A falsification gate written at publish time (metric, threshold, cohort min, deadline) |
| REPORT | A digest ≤ 4 KB, refusals first, with mode, measured cadence, budgets and the unmeasured list |

## 3. Ship the evidence

- A receipt for every decision, hash-chained, with `verify_chain() == true` at run end
- At least one run of every action: a `PUBLISH`, an `ESCALATE` (with the preserved
  hostile or under-corroborated quote), a `NO_CHANGE`, and—if you can produce it
  honestly—a `REVERT` or an `unmeasured` gate
- An error-workflow receipt: proof that a thrown error became a line in the digest
- A gold set for your policy: at minimum 40 rows including a hostile-page trap, a
  single-voice trap and a contradiction trap, each labelled before any comparison run

## 4. Grading rubric

| Criterion | Weight | What we look for |
|-----------|--------|------------------|
| Subject choice & source plan | 15% | Two-voices reasoning is real, not decorative |
| Loop completeness | 30% | All six phases, each leaving its named artifact |
| Judgment design | 20% | Models propose, code decides; judge never sees thresholds |
| Evidence honesty | 25% | Refusals shown, unmeasured printed, nothing claimed without its n |
| Degrade plan | 10% | Canvas down, actor down, judge down: each has a labelled fallback |

## 5. Honesty rules (violations fail the project)

Numbers without their artifact or command are claims, and claims are graded
adversarially. A sim run must be labelled sim. A cohort that is fixtures must be
labelled fixtures. If your gate never fired, report `unmeasured` and show the rule
that would have fired. The most impressive thing your system can do is decline to
act on bad evidence — build so that it gets the chance.
