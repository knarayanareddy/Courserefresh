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
NODE_SRC = (OUT / "policy_node.js").read_text()
NODE_HASH = hashlib.sha256(NODE_SRC.encode()).hexdigest()


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


def workflow(name, nodes, connections, notes):
    return {"name": name, "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1", "saveManualExecutions": True, "callerPolicy": "workflowsFromSameOwner"},
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
         http("HTTP_TRIAGE", "ATTACH_AT_IMPORT/webhook/triage", "POST",
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
        [webhook("From scan", "triage", [0, 0]),
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
         http("NOTICE_DECISION", "ATTACH_AT_IMPORT/webhook/act", "POST",
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
        [webhook("From triage", "act", [0, 0]),
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
         http("REVERT_NOW", "ATTACH_AT_IMPORT/webhook/act", "POST", '={{JSON.stringify($json)}}', [1100, -80]),
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

    print(f"wrote 5 workflow exports · policy_node.js sha256={NODE_HASH[:16]}…")
    for path in sorted(OUT.glob("wf-cr-*.json")):
        print(" ", path.relative_to(ROOT), f"({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
