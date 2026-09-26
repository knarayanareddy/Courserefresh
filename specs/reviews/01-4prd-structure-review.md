# Sitting 0 — End-to-end review of `knarayanareddy/4prd/specs`
## A nine-seat domain panel reads the reference project before we copy anything from it

**Charged with:** extract the gold standard from `4prd`, refuse to inherit its defects, and produce a port list for **Courserefresh** (`knarayanareddy/Courserefresh`).
**Method:** every claim below was checked against the cloned repo (`git clone --depth 1`, reviewed at commit `HEAD` of `main`, 26 Sep 2026). File/line evidence is given. Nothing here is a matter of taste without a count attached.

---

## 0. Panel roster & mandates

| Seat | Domain | Mandate | Keeps on the wall |
|---|---|---|---|
| **Nora Okonkwo** | Spec-driven development (Spec Kit) | Constitution, spec/plan/tasks separation, spec supremacy | "Code that disagrees with a spec is a bug" |
| **Sofia Park** | Eval & gold-set science | n, traps, three columns, no self-dealing, honest `unmeasured` | "Say *learns* again and show me the table" |
| **Tomás Ferreira** | Instructional design / content ops | Does the artifact teach? Assessment validity. Versioning for learners | "A confused learner is a failed acceptance test" |
| **Ingrid Sørensen** | Learning science / psychometrics | Spacing, retrieval practice, validity of "improvement" claims | "Quiz-score delta over 48 h is a hypothesis, not a fact" |
| **Wei Chen** | DevRel curriculum in fast-moving infra | Docs-as-code, changelog hunting, subject that ships daily | "The subject changed at 23:40. What did your course do?" |
| **Amara Okafor** | Records, provenance & traceability | Citation lineage, diff review, rollback, retention | "A rewrite without a diff is a rumour" |
| **Rhea Solanki** | AppSec / agentic security (OWASP + ASI) | Injection, tool allowlists, budgets, receipts, kill switch | "Untrusted input is the architecture, not a test case" |
| **Priya Raghavan** | Product & 2-minute video narrative | ONE wow, proof on screen in 15 s, no unwired buzzwords | "The refusal is the frame judges remember" |
| **Kenji Mori** | One-weekend ship economics | Task order, dated stop-the-lines, time budgets | "Cut the spec, not the clock" |

---

## 1. What `4prd` gets right (the parts we are porting, not paraphrasing)

These are the structural inventions that make it a reference implementation of spec-driven development for an agent-built product. Each one is a *mechanism*, not a document title.

| # | Mechanism | Where it lives | Why it works |
|---|---|---|---|
| **G1** | **Constitution with an amendment rule that constrains agents, not just humans** — "a `plan.md` may *narrow* scope; it may not relax Articles I–VI or XI–XII" | `specs/constitution.md` (Art. I–XII, v3.1) | Gives a coding agent a legal test for every change. Prevents the classic agent failure: silently widening the problem. |
| **G2** | **Three-file product tree: `spec.md` (WHAT) → `plan.md` (HOW) → `tasks.md` (TODO with T-numbers)** | `specs/{listguard,clausewindow,menumind,exhibit}/` | Separation of concerns survives a weekend and a re-read at 02:00. T-numbers make review feedback addressable ("T13 is stale"). |
| **G3** | **Policy lives in code; models propose, code disposes; closed sets are data files** | `constitution.md` Art. IV; `app/skins/*/policy.py`, `allergens.json`, `buckets.json` | The single highest-value move in the repo. It is the difference between a demo and a system. |
| **G4** | **Hostile input is in-scope, and hostile goes first in the demo** | Art. V; `specs/*/spec.md` "Opening Fixture" | Turns the weakest part of every LLM demo (injection) into the strongest 15 seconds. |
| **G5** | **Receipts with `actor=human` persisted on the stored record, not in RAM** | Art. VI.1; `exhibit`/`menumind` specs; `app/harness/receipts.py` | Makes governance auditable rather than claimed. |
| **G6** | **Design lockfile with an explicit *banned* list** ("if a later agent makes it pop, it violated this file") | `specs/design/MASTER.md` | The only reliable defence against 2026 AI-slop chrome. Persisted tokens + anti-patterns + a pre-delivery checklist. |
| **G7** | **Sittings as permanent artifacts: jury + council + dissent log + binding change list** | `specs/build-council-debate.md`, `specs/sitting-{7,8,9}-*.md`, `specs/exhibit-sittings.md`, `specs/security-ux-sitting.md` | Rationale survives the weekend. Disagreements are recorded, not resolved by whoever spoke last. This is the process we are asked to reproduce. |
| **G8** | **`ORIGIN.md` as a memory of killed ideas** ("do not reopen killed ideas") | `app/skins/*/ORIGIN.md` | Stops an agent from "helpfully" resurrecting a killed feature. Directly addresses agent regression at the strategy layer. |
| **G9** | **Walking-skeleton discipline: loop first, gate second, with a named role holding a veto** | `build-weekend/marketmind/constitution.md` Art. I + Core-First Warden | The single best mentor lesson in the repo. It is the difference between a working demo and a beautiful safety system over a non-product. |
| **G10** | **Claims audit + kiss-of-death list, enforced before recording** | `build-weekend/checklists.md` §6, `04-judge-panel-review.md` §4 | Converts "don't overclaim" from advice into a checklist with named red lines. |
| **G11** | **Agent-operability layer**: `AGENTS.md` (operational directives), `AGENT_BOOTSTRAP_PROMPT.md` (mandatory read order), per-skin `AGENT_PROMPT.md` + `BUILD.md` | repo root + `app/skins/*/` | The repo is written for the entity that will actually do the work. Courserefresh needs this from day one. |
| **G12** | **Threat model with a numbered test list that maps to the constitution** | `specs/security/owasp-threat-model.md` §10; `build-weekend/marketmind/threat-model.md` §4 | Security controls you can run, not a posture you assert. |

**Panel verdict on structure:** the *shape* (`constitution → harness → product spec/plan/tasks → design lockfile → threat model → sittings`) is the gold standard and is worth copying wholesale. The failures below are all failures of **maintenance between the documents**, not of the shape.

---

## 2. Hole catalog (each finding is a count, a path, or a contradiction)

### H1 — The constitution's own eval floor is violated by its own artifacts (severity: constitutional)

`specs/constitution.md` Art. III: "**at least** these columns, on a **frozen** eval of **n ≥ 40** (including traps)" for *every* product.

Measured on 26 Sep 2026:

```
app/evals/menumind/gold.jsonl      40 rows   ✅
app/evals/exhibit/gold.jsonl       12 rows   ❌ (30% of floor)
app/evals/listguard/gold.jsonl      5 rows   ❌ (12.5% of floor)
app/evals/clausewindow/gold.jsonl   3 rows   ❌ (7.5% of floor)
app/evals/stub/gold.jsonl          12 rows   (harness stub, exempt)
```

Sitting 9 (`specs/sitting-9-four-products.md`, council vote #5) quietly downgraded the promise to "seed gold for the *named* ids (not n=40)". A constitution that is amended by a meeting minute in a different file and never versioned is no longer a constitution. **Fix pattern for Courserefresh:** the floor and the degrade path must live in the *same* article, with an explicit legal wording for a smaller n (`n=<actual>`, no advantage claim) and a task that pads the set before the table is allowed to ship.

### H2 — The same document family asserts unmeasured numbers as facts (severity: trust)

Constitution Art. III.2–3: "Self-labelled 'we beat GPT on quality' without the vanilla-TF column is a constitution violation… Honest cost/abstention wins beat fake F1." Art. V.1 also bans invented numbers in the Build-Weekend lineage.

Then, in the specs:

| Claim | File | Status |
|---|---|---|
| "€0.08 on Token Factory vs. €2.40 on Claude 3.5 Sonnet (**30× cost advantage**)" | `specs/menumind/spec.md` §US-7 | Unmeasured; comparator (Claude 3.5) is stale for Sep 2026 |
| "**26× lower cost** and **sub-100ms latency** with **0% hallucinations**" | `README.md` §5 | "0% hallucinations" is not a measurable claim; contradicts Art. V ("prompt injection is unsolved") |
| "€0.003 / listing (**26× cheaper than GPT-4o**)" | `specs/listguard/spec.md` §US-6 | Third comparator (GPT-4o) in the same family; no receipt |
| "quality, latency, and **26× cost advantages**" | `specs/shared/harness.md` Phase 5 | The 26× is a *Prosus-published vendor number about Token Factory overall*, not this system's measurement — and the file presents it as ours |
| "**Winnow Compactor … 1.4ms**", "reducing token consumption by up to 50%" | `specs/shared/harness.md` §2, all four specs | No test, no artifact, and it is in the critical path of every Mermaid diagram |
| MenuMind benchmark claims "**17 gold fixtures**" | `specs/menumind/spec.md` §US-7 | Actual file has 40 rows. The two numbers coexisted in the same repo |
| "**71/71 passing unit tests**" | `specs/menumind/tasks.md` T04, `README.md` §4 | Not reproducible in this sandbox (`pytest` absent, no network for `uv sync`); 11 test files exist. Claim is plausible but *unverified in place* — an audit trail (`last_report.md`) is not committed |

Also missing: MenuMind's benchmark AC has **two** columns (TF vs Claude) where Art. III mandates **three** (proprietary wrapper / vanilla TF / ours). The constitution is violated *by the spec it governs*, and no test catches it.

**Fix pattern for Courserefresh:** a machine-checked claims register. Every number that appears in a spec must exist in `RECEIPTS.md` with a source (`receipt | eval-report | vendor-published`), and `app/tests/test_claims.py` fails the build when a bare `N×`/`€N`/`Nms` claim appears in `specs/`. Numbers about our system may only cite our own eval report; vendor numbers are labelled as vendor numbers.

### H3 — Tasks contradict Phase 0, three times, in the same files (severity: agent chaos)

`specs/menumind/tasks.md` opens with "Phase 0 is already validated in `app/`" (`[x] T01–T04`), then:

- T05 configures `.env` "with live Nebius Token Factory credentials" (fine — but it is presented as a build step, not a key step)
- T06 "Wire `WinnowCompactor` into `app/skins/menumind/__init__.py`" — the shared harness this task refers to is `[x]` complete in T01–T04
- T12 "Update `app/web/templates/home.html` **and Lovable React client**: add **dark slate layout** with high-contrast safety yellow" — the design lockfile (`design/MASTER.md` §0, §2) bans both dark-mode-for-its-own-sake and any palette other than paper `#F3EFE7` + ink `#1C1915`, and Art. X forbids the Lovable client from owning the visual system
- T13–T15 are eval tasks; T15 re-specifies `/eval` rendering that Phase 0 already ships

Sitting 9 saw this and mandated "Phase 0 tasks = done in `app/`. Tuesday starts T12" — the fix was written into the *sitting*, and the affected `tasks.md` files were **not** regenerated. A coding agent reading `tasks.md` today will rebuild the desk.

**Fix pattern for Courserefresh:** tasks are generated *from* the AC traceability matrix; every task carries a `state` (`done-in-harness | todo | cut`) and a machine-checkable "files touched" list. A lint test fails if a task touches a path that another task already marks done.

### H4 — No traceability: acceptance criteria are testable *in principle* and untested *in fact* (severity: high)

Art. IX.2: "Acceptance criteria are testable without a pitch deck." Yet nothing in the repo maps an AC to a test, a fixture, or a receipt field. Consequences found:

- `app/evals/menumind/gold.jsonl` contains one injection row; MenuMind US-4 asserts `injection confidence ≥ 0.95` — no test asserts the threshold, and no `0.95` calibration exists.
- MenuMind US-3's Disabled-Publish button is a UI AC with no automated check (no test for `app/web/templates/home.html`).
- Exhibit US-4's `GET /exhibit/{job_id}` "non-empty `art14_review`" has no test in `app/tests/`.

**Fix pattern for Courserefresh:** `TRACEABILITY.md` with one row per AC: `AC id → fixture id(s) → command → observable (receipt field / file / HTTP response) → last verified`. Ships with the spec, not with the code.

### H5 — The review ritual is excellent; the *implementation* of the review's own output is partial (severity: process)

Sitting 9 flagged "MenuMind: Plan says red `unknown` chips → MASTER says yellow + ink + the word UNKNOWN. That is a fail." The `plan.md` and `spec.md` were corrected; `tasks.md` T12 was left with **"dark slate layout"**. So the same error survived in a third file after being explicitly declared a fail. The process has no "amendment applied and verified" step.

**Fix pattern for Courserefresh:** every review produces a numbered change list (`F-##`), and the amendment log is a table with `finding → file → exact change → verification command → result`. A finding is not closed until the command is pasted.

### H6 — Gold-set quality is asserted, never *adjudicated* (severity: medium-high)

Art. III mentions "including traps", and `build-weekend/marketmind/checklists.md` names a 9-fixture gold set with "6 hostile of 9" honesty. But no spec says:
who labels, what the labelling rules are, how disagreements are resolved, what the expected-action vocabulary is, or how the gold set is versioned. `app/evals/*/gold.jsonl` are committed without a schema or a revision id.

**Fix pattern for Courserefresh:** `specs/shared/eval.md` — labelling protocol, adjudication rule (two labellers, third breaks ties; each row carries `label_author`, `adjudicated_by`, `expected_action`), `gold_version`, and a rule that any row added after the freeze requires a spec amendment.

### H7 — No data model and no interface contracts (severity: high for agent-builds)

`shared/harness.md` says "models emit probabilities; pure Python evaluates rules", and the product specs use primitives named `Choice | Score | Noul`. Nowhere in the repo are these primitives defined (arity, domains, coercion on invented labels, serialisation). Likewise there is no HTTP surface contract, no error taxonomy, no CLI contract. `app/harness/types.py` exists, so the *implementation* defines the interface — backwards for a spec-first repo.

**Fix pattern for Courserefresh:** `data-model.md` (every object, every field, every coercion rule, every closed set) and `interfaces.md` (HTTP routes, CLI commands, n8n node contracts, error codes, idempotency) *before* code.

### H8 — Lifecycle is missing: no rollback, no revert, no retention, no sunset (severity: high for this idea in particular)

There is a rule for *acting* (fail-closed), a rule for *receipts*, and a rule for *dissent* — but no article for **undo**. MarketMind's audit (C5) had to discover in code review that receipts were overwritten per run (`open("w")`). An autonomous system that edits published artifacts needs a rollback contract, version pins, and a retention statement. Courserefresh would inherit exactly this hole and it is a *worse* hole for a product whose entire promise is "versions the change".

**Fix pattern for Courserefresh:** `revert` is a first-class action; every publish receipt carries the falsification condition that authorises its own auto-revert; previous version id is mandatory; retention and deletion are specified (learner data, source snapshots, receipts).

### H9 — Cross-file duplication with silent drift (severity: medium)

"Model roster", "5-phase pipeline", and the Mermaid diagram are repeated in `shared/harness.md`, `README.md`, and all four product specs. Observed drift: `shared/harness.md` says 26×, MenuMind says 30×, ListGuard says 26× vs GPT-4o, README says "0% hallucinations". Duplication is fine for readability; duplication *without a single source of truth and a drift check* is a defect. There is no CHANGELOG for spec versions (constitution is v3.1; product specs are unversioned).

**Fix pattern for Courserefresh:** one canonical definition per concept with an `x-ref`-style pointer from the copies; every spec file carries `Version` + `Last amended` + `Amends` fields; a drift test asserts the invariant lines (e.g. the action enum) are byte-identical across files.

### H10 — Security model is strong, but security *tests* weren't shipped in the same directory as the specs (severity: medium)

`specs/security/owasp-threat-model.md` has 179 lines and a §10 test list; `app/tests/` has 11 files, and there is **no `test_security.py`**, `redact.py` is referenced by two test files only in passing, and no test asserts "never fetch a user-supplied URL". The controls are real in the codebase (intake hashing, budgets); the *mapping* from the threat model to a green test is not.

**Fix pattern for Courserefresh:** `specs/security/threat-model.md` §N enumerates numbered tests; `app/tests/test_threat_model.py` contains one test per numbered item, named `test_TM07_...` so a reviewer can check the mapping mechanically.

### H11 — Repo hygiene contradicts its own rules, and artefacts are committed (severity: medium)

`app/.gitignore` correctly lists `*.egg-info/`, `evals/*/last_report.json`, `uploads/*`. Nonetheless `git ls-files` shows committed:

```
app/accel_harness.egg-info/PKG-INFO, SOURCES.txt, dependency_links.txt, requires.txt, top_level.txt
app/evals/receipts.sqlite
app/evals/spans.jsonl
```

Ignore rules do not untrack what was already added. The same class of defect was found and fixed in the sibling project (`build-weekend/AUDIT.md` C1 — an anchored `.gitignore` that never matched the real path). Courserefresh inherits the lesson, not the debt: ignore rules land **before** the first commit of `out/` and `*.sqlite`, and a hygiene check is part of the verification battery.

### H12 — "Proven in real use" has no evidence schema (severity: medium; directly costs 25% of a hackathon score)

`build-weekend` does this properly (`checklists.md` §3 capture-on list, `AUDIT.md` verification battery, `M0-REPORT.md`). `specs/` does not: no run-log format, no nightly-run checklist, no "what a good receipt looks like" example, no definition of "unattended". An agent asked to produce the overnight proof has no template to satisfy.

**Fix pattern for Courserefresh:** `EVIDENCE.md` — the exact run-log schema, the capture list, the hero-run checklist, the fallback ladder (replay labelled as replay), and three worked example receipts (clean publish, refusal, auto-revert).

### H13 — Documentation assumes a live human who knows the event (severity: low-medium)

`specs/README.md` references "the Monday 18:00 table" and "T12" as if the reader has the calendar in their head; `plan.md` files reference dates without a day-label convention; the *deadline* appears in some files and not others. An agent reading a stale clone cannot tell whether a date is past.

**Fix pattern for Courserefresh:** D-labels (`D-3 kickoff prep`, `D1 build`, `D2 submit 15:00`) as the primary time axis, dates only in `kickoff/PREREGISTRATION.md`, and a `TIME-NOW` block at the top of `tasks.md` that must be updated at every session start.

### H14 — Missing artefacts a gold-standard package needs (severity: structural)

Not present anywhere in `4prd/specs/`, all of which a Courserefresh-calibre package must carry:

1. `kickoff/PREREGISTRATION.md` — hypotheses frozen *before* the run (exists only in the sibling project)
2. `WIRING.md` — keys, accounts, account-warming, smoke-test procedure
3. `HUMAN-PLAYBOOK.md` — the steps code cannot do, with time estimates
4. `VIDEO-SHOTLIST.md` — a production plan, not just a script
5. `TRACEABILITY.md` — AC → fixture → test → receipt → video beat
6. `RECEIPTS.md` / claims register — numbers with provenance
7. `OPERATIONS.md` — runbook, kill switch, budgets, on-call, degraded modes
8. `AMENDMENTS.md` — spec version history (the constitution has a version; the trees do not)
9. Cost model — €/change, €/night, TF price table with provenance
10. Sunset/exit criteria — what happens to learners, data, and the course when the project stops

---

## 3. Cross-examination — six clashes the panel could not resolve by politeness

### ⚔️ Clash 1 — "The constitution is the best artefact in the repo" vs "the constitution is already fiction" *(Nora vs Sofia)*

> **Nora:** Article III's floor is the constitution's spine. Violating it in three of four products is not a rounding error; it means the document is decorative where it is most specific.
> **Sofia:** I said this in the sibling project: "I will not sign n=12." The panel's answer there was to *author fixtures in the spec before the day*, so the day only *runs* them. `4prd` never applied that remedy to its own trees. My position: a floor must be **enforced by a test that reads the JSONL and fails**, or it is a wish.
> **Resolution:** Courserefresh's floor is enforced by `test_gold_floor.py` (reads the file, counts rows, checks label coverage) and the constitution states the **legal degrade** (`n=<actual>`, no advantage claim, `unmeasured` for unsupported columns).

### ⚔️ Clash 2 — "Port the sittings ritual" vs "the sittings caused the drift" *(Priya vs Kenji)*

> **Priya:** The sittings are why the repo is credible: dissent preserved, change lists explicit, judges named. Copy it.
> **Kenji:** The sittings are *also* where a constitution article got quietly softened (H1), where a fail (H5) was declared and left in a third file, and where the two most important numbers in the pitch (26×, 30×) were never reconciled (H2). The ritual is only as good as the closing loop.
> **Resolution (Priya, conceded):** the ritual stays; a **closure step is added**: every sitting ends with an `AMENDMENTS` table and a *command* per row. A finding with no command is `open`, visibly.

### ⚔️ Clash 3 — "Three columns is enough" vs "three columns hides the only failure that matters" *(Sofia vs Ingrid)*

> **Sofia:** Proprietary wrapper vs vanilla model vs ours is the honest benchmark. Ship it.
> **Ingrid:** For a *course*, the interesting metric is not only "did the rewrite match the gold label" but "did the learner learn more, and did the rewrite not break the ones it didn't touch". Your three columns measure the *system's* answer; they say nothing about *learning*. And a quiz-score delta with n=4 is not evidence.
> **Resolution:** two eval layers, never conflated: **(E1) decision eval** (3 columns, system metrics, n≥40) and **(E2) learner eval** (pre-registered, cohort ids hashed, `n<5 ⇒ unmeasured`, no claim of efficacy, revert gate is mechanical rather than statistical bravado). The video shows E1's table as a *sentence* and E2 as a *receipt*.

### ⚔️ Clash 4 — "Rollback is a feature" vs "rollback is a *control*" *(Amara vs Rhea)*

> **Amara:** A course that rewrites itself without a diff and a restore point is not version control, it is vandalism with a changelog. Previous-version id must be mandatory in the publish receipt.
> **Rhea:** Stronger: the revert must be *pre-authorised at publish time*. If the publish receipt doesn't state the falsification condition, the system has no right to revert, because "we improved it" is unfalsifiable after the fact. Revert without a pre-registered gate is just a second opinion.
> **Resolution:** adopted verbatim as the **Falsification Clause**: no publish without a `revert_gate` in its receipt; no revert without a satisfied gate; no revert without `previous_version_id`.

### ⚔️ Clash 5 — "Naming a real learner is the 25%" vs "naming a real learner is a consent incident" *(Priya vs Rhea & Tomás)*

> **Priya:** Criterion 2 is 25% and says *proven in real use*. A cohort of three named hackathon participants with real quiz records is the strongest proof on the board.
> **Rhea:** Then the data is personal data. Consent must be written per-learner, purpose-bound, revocable, deleted on request, and the *published* surfaces must show hashed handles plus aggregate counts only.
> **Tomás:** And the notification must be honest about what it is: *"your course changed; here is the diff; here is why"* — never *"we personally improved your learning"*.
> **Resolution:** the **Named Learner rule**: the submission may name **one** consenting learner (name + role, written consent, revocable) exactly as `4prd` names a "named human"; all other learners are `learner:<hash[:8]>`; every cohort-surface number is `n`-qualified; deletion request honoured within 24 h and evidenced by a receipt.

### ⚔️ Clash 6 — "Copy `4prd`'s harness wholesale" vs "the harness has no undo, no contracts, no evidence schema" *(Wei vs Nora)*

> **Wei:** The harness is 73 lines and defines phases and components; it is a good skeleton but not a runtime contract. Copying it verbatim imports H7, H8, H12.
> **Nora:** Copy the *discipline* (phases, closed sets, receipts, fail-closed, design lockfile) and write the four missing contracts: data model, interfaces, operations, evidence.
> **Resolution:** Courserefresh's `shared/harness.md` is a **6-phase loop** (Notice → Verify → Decide → Act → Learn → Report) plus four sibling contracts. Nothing is "already in `app/`"; the app is generated from the contracts, and a `test_contracts.py` checks that the code's enums equal the spec's enums.

---

## 4. Scorecard — is this a gold standard to copy?

| Pillar | Score | One line |
|---|---|---|
| **Spec structure & separation** | **A** | Constitution / harness / spec / plan / tasks / lockfiles is the right shape; copy it. |
| **Governance & policy-in-code** | **A** | The strongest part of the repo; a hackathon submission with receipts is rare. |
| **Review process & preserved dissent** | **A−** | Excellent ritual; the closing loop leaks (H1, H5). |
| **Security model** | **B+** | Strong threat model, real controls, weak threat-model→test mapping (H10). |
| **Eval honesty** | **C+** | Right *values*, wrong *numbers*: unmeasured claims presented as findings, comparator drift, one floor violated three times (H2). |
| **Contract completeness (data/interface/ops)** | **D+** | Absent; the implementation is the spec (H7, H8, H12). |
| **Traceability (AC → test → receipt)** | **D** | Absent; "testable without a pitch deck" is aspirational (H4). |
| **Repo hygiene / reproducibility** | **C−** | Build metadata and runtime DB committed; 71/71 unverifiable in place (H11). |
| **Overall as a template** | **A− (shape) · C (enforcement)** | Copy the shape, add the four missing contracts, and make every promise machine-checkable. |

---

## 5. Binding port list for Courserefresh

**Port (unchanged in spirit):** G1 constitution + amendment rule · G2 spec/plan/tasks · G3 policy-in-code + closed sets · G4 hostile-first · G5 receipts with stored `actor` · G6 design lockfile with banned list · G7 sittings with dissent + binding change lists · G8 ORIGIN/KILLED memory · G9 walking skeleton first + a named warden with veto · G10 claims audit + kiss-of-death list · G11 agent-operability docs · G12 threat model with numbered tests.

**Add (the four missing contracts + two enforcement mechanisms):**

| # | Artefact | Kills which hole |
|---|---|---|
| A1 | `shared/data-model.md` — objects, enums, coercion, ids, versioning | H7 |
| A2 | `shared/interfaces.md` — HTTP/CLI/n8n contracts, error taxonomy, idempotency | H7 |
| A3 | `shared/eval.md` + `test_gold_floor.py` — labelling, adjudication, floor enforced by test | H1, H6 |
| A4 | `OPERATIONS.md` — runbook, kill switch, budgets, degraded modes, retention, sunset | H8, H14 |
| A5 | `TRACEABILITY.md` + `JUDGING-MAP.md` — AC → fixture → command → receipt → video beat | H4, H12 |
| A6 | `RECEIPTS.md` + `test_claims.py` — every published number has a provenance row | H2 |
| A7 | `AMENDMENTS.md` + closure rule: a finding is open until its verification command is pasted | H5, H9 |
| A8 | `EVIDENCE.md` — run-log schema, capture list, hero-run checklist, labelled replay ladder | H12 |
| A9 | `kickoff/PREREGISTRATION.md`, `WIRING.md`, `HUMAN-PLAYBOOK.md`, `VIDEO-SHOTLIST.md` | H14, H13 |
| A10 | `test_threat_model.py` — one test per numbered threat-model item | H10 |
| A11 | Hygiene gate: `out/`, `*.sqlite`, `*.egg-info/` ignored **before** first artifact commit; `test_hygiene.py` | H11 |
| A12 | D-label time axis; dates only in `kickoff/PREREGISTRATION.md` | H13 |

**Refuse:** four products in one repo · a floor that a meeting can lower · "unmeasured" numbers presented as findings · LoRA/vector-store/browser-agent surface without a receipt · any published learner-identifying data without written consent · gate work before the loop closes · asking the design lockfile for permission to look modern.

---

## 6. What this sitting hands to the builder agents

1. `specs/constitution.md` — the non-negotiables, including the **claims register**, the **Falsification Clause**, the **Named Learner rule**, and the **floor + legal degrade**.
2. `specs/shared/{harness,data-model,interfaces,eval}.md` — the runtime contracts (the four things `4prd` was missing).
3. `specs/courserefresh/{spec,plan,tasks,BUILD,ORIGIN}.md` + `checklists.md` + `VIDEO-SHOTLIST.md` + `WIRING.md` + `EVIDENCE.md` + `TRACEABILITY.md` + `JUDGING-MAP.md` + `RECEIPTS.md` + `kickoff/*` + `skin/*`.
4. Sittings `02`–`04` in this folder: judges review the built package, the builder agents answer with a real diff, and the audit closes with pasted command output.

*Proceedings of Sitting 0 closed. Findings H1–H14 are binding inputs to the constitution. A finding is not closed until its verification command has been run and pasted.*
