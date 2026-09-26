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

## 7. Credentials (env only; never in the repo, never in a receipt)

`APIFY_TOKEN` · `N8N_WEBHOOK_BASE` · `GITHUB_TOKEN` (branch-scoped) · `SMTP_DSN` (or Telegram bot
token) · `NOTION_TOKEN` (P1) · `CR_DEMO_TOKEN` · `OBSERVE_MODEL`/`JUDGE_MODEL` keys.
Least privilege (Art. XIV.4): the Git token can push `bot/courserefresh` and open a PR; it cannot
merge to `main` or edit workflows. The receipt writer strips any key matching
`(?i)(token|key|secret|password)` — `test_hygiene.py` asserts no such string ever lands in
`app/out/**` (TM12).
