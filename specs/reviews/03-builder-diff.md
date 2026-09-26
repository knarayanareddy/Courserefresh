# Sitting 03 — builder diff: what was ported from review 01, and what was not
`Version 1.0 · Last amended D-0 · Amends: AMENDMENTS.md 1.1 (F-rows)`

Review 01 ended with a binding port list (A1–A12) and fourteen holes (H1–H14). This sitting is the
build-side answer, item by item, with the file that now carries the obligation and the command that
proves it. Nothing here is aspirational prose: a row without a command is a hole (Art. XVI.3).

## 1. Port list vs the built package

| # | Promise (review 01) | Status | What carries it now |
|---|---|---|---|
| A1 | Data model with enums + coercion | **ported** | `shared/data-model.md` §4.1–4.4; `test_contracts.py` parses the enum tables and compares them to `skin/change_taxonomy.json` |
| A2 | Interface contracts (HTTP/CLI/n8n) + error taxonomy + idempotency | **ported (CLI/n8n), partial (HTTP)** | `shared/interfaces.md`; the CLI flags are checked against the skeleton by `test_contracts.py`; the console's POST routes are specified but not implemented (Phase 2, T21) |
| A3 | `shared/eval.md` + floor enforced by a test with a legal degrade | **ported** | `skin/gold.jsonl` (`gold-v0.3`, n=59) · `test_gold_floor.py` (8 checks) · `policy.py --eval` exits 0 |
| A4 | `OPERATIONS.md` — runbook, kill switch, budgets, retention, sunset | **ported (spec) / sim (code)** | `OPERATIONS.md`; `--pause`/`--resume` tested in `--selftest` (13/13) and by TM14; retention and sunset are paper until the live run |
| A5 | `TRACEABILITY.md` + `JUDGING-MAP.md`, AC → fixture → command | **ported** | 36 ACs with ids in `spec.md` §4; `test_contracts.py` fails in both directions |
| A6 | `RECEIPTS.md` + `test_claims.py` | **ported** | register v1.1 (measured where a command ran, `<placeholders>` where not); lint green over 56 numeric claims |
| A7 | `AMENDMENTS.md` + the closure rule, honoured | **ported, with self-correction** | F-01…F-16; F-01–F-12 were reverted to `open` in version 1.1 because `reviews/04` had not pasted output — the closure rule applies to the spec's own paperwork too (F-16 is that repair) |
| A8 | `EVIDENCE.md` — run-log schema, capture list, hero protocol, replay ladder | **ported** | `EVIDENCE.md` §1–5; §4 now has a labelled **sim** row from the D-0 run |
| A9 | Kickoff docs, wiring, visual lockfile, shot list | **ported** | `kickoff/{PREREGISTRATION,CONSENT,SOURCE-PLAN,LEARNER-PLAN}.md`, `WIRING.md`, `VIDEO-SHOTLIST.md`, `design/MASTER.md` |
| A10 | `test_threat_model.py` — one test per numbered threat | **ported** | TM01–TM18, 18/18 green against the frozen gold set, including the path-escape and host-spoof containment checks |
| A11 | Hygiene gate before the first artifact commit | **ported** | root `.gitignore` + `test_hygiene.py` (7 checks, including a working-tree sweep) |
| A12 | D-label time axis; dates only in the pre-registration | **ported and enforced** | `test_hygiene.py` fails on any `20\d\d-` date under `specs/` outside `PREREGISTRATION.md`; F-16 repaired F-11's self-referential grep |

## 2. Holes (H1–H14) vs the built package

| Hole | Closed by | Residual risk |
|---|---|---|
| H1 eval floor violated by own artifacts | `gold-v0.3` n=59; `test_gold_floor.py` fails below 40 and the eval exits non-zero | none at spec level; the *live* comparator column (a) stays `n/a` without a key |
| H2 unmeasured numbers asserted as facts | register v1.1 + `test_claims.py` (56 claims resolved, 0 bare) | the pitch must keep saying `unmeasured` where the value is not yet measured (J-06) |
| H3 tasks contradict Phase 0 | T06 corrected to `[~]`; Phase 1 marked `[~]` with the cut named; `test_contracts.py` now fails when a `[ ]` task names an existing path | the live tasks (T16–T22) are still `[ ]` by design until Phase 2 |
| H4 no traceability | 34 ids, both directions checked | AC-2.4's fixture (`cr-paywall-01`) exists in gold and in the loop's file? — **gold only**; the loop's fixture set carries the same traps in `01`–`10` numbering (see §3) |
| H5 review output implemented only in part | this sitting + `reviews/04` + `AMENDMENTS.md` | reviews are only as good as their pasted output — `reviews/04` §2 is that paste |
| H6 gold never adjudicated | per-row `label_author` + `label_notes`, frozen version id, floor test | the labeller is the author-agent, not an external expert — stated in `shared/eval.md` §2 |
| H7 no data model / interfaces | A1, A2 above | HTTP surface is specified, unimplemented |
| H8 no rollback/revert/retention/sunset | Art. XI + `revert_gate` on every publish + the night-2 revert firing end-to-end | live retention needs the console |
| H9 cross-file drift | `test_contracts.py` (enums, reason codes, rule order, AC ids, task hygiene, CLI flags) | rule *rationale* text still lives in three files; the normative order line is single-sourced |
| H10 security tests not shipped with specs | TM01–TM18, one per numbered item in `threat-model.md` §7 | the console-side TMs (CSP, token) are asserted at the function level, not through HTTP |
| H11 committed artifacts | `.gitignore` + `test_hygiene.py` working-tree sweep | nothing is committed yet; the sweep runs before any commit |
| H12 no evidence schema | `EVIDENCE.md` §1 schema + §4 register + replay ladder | the hero-run row is still empty until the live night |
| H13 documentation assumes a live human | D-label axis enforced; `AGENTS.md` gives an agent the read order; `app/check.sh` gives one command | the calendar (D1/D2) stays in `kickoff/PREREGISTRATION.md` only |
| H14 missing artefacts | A4, A8–A12: OPERATIONS, EVIDENCE, kickoff set, shot list, hygiene, `AGENTS.md` | `app/n8n/wf-cr-*` exports and the console are Phase 2 |

## 3. Deliberate deviations from the port list (with reasons)

1. **Fixture ids vs gold ids.** The loop's fixture for the labelled-seed rehearsal is `cr-seed-03`,
   because gold already uses `cr-seed-01` for a *different* row — the "seeded event misrepresented
   as upstream" trap (`ESCALATE(seeded_source_misrepresented)`). Reusing the id would have made two
   different scenarios share one name; `test_contracts.py` would not have caught it, but a human
   reading the receipts would have been misled.
2. **`--arm` became `--pause`/`--resume`; the labelled rehearsal is `--seed-demo`.** The hero run needs a freeze
   switch, not a second arming flag; the revert night is a *separate* run so the demo shows one
   publish, then one measured undo — not both in one breath.
3. **The digest renders only the current run's receipts.** Rendering the whole ledger made a
   second run's digest reprint the first run's refusals (a small lie in the most-read artifact).
4. **`test_gate_parity.py` is a Node script** (despite the `.py` suffix inherited from
   `harness.md` §10) because the JS node is what it must load; it shells out to the Python oracle.
5. **No `AGENT_BOOTSTRAP_PROMPT.md`** (T06 `[~]`): `AGENTS.md` covers the bootstrap, and a second
   prompt file is another surface to drift (H9).

## 4. What the builder did *not* do

- No live Apify actor runs, no n8n execution, no console, no real cohort: **Phase 2**.
- No cost measurement: `prices.json` values are `null` by design, receipts say `unmeasured (sim run)`.
- No claim that the 4 KB digest, the cadence, or `PA2 earned` are measured: they are contract-tested
  (`test_digest_fits_the_4kb_contract`) or printed as `unmeasured`.

**Verdict:** the spec-side obligations of review 01 are ported or explicitly cut; the live
obligations are Phase 2 and are listed in `tasks.md` as `[ ]`, not as done.
