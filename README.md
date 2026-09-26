# Courserefresh — a course that stays true to a moving subject

**Courserefresh** monitors the upstream world a course teaches (release notes, changelogs, spec
repos, docs, learner telemetry), decides whether the course is now *wrong*, and — when the evidence
is strong enough and its trust ladder allows it — rewrites the lesson itself, regenerates the quiz,
notifies the humans who opted in, learns whether the change actually helped, and **reverts its own
bad edits without being asked**. It refuses to act on one source, and it says so out loud.

- **Brief it serves:** Build Weekend — *"Build a course that updates as its subject changes. Spot
  when a learner is stuck before they ask."* Judged on autonomy 25% · proven in real use 25% ·
  Apify & n8n 20% · problem fit 15% · product & presentation 15%.
- **The three questions the judges ask, answered by the package:** *where are the rules?*
  (`skin/policy.py` + `app/n8n/policy_node.js`, parity-tested) · *what did it do while nobody was
  watching?* (`EVIDENCE.md`, chained receipts, the overnight digest) · *when does it stop?*
  (authority ladder PA0–PA3, revert gates, kill switch — `constitution.md` Art. II, XI, XIV).

## Read these first (in this order)

| # | File | Why |
|---|---|---|
| 1 | [`Idea.md`](Idea.md) | The originating idea, in the author's words |
| 1b | [`HANDOFF.md`](HANDOFF.md) | **Continuing this session?** Where the project stands, what is left, and every command in order |
| 2 | [`specs/README.md`](specs/README.md) | The package index, status, and the 10-minute verification path |
| 3 | [`specs/constitution.md`](specs/constitution.md) | The 16 non-negotiables; the rest of the package is machinery for these |
| 4 | [`specs/reviews/01-4prd-structure-review.md`](specs/reviews/01-4prd-structure-review.md) | What the reference corpus (4prd) got right and wrong — the source of this package's shape |
| 5 | [`specs/courserefresh/spec.md`](specs/courserefresh/spec.md) | What Courserefresh is (user stories, acceptance criteria, non-goals) |
| 6 | [`specs/courserefresh/plan.md`](specs/courserefresh/plan.md) | How it is built and run (Apify → n8n → repo → learners → digest) |
| 7 | [`specs/reviews/04-post-build-panel-and-audit.md`](specs/reviews/04-post-build-panel-and-audit.md) | The post-build panel (product · engineer · founder · curriculum lead · learner · judge) and the closing audit with pasted output |
| 8 | [`specs/reviews/05-specialist-debate.md`](specs/reviews/05-specialist-debate.md) | The specialists' debate (n8n · Apify · judge rubric · UX · teacher · learner · security) — the argument, the fixes, and the four disagreements left on the record |
| 9 | [`specs/reviews/06-build-round-3.md`](specs/reviews/06-build-round-3.md) | **The build, peer-supervised**: who built what, who watched, the 16 defects found in each other's work, and the check that fails if one returns |
| 10 | [`specs/courserefresh/SETUP.md`](specs/courserefresh/SETUP.md) | **The only page you need to go live**: paste the keys, `--preflight --probe`, import the canvas, run the first cycle |

**Verify it yourself:** `sh app/check.sh` → `ALL GREEN` (**179 checks, 13 stages**) on a clean checkout
with **no credentials** — the live path (Apify client, judge, n8n client, telemetry intake, console,
notify channels, one end-to-end dry cycle) is exercised through injected transports. The frozen hero run
`cr-20260926-1421-001` (19 files) and the round-3 engine rehearsal `cr-20260926-1441-130` (14 files) are
recorded in `specs/courserefresh/EVIDENCE.md` §4/§4b.

**Run it now, with no keys at all:**

```bash
python3 app/run_live.py --preflight               # what is wired, what is not, by key name only
python3 app/run_live.py --root app/out/e8 --seed-baseline
python3 app/run_live.py --root app/out/e8 --dry-run --once
python3 app/serve.py --root app/out/e8            # console 0.0.0.0:8080 · telemetry 0.0.0.0:8787
```

Then paste keys into `.env` (`.env.example` is the checklist) and re-run
`python3 app/run_live.py --preflight --probe`.

## The whole package, in one table

| Layer | Files | What it fixes |
|---|---|---|
| Law | `specs/constitution.md` | What may never be traded for a demo |
| Shared contracts | `specs/shared/{harness,data-model,interfaces,eval}.md` | Runtime, data, interfaces, measurement |
| Risk | `specs/security/threat-model.md` | Hostile input, containment, the numbered TM tests |
| Design | `specs/design/MASTER.md` | Paper-and-ink lockfile; the learner diff card; banned list |
| Product | `specs/courserefresh/{spec,plan,tasks,BUILD,TRACEABILITY,JUDGING-MAP}.md` | What, how, when, in which order, proven how, scored how |
| Truth | `specs/courserefresh/{RECEIPTS,EVIDENCE,AMENDMENTS}.md` | Every number and where it came from; every change to this package |
| Operations | `specs/courserefresh/{OPERATIONS,WIRING,checklists,VIDEO-SHOTLIST}.md` | Run it, wire it, check it, film it |
| Kickoff | `specs/courserefresh/kickoff/{PREREGISTRATION,CONSENT,SOURCE-PLAN,LEARNER-PLAN}.md` | What we promised to measure before we measured it |
| Skin | `specs/courserefresh/skin/*` | The executable policy, thresholds, closed sets, gold set |
| Evidence | `app/**`, `app/out/**` | The loop, the receipts, the battery, the digest |
| Review | `specs/reviews/01…04` | The panel that reviewed it; findings and their closure |

## Verify it in ten minutes (no credentials needed)

```sh
sh app/check.sh     # gold floor → gate parity → walking skeleton → threat model → claims → hygiene
```

Everything above runs offline on fixtures. The live loop (Apify + n8n + the real cohort) is Phase 2:
`specs/courserefresh/tasks.md`, and its outcomes land in `app/out/` and `EVIDENCE.md` — never in prose.

*Drafted D-3 · Docs v0.1 · No number in this repository is a claim until `RECEIPTS.md` says so.*
