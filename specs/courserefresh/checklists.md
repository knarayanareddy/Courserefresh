# Courserefresh — checklists (the gates, in the order they occur)
`v0.1 (draft) · A tick requires an artifact path; an unticked box is a cut, named in AMENDMENTS.md`

## §0 — Warden's M0 gate (sign before any M2 work)

| # | Check | Artifact |
|---|---|---|
| 0.1 | A change was published by the machine with a diff, a version, and a receipt | run log + `course/.../v4.md` |
| 0.2 | A hostile page was refused, with the string preserved and a reason code | receipt `injection_or_jailbreak` |
| 0.3 | A revert executed on a satisfied gate, as a new version | night-2 receipt + `v5.md` |
| 0.4 | A stuck learner signal dispatched a micro-lesson — or was refused for consent | dispatch receipt / `consent_missing` |
| 0.5 | The digest renders refusals first and fits 4 KB | `app/out/digest.md` |
| 0.6 | `sh app/check.sh` exits 0 | `app/out/evidence/battery.txt` |
| 0.7 | Nothing above needed a human to press a button mid-run | receipts `actor: system` |

Warden signs (name + D-label) in `reviews/04` §0. **Skip = veto.**

## §1 — Pre-live (D-1, before arming the overnight run)

| # | Check | Artifact |
|---|---|---|
| 1.1 | Actors pinned (id + build) and one real run id recorded | `WIRING.md` §1, §6 |
| 1.2 | Allowlist mirrored and hashed into the run header | `app/out/state/allowlist.json` |
| 1.3 | Models pinned; judge ≠ observe; judge never sees thresholds | `WIRING.md` §4 |
| 1.4 | Budgets set and printed in the run header | run log |
| 1.5 | Consent list frozen; handles hashed; opt-out link works (tested) | `kickoff/CONSENT.md` + test output |
| 1.6 | Kill switch tested in live mode (freeze → no writes → resume) | freeze receipts |
| 1.7 | Fallbacks rehearsed: actor fail → cached; canvas down → offline twin | `EVIDENCE.md` §5 |
| 1.8 | Evidence freezer dry-run: manifest hashes match artifacts | `app/out/evidence/<run_id>/MANIFEST.sha256` |

## §2 — Morphing the morning (D1)

| # | Check | Artifact |
|---|---|---|
| 2.1 | Digest read; every number traced to a receipt or `unmeasured` | digest + `RECEIPTS.md` |
| 2.2 | Escalation queue triaged: each row accepted/overridden/rejected **as a new receipt** | receipts `actor: human:<name>` |
| 2.3 | Gate states inspected; any `unmeasured` explained in the digest's next run | run log |
| 2.4 | Chain verified; coverage 100% | `--selftest` output |
| 2.5 | Any incident written to `OPERATIONS.md` §7 | incident row |

## §3 — Pre-submit (D2, before 15:00)

| # | Check | Artifact |
|---|---|---|
| 3.1 | Evidence frozen **before** any video edit; manifest hashes pasted into `EVIDENCE.md` §4 | manifest |
| 3.2 | Every number in the script appears in `RECEIPTS.md` (claims lint green) | `test_claims.py` output |
| 3.3 | Every sim/seeded/degraded artifact has its label; the plan to show it is in the shot list | `VIDEO-SHOTLIST.md` |
| 3.4 | Video ≤ 2:00, audio intelligible, first line says `mode`; upload tested | video file + upload log |
| 3.5 | Repo state: `bot/courserefresh` pushed, PR opened, `main` untouched | git log |
| 3.6 | `reviews/04` written: findings closed with pasted output or explicitly open | review doc |
| 3.7 | README's ten-minute path still works on a clean checkout | `sh app/check.sh` |

## §4 — Pre-record (the two-minute video)

| # | Check |
|---|---|
| 4.1 | Cold open states what it is: "This course updated itself overnight. Here is what it refused." |
| 4.2 | Refusal shown with the hostile/single-source quote visible and the reason code on screen |
| 4.3 | Real commit, real diff, real timestamp (not a mockup) |
| 4.4 | Stuck-learner card shown as the learner receives it (hashed handle, opt-out visible) |
| 4.5 | Revert shown with its gate metadata; if `unmeasured`, that word is on screen |
| 4.6 | n8n canvas + policy node on screen ≥6 s; Apify run list on screen ≥4 s |
| 4.7 | No adjective without an artifact; no number without a receipt row |
| 4.8 | Captions burned in; nothing important below 12 px on a phone |

## §5 — Q&A drill (before the live final)

| # | Question (from `JUDGING-MAP.md` §6) | Answered with |
|---|---|---|
| 5.1 | "Isn't this an LLM rewriting a doc?" | parity output + column (b) hostile→publish |
| 5.2 | "What if the source is wrong?" | corroboration rule + conflict row |
| 5.3 | "Who is responsible for the edit?" | commit + PR + authority ladder |
| 5.4 | "What if Apify/n8n dies on stage?" | pre-registered fallback ladder (labelled) |
| 5.5 | "Show me it learning" | gate state + revert/tuning receipts, or `unmeasured` |
| 5.6 | "Why will a course author pay?" | the 30-second story; the digest as the product |
| 5.7 | "What did you cut?" | `AMENDMENTS.md` cut list — answered without defensiveness |

## §6 — Post-event (handoff, day after)

| # | Check |
|---|---|
| 6.1 | `SUNSET` set (or schedules disabled) — the course is hand-maintained after today |
| 6.2 | Learner data deleted per Art. V.4 (only aggregates remain) |
| 6.3 | Repo tagged `d2-final`; evidence folder kept read-only |
| 6.4 | A one-page "what we would build next" written, with the *measured* gaps it would close |
