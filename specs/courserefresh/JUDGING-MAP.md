# Courserefresh — judging map (criterion → evidence → answer)
`v0.1 (draft) · For: the 2-minute video, the 3-minute live pitch, and the ~5 minutes of Q&A`

Every judging criterion is answered by an artifact that already exists, in a place the judges can
be shown (not described). The right column is the sentence to say — short, specific, and true.

---

## 1. Autonomy — 25%

| Sub-criterion | Evidence (show this) | Say this |
|---|---|---|
| Notices without being asked | Apify run history + `run_log.jsonl` (`sources scanned`, `no_delta` rows) | "It scans on a schedule whether or not anyone is watching." |
| Decides | The `POLICY` node on the canvas + receipts with reason codes | "The action is chosen by this node — one screen, deterministic, same rules in Python and JS." |
| Acts | The commit on `bot/courserefresh`, the `v3→v4` diff, the learner card | "It wrote the lesson, the quiz, and the changelog itself." |
| Learns | Gate state + revert receipt; dispatch receipts | "It recorded what would make the change wrong — and when that happened, it undid itself." |
| Tells you what happened | The 07:30 digest, refusals first | "The first thing the digest lists is what it refused to do." |
| Knows when to escalate / stop | The refusal receipts (single source, contradiction, assessment, hostile) + the budget and freeze lines | "Four stop conditions fired this run. Here they are with their reasons." |
| Earned, not declared (bonus) | Ladder state derived from receipts (PA1 → PA2 rule) | "Authority is earned by three clean publishes, and one rollback resets it." |

## 2. Proven in real use — 25%

| Sub-criterion | Evidence | Say this |
|---|---|---|
| Real data | Apify run ids + snapshot hashes + source URLs | "These are real pages, fetched at 03:02, hashed — here's the same page now." |
| Real actions | Git history, the card artifact, the micro-lesson artifact | "It committed at 03:12; this is the commit." |
| Real logs | `receipts.jsonl` chain + `run_log.jsonl` | "Every decision has a row; the rows are hash-chained." |
| Run while nobody watched | Overnight window timestamps (≥3 h) | "Nobody touched it from midnight to 07:30." |
| A failure handled on its own | Degraded receipt (actor failure or stale source) + digest line | "The actor failed at 04:10; it held, said so, and did not publish blind." |
| Honesty about what is not real yet | `mode` labels, `RECEIPTS.md` rows marked `unmeasured` | "Anything we could not measure says `unmeasured` on purpose." |

## 3. Apify & n8n — 20%

| Sub-criterion | Evidence | Say this |
|---|---|---|
| Apify pulls real-world data | Actor list with ids/builds; dataset shapes; run history | "Four actors, pinned builds, run history is right here." |
| n8n runs the workflows **and the decisions** | Canvas: the five workflows with the embedded `POLICY` node; execution log | "n8n isn't the plumbing — the decision node on this canvas is the product's rulebook." |
| Depth (the more they power the system, the better) | `WIRING.md` inventory: which actor feeds which workflow node; cadence; retries | "Every input in this system is an Apify dataset row; nothing is invented." |
| Why not a Python script? | Parity test | "Python is the oracle we test against; production runs the same rules in the node." |

## 4. Problem fit — 15%

| Sub-criterion | Evidence | Say this |
|---|---|---|
| Small and sharp | One course (six lessons), one subject, one sentence | "We keep **one** course true — not 'all knowledge'." |
| The brief's own sentence | The loop, verbatim | "It updates the course as its subject changes, and it reaches stuck learners before they ask." |
| Who pays / why it matters | The 30-second author story: stale lesson → confused learners → the bug report you find a week later | "Technical courses rot in weeks; today you find out from a support ticket." |

## 5. Product & presentation — 15%

| Sub-criterion | Evidence | Say this |
|---|---|---|
| One memorable moment | The refusal: hostile or single-source page → `ESCALATE`, nothing published | "The most impressive thing it did was decline to act." |
| The face of the product | The 07:30 digest (paper-and-ink, refusals first) | "The product's face is one page a lecturer reads with coffee." |
| Rehearsed, honest demo | Pre-registered fallbacks; labels on screen | "If the canvas is down, this is the parity-tested twin — same rules, labelled." |
| No slop | Design lockfile; banned list enforced in tests | "The design is a lockfile, not a mood board." |

## 6. The seven hardest questions (and the answers)

1. **"Isn't this an LLM rewriting a doc?"** — "No: the LLM answers seven closed questions; the
   action comes from a deterministic rulebook in code. The eval shows the same models *without*
   the rulebook publishing hostile and uncorroborated changes."
2. **"What if the source is wrong?"** — "One source never publishes. Contradictions escalate. And
   every publish promises its own undo condition — the gate you see on the receipt."
3. **"What does it do when a learner is stuck?"** — "A consented learner with 2 consecutive wrong
   answers or 3× the median dwell gets one concept, two minutes, one practice item — before asking."
4. **"Who edits the lesson, and who is responsible?"** — "The machine edits; the author owns the
   branch and merges; every machine action is a receipt and a revertible commit."
5. **"What happens when it is wrong?"** — "The gate catches it and the machine reverts itself, as a
   new version — shown in this receipt." (If the live run did not reach a gate: "It is
   `unmeasured`; here is the rule that will fire.")
6. **"Why should I trust the numbers?"** — "`RECEIPTS.md`: every number names its artifact and the
   command that produced it; the rest are `unmeasured` on purpose."
7. **"What is the business?"** — "Course teams pay to stop shipping stale lessons: one subscription
   per course, the digest is the product, the eval is the audit." (Pitch line; not measured.)

## 7. Score-the-room drill (before the live final)

Each line above is read aloud once, timed. The demo dies on adjectives ("powerful", "seamless") —
every claim is replaced by a pointer to an artifact in `app/out/evidence/`.
