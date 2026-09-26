# design/MASTER.md — the visual lockfile
`v0.1 (draft) · Depends on: constitution.md Art. XV · Owner: the build agent (acting as designer)`

Two surfaces, one mood: **paper and ink, not dashboard**. The product should look like a careful
lecturer annotated last night's page: quiet, textual, dated. It must not look like an AI product.

**Lockfile rule:** the tokens below are frozen at kickoff. Changing one is an `AMENDMENTS.md` row,
not a taste decision.

---

## 1. Tokens

```css
:root{
  --paper:#F3EFE7; --paper-2:#EAE4D8; --rule:#C9C0AE;
  --ink:#1C1915;   --ink-soft:#4A443A; --ink-faint:#7A7264;
  --accent:#6B4E2E;            /* margins, links, small marks */
  --status-publish:#3F5A2A;    /* olive  — a change shipped */
  --status-queue:#A15C07;      /* ochre  — drafted / awaiting human */
  --status-revert:#9B2C1F;     /* oxide  — undone, or refused */
  --status-nochange:#5C564C;   /* muted ink */
  --status-unknown:#C5A202;    /* signal yellow — unknown/unmeasured */
  --mark:rgba(197,162,2,.28);  /* highlight for quotes from sources */
  --radius:2px; --measure:68ch; --pad:var(--s4);
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px;
  --font-sans:"IBM Plex Sans",system-ui,sans-serif;
  --font-serif:"Source Serif 4",Georgia,serif;
  --font-mono:"IBM Plex Mono",ui-monospace,monospace;
}
```

**Banned, on sight:** purple/indigo gradients, glassmorphism, glow, sparkle icons, robot mascots,
"AI-powered" badges, drop shadows > 2px, inter (as a default), pill buttons, emoji as status,
animated counters, dark mode as a default, charts without a source line.

## 2. Type scale

| Role | Size/weight | Notes |
|---|---|---|
| Lesson body | 17/1.65 serif | 68ch measure; sources block in sans 13px |
| Diff | 14/1.5 mono | `−`/`+` gutters; a change may never be signalled by colour alone |
| Console titles | 13px sans, letterspaced +0.04em, uppercase | dates in mono, `YYYY.MM.DD` |
| Digest | 15/1.6 sans, refusals in serif italic | the digest is read, not scanned |
| Status word | 12px sans uppercase | always the *word* (`PUBLISHED`, `REVERTED`, `REFUSED`) + colour |

## 3. Author console (instrument)

Layout: a single column, max 1100px, `--paper` background, 1px `--rule` separators, no cards with
shadows. Left rail (collapsible) = runs; main = the digest; right rail = receipts for the selected
run. Components: **run header** (mode · run_id · attended · cadence · budgets used), **refusal
list** (first, each with reason code + link), **change list** (lesson, `v3→v4`, diff link, gate),
**learner panel** (cohort n, window, gate state, `unmeasured` badge where true), **discipline
strip** (chain ✓, receipt coverage, `unmeasured` list), **eval page** (three columns, floor badge,
`gold_version`, hostile/unsupported rows highlighted). Every number is a link to its receipt.

## 4. Learner card (three lines)

```
Lesson 4 changed (v3 → v4) · 2026.09.26
Why it matters: n8n 1.85 renames the setting this lesson teaches.
What to do: the old name still works until 1.86; update your flows by then. Wrong? Tell us.
[See the diff]   [Stop updates]
```

Rules: no greeting theatre, no "Hope you're well", no AI attribution, no tracking pixels besides
the click that counts as "seen". Plain-text version is the canonical one; HTML must not add layout
that changes meaning. Accessibility: contrast ≥ 4.5:1 on paper, focus visible, links underlined,
`prefers-reduced-motion` respected (no motion by default anyway).

## 5. The policy node on canvas (a design requirement)

The `POLICY` node must be readable at 100% zoom in a 1080p screen recording: ≤ 24 lines of code
visible, rule names on their own lines (`R2 injection → ESCALATE`), thresholds imported from a
`THRESHOLDS` node, and a comment block at the top with the rule order. If it needs scrolling to
answer "where are the rules?", it is not done.

## 6. Accessibility & content floor (Art. IV.4)

- WCAG 2.2 AA contrast (≥ 4.5:1) on paper; status is never conveyed by colour alone — a word and a `−`/`+` marker carry it too; charts carry a source line (`sources: …`).
- `prefers-reduced-motion: reduce` is respected: there is no motion to reduce, and nothing auto-plays.
- All learner-facing text at least 16px, headings semantic (`h1`→`h3`, no skipped levels).
- The learner card and micro-lesson work without images and without JS.
- One language per document (`lang="en"`), dates in `YYYY.MM.DD`, times UTC with the local time in
  parentheses where a learner might act on it.
- No counts of "you" that could identify a learner in a cohort of n<3 (Art. V.3).

## 7. How the design is checked (no opinion required)

1. `app/tests/test_design.py` parses this file for the token block and the banned list, then greps
   the console templates and the card for: banned words, colour-only status, missing `lang`,
   missing `alt`, and any hex colour not in the token block.
2. A screenshot of the console at 1280×800 and of the card at 375×667 is stored in `app/out/ui/`
   with the run id — evidence for the video and for review.
3. The paper/ink palette is checked against the running ledger: `PUBLISH` olive, `REVERT` oxide,
   `UNKNOWN` yellow — the same tokens on the console, the card, and the video slides.
