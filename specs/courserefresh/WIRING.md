# Courserefresh — wiring sheet (Apify ⇄ n8n ⇄ repo ⇄ learners)
`v0.1 (draft) · Filled at D-1 with real ids; an empty cell is a task, not a footnote`

Judges ask "what actually powers this?" — this file is the answer, and every row is verifiable by
opening the platform it names.

---

## 1. Apify actors (pinned id + build; record the first real run id)

| Actor | Source family | Input | Output → snapshot field | Run id (first) |
|---|---|---|---|---|
| `apify/website-content-crawler` | Docs/changelog pages (vendor docs) | `startUrls` (≤5), `maxPages`, `crawlerType=cheerio` | `markdown`, `url`, `published_at` | `<…>` |
| `apify/website-content-crawler` (second config) | Release notes / blog index | same, different start urls | same | `<…>` |
| GitHub releases actor (pinned id at D-1) | Spec repo releases | `owner/repo`, `perPage` | `markdown`, `published_at` | `<…>` |
| RSS/changelog actor (pinned id at D-1) | Vendor changelog feed | feed url | `markdown` | `<…>` |

Fallback when an actor fails: n8n HTTP node against the declared `fallback_url` (GitHub API, RSS);
when *that* is used, the digest prints `source: fallback` (Art. XIII.3 — no silent substitution).

## 2. Source allowlist (exact hosts; HTTPS only; no redirects off-list)

| Host | Why | Independence group |
|---|---|---|
| `docs.n8n.io` | n8n product docs | `n8n-vendor` |
| `github.com` (path prefix `/n8n-io/n8n/releases`) | n8n release notes | `n8n-vendor` |
| `blog.n8n.io` | n8n announcements | `n8n-vendor` |
| `apify.com` (path prefix `/changelog`) | Apify platform changelog | `apify-vendor` |
| `docs.apify.com` | Apify docs | `apify-vendor` |
| `github.com` (path prefix `/modelcontextprotocol/…/releases`) | MCP spec releases | `mcp-org` |
| `blog.modelcontextprotocol.io` | MCP news | `mcp-org` |

Independence rule (Art. III.1): `independence_group` must differ — `docs.n8n.io` + `github.com/n8n-io`
are **one** source, even though they are two URLs. The allowlist above is the *subject's* list; for
another subject, `SOURCE-PLAN.md` replaces it and the list is mirrored to
`app/out/state/allowlist.json` at preflight (hashed into the run header).

## 2b. Source roles (independence done properly — review 05, AP-01/AP-02)

Counting publishers is necessary and not sufficient: two pages under one vendor are one voice. Each
source therefore carries a **role**, checked before the corroboration maths runs.

| Role | Who | Counts as independent evidence? |
|---|---|---|
| `authoritative` | the vendor's own release notes / changelog for the thing that changed | yes, once per publisher |
| `corroborating` | an independent publisher (community package, third-party docs, press) | yes |
| `none` | a mirror, a re-post, a scraper of the same upstream, a page with no publication date | **no** — recorded, never counted |

Rules: a source with `role: none` may still be *shown* (the receipt keeps its quote) but it cannot
lift a single-publisher claim over the floor; `role` is assigned in `SOURCE-PLAN.md` per host and
path prefix, and the assigned role appears on the receipt. This is the difference between "two
URLs" and "two voices" — the subject's docs site and its GitHub releases are one voice.

## 3. Workflow inventory (nodes and where the decisions live)

| Workflow | Trigger | Key nodes | Reads | Writes |
|---|---|---|---|---|
| `wf-cr-0-scan` | Schedule 60 min; `POST /scan` | `THRESHOLDS` → Apify (actors §1) → `Normalize` → `Dedupe` → `HTTP: triage` | actors, `state/seen.json` | snapshots, run log |
| `wf-cr-1-triage` | Webhook | `BuildPrompt` → `OBSERVE` → `AnchorQuotes` → `JUDGE` → **`POLICY`** → `Receipt` → `IF` act/escalate | snapshots, thresholds, gold (offline only) | receipts, escalation queue |
| `wf-cr-2-act` | Webhook | `RenderBody` → `RenderDiff` → `UpdateQuiz?` → `GitCommit (bot/courserefresh)` → `Card` → `Receipt` | queue, lesson bodies | `course/**`, `CHANGELOG.md`, cards |
| `wf-cr-3-learn` | Schedule 15 min | `ReadTelemetry` → `CohortWindow` → `GateEval` → `decide_revert` → `StuckCheck` → `decide_learner` → `Dispatch` | telemetry, receipts | micro-lessons, dispatch receipts |
| `wf-cr-4-digest` | Schedule 07:30; `POST /digest` | `ReadReceipts(window)` → `OrderSections` → `Render (≤4 KB)` → `Send` → `VerifyChain` | receipts | digest, run log |

The **`POLICY` node** embeds `app/n8n/policy_node.js` verbatim; `THRESHOLDS` supplies
`skin/thresholds.json` values. Nothing else in the canvas makes a decision.

### 3.1 n8n build requirements (what "powered by n8n, not decorated with it" means)

| Requirement | Why (review 05, N8N-01…N8N-05) | Where it shows |
|---|---|---|
| Every workflow runs **execute-once**; the scan trigger passes a run key and the workflow refuses a duplicate key | a daily schedule that double-fires must not publish twice | `wf-cr-0-scan` sticky-note + the run key in the receipt |
| The decision node is a **Code node whose body is the rulebook file** (`policy_node.js`), drift-checked byte-for-byte | "code decides" must be inspectable in the canvas | `test_contracts.py` compares the embedded body to the file |
| Queue-mode instances: the error branch is `IF error → RETRY(dlq, once) → RECEIPT(degraded) + digest line` | a failure that is not reported is a silent failure | `wf-cr-*` error outputs wired to the shared node |
| One **error workflow** attached to all five, so an unhandled throw still lands as a receipt row | the loop's honesty must survive its own bugs | instance setting, recorded at D-1 |
| Instance pin: n8n version recorded in §4 before the hero run; expressions avoid version-added helpers | "works on my canvas" is not evidence | §4 row, filled at D-1 |
| Apify calls: actor pins include the **build**, and the retry budget is an explicit number, not "a few tries" | the retry policy is part of the unit budget | §1 + receipt `cost.apify_units` |

## 4. Model pins (recorded, never "latest")

| Knob | Provider / model | Version pin | Used by |
|---|---|---|---|
| `OBSERVE_MODEL` | `<provider/model@version>` | `<pin>` | claim extraction, topic tags |
| `JUDGE_MODEL` | `<provider/model@version>` | `<pin>` | the seven closed questions |
| `COMPARATOR_MODEL` | `<name + version + date>` | frozen when run | eval column (a) only |

## 5. Prices (needed before cost can be anything but `unmeasured`)

| Item | Unit price | Source (URL + date captured) |
|---|---|---|
| Judge tokens (in/out per 1 k) | `<€>` | `<url>` |
| Observe tokens (in/out per 1 k) | `<€>` | `<url>` |
| Apify compute unit | `<€>` | `<url>` |

Until this table has values, every cost surface prints `unmeasured` (Art. VI).

## 6. First real runs (the only acceptable proof of "it is wired")

| What | Platform | Id / link | Date |
|---|---|---|---|
| Actor run #1 | Apify console | `<run id / url>` | — |
| n8n execution #1 (`wf-cr-1-triage`) | n8n executions | `<exec id / url>` | — |
| First bot commit | Git host | `<commit sha>` | — |
| Digest #1 | channel | `<message id>` | — |

## 6.1 What the first runs must prove (review 05 added two rows)

| # | Proof | Where the id/artifact goes |
|---|---|---|
| 1 | an Apify actor run with a real dataset | §1 run-id column |
| 2 | an n8n execution of `wf-cr-1-triage` whose POLICY node decided | §3 execution link |
| 3 | one delivered learner card (or the word "staged" on screen) | §5 |
| 4 | **an API-contract drift check**: one declared field that the live API does not return (or returns as `null`), handled as a degraded receipt rather than a crash | §2b + receipt `source_stale` |
| 5 | **a witnessed failure**: `--chaos write-fail` (offline) then a live equivalent, reported in digest and console | `EVIDENCE.md` E7 |

## 7. Credentials (env only; never in the repo, never in a receipt)

`APIFY_TOKEN` · `N8N_WEBHOOK_BASE` · `GITHUB_TOKEN` (branch-scoped) · `SMTP_DSN` (or Telegram bot
token) · `NOTION_TOKEN` (P1) · `CR_DEMO_TOKEN` · `OBSERVE_MODEL`/`JUDGE_MODEL` keys.
Least privilege (Art. XIV.4): the Git token can push `bot/courserefresh` and open a PR; it cannot
merge to `main` or edit workflows. The receipt writer strips any key matching
`(?i)(token|key|secret|password)` — `test_hygiene.py` asserts no such string ever lands in
`app/out/**` (TM12).
