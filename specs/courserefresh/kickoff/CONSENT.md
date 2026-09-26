# kickoff/CONSENT.md — the learner consent text (frozen before the window; Art. V)
`v0.1 (draft) · This text is shown to every participant before any telemetry is stored`

## 1. What Courserefresh asks for (plain language)

> **Taking part in a pilot that updates this course automatically**
>
> This six-lesson course is being kept up to date by a program. As part of the pilot I would like to:
>
> 1. **Track my practice** — which quiz items I attempt, whether I get them right, and how long I
>    spend on a lesson, stored under a random pseudonym (not my name).
> 2. **Send me at most one short message a day** when a lesson I use has changed, or when the
>    program thinks I am stuck — one concept, two minutes, one practice item, with a link to stop.
>
> **What never happens:** no grading, no changes to my score or answers, no messages to anyone else
> about me, no profiling, no data sold or shared outside the pilot. My name is never written into the
> program's logs — only a pseudonym like `learner:5b7c1e4a`.
>
> **My choice is my own:** yes/no to tracking, yes/no to messages. I can stop messages with one click
> in any message, and ask for deletion at any time (`<contact>`); practice data is deleted after 14
> days or at the end of the pilot, whichever comes first, and only aggregate counts remain.

## 2. What the system stores (and what it never stores)

| Stored | Never stored |
|---|---|
| Hashed handle (`learner:<sha256[..8]>`) | Name, email, or any account identifier |
| Item attempts (`item`, `correct`) | Free-text answers or any typed content |
| Dwell times in seconds | Location, device fingerprints, IP (not persisted) |
| Message receipts (`sent`, `seen`, `opted_out`) | Any learner's data outside the consented rows |

## 3. Consent record shape (what the code writes)

```jsonc
{"learner_ref": "learner:5b7c1e4a", "phone_or_email_ref": "c:<hash>", "tracking": true, "messaging": true,
 "consent_text_version": "CONSENT.md v0.1", "consented_at": "…", "revoked_at": null, "source": "form|dm|in-person"}
```

The consent version string must match the frozen `CONSENT.md` hash; a mismatch invalidates the
record and the learner is treated as **not consented** (fail closed, `consent_missing`).

## 4. Messaging rules (enforced in code, stated to the learner)

1. At most **1/learner/day** and **3/learner/week**.
2. Every message: what changed · why it matters · what to do if it is wrong · opt-out link.
3. No marketing, no streaks, no "you're falling behind", no countdowns.
4. A micro-lesson is sent **once per concept-signal per 7 days**; repeating it is noise.
5. Withdrawal is instant: the next dispatch is skipped and a `consent_revoked` receipt is written
   (the learner's own request is the reason; no further message follows, including a confirmation).

## 5. Minors, vulnerability, and the demo

- If a participant is under 18 or asks to be excluded, they are excluded, and the exclusion is
  recorded as a count only.
- No learner's message or name appears in the video or any document. The card shown on screen uses a
  fixture handle.
- Aggregate numbers are only shown at `n ≥ 3`, and never in a way that identifies one learner
  (Art. V.3).

## 6. The one-line pitch of this file

*The machine reads practice to notice a struggle, writes pseudonyms instead of names, never grades,
and can always be switched off in one click — and the pitch says exactly that, because it is true.*
