# kickoff/SOURCE-PLAN.md — what the course watches, and why it may publish
`v0.1 (draft) · Depends on: constitution.md Art. III; WIRING.md §1–§2`

## 1. The subject and its source families

Course: **Agent Ops** — six lessons on shipping agents with n8n + Apify.

| Family | `source_id` | Publisher | Independence group | Why it matters to the course |
|---|---|---|---|---|
| n8n product docs | `n8n-docs` | n8n GmbH | `n8n-vendor` | The API/setting names lessons 2–4 teach |
| n8n release notes | `n8n-releases` | n8n GmbH | `n8n-vendor` | Breaking renames/deprecations, dated |
| Apify platform changelog | `apify-changelog` | Apify | `apify-vendor` | Actor runtime and API changes lesson 3 uses |
| Apify docs | `apify-docs` | Apify | `apify-vendor` | The concepts lesson 3 defines |
| MCP spec releases | `mcp-spec` | MCP org | `mcp-org` | The protocol lesson 1 introduces |
| MCP news/blog | `mcp-blog` | MCP org | `mcp-org` | Announcements that precede spec text |

**Independence test (Art. III.1):** two sources corroborate only when their `independence_group`
differs **and** the claims they support are about the same fact. `n8n-docs` + `n8n-releases` = one
voice: the vendor. Two vendors or a vendor + the spec org = corroboration.

## 2. What counts as a change event

| Change class | Materiality | Notes |
|---|---|---|
| Setting/API renamed, removed, or default-changed | `material_breaking` | Requires corroboration + PA2 (cohort card) |
| Feature deprecated with a sunset | `material_deprecation` | Requires the sunset date in the quote |
| New capability the lesson should mention | `material_new_capability` | Publish only if the lesson's learning objective is affected |
| Wording, examples, formatting | `cosmetic` | Draft only; never notifies the cohort |
| Marketing announcements, pricing, events | `marketing_noise` | `NO_CHANGE` |
| A claim we cannot fully interpret | `ambiguous` | Escalate; never publish |
| Two sources disagree | `contradictory` | Escalate with both quotes |
| Paywalled/404/empty | `unverifiable` | Escalate; snapshot keeps the HTTP status |

A claim only creates an event if it maps to a lesson's `concepts:` tags in the course front matter.
A change to an unrelated part of the docs is recorded as `no_delta` for the course.

## 3. Fetching plan (Apify first, fallbacks declared)

| Source | Apify actor | Fallback | Cadence |
|---|---|---|---|
| docs pages | `apify/website-content-crawler` | n8n HTTP + html-to-text (labelled `source: fallback`) | 60 min |
| release notes | crawler (news config) | GitHub Releases API | 60 min |
| changelog | changelog crawler | RSS feed | 60 min |
| spec repo | GitHub releases actor | GitHub Releases API | 120 min |

Every fetch is cached verbatim (`app/out/snapshots/`) and hashed before parsing. A cached snapshot
is used at most `thresholds.stale_hours` (12) before the loop degrades to observe-only
(`harness.md` §7).

## 4. The two corroboration patterns we expect

1. **Same fact, two vendors** — e.g., "Apify's actor runtime now requires Node 22" stated in the
   Apify changelog **and** reflected in the MCP/Apify integration docs.
2. **Vendor + spec** — e.g., a protocol change announced in the MCP blog **and** written into the
   spec repo's release notes.

If neither pattern appears during the window, the honest outcome is `ESCALATE(insufficient_
corroboration)` rows in the digest — which are still evidence the rule works, and are shown as such.

## 5. Anti-patterns (things that must not count as corroboration)

| Pattern | Why it is not corroboration |
|---|---|
| A vendor's docs page + the same vendor's release note | Same voice |
| A news article quoting the vendor's announcement | Second-hand, same origin |
| A forum post | Not a source of record; may be used only as an escalation hint |
| A page that claims its own approval/verification | Self-certifying; suspicion asymmetry (Art. X.3) |
| A change we cannot quote | Not a claim (Art. III.1a) |

## 6. Source health (what the digest shows)

`snapshots fetched · new vs cached · discarded rows · per-source last-success age · fallback uses`.
A source silent for 3× its cadence is marked `stale` in the digest — a quiet source is not a
healthy one, it is an unknown one.
