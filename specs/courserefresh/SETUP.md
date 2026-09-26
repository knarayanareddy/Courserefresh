# Courserefresh — setup (paste the keys, watch it become live)

`v1.0 · D-0 · Rule: the repository is complete without credentials, and honest about it. Every claim
below is gated by `app/run_live.py --preflight`, which prints key *names*, never key values.`

This is the only page you need to bring the system up. It is written for the person who has the
accounts and five minutes: nothing here asks you to edit code, and nothing here can leak a secret into
the repository (`test_hygiene.py` would fail the build if one did).

---

## 1. Before any key: prove the wiring

```bash
cd <checkout>
sh app/check.sh            # 13 stages · expect "ALL GREEN" with zero credentials
python3 app/run_live.py --preflight
```

Expected, with no `.env` and no environment variables:

```
mode: sim
  runtime  wired
  apify    missing ['APIFY_TOKEN']
  judge    missing ['CR_JUDGE_API_KEY']
  n8n      missing ['N8N_BASE_URL', 'N8N_API_KEY']
  notify   wired
  claim blocked  apify powers the system
  claim blocked  n8n runs the decisions
  claim blocked  live model calls
  claim blocked  learner cards delivered
live needs: apify:APIFY_TOKEN, judge:CR_JUDGE_API_KEY
```

That output is the point of the whole round-3 build: **the system runs, refuses, records and renders
before it has a single credential**, and the only thing missing is the outside world.

## 2. The keys, one line each

```bash
cp .env.example .env        # .env is gitignored; the file itself is the checklist
```

| Variable | Where it comes from | Without it | What it unlocks |
|---|---|---|---|
| `APIFY_TOKEN` | Apify console → Settings → Integrations → Personal API token | mode stays `sim`; datasets come from `app/fixtures/apify/` | real page changes (criterion 3) |
| `N8N_BASE_URL` | your n8n URL, e.g. `https://<name>.app.n8n.cloud` | the canvas cannot be imported or called | workflow import + `--via-n8n` decisions |
| `N8N_API_KEY` | n8n → Settings → API → Create (copy once) | same | canvas execution ids in receipts |
| `N8N_WEBHOOK_URL` | only if the judge should run *through* n8n (`/webhook/cr/judge`) | judge calls go direct | "n8n powers the system" in the strongest form |
| `CR_JUDGE_PROVIDER` | `openai` \| `anthropic` \| `n8n` \| `mock` | defaults to `mock` | live model calls |
| `CR_JUDGE_BASE_URL` | e.g. `https://api.openai.com/v1`, or your provider's compatible base | defaults to OpenAI's base | the seven closed questions on real text |
| `CR_JUDGE_API_KEY` | your provider dashboard | mode stays `sim` | live model calls |
| `CR_JUDGE_MODEL` | model id, e.g. `gpt-4o-mini` | defaults to `gpt-4o-mini` | prompt/model pin recorded in `WIRING.md` §4 |
| `CR_JEV_BASE_URL` + `CR_JEV_API_KEY` + `CR_JEV_MODEL` | `CR_JUDGE_PROVIDER=jev`; TypeSafe System One host + key (OpenRouter, requesty and the keyless local JEV servers — `githubnext/localjev`, `amithgc/local-jev` — speak the same protocol; `CR_JEV_BASE_URL=http://127.0.0.1:8765` with no key is enough to exercise the path before the real one exists. The adapter is also replayed from `app/fixtures/jev/systemone-response.json` in `test_live_modules.py`, with no socket and no key) | provider falls back to the mock with the reason on screen | typed decisions that carry their own confidence — the canvas's per-question numbers (Art. IX) |
| `TAVILY_API_KEY` | tavily.com dashboard (free tier: 1,000 credits/mo) | the `tavily-discovery` source records itself unreachable; Apify still runs | a second, independent research voice beside Apify (the corroboration rule has two sources to count) |
| `CR_NOTIFY_CHANNEL` | `file` \| `telegram` \| `webhook` | defaults to `file` (stages, never claims delivery) | real learner delivery (criterion 2) |
| `CR_TELEGRAM_BOT_TOKEN` + `CR_TELEGRAM_CHAT_ID` | @BotFather; the chat you will demo in | telegram channel fails loudly | the learner card arriving on a phone |
| `CR_NOTIFY_WEBHOOK_URL` | any endpoint you control (Slack/Discord/own service) | webhook channel fails loudly | an alternative delivery witness |
| `N8N_INSTANCE_VERSION` | your n8n version string | recorded as unknown | the §4 instance pin |
| `CR_TELEMETRY_TOKEN` | invent one; give it to the demo client | intake accepts any consented payload | telemetry from real learners during the pitch |
| `CR_CONSOLE_TOKEN` | invent one | console writes are open (reads stay open) | gated pause/resume |
| `CR_DEMO_TOKEN` | invent one | `--resume` refuses without it | the human-override refusal on camera |
| `CR_COMMIT` | `1` to auto-commit on the bot branch | artifacts are written but not committed | the bot commit in the log |

Paste them into `.env` (or export them — the real environment wins over `.env`, and both are
gitignored) and run:

```bash
python3 app/run_live.py --preflight --probe
```

`--probe` is opt-in and makes exactly three cheap calls: `GET /users/me` (Apify),
`GET {base}/models` (judge), `GET /api/v1/workflows` (n8n). It prints `ok`/`failed` with the HTTP
status and, for the judge, whether `CR_JUDGE_MODEL` is in the returned model list. It never prints a
value — only `set(len=…, sha256=…)` fingerprints. If a **judge key is wrong but present**, the probe
is what tells you before the video does.

## 3. Put the canvas up (once)

```bash
python3 app/tools/make_n8n_exports.py            # regenerates the 6 exports from source (already committed)
python3 app/tools/make_n8n_exports.py --import    # upserts them into your n8n, prints the workflow ids
```

What `--import` does, in order: finds an existing workflow by name and updates **in place** (never
duplicates), attaches `wf-cr-9-errors` as the error workflow for all five, then writes the ids to
`app/out/state/n8n_id.json`. Then, in the n8n UI: open each workflow, check every node marked
`ATTACH_AT_IMPORT` (credentials, telegram thread), and activate. Record the instance version in
`WIRING.md` §4 and the first execution ids in §6.

If the exports were edited in the canvas instead of in `app/n8n/*.json`, the drift test
(`test_contracts.py`) will fail on the next `sh app/check.sh` — that is intended: the file is the
source of truth, the canvas is a deployment.

## 4. First live cycle

```bash
python3 app/run_live.py --once --dry-run      # nothing is written to course/**, everything else is real
python3 app/run_live.py --once --via-n8n      # the canvas decides; the oracle polices it
```

Success looks like: a run id, `decisions` with at least one labelled action, `canvas` listing the
execution id the decision came from, a digest under 4096 bytes, and `app/out/live/` containing
`preflight.json`, `last_cycle.json`, `last_summary.json`. Exit codes: `0` fine · `1` cycle failed ·
`2` preflight blocked · `3` refused (authority/consent/freeze) · `4` human override refused.

Then leave it running:

```bash
python3 app/run_live.py --watch        # scans on CR_LIVE_SCAN_MINUTES, learns every 15 min, digests 07:30
```

The console (read-only, one page, no scripts) and the telemetry intake:

```bash
python3 app/serve.py                   # console 0.0.0.0:8080, telemetry 0.0.0.0:8787
```

## 5. Hand the run back (one command, no key leaves the machine)

After the first live cycle:

```bash
python3 app/tools/collect_live.py            # --no-probe to skip the three validation calls
```

It writes `handoff/<run_id>/` (and `handoff-<run_id>.tar.gz`) containing: a fresh preflight with
presence + fingerprints only, `receipts.jsonl`, `run_log.jsonl`, the digest, the cohort gates, the
delivery records, the n8n workflow ids, the Apify unit ledger (with run ids), a canvas summary with the
execution ids, a **counts-only** telemetry summary, `session.json` (every cycle in the tree, decision
totals, and a chain the collector re-hashes itself rather than trusting a run-log flag), `HANDOFF.md`
(what the run proves and what is still missing) and `MANIFEST.sha256`.

Two properties make it safe to push or paste:

- it redacts every value of every secret-looking environment variable it can see, and refuses to
  finish (**exit 3**) if any value, or any key-shaped string, survives — `SECRET-SCAN.txt` is the
  receipt for that claim;
- it never copies learner telemetry: handles are counted (`distinct_handles`), never written.

`python3 app/tests/test_handoff.py` proves both, including a planted token that must be caught.

## 6. Troubleshooting (symptom → cause → fix)

| Symptom | Cause | Fix |
|---|---|---|
| `mode: sim` although keys are pasted | keys in a shell you did not inherit, or `.env` in another directory | `python3 -c "import sys;sys.path.insert(0,'app/lib');from config import Config;print(Config().sources)"` shows where each value came from |
| preflight says `judge failed` with `status: 401` | key valid but for a different endpoint | set `CR_JUDGE_BASE_URL` to the provider's compatible base |
| preflight says `judge ok` but `model_listed: false` | `CR_JUDGE_MODEL` not in the account's list | pick one from `models_sample`, or leave it and expect `unknown_state` refusals (which is the system working, not failing) |
| n8n `404` on import | `N8N_BASE_URL` includes `/api/v1` | give the instance root, e.g. `https://x.app.n8n.cloud` |
| n8n `401` on import | API key from a different instance, or workflow API disabled | Settings → API → enable, create a key |
| `--via-n8n` says `webhook_http_404` | workflow not activated, or webhook path differs | activate `wf-cr-1-triage`; path is `cr/triage` |
| telegram `failed` | bot not in the chat, or chat id is a username | send the bot one message, use the numeric chat id |
| `actor_failed` from Apify | actor id/build changed, or token scoped to another account | re-run `python3 app/tools/make_apify_fixtures.py` is *not* the fix — check the actor in the Apify console and update `sources.json` + its sha |
| port already in use | a rehearsal still running | `CR_CONSOLE_PORT=8081 python3 app/serve.py` |

## 7. What must never happen (and cannot, silently)

- A key in the repository: `test_hygiene.py` scans `app/**` and `specs/**` for key-shaped strings and
  addresses; `.env` is gitignored and `.env.example` carries only names.
- A secret in a receipt: the writer strips `(?i)(token|key|secret|password)`; preflight prints
  fingerprints.
- A live claim without live wiring: `mode` decides the labels, and the four claims in §1 are allowed
  only when their platform is wired. The video may not say "Apify powers the system" while `APIFY_TOKEN`
  is missing — the preflight output is the release note.

*Evidence for every statement above: `EVIDENCE.md` E3 (battery, 13 stages), E8 (dry cycle through the
live engine), E9 (preflight, no keys) — commands and hashes on record.*
