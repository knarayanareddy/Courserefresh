# Courserefresh — origin, story, and the kill list
`v0.1 (draft) · Source: Idea.md (verbatim idea) + the drafting decisions in AMENDMENTS.md`

## 1. The idea, in the author's words

> "A course that updates as its subject changes. It watches the sources the course teaches from —
> release notes, changelogs, docs — and when something material changes, it rewrites the affected
> lesson, regenerates the quiz and notifies the learners. It also watches learners: if several get
> stuck on the same concept, it writes a short micro-lesson for it. And it learns: if a rewrite
> does not help, it reverts its own change." — `Idea.md`, condensed

Two clauses carry the whole hackathon brief, and the product is built around them:

1. **Updates as its subject changes** — notice, decide, act, on the *real* course, without a human.
2. **Spots when a learner is stuck before they ask** — the learner loop, with consent, at human scale.

## 2. The 30-second story (for the video and the pitch)

A lecturer ships lesson 4 on Tuesday. n8n renames the setting it teaches on Thursday. Nobody notices
until a learner files a confused support ticket the following week — or the cohort quietly learns
the wrong thing. Courserefresh notices within the scan cycle, corroborates the change across two
independent sources, rewrites the lesson and its quiz, tells the learners who opted in, and — if the
change did not help — undoes itself. The product is not a chatbot; it is a night shift for a course.

## 3. Why this subject (*Agent Ops*)

- Its sources move **during any build window**: n8n, Apify, and the MCP spec all ship on weekly or
  faster cadences.
- The sources are **independent of each other** (vendor docs vs a second vendor vs a specification
  repo), so corroboration is real, not simulated.
- The learners are **reachable and honest**: this hackathon's own participants read and use this
  material, and many will say when a lesson is wrong.
- It is small and sharp: **one course, six lessons**. The judging rubric says small and sharp beats
  big and generic.

## 4. What was killed, and why (the do-not-revive list)

| Killed | Why it stays dead |
|---|---|
| "Rewrite any course from any URL" | Generic; corroboration becomes impossible; the demo becomes a toy |
| A chatbot tutor over the course | A different product, and it answers only when asked — the brief's opposite |
| Auto-grading and adaptive quizzes | Assessment is human-only (Art. IV.1); it is also the fastest way to lose a judge's trust |
| A dashboard with charts | The digest is the product's face; charts without a source line are banned |
| Learner profiles / personalisation | Profiling minors-adjacent data for a demo; out of scope by consent design |
| Scraping learner forums for "signals" | Scope creep and ethics; consent-gated telemetry only |
| Multi-agent swarm framing | One loop, one policy node, one screen — the argument is legibility |
| A vector database | Not needed for six lessons; the diff is the retrieval |

## 5. The three sentences to keep saying (they are the rubric)

1. "It decides by rulebook, not by vibes — and here is the node."
2. "It refused three times last night, and here is what it refused."
3. "It promised to undo itself at publish time, and then it did."

## 6. Success, honestly defined

The project succeeds if, on D2, we can say — with artifacts — that the loop ran unattended, made at
least one real decision on real sources, refused at least one change, and undid one of its own
changes (or that its gate was `unmeasured`, and why). It fails if the most impressive thing in the
video is a mockup.
