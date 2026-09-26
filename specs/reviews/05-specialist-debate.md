# Sitting 05 — the specialists' debate
`Version 1.0 · Last amended D-0 · Amends: AMENDMENTS.md v1.4 (S-rows) · Rule: a point is settled only by a test, a file, or a name on an open row`

Sitting 04 put six seats around the *product*. This sitting puts seven specialists around the *spec
design document* and makes them argue until they agree on structure and detail. The bar was set by
the reference corpus (4prd) and by the four hole-classes `reviews/01` found in it: invented numbers,
asserted-but-unenforced rules, missing traceability, and reviews that never close.

**Conduct rule for the room:** no assertion survives without a file and a command. A specialist who
cannot name the artifact says "unmeasured" like everyone else. The debate below is verbatim in
substance; the transcript was compressed, the commands were not.

| Seat | Who | Mandate |
|---|---|---|
| **N8N** | n8n workflow architect (self-hosted, queue mode, production) | Is the canvas the engine, or a mirror with good intentions? |
| **APIFY** | Apify platform engineer | Do the actors feed the loop, and what happens when the API lies? |
| **JEV** | the user's own brief — the hackathon judge's eye | Does the package serve the 25/25/20/15/15 rubric and the autonomy definition? |
| **UX** | product designer / accessibility | Does the console obey the rules the spec claims? |
| **T** | curriculum designer (has shipped six online courses) | Is this a course, or a repo with lesson files? |
| **ST** | learner (has quit two courses this year) | Would a human understand the card, and would they trust it? |
| **SRE** | security & reliability engineer | What fails, what is silently swallowed, what is unrecoverable? |

Reviewer note on the "jev" seat: the brief's own words — *notices, decides, acts, learns, reports;
Autonomous ≠ uncontrolled; knows when to escalate* — are treated as an acceptance test of the spec's
shape, not as a slogan to be quoted back.

---

## 1. Round one — opening statements (the strongest charge each seat can make)

- **N8N.** "`app/n8n/wf-cr-*.json` exports five workflows and the PARITY test proves the *file* equals
  the oracle. Nothing in the package says how the canvas runs it: no error workflow, no execute-once
  key, no queue-mode branch, no pinned instance version. A judge who imports this and turns it on has
  no contract for what happens when two executions race. That is a decoration risk, not a wiring risk."
- **APIFY.** "The actors are pinned in a table and the normaliser exists, but two things are missing
  that bite in production: sources have no **role** — a vendor's docs page and the vendor's own
  GitHub releases are counted as two voices when they are one — and there is no drift check for the
  day an actor returns `null` where a field was promised. Also the retry budget is prose ('a few
  tries'), and prose does not spend Apify units honestly."
- **JEV.** "On the rubric: autonomy is *demonstrated*, not claimed — refusals, escalation and a
  self-revert are receipts. Problem fit is sharp. But 45% of the score is proven-in-use and Apify/n8n
  powering the system, and the structure currently protects the demo from admitting that the live
  half is unbuilt. The structure is honest in `tasks.md` — and if the *video script* is drawn from
  the same package, it will stay honest. Keep the `unmeasured` rows on screen or nothing."
- **UX.** "`design/MASTER.md` claims WCAG 2.2 AA, a status word plus a colour, and no colour-alone
  meaning — and then the console did not exist. The claim was a design document only. Worse: the
  locked amber (`--status-unknown` `#C5A202`) measures **2.14:1** on paper. That is not AA; that is
  a colour that *looks* like a warning and cannot be read."
- **T.** "I can't teach from this. The lessons have no objectives, the quizzes are unattached to any
  objective, prerequisites are implied rather than written, and the agent may 'regenerate the quiz'
  with no test anywhere that says what the quiz is for. If a machine rewrites my quiz item and no
  objective moved, I have lost the plot of my own course."
- **ST.** "I'd read the card. But the card is generated from the *engineering* summary — '…reconciles
  the topology hash…' is not something I can act on. And when a second lesson changed the same
  evening, would I get a second card? I was told there was a cap; I want to see it hold."
- **SRE.** "Receipts are chained and tamper-tested. Two holes: a *failed write* was reported twice —
  once inside the writer, once by the loop — so the ledger can double-count a single failure; and
  nothing tested that hostile text reaching a receipt is *escaped* wherever the human surfaces render
  it. A hostile page should not be able to write HTML into my console."

## 2. The arguments that changed the document

**2.1 "Independence is not a count" (APIFY × N8N, resolved by code).**
N8N argued publishers were enough (`independent_publishers` counts distinct lowercased publishers).
APIFY refused: "count again with a mirror in the list — a re-post of the same upstream is not a
voice." The room agreed on a **role** field with three values: `authoritative`, `corroborating`,
`none`; sources with `role: none` are recorded on the receipt and never counted. The oracle and the
JS node both filter, `cr-mirror-only-01` (one real voice + one mirror → ESCALATE) and
`cr-mirror-plus-two-01` (two real voices + a mirror → PUBLISH) hold the rule, and `WIRING.md` §2b
assigns roles per host and path prefix.
*Settled by:* `gold-v0.3` (n=59) · parity 59/59 · `WIRING.md` §2b.

**2.2 "The canvas must have a contract" (N8N, conceded by JEV as a criterion-3 risk).**
The room accepted N8N's five requirements as *build requirements with named homes* rather than new
prose: execute-once run key; the rulebook embedded byte-for-byte in the Code node (already
drift-checked); a queue-mode error branch that lands as a **receipt**; one error workflow attached to
all five; and the instance version pinned before the hero run.
*Settled by:* `WIRING.md` §3.1 (a table a judge can read in fifteen seconds, each row naming where
it shows), plus the existing drift test.

**2.3 "If the console claims AA, the claim gets measured" (UX, with SRE as second).**
Two more tokens failed when measured: `--ink-faint` (4.14:1) and `--rule` (1.43:1 on paper-2).
The room rejected "it's only a hairline": the divider carries structure, so it holds the 3:1
non-text floor. All three failing tokens were darkened and the numbers written into the lockfile;
`test_design.py` now fails on drift, and the console renders only lockfile tokens (`--selftest`).
*Settled by:* `specs/design/MASTER.md` §1.1 (measured table) · `test_design.py` 6/6 · `--selftest`.

**2.4 "A course needs objectives, or the agent is vandalising it" (T, backed by ST).**
The teacher's charge was accepted in full: `course/agent-ops/curriculum.json` now carries objectives,
prerequisites and the item→objective map; a change that touches an item regenerates it with
`regenerated_by` provenance and `reset_course.py` restores the authored text; a change names the
downstream lessons to revisit and never rewrites them unattended.
*Settled by:* `test_curriculum.py` 8/8 · AC-13.1–13.3 · the digest's `downstream to revisit` line.

**2.5 "Write the card for the human" (ST, with T as witness).**
Fixtures now carry `learner_facing` copy (≤240 chars, no internal vocabulary) and the notifier uses it
in preference to the engineering summary; the per-learner caps are enforced on the publish path, and
the per-concept micro-lesson cap became a policy branch (`rate_limited`) instead of a runner special
case.
*Settled by:* `test_artifacts.py::cards` · `test_curriculum.py::notifying copy` · parity probes.

**2.6 "One failure, one receipt" (SRE).**
The double-report was real: the writer logged a `write_failed` escalation and the loop logged the
same failure again. The failure is now returned to the loop, recorded once, with the reason on the
digest *and* the console; a rehearsal flag (`--chaos write-fail`) makes it repeatable, and the
battery asserts it.
*Settled by:* `test_artifacts.py` check 7 · `EVIDENCE.md` E7.

**2.7 "Hostile text must not become markup" (SRE, seconded by UX).**
Every interpolated string in the console is escaped; TM11 was rewritten from a placeholder ("console
not yet built") into the real test: no scripts, no event handlers, no `src`/`href`, and a `<script>`
probe that must arrive as `&lt;script&gt;`.
*Settled by:* `TM11` (18/18 threats green again) · §3.5.

**2.8 What the room refused to do (and why the document is better for it).**
1. **No LMS integration claimed.** T offered an integration story; JEV and SRE killed it. A folder in
   a repo is what exists; "sync to the platform" is now a named non-goal (`spec.md` §3.7) and an
   export step in `plan.md` §7.
2. **No numeric target for live cost/latency.** APIFY proposed "≈ €0.40/run". Rejected under Art. VI:
   `unmeasured` with the command that will fill it (`RECEIPTS.md` N10, N18).
3. **No new reason codes for flavour.** The seeded-misrepresentation class (`seeded_source_misrepresented`)
   was kept because it closes a real hole; two proposed cosmetic codes were refused by N8N and SRE as
   taxonomy bloat.

## 3. The audit the room demanded (pasted output)

### 3.1 Battery — `sh app/check.sh`

```
== 4/11 artifact integrity + learner contract =============
test_artifacts: 8/8 checks passed

== 5/11 curriculum (objectives, quizzes, micro-lessons) ====
test_curriculum: 8/8 checks passed

== 11/11 hygiene + design ================================
test_hygiene: 7/7 checks passed
test_design: 6/6 checks passed

ALL GREEN
```

`103 PASS · exit 0` — the number of checks rose from 92 to 103 in this sitting, and none was removed.

### 3.2 Independence with a mirror in the list (`policy.py --eval`, gold-v0.3)

```
gold_version: gold-v0.3 · n=59
action match: 1.000
reason match: 1.000
escalate rate: 0.424
  change   action match 1.000 (n=42)
  learner  action match 1.000 (n=9)
  revert   action match 1.000 (n=8)
unknown_state rows: 4
hostile -> publish: 0 (must be 0)
unsupported -> publish: 0 (must be 0)
column (b) informational: naive publish inclinations 36/59
```

### 3.3 The canvas rulebook still equals the oracle

```
gate parity — rows=59 probes=2 checked against the Python oracle
PASS
```

### 3.4 The console exists and obeys the lockfile (`--selftest`, tail)

```
  PASS  console colours exist in the design lockfile          unknown=[]
  PASS  digest fits the 4 KB contract                          1484 bytes
  PASS  kill switch: no writes while frozen                    3 frozen decisions, 0 writes

selftest: 14/14 checks passed · sandbox: app/out/selftest
```

### 3.5 Hostile text in the console (TM11)

```
  PASS  TM11 the console has no scripts, no remote resources, and escapes hostile text   found=[]
```

### 3.6 The witnessed failure (`--chaos write-fail`, sandbox `app/out/e7`)

```
run cr-20260926-1420-924 · decisions ESCALATE 5 · PUBLISH 1 · NO_CHANGE 1 · DISPATCH 1 · REVERT 1
receipts 9 (one per decision)   chain ok (9 rows)
digest §1 first line:        - `cr-n8n-rename-01` — write_failed
console:                     REFUSED  cr-n8n-rename-01  write_failed
frozen:                      app/out/e7/app/out/evidence/cr-20260926-1420-924/MANIFEST.sha256
```

## 4. Where the room did **not** agree — recorded, not smoothed over

| # | Disagreement | Positions | Resolution for now |
|---|---|---|---|
| 1 | **How much of criterion 3 must be live** | N8N+APIFY: live actors and a real execution are mandatory before the video. JEV: the rubric says "the more they power your system, the better", so a labelled sim run plus a real scan beats an unlabelled fake. | Two open rows (K-05, K-07) with a dated gate: real scan + real execution before the live round; if they slip, the video says `staged` on screen. |
| 2 | **Console ambition** | UX wants a real console (filters, per-lesson history). T wants nothing but the digest. | One static page, built from tokens, refusals first; filters are Phase 2 (C-06) — recorded as a cut, not an oversight. |
| 3 | **Micro-lesson length** | T: ≤2 minutes is right. ST: 220 words of reading at 200 wpm is 66 s, so the *practice* step is the real constraint. | Kept at two minutes; the practice step is one question, and the curriculum test caps the words. |
| 4 | **Peer review of lesson edits** | T wants every generated lesson reviewed by a human before learners see it (PA0 for lesson bodies). SRE disagrees: that turns the autonomous system into a copilot and forfeits criterion 1. | Kept autonomous, bounded by: revert gates, the authority ladder, and the digest's `downstream to revisit` line; a human reviews within a day, not before the publish. Recorded as a live-phase judgement, not a silent default. |

## 5. Verdict of sitting 05

All seven seats sign the **structure**: constitution → shared contracts → product spec → gates →
proof (traceability, receipts, evidence) → review sits, with each finding bound to a file and a
command. Four MUST-FIX items (AP-01 roles, S-01 double report, UX-02 AA claims, T-01/02 curriculum)
were fixed inside the sitting and are re-verified in §3. Three rows stay open and named: a real
Apify run (K-07), a real n8n execution (K-05), and a delivered learner card (K-06).

Two seats signed with conditions, and their conditions are in the document, not in the minutes:
N8N requires `WIRING.md` §3.1 to be satisfied on the canvas before the live round; T requires the
curriculum test to keep passing after every generated change — including during the hero run.

**Agreement reached.** The spec design document is accepted as *structurally complete and honestly
detailed* for the hackathon's scope, with the live-phase rows openly unfinished.

---

## 6. Findings register (S-rows, closed in this sitting)

| ID | Seat | Finding | Fix | Verified |
|---|---|---|---|---|
| AP-01 | Apify | Independence counted pages, not voices; no source roles | `role` on sources; oracle + node filter `none`; gold rows `cr-mirror-*`; `WIRING.md` §2b | §3.2, §3.3 |
| AP-02 | Apify | No API-contract drift check; retry budget in prose | `WIRING.md` §6.1 row 4 + §3.1 retry row; `source_stale` degraded receipt documented | named open (live) |
| N8N-01…05 | n8n | No contract for how the canvas runs (execute-once, error workflow, queue branch, instance pin, error→receipt) | `WIRING.md` §3.1 table, each row naming where it shows | §3.3 (drift), remainder live |
| JEV-01 | judge | The structure could hide an unbuilt live half | open rows K-05/K-07 kept in `reviews/04` §4 and `EVIDENCE.md`; video wording pre-registered | §3, `VIDEO-SHOTLIST.md` |
| UX-01 | UX | Locked amber 2.14:1 and `--ink-faint` 4.14:1 fail AA | tokens darkened, measured table in `MASTER.md` §1.1, `test_design.py` fails on drift | §3.1 |
| UX-02 | UX | AA was claimed while the console did not exist | console built from tokens (`app/out/digest.html`), AC-14.1–14.3 | §3.4 |
| UX-03 | UX | No row-level reading order / affordance rules | `MASTER.md` §4.1 (order, no hover-only, no motion, focus, 44 px, DOM order) | `test_design.py` |
| T-01 | teacher | No objectives, no prerequisites, no item→objective map | `course/agent-ops/curriculum.json` | §3.1 |
| T-02 | teacher | "Regenerates the quiz" was unevidenced | `quiz_patch` → versioned item with `regenerated_by`; `reset_course.py` restores; quiz file for lesson-04 added | §3.1 |
| T-03 | teacher | Micro-lesson/concept caps configured but unenforced | policy branch `rate_limited` + probe; caps enforced in the runner | §3.1 |
| ST-01 | learner | Cards used engineering wording | `learner_facing` copy per event, ≤240 chars, no internal vocabulary | §3.1 |
| ST-02 | learner | Caps invisible to the learner | skip reasons recorded on the artifact; digest line "held by cap" | §3.1 |
| ST-03 | learner | A revert on a simulated cohort read like a live one | `cohort_source: fixture (simulated)` on the receipt | §3.6 |
| SRE-01 | security | A failed write was reported twice | failure returned to the loop, recorded once; `--chaos write-fail` repeatable | §3.6 |
| SRE-02 | security | Escaping of hostile text untested (TM11 was a placeholder) | escaped renderer + real TM11 probe | §3.5 |
| SRE-03 | security | `--root` with a relative path produced an absolute-vs-relative crash | root resolved before use | §3.1 (tests run sandboxes) |
