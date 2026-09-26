#!/usr/bin/env python3
"""Generate the five n8n workflow exports (J-04).

The exports are importable skeletons: node types, parameters, connections and the *embedded*
policy rulebook are real, while credentials and thread ids are marked `ATTACH_AT_IMPORT`. The
POLICY code node embeds `app/n8n/policy_node.js` byte-for-byte and carries its sha256, so
`test_contracts.py` can fail the build if someone edits one copy and not the other.

Run: python3 app/tools/make_n8n_exports.py
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "n8n"
SKIN = ROOT / "specs" / "courserefresh" / "skin"
NODE_SRC = (OUT / "policy_node.js").read_text()
NODE_HASH = hashlib.sha256(NODE_SRC.encode()).hexdigest()
ERR_NAME = "CR-9 · errors → receipt"          # the one workflow whose id belongs in every other's settings
# one source of truth for the canvas paths (skin/wiring.json); the engine reads the same file
WIRING = json.loads((SKIN / "wiring.json").read_text())["webhooks"]


def code(name, js, position):
    return {"parameters": {"jsCode": js}, "id": name.lower().replace(" ", "-"), "name": name,
            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": position}


def http(name, url, method, body, position, notes=""):
    return {"parameters": {"method": method, "url": url, "sendBody": True, "specifyBody": "json",
                           "jsonBody": body, "options": {}},
            "id": name.lower().replace(" ", "-"), "name": name, "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2, "position": position, "notes": notes}


def sched(name, minutes, position):
    return {"parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": minutes}]}},
            "id": name.lower().replace(" ", "-"), "name": name,
            "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2, "position": position}


def webhook(name, path, position):
    return {"parameters": {"httpMethod": "POST", "path": path, "responseMode": "lastNode"},
            "id": name.lower().replace(" ", "-"), "name": name, "type": "n8n-nodes-base.webhook",
            "typeVersion": 2, "position": position}


def ifnode(name, expr, position):
    return {"parameters": {"conditions": {"options": {"caseSensitive": True, "version": 2},
                                          "conditions": [{"leftValue": expr, "rightValue": True,
                                                          "operator": {"type": "boolean", "operation": "true"}}]}},
            "id": name.lower().replace(" ", "-"), "name": name, "type": "n8n-nodes-base.if",
            "typeVersion": 2, "position": position}


def noop(name, position):
    return {"parameters": {}, "id": name.lower().replace(" ", "-"), "name": name,
            "type": "n8n-nodes-base.noOp", "typeVersion": 1, "position": position}


def once(name, position):
    """Execute-once guard (WIRING §3.1): a duplicate run key stops the workflow instead of repeating it."""
    js = ("// execute-once: the scan trigger passes a run key; a duplicate key stops this execution.\n"
          "const key = $json.run_key || $json.run_id || null;\n"
          "const store = $getWorkflowStaticData('global');\n"
          "if (key && store.lastRunKey === key) { return []; }\n"
          "if (key) store.lastRunKey = key;\n"
          "return $input.all();")
    return code(name, js, position)


def note(name, text, position, width=420, height=220):
    return {"parameters": {"content": text, "height": height, "width": width, "color": 4},
            "id": name.lower().replace(" ", "-") + "-note", "name": name,
            "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": position}


CONTRACT_NOTE = (
    "WIRING.md §3.1 contract:\n"
    "1. execute-once (this file has the guard)\n"
    "2. the POLICY node embeds app/n8n/policy_node.js byte-for-byte (drift-checked by test_contracts)\n"
    "3. errors land as receipts: error branch → RETRY(dlq, once) → RECEIPT(degraded)\n"
    "4. wf-cr-9-errors is attached to every workflow at import time (make_n8n_exports.py --import)\n"
    "5. instance version is recorded in WIRING.md §4 at D-1; expressions stay version-safe")


def insert_guard(nodes: list[dict]) -> list[dict]:
    """Put the execute-once guard between the trigger and everything else (WIRING §3.1 #1)."""
    trigger = nodes[0]
    if trigger["type"] not in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.webhook"):
        return nodes
    guard = once("ONCE", [trigger["position"][0] + 220, trigger["position"][1]])
    return [trigger, guard] + nodes[1:]


def rewire_guard(name: str, nodes: list[dict], connections: dict) -> dict:
    trigger = nodes[0]
    if trigger["type"] not in ("n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.webhook"):
        return connections
    targets = connections.get(trigger["name"], {"main": [[]]})["main"][0]
    connections[trigger["name"]] = {"main": [[{"node": "ONCE", "type": "main", "index": 0}]]}
    connections["ONCE"] = {"main": [targets]}
    return connections


def workflow(name, nodes, connections, notes):
    nodes = insert_guard(nodes)
    connections = rewire_guard(name, nodes, connections)
    return {"name": name, "nodes": nodes + [note("CONTRACT", CONTRACT_NOTE, [0, -420])],
            "connections": connections,
            "settings": {"executionOrder": "v1", "saveManualExecutions": True, "callerPolicy": "workflowsFromSameOwner",
                         "errorWorkflow": None},   # set to wf-cr-9-errors' id at import time
            "staticData": None, "meta": {"instanceId": "ATTACH_AT_IMPORT",
                                          "templateCredsSetupCompleted": False,
                                          "courserefresh": {"generated_by": "app/tools/make_n8n_exports.py",
                                                            "policy_node_sha256": NODE_HASH, "notes": notes}},
            "tags": [{"name": "courserefresh"}], "pinData": {}, "versionId": NODE_HASH[:8], "active": False}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    scan = workflow(
        "wf-cr-0-scan",
        [sched("Every 60 minutes", 60, [0, 0]),
         code("THRESHOLDS", "// loads specs/courserefresh/skin/thresholds.json (mirrored at preflight)\n"
                            "return [{json: require('./thresholds.json')}];", [220, 0]),
         code("SOURCES", "// one item per source in kickoff/SOURCE-PLAN.md §1, with its independence group\n"
                         "return $json.sources;", [440, 0]),
         http("APIFY_RUN_ACTOR", "https://api.apify.com/v2/acts/{{$json.actor_id}}/runs?token=ATTACH_AT_IMPORT",
              "POST", '={"run_mode":"single","input":{{JSON.stringify($json.input)}}}', [660, 0],
              "Pinned actor id + build from WIRING.md §1; credentials never inline"),
         code("NORMALIZE", "const rows = $json.items || [];\n"
                           "const crypto = require('crypto');\n"
                           "return rows.filter(r => r.url && r.markdown).map(r => ({json: {\n"
                           "  url: r.url, title: r.title || '', markdown: r.markdown,\n"
                           "  content_hash: 'sha256:' + crypto.createHash('sha256').update(r.markdown).digest('hex'),\n"
                           "  published_at: r.published_at || null, actor_run_id: $json.run_id }}));", [880, 0]),
         code("DEDUPE", "// drops anything whose content_hash is already in state/seen.json\n"
                        "const seen = JSON.parse(await this.helpers.getBinaryDataBuffer ? '{}' : '{}');\n"
                        "return $input.all().filter(i => !seen[i.json.content_hash]);", [1100, 0]),
         http("HTTP_TRIAGE", "ATTACH_AT_IMPORT/webhook/" + WIRING["triage"], "POST",
              '={"run_id":"{{$json.actor_run_id}}","snapshots":{{JSON.stringify($json)}}}', [1320, 0]),
         code("RECEIPT", "// appends one row per run to receipts.jsonl (mode: live) and the run log\n"
                         "return [{json: {actor: 'system', mode: 'live', stage: 'scan', deltas: $input.all().length}}];", [1540, 0])],
        {"Every 60 minutes": {"main": [[{"node": "THRESHOLDS", "type": "main", "index": 0}]]},
         "THRESHOLDS": {"main": [[{"node": "SOURCES", "type": "main", "index": 0}]]},
         "SOURCES": {"main": [[{"node": "APIFY_RUN_ACTOR", "type": "main", "index": 0}]]},
         "APIFY_RUN_ACTOR": {"main": [[{"node": "NORMALIZE", "type": "main", "index": 0}]]},
         "NORMALIZE": {"main": [[{"node": "DEDUPE", "type": "main", "index": 0}]]},
         "DEDUPE": {"main": [[{"node": "HTTP_TRIAGE", "type": "main", "index": 0}]]},
         "HTTP_TRIAGE": {"main": [[{"node": "RECEIPT", "type": "main", "index": 0}]]}},
        "Apify actor runs are the system's only eyes; a zero-delta run still writes a receipt.")
    (OUT / "wf-cr-0-scan.json").write_text(json.dumps(scan, indent=2) + "\n")

    triage = workflow(
        "wf-cr-1-triage",
        [webhook("From scan", WIRING["triage"], [0, 0]),
         code("BUILD_PROMPT", "// assembles the observe prompt from the snapshot text; the judge never sees it\n"
                              "return $input.all();", [220, 0]),
         http("OBSERVE", "ATTACH_AT_IMPORT/v1/chat/completions", "POST",
              '={"model":"{{$env.OBSERVE_MODEL}}","temperature":0,"messages":{{JSON.stringify($json.messages)}}}',
              [440, 0], "OBSERVE_MODEL pinned in WIRING.md §4"),
         code("ANCHOR_QUOTES", "// keeps only quotes that occur verbatim in the cached snapshot\n"
                               "return $input.all();", [660, 0]),
         http("JUDGE", "ATTACH_AT_IMPORT/v1/chat/completions", "POST",
              '={"model":"{{$env.JUDGE_MODEL}}","temperature":0,"response_format":{"type":"json_object"}}',
              [880, 0], "The seven closed questions in skin/questions.json"),
         code("POLICY", NODE_SRC, [1100, 0]),
         ifnode("Publish or revert?", "={{ ['PUBLISH','REVERT'].includes($json.decision.action) }}", [1320, 0]),
         http("NOTICE_DECISION", "ATTACH_AT_IMPORT/webhook/" + WIRING["act"], "POST",
              '={{JSON.stringify($json)}}', [1540, -80]),
         noop("Queue for a human", [1540, 120]),
         code("RECEIPT", "// one chained row per decision: quotes, judge answers, action, reasons, artifact hash\n"
                         "return $input.all();", [1760, 0])],
        {"From scan": {"main": [[{"node": "BUILD_PROMPT", "type": "main", "index": 0}]]},
         "BUILD_PROMPT": {"main": [[{"node": "OBSERVE", "type": "main", "index": 0}]]},
         "OBSERVE": {"main": [[{"node": "ANCHOR_QUOTES", "type": "main", "index": 0}]]},
         "ANCHOR_QUOTES": {"main": [[{"node": "JUDGE", "type": "main", "index": 0}]]},
         "JUDGE": {"main": [[{"node": "POLICY", "type": "main", "index": 0}]]},
         "POLICY": {"main": [[{"node": "Publish or revert?", "type": "main", "index": 0}]]},
         "Publish or revert?": {"main": [[{"node": "NOTICE_DECISION", "type": "main", "index": 0}],
                                          [{"node": "Queue for a human", "type": "main", "index": 0}]]},
         "NOTICE_DECISION": {"main": [[{"node": "RECEIPT", "type": "main", "index": 0}]]},
         "Queue for a human": {"main": [[{"node": "RECEIPT", "type": "main", "index": 0}]]}},
        "The POLICY node is the product's rulebook: one screen, deterministic, never throws.")
    (OUT / "wf-cr-1-triage.json").write_text(json.dumps(triage, indent=2) + "\n")

    act = workflow(
        "wf-cr-2-act",
        [webhook("From triage", WIRING["act"], [0, 0]),
         code("RENDER_BODY", "// writes course/<lesson>/v<n+1>.md from the previous version + the anchored edit\n"
                             "return $input.all();", [220, 0]),
         code("RENDER_DIFF", "// unified diff of previous vs new; refuses if > thresholds.diff.max_lines\n"
                             "return $input.all();", [440, 0]),
         {"parameters": {"operation": "commit", "repository": "ATTACH_AT_IMPORT", "branch": "bot/courserefresh",
                         "filePath": "={{$json.body_path}}", "commitMessage": "=cr: {{$json.decision.action}} {{$json.lesson_id}} {{$json.previous_version}} → {{$json.new_version}} [{{$json.receipt_id}}]"},
          "id": "git-commit", "name": "COMMIT (bot branch)", "type": "n8n-nodes-base.github",
          "typeVersion": 1, "position": [660, 0],
          "notes": "Never main; the human merges (Art. XIV.4)"},
         ifnode("Notify the cohort?", "={{ $json.decision.action === 'PUBLISH' && $json.notify }}", [880, 0]),
         {"parameters": {"fromEmail": "ATTACH_AT_IMPORT", "toEmail": "={{$json.learner_ref}}",
                         "subject": "=Lesson updated: {{$json.title}} ({{$json.previous_version}} → {{$json.new_version}})",
                         "text": "={{$json.card_text}}"},
          "id": "card", "name": "CARD (consented only)", "type": "n8n-nodes-base.emailSend",
          "typeVersion": 2.1, "position": [1100, -80],
          "notes": "Three lines; opt-out in every message (Art. IV.3)"},
         code("RECEIPT", "// chain row: action, artifact hashes, notified handles (hashed), cost\n"
                         "return $input.all();", [1320, 0])],
        {"From triage": {"main": [[{"node": "RENDER_BODY", "type": "main", "index": 0}]]},
         "RENDER_BODY": {"main": [[{"node": "RENDER_DIFF", "type": "main", "index": 0}]]},
         "RENDER_DIFF": {"main": [[{"node": "COMMIT (bot branch)", "type": "main", "index": 0}]]},
         "COMMIT (bot branch)": {"main": [[{"node": "Notify the cohort?", "type": "main", "index": 0}]]},
         "Notify the cohort?": {"main": [[{"node": "CARD (consented only)", "type": "main", "index": 0}], []]},
         "CARD (consented only)": {"main": [[{"node": "RECEIPT", "type": "main", "index": 0}]]}},
        "One commit per decision; the receipt names the commit and the commit names the receipt.")
    (OUT / "wf-cr-2-act.json").write_text(json.dumps(act, indent=2) + "\n")

    learn = workflow(
        "wf-cr-3-learn",
        [sched("Every 15 minutes", 15, [0, 0]),
         code("READ_TELEMETRY", "// consented rows only; hashed handles; rejects are counted\n"
                                "return $input.all();", [220, 0]),
         code("COHORT_WINDOW", "// per published version: n, quiz_delta, hours_since_publish (or unmeasured)\n"
                               "return $input.all();", [440, 0]),
         code("GATE_EVAL (policy revert)", "const {decide} = require('./policy_node.js');\n"
                                           "return $input.all().map(i => ({json: {decision: decide(i.json.input)}}));", [660, 0]),
         ifnode("Gate satisfied?", "={{ $json.decision.action === 'REVERT' }}", [880, 0]),
         http("REVERT_NOW", "ATTACH_AT_IMPORT/webhook/" + WIRING["act"], "POST", '={{JSON.stringify($json)}}', [1100, -80]),
         code("STUCK_CHECK", "// consecutive_wrong >= 2 or dwell >= 3x median, per concept\n"
                             "return $input.all();", [1100, 120]),
         code("DISPATCH", "// one concept, two minutes, one practice item, opt-out in the message\n"
                          "return $input.all();", [1320, 120])],
        {"Every 15 minutes": {"main": [[{"node": "READ_TELEMETRY", "type": "main", "index": 0}]]},
         "READ_TELEMETRY": {"main": [[{"node": "COHORT_WINDOW", "type": "main", "index": 0}]]},
         "COHORT_WINDOW": {"main": [[{"node": "GATE_EVAL (policy revert)", "type": "main", "index": 0}]]},
         "GATE_EVAL (policy revert)": {"main": [[{"node": "Gate satisfied?", "type": "main", "index": 0}]]},
         "Gate satisfied?": {"main": [[{"node": "REVERT_NOW", "type": "main", "index": 0}],
                                      [{"node": "STUCK_CHECK", "type": "main", "index": 0}]]},
         "STUCK_CHECK": {"main": [[{"node": "DISPATCH", "type": "main", "index": 0}]]}},
        "n < 5 or a missing metric is `unmeasured` — the loop never reverts on a hunch (Art. XI).")
    (OUT / "wf-cr-3-learn.json").write_text(json.dumps(learn, indent=2) + "\n")

    digest = workflow(
        "wf-cr-4-digest",
        [sched("07:30 daily", 1440, [0, 0]),
         code("READ_RECEIPTS", "// the last 24h, chained; verify_chain() before rendering\n"
                               "return $input.all();", [220, 0]),
         code("ORDER_SECTIONS", "// refusals first, then what changed, learners, discipline\n"
                                "return $input.all();", [440, 0]),
         code("RENDER_4KB", "// trims oldest-first, never refusals; prints `unmeasured` where true\n"
                            "return $input.all();", [660, 0]),
         {"parameters": {"operation": "sendMessage", "chatId": "ATTACH_AT_IMPORT", "text": "={{$json.digest}}",
                         "additionalFields": {}},
          "id": "send-digest", "name": "SEND (Telegram)", "type": "n8n-nodes-base.telegram",
          "typeVersion": 1.2, "position": [880, 0]},
         code("VERIFY_CHAIN", "// exit 1 with a DIGEST FAILED banner if any row hash is off\n"
                              "return $input.all();", [1100, 0])],
        {"07:30 daily": {"main": [[{"node": "READ_RECEIPTS", "type": "main", "index": 0}]]},
         "READ_RECEIPTS": {"main": [[{"node": "ORDER_SECTIONS", "type": "main", "index": 0}]]},
         "ORDER_SECTIONS": {"main": [[{"node": "RENDER_4KB", "type": "main", "index": 0}]]},
         "RENDER_4KB": {"main": [[{"node": "SEND (Telegram)", "type": "main", "index": 0}]]},
         "SEND (Telegram)": {"main": [[{"node": "VERIFY_CHAIN", "type": "main", "index": 0}]]}},
        "A broken chain is louder than a missing message: DIGEST FAILED, exit 1.")
    (OUT / "wf-cr-4-digest.json").write_text(json.dumps(digest, indent=2) + "\n")

    errors = workflow(
        "CR-9 · errors → receipt",
        [{"parameters": {}, "id": "error-trigger", "name": "ERROR TRIGGER",
          "type": "n8n-nodes-base.errorTrigger", "typeVersion": 1, "position": [0, 0]},
         code("BUILD_RECEIPT",
              "// an unhandled failure still lands on the ledger (WIRING §3.1, requirement 4)\n"
              "const err = $json.error || {};\n"
              "return [{ json: { event_id: 'op-error', kind: 'change', mode: 'live',\n"
              "  decision: { action: 'ESCALATE', reason_codes: ['write_failed'], authority: 'PA0' },\n"
              "  artifact: null, actor: 'system', label: (err.message || 'workflow error').slice(0, 160),\n"
              "  workflow: $json.workflow && $json.workflow.name, execution: $json.execution && $json.execution.id } }];",
              [220, 0]),
         http("APPEND_RECEIPT", "http://runner:8081/receipt", "POST",
              "={{ JSON.stringify($json) }}", [440, 0], "the local runner appends it to the chain"),
         http("DIGEST_LINE", "http://runner:8081/degraded", "POST",
              "={{ JSON.stringify({ reason: 'workflow_error', receipt_id: $json.receipt_id }) }}",
              [660, 0], "the digest must say it out loud")],
        {"ERROR TRIGGER": {"main": [[{"node": "BUILD_RECEIPT", "type": "main", "index": 0}]]},
         "BUILD_RECEIPT": {"main": [[{"node": "APPEND_RECEIPT", "type": "main", "index": 0}]]},
         "APPEND_RECEIPT": {"main": [[{"node": "DIGEST_LINE", "type": "main", "index": 0}]]}},
        "Attached to every CR workflow's error output at import time; a crash must be a receipt, not silence.")
    (OUT / "wf-cr-9-errors.json").write_text(json.dumps(errors, indent=2) + "\n")

    print(f"wrote {len(list(OUT.glob('wf-cr-*.json')))} workflow exports · policy_node.js sha256={NODE_HASH[:16]}…")
    for path in sorted(OUT.glob("wf-cr-*.json")):
        print(" ", path.relative_to(ROOT), f"({path.stat().st_size} bytes)")


def do_import() -> int:
    """Import the exports into the configured n8n instance and record the ids (WIRING §6)."""
    import sys
    sys.path.insert(0, str(ROOT / "app" / "lib"))
    import n8n
    from config import Config
    cfg = Config()
    client = n8n.N8nClient(cfg.get("N8N_BASE_URL"), cfg.get("N8N_API_KEY"),
                           instance_version=cfg.get("N8N_INSTANCE_VERSION"))
    result = client.import_exports(OUT)
    print(json.dumps({"ok": result["ok"], "ids": result["ids"], "path": result["path"]}, indent=2))
    return 0 if result["ok"] else 2


def verify_import(client) -> dict:
    """Audit the instance's own copies against the import contract (review C2).

    The demo-day failure mode this gate exists for: `--import` says OK, the canvas looks right,
    and the first run dies on a node that still says `ATTACH_AT_IMPORT` (a placeholder URL the
    export was never allowed to fill) or on an error workflow nobody attached. So the gate reads
    every workflow back from the instance and checks the three things a rehearsal can't paper
    over -- whatever `--import` just claimed is irrelevant here; only the stored object counts:

      1. present: every generated workflow name exists on the instance (by id or by name);
      2. no placeholders: no `ATTACH_AT_IMPORT` anywhere in any stored parameter or credential
         ref, and every offender is reported as workflow · node · parameter;
      3. error wiring: `wf-cr-9-errors`' id is in `settings.errorWorkflow` of the other five.

    Returns {ok, checked, problems: [{workflow, node, parameter, problem}]} — never print secrets:
    placeholders are constants in the exports, so naming them leaks nothing.
    """
    problems = []
    ids: dict = {}
    listing = client.list_workflows()
    if not listing["ok"]:
        return {"ok": False, "checked": 0,
                "problems": [{"workflow": "*", "node": "-", "parameter": "-",
                              "problem": f"cannot list workflows: {listing.get('message', 'not ok')}"}]}
    by_name = {w.get("name"): w for w in listing.get("workflows", [])}
    for path in sorted(OUT.glob("wf-cr-*.json")):
        export = json.loads(path.read_text())
        name = export.get("name")
        match = next((w for w in listing.get("workflows", []) if w.get("name") == name
                      and w.get("id") is not None), None)
        # The instance's own listing is the source of presence. The importer's ids file is only a
        # hint for reading back a copy the listing already vouches for — trusting it for presence
        # would let a stale ids file (from another deployment, another checkout) tell the gate a
        # workflow exists when the instance never heard of it. If the name is not in the listing,
        # the workflow is not deployed, and the gate says so.
        wid = match["id"] if match else None
        if not wid:
            problems.append({"workflow": name, "node": "-", "parameter": "-",
                             "problem": "not found on the instance (run --import first)"})
            continue
        ids[name] = wid
        fetched = client.get_workflow(wid)
        if not fetched["ok"]:
            problems.append({"workflow": name, "node": "-", "parameter": "-",
                             "problem": f"read-back failed: {fetched.get('message', 'not ok')}"})
            continue
        stored = fetched["workflow"] or {}
        for node in stored.get("nodes", []):
            for key, value in (node.get("parameters") or {}).items():
                if isinstance(value, str) and "ATTACH_AT_IMPORT" in value:
                    problems.append({"workflow": name, "node": node.get("name"), "parameter": key,
                                     "problem": "still a placeholder: attach the real value (SETUP §3)"})
            for key, value in (node.get("credentials") or {}).items():
                if isinstance(value, dict) and "ATTACH_AT_IMPORT" in json.dumps(value):
                    problems.append({"workflow": name, "node": node.get("name"), "parameter": f"credentials.{key}",
                                     "problem": "credential is a placeholder, not an attached id"})
    error_id = ids.get(ERR_NAME)
    for name, wid in ids.items():
        if name == ERR_NAME:
            continue
        fetched = client.get_workflow(wid)
        if fetched["ok"]:
            attached = ((fetched["workflow"] or {}).get("settings") or {}).get("errorWorkflow")
            if attached != error_id:
                problems.append({"workflow": name, "node": "-", "parameter": "settings.errorWorkflow",
                                 "problem": f"error workflow not attached (is {attached}, want {error_id})"})
    return {"ok": not problems, "checked": len(ids) + sum(1 for p in problems if "not found" in p["problem"]),
            "problems": problems}


def do_verify_import() -> int:
    import sys
    sys.path.insert(0, str(ROOT / "app" / "lib"))
    import n8n
    from config import Config
    cfg = Config()
    client = n8n.N8nClient(cfg.get("N8N_BASE_URL"), cfg.get("N8N_API_KEY"),
                           instance_version=cfg.get("N8N_INSTANCE_VERSION"))
    if not client.configured():
        print("verify-import: N8N_BASE_URL / N8N_API_KEY missing (SETUP §2)")
        return 2
    verdict = verify_import(client)
    for problem in verdict["problems"]:
        p = problem["problem"][0].upper() + problem["problem"][1:]
        print(f"  BROKEN  {problem['workflow']} · {problem['node']} · {problem['parameter']}: {p}")
    print(f"verify-import: {'OK' if verdict['ok'] else 'BROKEN'} — "
          f"{verdict['checked']} workflows checked, {len(verdict['problems'])} problem(s)")
    return 0 if verdict["ok"] else 2



def check() -> int:
    """--check: regenerate in memory and fail if any export on disk would change."""
    before = {p.name: p.read_text() for p in sorted(OUT.glob("wf-cr-*.json"))}
    main()
    after = {p.name: p.read_text() for p in sorted(OUT.glob("wf-cr-*.json"))}
    drift = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    if drift:
        print(f"DRIFT: {', '.join(drift)} — commit the regenerated exports")
        return 1
    print(f"in sync: {len(after)} exports match app/n8n/policy_node.js sha256={NODE_HASH[:16]}…")
    return 0


if __name__ == "__main__":
    import sys
    if "--import" in sys.argv:
        raise SystemExit(do_import())
    if "--verify-import" in sys.argv:
        raise SystemExit(do_verify_import())
    if "--check" in sys.argv:
        raise SystemExit(check())
    main()
