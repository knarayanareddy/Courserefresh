# specs/ — the Courserefresh specification package

`v0.5 · Last amended D-0 · Amends: courserefresh/AMENDMENTS.md v1.2 · Owner: the build agent · Ratified at kickoff`

This package is written so that **an autonomous build agent can execute it without a human in the
loop**, and so that a judge can verify every claim by running one command. It follows the structure
of the reference corpus `4prd` (constitution → `shared/` contracts → product spec/plan/tasks →
reviews), with the gaps found in `reviews/01` closed: traceability, claims discipline, an
ain't-happened list, and a review that closes findings only with pasted output.

## Status

| File | State | Notes |
|---|---|---|
| `constitution.md` | draft | 16 articles; ratified at kickoff, then amendable only via `courserefresh/AMENDMENTS.md` |
| `shared/harness.md` | draft | Runtime contract: loop phases, model knobs, budgets, latency doctrine, degraded modes |
| `shared/data-model.md` | draft | Objects, closed sets, hashes, coercion rules |
| `shared/interfaces.md` | draft | n8n / Apify / repo / console contracts, error taxonomy, exit codes, idempotency |
| `shared/eval.md` | draft | Three columns, gold protocol, floor n≥40, legal degrade |
| `security/threat-model.md` | draft | Surfaces → threats → containment; TM01–TM18 as named tests |
| `design/MASTER.md` | draft | Paper-and-ink lockfile; author console + learner card |
| `courserefresh/*.md` | draft | The product: spec, plan, tasks, build order, traceability, judging map, receipts, evidence, wiring, ops, checklists, shot list, amendments, origin, kickoff docs |
| `courserefresh/skin/*` | executable | Policy oracle, thresholds, closed sets, gold set `gold-v0.3` (n=59, incl. mirror and rehearsal traps) |
| `reviews/01` | complete | Structural review of the 4prd reference corpus, with measured evidence |
| `reviews/02` | complete | Judges' pre-mortem: six seats, J-01…J-12, verdict *proceed to the live phase* |
| `reviews/03` | complete | Builder's answer to review 01: A1–A12 ported/cut, H1–H14 closed with commands |
| `reviews/05` | complete | The specialists' debate (n8n · Apify · judge · UX · teacher · learner · SRE): S-rows closed by tests, four disagreements recorded, agreement reached |
| `reviews/04` | complete | Post-build panel (product · engineer · founder · curriculum lead · learner · judge): K-01–K-08, four MUST-FIXes fixed with tests, three live-phase rows named open; closing audit with pasted output |

## The order to read (and the order an agent should build)

1. `constitution.md` — nothing below may violate it; if a doc does, the doc is wrong.
2. `shared/harness.md` — the loop, the knobs, the stop rules.
3. `shared/data-model.md` + `shared/interfaces.md` — the shapes and the contracts.
4. `courserefresh/spec.md` — user stories US-1…US-12 with acceptance criteria AC-x.y.
5. `courserefresh/plan.md` — the architecture and the 72-hour shape.
6. `courserefresh/tasks.md` — M0 → M1 → M2 → M3 with definition of done.
7. `courserefresh/BUILD.md` — the build constitution: order, gates, forbidden moves.
8. `security/threat-model.md` — what must not be possible, and the tests that say so.
9. `design/MASTER.md` — what the two surfaces look like (locked before code).
10. `courserefresh/kickoff/*` — promises made before the window opens.
11. `courserefresh/{WIRING,OPERATIONS,checklists,VIDEO-SHOTLIST}.md` — run, wire, check, film.
12. `courserefresh/{TRACEABILITY,JUDGING-MAP,RECEIPTS,EVIDENCE,AMENDMENTS}.md` — proof that it happened.
13. `reviews/*` — the panel record; findings close only with pasted output.

## Vocabulary (all closed sets live in `courserefresh/skin/`)

| Term | Meaning |
|---|---|
| **Subject** | The thing the course teaches. Chosen so its upstream sources move during the build window |
| **Snapshot** | One fetched source page/release, content-hashed, cached verbatim |
| **Claim** | A model-extracted, quote-anchored assertion from one snapshot |
| **Change event** | ≥1 claim against a topic the course covers, deduped by `event_id` |
| **Materiality** | Closed set: `material_breaking` · `material_deprecation` · `material_new_capability` · `cosmetic` · `marketing_noise` · `ambiguous` · `contradictory` · `unverifiable` |
| **Decision** | Closed set: `NO_CHANGE` · `DRAFT` · `PUBLISH` · `REVERT` · `ESCALATE` (learner stream: `NO_CHANGE` · `DISPATCH` · `ESCALATE`) |
| **Receipt** | Append-only JSONL row: what was seen, what was decided, why, what changed, what it cost |
| **Trust ladder** | PA0 observe · PA1 auto-publish (no notify) · PA2 auto-publish + cohort notify · PA3 human-only |
| **Revert gate** | The pre-registered condition under which the agent must undo its own publish |
| **Cohort window** | A consented learner group of n≥5 observed for ≥48 h after a publish |
| **Hallucinated** | Adjacent to the truth, plausible, smooth, wrong — used in `policy.py` to name the `ambiguous`/`unverifiable` failure |
| **Sim / live** | Sim = fixtures, offline, no model calls. Live = real Apify runs, real n8n executions, real cohort |

## The ten-minute verification

```sh
sh app/check.sh
```

That command is the only “it works” claim this package makes. Last run: **103 PASS, exit 0
(`ALL GREEN`)**, output archived at `app/out/evidence/battery.txt`; the frozen hero run is
`app/out/evidence/cr-20260926-1421-001/`. Anything that has not been measured
is written `unmeasured` (Art. VI) — and anything labelled **measured** in `RECEIPTS.md` names the
command and the artifact that produced it.

## Conventions

- **Day labels, not dates.** `D-3` spec/kickoff · `D-2` build + dry runs · `D-1` wire live + arm the
  hero run · `D1` build, run the loop overnight · `D2` harvest, film, **submit 15:00**, live final 16:15.
  Wall-clock dates exist only in `courserefresh/kickoff/PREREGISTRATION.md`, and the hygiene test
  enforces that (`app/tests/test_hygiene.py`).
- **Status vocabulary in tasks:** `[ ]` todo · `[x]` done (evidence linked) · `[~]` cut or degraded
  (what and why, written down) · `[!]` blocked (who unblocks).
- **Amendment rule:** change the spec first, add the `AMENDMENTS.md` row, then the code.
- **Receipts over prose.** A number without a receipt is deleted, softened to `unmeasured`, or the
  command that produces it is added to `check.sh`.
