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
  --paper:#F3EFE7; --paper-2:#EAE4D8; --rule:#8E8160;    /* hairlines: separators carry meaning, so they hold 3:1 (measured) */
  --ink:#1C1915;   --ink-soft:#4A443A; --ink-faint:#68604F;
  --accent:#6B4E2E;            /* margins, links, small marks */
  --status-publish:#3F5A2A;    /* olive  — a change shipped */
  --status-queue:#96550A;      /* ochre  — drafted / awaiting human (5.09:1 / 4.61:1 measured) */
  --status-revert:#9B2C1F;     /* oxide  — undone, or refused */
  --status-nochange:#5C564C;   /* muted ink */
  --status-unknown:#7A5C00;    /* dark ochre — unknown/unmeasured (a yellow that looked
                                 right measured 2.14:1 on paper and failed AA) */
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

### 1.1 Contrast, measured (review 05, UX-01/UX-02)

White paper lies to the eye. Each token was measured against both paper tones; two changed as a
result, and `test_design.py` now fails if any of them drifts back.

| Token | Value | On `--paper` | On `--paper-2` | Verdict |
|---|---|---|---|---|
| `--ink` | `#1C1915` | 15.27:1 | 13.79:1 | AA/AAA |
| `--ink-soft` | `#4A443A` | 8.40:1 | 7.58:1 | AA/AAA |
| `--ink-faint` | `#68604F` *(was `#7A7264`, 4.14:1 — failed)* | 5.43:1 | 4.92:1 | AA |
| `--rule` | `#8E8160` *(was `#C9C0AE`, 1.43:1 — failed)* | 3.35:1 | 3.04:1 | non-text 3:1 |
| `--status-publish` | `#3F5A2A` | 6.76:1 | 6.11:1 | AA |
| `--status-queue` | `#96550A` *(was `#A15C07`, 4.10:1 on paper-2 — failed)* | 5.09:1 | 4.61:1 | AA |
| `--status-revert` | `#9B2C1F` | 6.60:1 | 5.96:1 | AA |
| `--status-nochange` | `#5C564C` | 6.33:1 | 5.72:1 | AA |
| `--status-unknown` | `#7A5C00` *(was `#C5A202`, 2.14:1 — failed)* | 5.45:1 | 4.94:1 | AA |

Amber is the designer's trap on paper: it reads as "warning" and measures as "unreadable".

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

## 4.1 Console page (built, one page, no scripts)

The console is a single static page (`app/out/digest.html`) rendered from the lockfile tokens; the
digest is the same content in text. It exists because "show the logs" (criterion 2) is easier to
believe when a human can open them.

- **Order:** refusals first, then changes, then learners, then discipline — the digest's order.
- **Rows:** status *word* (SENT / QUEUED / REFUSED / PUBLISHED / REVERTED / NO CHANGE) + colour + the
  `event_id` in mono + reason codes in `--ink-soft` + one line of detail.
- **Affordances:** no hover-only information, no motion, no toasts; focus ring on any future control;
  touch targets ≥ 44 px; reading order equals DOM order (screen readers get the same refusals first).
- **Nothing dynamic is trusted:** every interpolated string is HTML-escaped (TM11), and no token that
  is not in §1 may appear (`--selftest` fails on an unknown hex).

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
