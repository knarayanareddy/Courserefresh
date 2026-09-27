# Agent Ops 101 — Agents, Autonomy & Operations in Production

A 24-lecture, university-style course on building, running and governing autonomous
agents with n8n and Apify. It is the extensive expansion of the six-lesson subject
course (`course/agent-ops/`, managed by the live loop): same subject, taught as a
full classroom series — lectures, labs, quizzes and a capstone.

**Course code:** AO-101 · **Format:** 24 lectures × ~50 min, 5 modules, weekly labs ·
**Credits:** 6 ECTS · **Author:** author (PA3 — every page human-authored)

---

## How to read this course

Each lecture is a directory `lesson-NN-slug/` containing `v1.md` (the lecture notes,
with YAML frontmatter). Each lecture has 2–3 numbered learning objectives declared in
`curriculum.json`, and a quiz in `quizzes/lesson-NN.json` whose every item maps to a
declared objective. Prerequisites form a linear chain: lecture *N* assumes lecture
*N−1*. The curriculum contract is the same one the live loop enforces on the subject
course: a lecture without objectives, a quiz item without an objective, or a
prerequisite cycle is a curriculum defect.

## Syllabus

| # | Lecture | Module | Concepts |
|---|---------|--------|----------|
| 01 | What is agent operations? | I · Orientation | agent-ops · loop-anatomy |
| 02 | The autonomy ladder | I | autonomy · earned-authority |
| 03 | Anatomy of a production agent | I | loop-anatomy · components |
| 04 | Failure modes & the safety case | I | failure-modes · stop-conditions |
| 05 | n8n fundamentals: nodes, items, executions | II · n8n | n8n · items · executions |
| 06 | Triggers, schedules & idempotence | II | triggers · idempotence · dedupe |
| 07 | The Code node: deterministic decisions | II | policy-node · determinism |
| 08 | Error workflows: a crash is never silence | II | error-workflows · degradation |
| 09 | Calling the world: HTTP, credentials, budgets | II | http · credentials · budgets |
| 10 | Actors, datasets & key-value stores | III · Apify | apify · actors · datasets |
| 11 | Running actors from n8n | III | pinning · run-to-finish · paging |
| 12 | Snapshots, hashes & evidence discipline | III | snapshots · hashing · anchoring |
| 13 | Source independence: voices, not URLs | III | corroboration · independence |
| 14 | The two-stage judge | IV · Judgment | observe · judge · closed-questions |
| 15 | The POLICY node: ordered rules | IV | policy-node · parity |
| 16 | Receipts, diffs & hash-chained memory | IV | receipts · audit-chain |
| 17 | Tool permissions & the human exit | IV | tool-permissions · human-exit |
| 18 | Revert gates: promising to undo | IV | revert-gate · falsification |
| 19 | Learner telemetry & the consent wall | V · Learning loop | telemetry · consent |
| 20 | Micro-lessons & messaging caps | V | micro-lessons · rate-limits |
| 21 | Evals that survive a judge | V | gold-set · traps · columns |
| 22 | The morning digest | V | digest · discipline-strip |
| 23 | Costs, budgets & the discipline of units | V | units · token-ledger · budget |
| 24 | Capstone: run the loop on your own subject | V | capstone · full-loop |

## Prerequisites

- Basic programming (any language; JavaScript and Python appear in labs)
- REST APIs and JSON (L09 and L11 use them directly)
- No prior n8n, Apify or LLM experience — Modules I–III build it

## Learning outcomes

By the end of the course you can: (1) explain what separates an agent from a script
and place any system on the autonomy ladder; (2) build the input layer (Apify actors,
snapshots, hashing) and the decision layer (n8n Code-node policy with error
workflows); (3) design judgment (two-stage judge, closed questions, ordered rules)
and accountability (receipts, chains, permissions, revert gates); (4) run the
learning loop (consented telemetry, micro-lessons, evals, digests) under budgets;
and (5) assemble the whole loop for a subject of your own in the capstone.

## Assessment

| Component | Weight | Notes |
|-----------|--------|-------|
| Per-lecture quizzes | 40% | 4 items each; every item maps to a declared objective |
| Labs | 30% | One lab per module, run against the real stack |
| Capstone | 30% | See `FINAL-PROJECT.md`; graded on the honesty of the artifacts |

## How this course stays true

This tree is authored, not yet loop-managed: `generated: false` on every version,
authority PA3 (human-only) throughout. It is built in the same schema the live loop
enforces (curriculum objectives, quiz alignment, receipted versions), so the loop
could adopt it the way it keeps `course/agent-ops/` current — scanning n8n, Apify
and MCP releases and proposing lesson amendments with receipts and revert gates.

## Reading list (primary)

n8n docs (docs.n8n.io) · n8n releases (github.com/n8n-io/n8n/releases) · Apify docs
(docs.apify.com) · Apify changelog (apify.com/changelog) · MCP specification
(github.com/modelcontextprotocol) · this repo's `specs/constitution.md`,
`specs/courserefresh/WIRING.md`, `specs/shared/eval.md`.
