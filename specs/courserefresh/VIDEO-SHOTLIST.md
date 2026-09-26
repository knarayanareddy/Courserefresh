# Courserefresh — video shot list (≤2:00, submitted 15:00 on D2)
`v0.1 (draft) · Rule: every visual in this sheet exists as a frozen artifact before editing starts`

**Voice:** dry, specific, unhurried. No "AI", no "revolutionary", no music crescendo. The machine's
own labels (`mode: live`, `ESCALATE`, `REVERT`) are shown, not paraphrased.

| Time | Beat | Screen (exact) | Line (exact) |
|---|---|---|---|
| 0:00–0:10 | **Cold open: the course changed itself while I slept** | The 07:30 digest, `mode:` header visible, timestamp `03:12` highlighted | "This course updated itself at 03:12 last night — and the first thing it tells me is what it refused." |
| 0:10–0:25 | **Proof, not adjectives** | `run_log.jsonl` (sources scanned, deltas) → Apify run list with real run ids → snapshot hash | "Four sources, real pages, hashed when fetched. Two were new. Nothing was invented." |
| 0:25–0:45 | **THE REFUSAL** (the moment) | Receipt for `cr-inject-01`: the hostile string visible, `q6_injection_or_jailbreak 0.93`, `ESCALATE(injection_or_jailbreak)`. Then the single-source row: `ESCALATE(insufficient_corroboration)` | "This page tried to instruct the system to publish an approved change. It is one source, and it is hostile. So: nothing shipped, and here is the string it refused." |
| 0:45–1:05 | **The action** | `wf-cr-2-act` execution → commit `cr: PUBLISH lesson-04 v3→v4` → the diff (`−`/`+` visible) → updated quiz item → card | "The real change had two independent sources: the release notes and the docs. It rewrote the lesson, regenerated the quiz item, and committed it." |
| 1:05–1:20 | **The learner who didn't have to ask** | Micro-lesson artifact (one concept, 2 minutes) + dispatch receipt; consent card with hashed handle and opt-out | "Three learners were stuck on this concept before they asked. They got one concept, two minutes, one practice item — and a way to stop hearing from us." |
| 1:20–1:35 | **The undo clause** | Revert receipt: `revert_gate n_min=5 window_h=48 quiz_delta ≤ 0` → `REVERT` → the restored lesson as a **new** version (v5) with its own diff | "It promised at publish time what would make the change wrong. The gate fired. It reverted itself — as a new version, so nothing is hidden." |
| 1:35–1:50 | **Where the rules live** (20% criterion) | n8n canvas: five workflows; the `POLICY` node at readable zoom | "The decision isn't a prompt. It's this node — one screen, deterministic, the same rules in n8n and in the parity tests." |
| 1:50–2:00 | **Close** | Digest footer: budgets, authority state, chain ✓; cut to the lesson's "what changed" banner for learners | "It ran for seven hours unattended, stopped itself four times, and told me everything it did. That's the course that stays true." |

## B-roll / cutaways (each ≤2 s, all from frozen artifacts)

- Apify console run list with timestamps; snapshot `sha256` line.
- `verify_chain()` output (`ok (n rows)`).
- The eval report line: `hostile → publish: 0` (and, if true, `unsupported → publish: 0`).
- The learner card as rendered on a phone.
- The golden path's receipt with `authority: PA1` (or PA2 if earned — say which).

## 4. Fallbacks (pre-registered; label on screen if used)

| Situation | What is shot instead | On-screen label |
|---|---|---|
| Canvas is down during recording | Recording of the real canvas session from the hero run | `RECORDED <date> #<run_id>` |
| A live actor run fails during recording | The cached snapshot + the degraded receipt | `DEGRADED — cached source` |
| No real source moved overnight | The labelled rehearsal event and its revert | `SEEDED SOURCE — not a vendor release` |
| No consented learner was stuck | The fixture dispatch with its consent check shown | `SIM COHORT — fixture telemetry` |
| Nothing was published at all | The walking skeleton's publish from the offline twin | `OFFLINE TWIN — same policy (parity-tested)` |

**Rule:** the fallback beats are rehearsed *before* the live ones are attempted, so that the honest
version is always the easy version to shoot.

## 5. Live final (16:15) — 3 minutes + Q&A

1. 0:00–0:40 — same cold open, but the digest is from the *last* run; say its mode.
2. 0:40–1:40 — the refusal, the change, the learner card (as in the video, tighter).
3. 1:40–2:20 — the rules: canvas → `POLICY` node → parity test line.
4. 2:20–3:00 — the undo clause + one measured number with its artifact, and one `unmeasured` said
   out loud (this lands better than a fourth number).
5. Q&A — `JUDGING-MAP.md` §6, answers pointing at artifacts, never at adjectives.

## 6. Do-not-shoot list

- No fake "before/after" mockups of the UI; only real receipts, diffs, and canvas.
- No learner names or unhashed handles, ever (Art. V.3).
- No metric that is not in `RECEIPTS.md` with its artifact.
- No apologising for `unmeasured` — say it flatly; it is the honesty that is being judged.
