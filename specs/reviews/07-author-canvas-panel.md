# Review 07 — the Teacher/Author canvas, Tavily scope, and typed decisions (seat panel)

`D-0 · seats: T (teacher), AU (author / curriculum lead), ST (student advocate), UX, ART (Art. VI
claims auditor), SRE, N8N, TAVILY (evidence seat), JEV (typed decisions), COST · rule: a seat that
proposes a feature must name (a) the receipt it reads, (b) the check that fails if the feature breaks,
(c) what it would cost. Every finding below cites file:line or a command, because the one thing this
project refuses is an opinion with no artifact (Art. VI).`

**The brief (as asked).** Build a Teachers'/Author's canvas: the *before/after diff* beside the
*sources* and the *reasoning*, for the rows where confidence is not high, so a person can make an
informed decision. Review it. Also: Tavily alongside Apify for grounded research; JEV researched for
additive integration; and whatever complementary features the panel thinks this needs.

**Panel's answer in one line.** The canvas as *information* is already better than what most teaching
tools ship — every pixel of it is a receipt — but it was not a *decision* surface: nothing the
author did changed what the loop did next. That is the same defect the review found in the engine
(`REVIEW.md` F2), seen from the other side, and it was the panel's single blocking condition.

**Status (after the build).** C-01, C-02, C-03, C-04, C-06, C-07, TV-03, JV-02 and the label half of
JV-03 are **implemented and checked**; TV-02's *action* half (proposals from the canvas), C-05, C-08,
JV-05 and the calibration record are **open**, each with the check that will close it named in its
row. What the panel refused stays refused.

---

## 1. What the panel read (and what was measured, not remembered)

| Artifact | State the panel verified |
|---|---|
| `app/lib/canvas.py` | `build()` → `app/out/canvas.json` + `canvas.html`; per row: action, lesson + version pair, diff, source table (publisher · role · counted as a voice), quotes, plain-language reasons, flip analysis, provider confidences, author rulings |
| console | `GET /canvas` renders the same document on demand (`console.py:107`); `POST /canvas/decision` writes the ruling + a PA3 receipt (`console.py:210`) |
| live proof | `app/tests/test_live_modules.py` §12 — token 403, bad ruling 400, off-set reason code 400, ruling written, read back, row leaves `needs_review`; battery `sh app/check.sh` → **259 PASS, audit 29/29, exit 0** |
| hero run | `specs/evidence/cr-20260926-1726-793/` — 9 decisions (2 PUBLISH, 4 ESCALATE, 1 NO_CHANGE, 1 DISPATCH, 1 REVERT), queue = `rcpt-20-745-003` (`insufficient_corroboration`) + `rcpt-20-745-004` (`conflicting_evidence`) |
| `skin/thresholds.json` | `evidence.min_sources 2` · `source_agreement_min 0.5` · `quote_supported_min 0.8` · `budgets.digest_bytes 4096` · `budgets.tavily_credits_per_day 30` · `diff.max_lines 400` |
| `skin/sources.json` v1.2 | 6 Apify sources (roles · independence groups · HTTP fallback) + `tavily-discovery` (`fetch.kind: "tavily"`, cadence 120) |
| `policy.py:75,87,145` | `thresholds.evidence.discovery_roles` is recorded on the receipt and **never counted** — a discovery lead cannot become a voice by accident |
| `app/lib/jev.py`, `judge.py:154,202` | `CR_JUDGE_PROVIDER=jev` → `POST {base}/v1/systemone`; q1/q7 → `choice`, q2–q6 → `noul`; confidences recorded per question, unchanged answer contract |
| `grep -rn author_decisions app/` | read by `canvas.py` and the tests **only** — nothing in the decision path consults a ruling |

---

## 2. The canvas, judged seat by seat

### C-01 · **closed** · the ruling is a record, not an input *(raised by AU, seconded by T, SRE)*

The author can approve or reject a queued row; the write is honest (append-only, PA3, `human:author`)
and it is correctly shown back in the canvas. Then the next run does the same thing it would have done
anyway: `state/author_decisions.jsonl` is read by `canvas.py:346` and nowhere else. So "approve" on
`insufficient_corroboration` does not let the change publish, and "reject" does not stop it from being
re-proposed — which is what a teacher will believe they just did. `AMENDMENTS` D-22 and spec
AC-16.1 say the canvas decides; the same gap exists at engine level (`REVIEW.md` F2).

*Condition.* A ruling must bind the next cycle, bound to the evidence it was made about:

* `approve` → the change may publish with `authority: PA3`, `decided_by: human:author`, and the
  ruling's receipt id named on the publish receipt (Art. IX: a person decided);
* `reject` → the delta closes with the author's reason code and is not re-raised while the event's
  evidence hash is unchanged;
* any ruling is **stale** once the event's evidence hash changes — the row returns to the queue with
  "the evidence changed since your ruling" (otherwise an approval is a blank cheque).

*Amendment:* `D-32` (adopted) — an author ruling binds the cycle it was made about and expires when
the evidence it was made about changes.

*Built:* `app/lib/rulings.py` (evidence fingerprint · `plan()` · the withheld-delta queue that keeps a
refused delta with its patch) + the engine's replay/resolution in `run_walking_skeleton.py:run()`, and
`human_signoff` in the closed vocabulary. *Proof:* `test_live_modules.py` §13 — approve → the next
cycle publishes at PA3 (`decided_by: human:author`, `human_signoff`, new version on disk); reject →
`NO_CHANGE` with the author's reason code; moved evidence → `stale`, the machine decides and the row
returns to the queue; a ruling on a machine guarantee is refused (`not_approvable`).

### C-02 · **closed** · the ruling has no UI *(UX, T)*

`grep -c "<form\|<input" app/lib/canvas.py` → `0`. The page the feature exists for cannot record a
decision; the only writer is an API call with `X-CR-Token`. A teacher will not "just POST".

*Built:* `render_html(doc, action_url=…)` renders a form per actionable row (Approve/Reject, the
closed reason select with plain-language labels, an optional note); the console injects the form *and*
the hidden token only for a request that already proved it has one, validates a form post exactly like
a JSON one, and answers it with a 303 back to the canvas. The CLI-written `canvas.html` stays
read-only. *Proof:* §13 — form present and no `<script>`; an unauthorised reader gets a page with no
token in it; no token on a form post → 403; bad reason code → 400; good → 303 + stored + read back.

### C-03 · **medium** · the canvas shows less than the receipt chain allows, silently *(ART)*

The diff is cut at 1500 characters (`canvas.py:469`) while the rulebook's own diff budget is 400 lines
(`thresholds.diff.max_lines`), and the quotes are cut at 220 characters. Truncation is fine; *silent*
truncation is a claim that the rest does not exist.

*Built:* the diff read cap is 20 000 bytes, full diffs render for queued rows, and every rendered diff
that was cut prints `showing N of M bytes` with the artifact path. *Proof:* §12.

### C-04 · **medium** · a teacher cannot tell which run they are reading *(SRE)*

`/canvas` rebuilds from the live `receipts.jsonl` on every GET (good: no stale page) but the page has
no run id, no receipt count, no build time. With `app/out/` accumulating across runs, "the canvas" is
ambiguous the moment it is screenshotted into a review.

*Built:* `provenance {run_id, mode, receipts, policy, built_at}` in the JSON and the same line on the
page. *Proof:* §12.

### C-05 · **open** · the queue is not ordered by consequence *(T, AU)*

Ordering today is "queued first, then ESCALATE" — defensible, but a quiz item that changes what
learners are assessed on sits at the same rank as a typo in a docs sentence. The two hero rows happen
to be right; the rule is not written down.

*Open.* The sort is still queued-first, then ESCALATE. Consequence ordering needs the assessment flag
carried onto the canvas row. *Closing check:* two queued rows, one touching `quizzes/…` — the quiz row
renders first.

### C-06 · **low** · "robust" overstates what was measured *(ART)*

When no single answer flips the decision the page says "Robust: no single answer flips this decision
(… margin inside the scan); judge confidence unmeasured". True inside the scan's step size, but the
step is 0.01 and the scan bounds are ±0.5 (`canvas.py:flip_analysis`) — a decision can be fragile at
±0.6 and the page will still say robust.

*Built:* the row says `No flip found in either direction, up to ±0.5 (step 0.01)` and claims nothing
outside that interval. *Proof:* §12.

### C-07 · **low** · the page never names a learner — keep it that way, and prove it *(ST)*

The canvas renders aggregate counts only; no handle, hashed or otherwise, appears. The ST seat's
condition is that this becomes a *checked* property, not an accident: a battery check over
`canvas.html` + `canvas.json` that fails on `learner:`-prefixed strings or on any string matching the
handle regex.

### C-08 · **low** · the author's most common real question has no verb *(AU)*

"This published change is wrong — pull it." There is no revert ruling; the revert path exists in the
engine (`revert_gate_satisfied`) but is cohort-gated (`n_min 5`, 48 h, `quiz_delta ≤ 0`), which is the
right gate for the machine and the wrong one for a human. A PA3 revert needs no cohort: it needs a
reason code and a receipt.

*Open.* Approve and reject are wired; a human revert needs a restore target (the receipt's artifact
already carries `previous_version`) and a co-sign rule for assessment items. *Closing check:* a
`revert` ruling on a published row produces a REVERT receipt at PA3.

---

## 3. Tavily, judged (the panel verified rather than assumed)

`TV-01 · the two rules that matter are already in the code.` Discovery output is recorded on the
receipt with `discovery_roles` and **never counted** as an independent voice (`policy.py:75,87,145`);
the spend lines already to-day (`tavily_credits_per_day 30`, `run_live.py:233`) and a hold is a
receipted refusal, not a crash (`tavily_budget_hold`, `run_live.py:171`). The panel's Tavily seat
signed this off as **ship** — with the three conditions below.

*TV-02 · half closed · a lead that is allowlisted but untracked is the valuable output, and it used to
die in a log line.* Closed half: the lead is surfaced in the digest (`source gaps found by discovery
(n, not counted as voices)`), `tavily-discovery` is a first-class entry in `skin/sources.json` with its
own credit budget, and the run records which source produced the gap. Open half — the action: leads
should land as a canvas queue row ("proposed source — add to the watchlist?") writing
`state/source_proposals.jsonl`, with the add staying a PA3 human edit (Art. XIV.1 — a model never
edits the allowlist). *Closing check:* a fixture lead → a proposal row → a PA3 add.
This remains the complementary feature with the best ratio in the whole review.

*TV-03 · closed · snippets are third-party text and must never be quoted as if fetched.* The engine's
rule is that an anchor quote comes from allowlisted, fetched content. A Tavily snippet is a search
result: label it `untrusted/discovery` in the canvas and the JSON, and let the existing
injection screen see it. *Built/checked:* discovery snapshots never become decision events, and §11
asserts that no receipt's `quotes` names a discovery source and no receipt's `sources` carries
`role: discovery`.

*TV-04 · low · keep Tavily out of the n8n exports until parity can cover it.* The exports are pinned
byte-for-byte against `policy_node.js` and the six workflow shapes; a discovery node in `wf-cr-0`
would need its own ONCE guard, budget node and parity test. The panel would rather ship discovery in
the Python loop only (report-only in n8n) than weaken the parity story for a log line.

---

## 4. JEV, judged

`JV-01 · verified: JEV's output is policed, and by the same gate as any other provider.` `normalise()`
copies what JEV returned; `validate_answers` (`judge.py:296–316`) enforces the closed option set
(`not_in_closed_set`), the unit interval, and completeness — a malformed or partial answer fails the
judgement closed with `unknown_state`, which the policy already treats as a refusal to publish. The
`choice: "x"` case is exercised in the live tests.

*JV-02 · closed.* §10 now answers a JEV call with an out-of-set `choice` (`catastrophic`) and a `noul`
of `1.4`, and asserts the judgement fails closed with `unknown_state` — the same gate every other
provider passes through.

*JV-03 · label closed / record open.* Built: the canvas prints `Judge confidence (predicted)` with
`calibration: unmeasured` beside it, and the JSON carries `"calibration": "unmeasured"`. Open: the
calibration record itself (n ≥ 20 published decisions with an observed outcome). Until it exists, no
page may turn those numbers into an accuracy claim (Art. VI). *Closing check:* the calibration file
exists and the page prints the measured rate instead of `unmeasured`.

*JV-04 · low · alternate hosts are a feature, not a hack.* `CR_JEV_BASE_URL` already accepts the
OpenRouter / requesty / rout.my forms; the panel notes the keyless local JEV servers
(`githubnext/localjev`, `amithgc/local-jev`) as the way to exercise this path in CI without
credentials — the same roll own. Document it in `SETUP.md` (already: the trio is listed) and add a
fixture replay so the adapter is tested with no network at all.

*JV-05 · refused: a `score` question for "materiality".* JEV supports `score`; the repo's seven
questions are closed on purpose and the materiality decision belongs to the rulebook, not to a
probability-weighted average. The panel refuses to add a question just because the provider has the
type (Art. III: the model answers, the code decides).

---

## 5. Complementary features the panel wants (ranked by ratio)

| # | Feature | Why it is the missing half | Owner seat | Proof |
|---|---|---|---|---|
| 1 | **Rulings that bind, and expire with the evidence** (C-01, D-32 proposed) | without it the canvas informs and changes nothing | AU + SRE | live-test: approve → publish with PA3 receipt; changed evidence → ruling ignored |
| 2 | **Ruling form on the page** (C-02) | a decision surface a teacher cannot submit into is a report | UX | HTTP test on the form POST (no JS) |
| 3 | **Source proposals from leads** (TV-02) | turns Tavily's advantage into a queue row instead of a log line | TAVILY + AU | fixture lead → `source_proposals.jsonl` → canvas row → PA3 add |
| 4 | **Two-key for assessment changes** (Art. IV) | a quiz rewrite that only one author approved is the highest-consequence row in the product | AU + T | check: assessment diff + single ruling → row stays queued |
| 5 | **Calibration record for typed decisions** (JV-03) | converts a model's confidence into a *measured* claim, or keeps saying `unmeasured` | ART | n ≥ 20 rows; report file regenerated by a tool |
| 6 | **Revert-from-canvas** (C-08) | the teacher's most common intervention has no verb today | AU | live-test: PA3 revert receipt, cohort gate bypassed for a human |
| 7 | **Queue-only / run-scoped view** (C-04) | 9 rows render in well under a second; the panel wants the boundary measured before someone points it at a term of receipts | SRE | timing check at n = 100/1000 receipts |
| 8 | **Time-to-decision receipt** ("the queue is short" is a claim) | `median time from queue to ruling`, `unmeasured` until n ≥ 20 rulings | ART | derived from ruling timestamps; a register row, not a vibe |

The panel explicitly keeps two things out of scope: any auto-approval after a timeout (a silence is
not a decision), and any learner-level detail on the canvas (aggregate counts only — C-07).

---

## 6. Votes

| Seat | Canvas | Tavily | JEV |
|---|---|---|---|
| T (teacher) | ship **with** C-01, C-02, C-05 | ship | ship |
| AU (author) | ship **with** C-01, C-08 | ship **with** TV-02 | ship |
| ST (student) | ship **with** C-07 checked | ship (no learner data involved) | ship |
| UX | ship **with** C-02, C-04 | ship | ship |
| ART | ship **with** C-03, C-06, JV-03 | ship **with** TV-03 | ship **with** JV-02, JV-04 |
| SRE | ship **with** C-01, C-04 | ship **with** TV-04 | ship |
| N8N | ship | ship (out of exports) | ship |
| TAVILY (evidence) | — | ship **with** TV-02 | — |
| JEV (typed decisions) | ship | — | ship |
| COST | ship | ship (30 credits/day + hold is receipted) | ship (usage.cost lands on the receipt) |

**Unanimous conditions.** (1) A ruling binds and expires (C-01/D-32). (2) No snippet is ever an
anchor (TV-03). (3) Model confidences are labelled predictions until calibration exists (JV-03).
(4) No learner-level data on the canvas, and that is checked (C-07). (5) "Teachers can review this"
stays `unmeasured` until feature 8 exists — the panel refuses to put a number on a queue nobody has
worked.

**Order of work (what the panel would build first).** C-01 + C-02 (the feature is half-built without
them) → TV-02 (the highest ratio) → JV-02/JV-03 (test + honesty label, cheap) → C-03…C-08 in rank
order. All of it lands on top of the existing review findings F1–F13, whose first-pass order the
review already set: F1 + F2 (the canvas path made real), then F3, then F10.

---

## 7. What the panel refused (and why)

* **Auto-approve after N hours.** A timeout is not a decision; it would make the loop's silence
  authoritative (Art. IX).
* **JEV as the renderer.** It generates no text — the panel's JEV seat was emphatic; the OBSERVE /
  rewrite model stays, and JEV stays additive.
* **A `score` question or a new threshold.** No question, no threshold, that the closed set does not
  need (Art. III/VI).
* **Tavily as an independent source.** One search API is one voice; discovery output is a lead and a
  queue row, never a second publisher (Art. III).
* **Learner-level detail in the canvas, even hashed.** Aggregate counts only (D-24).
* **A confidence cut-off ("queue everything below 0.7").** The queue is *fragility + fail-closed +
  disagreement + missing evidence*, which is why it is two rows and not nine.
