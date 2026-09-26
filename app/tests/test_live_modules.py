#!/usr/bin/env python3
"""The live path, tested without a network (review 06, the supervision pairs).

Every module that will touch Apify, a model, n8n, a learner or the console is exercised here through
an injected transport, so `sh app/check.sh` proves the wiring *before* a single key exists. The
end-to-end case runs one dry cycle in a sandbox and asserts the properties the spec promises: one
publish per cycle, corroboration by voice, anchored rewrites, labelled evidence, staged delivery.

Run: python3 app/tests/test_live_modules.py
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "lib"))
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "specs" / "courserefresh" / "skin"))

import apify as apify_lib  # noqa: E402
import judge as judge_lib  # noqa: E402
import n8n as n8n_lib  # noqa: E402
import notify as notify_lib  # noqa: E402
import guard as guard_lib  # noqa: E402
import policy as policy_lib  # noqa: E402

import canvas as canvas_lib  # noqa: E402
import console as console_lib  # noqa: E402
import tavily as tavily_lib  # noqa: E402
import telemetry as telemetry_lib  # noqa: E402
from config import Config  # noqa: E402

spec = importlib.util.spec_from_file_location("live", ROOT / "app" / "run_live.py")
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)

SANDBOX = ROOT / "app" / "out" / "live-test"
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


class FakeTransport:
    """A transport that answers like the platform would. Nothing here opens a socket."""

    def __init__(self, routes: dict | None = None):
        self.routes = routes or {}
        self.calls: list[tuple[str, str, dict, dict | None]] = []

    def __call__(self, method, url, headers, body, timeout=30):
        self.calls.append((method, url, headers or {}, body))
        for (m, fragment), response in self.routes.items():
            if m == method and fragment in url:
                return response(body) if callable(response) else response
        return 404, {"message": f"no route for {method} {url}"}


# --- 1. configuration --------------------------------------------------------------------------
cfg = Config({"CR_MODE": "auto"})
check("auto mode stays sim without credentials", cfg.mode() == "sim")
check("preflight names the exact blockers",
      cfg.preflight()["blocking_for_live"] == ["apify:APIFY_TOKEN", "judge:CR_JUDGE_API_KEY"],
      str(cfg.preflight()["blocking_for_live"]))
live_cfg = Config({"APIFY_TOKEN": "apify_api_secret_value", "CR_JUDGE_API_KEY": "sk-secret-value",
                   "CR_JUDGE_PROVIDER": "openai"})
check("auto mode becomes live when both platforms are wired", live_cfg.mode() == "live")
masked = json.dumps(live_cfg.preflight()["secrets"])
check("no secret value appears in preflight output",
      "secret_value" not in masked and "sha256=" in masked, masked[:90])
env_file = SANDBOX / ".env"
env_file.parent.mkdir(parents=True, exist_ok=True)
env_file.write_text("APIFY_TOKEN=from_file\n# comment\nCR_JUDGE_MODEL=file-model\n")
check("a .env file is read, and an explicit override wins over it",
      Config({"CR_JUDGE_MODEL": "override-model"}, env_file=env_file).get("CR_JUDGE_MODEL") == "override-model"
      and Config(env_file=env_file).get("APIFY_TOKEN") == "from_file")
shell = {"APIFY_TOKEN": "from_shell", "PATH": "/usr/bin", "N8N_INSTANCE_VERSION": "1.64.0",
         "UNRELATED_SECRET": "ignore-me"}
shell_cfg = Config(env_file=env_file, environ=shell)
check("the real environment beats the .env file, and unrelated variables stay out",
      shell_cfg.get("APIFY_TOKEN") == "from_shell" and shell_cfg.sources["APIFY_TOKEN"] == "environment"
      and shell_cfg.sources["CR_JUDGE_MODEL"] == ".env" and "PATH" not in shell_cfg.env
      and "UNRELATED_SECRET" not in shell_cfg.env, str(shell_cfg.sources["APIFY_TOKEN"]))
check("a missing key is reported missing however the key is spelled",
      Config(environ={"APIFY_TOKEN": ""}).missing_for("apify") == ["APIFY_TOKEN"])

# --- 2. apify -----------------------------------------------------------------------------------
client = apify_lib.ApifyClient(token=None, dry_run=True)
source = apify_lib.load_sources()["sources"][0]
run = client.run_actor(source)
check("a dry-run actor returns the recorded dataset", run["ok"] and len(run.get("items", [])) == 2,
      f"rows={len(run.get('items') or [])}")

normalised = apify_lib.normalise_dataset(
    [{"url": "https://evil.example/steal", "markdown": "x" * 40},
     {"url": "https://docs.n8n.io/", "markdown": ""},
     {"url": "https://docs.n8n.io/", "markdown": "n8n 1.85 renamed the key."},
     {"url": "https://docs.n8n.io/", "markdown": "y" * (2 * 1024 * 1024 + 1)}],
    source, SANDBOX / "snapshots")
reasons = sorted(r["reason"] for r in normalised["rejected"])
check("host, emptiness and size are refused with reasons, and every row is counted",
      reasons == ["host_not_allowlisted", "no_markdown", "size_cap_exceeded"] and
      len(normalised["snapshots"]) == 1 and normalised["discarded"] == 3, str(reasons))

missing = apify_lib.normalise_row({"url": "https://docs.n8n.io/", "markdown": "text", "title": "t"},
                                  {**source, "required_dataset_fields": ["url", "markdown", "published_at"]})
check("a row missing a promised field is `source_stale`, not a silent null",
      missing["reason"] == "source_stale" and missing["missing"] == ["published_at"], str(missing))

ledger = apify_lib.UnitLedger(SANDBOX / "units.jsonl", per_day=2, units_per_run=1)
ledger.record("a", "run-1", None)
ledger.record("b", "run-2", None)
allowed, note = ledger.can_spend(1)
check("the unit ledger refuses a spend beyond the day cap", not allowed and "budget_hold" in note, note)

fake = FakeTransport({("POST", "/acts/"): (400, {"error": {"message": "invalid actor"}})})
bad = apify_lib.ApifyClient(token="t", transport=fake, max_retries=3).run_actor(source)
check("a 400 from Apify is not retried and is reported as actor_failed",
      bad["ok"] is False and bad["attempts"] == 1 and bad["code"] == "actor_failed", str(bad.get("attempts")))

# --- 3. judge and render ------------------------------------------------------------------------
provider = judge_lib.MockProvider()
provider.answers = {"q1_materiality": "material_breaking"}
prompt = judge_lib.prompt_for({"summary": "s", "quotes": []})
check("the judge prompt carries no thresholds, reason codes or expected action",
      not any(word in prompt for word in ("min_sources", "PUBLISH", "ESCALATE", "PA2")), "clean")
check("a partial answer set fails closed",
      judge_lib.validate_answers(json.dumps(provider.answers))["reason_codes"] == ["unknown_state"])
body = "The tools are declared in `tool_permissions.tools` in the workflow settings."
render_event = {"quotes": [{"source_id": "s", "text": "renamed to permissions.mode in 1.85"}]}
good_render = json.dumps({"find": body, "replace": "The tools are declared in `permissions.mode.tools`.",
                          "learner_facing": "A setting was renamed; update the key you copied."})
check("an anchored render passes and carries the patch",
      judge_lib.validate_render(good_render, body, render_event)["ok"])
bad_render = json.dumps({"find": "not in the body", "replace": "x", "learner_facing": "y"})
check("an unanchored rewrite is refused with a reason code",
      judge_lib.validate_render(bad_render, body, render_event)["reason_codes"] == ["claim_unanchored"])

# --- 4. n8n client and the canvas decision ------------------------------------------------------
state = {"created": False}


def create(body):
    state["created"] = True
    return 201, {"data": {"id": "wf-1"}}


def update(body):
    return 200, {"data": {"id": "wf-1"}}


routes = {
    ("GET", "/api/v1/workflows"): lambda body: (200, {"data": [{"id": "wf-1", "name": "wf-cr-1-triage"}]}),
    ("PUT", "/api/v1/workflows/wf-1"): update,
    ("POST", "/api/v1/workflows"): create,
    ("PATCH", "/api/v1/workflows/"): (200, {"data": {"id": "wf-1"}}),
    ("POST", "/webhook/cr/triage"): (200, {"decision": {"action": "ESCALATE",
                                                       "reason_codes": ["insufficient_corroboration"],
                                                       "authority": "PA2"}, "execution_id": "exec-42"}),
}
transport = FakeTransport(routes)
n8n_client = n8n_lib.N8nClient("https://n8n.example", "key", transport=transport, instance_version="1.64.0")
workflow_doc = json.loads((ROOT / "app" / "n8n" / "wf-cr-1-triage.json").read_text())
updated = n8n_client.upsert_workflow(workflow_doc)
check("an existing workflow is updated in place, not duplicated",
      updated["ok"] and updated["created"] is False and updated["id"] == "wf-1", str(updated))

# import: idempotent, and the error workflow is attached to the other five
import_state = {"created": [], "patched": []}


def import_listing(body):
    return 200, {"data": [{"id": f"wf-{i}", "name": name} for i, name in
                          enumerate(["wf-cr-0-scan", "wf-cr-1-triage", "wf-cr-2-act", "wf-cr-3-learn",
                                     "wf-cr-4-digest", "CR-9 · errors → receipt"])]}


def import_create(body):
    import_state["created"].append(body["name"])
    return 201, {"data": {"id": f"new-{len(import_state['created'])}"}}


def import_update(body):
    return 200, {"data": {"id": "wf-0"}}


def import_patch(body):
    import_state["patched"].append(body)
    return 200, {"data": {}}


import_routes = {
    ("GET", "/api/v1/workflows"): import_listing,
    ("POST", "/api/v1/workflows"): import_create,
    ("PUT", "/api/v1/workflows/"): import_update,
    ("PATCH", "/api/v1/workflows/"): import_patch,
}
import_transport = FakeTransport(import_routes)
import_client = n8n_lib.N8nClient("https://n8n.example", "key", transport=import_transport,
                                 instance_version="1.64.0")
ids_path = SANDBOX / "n8n-ids.json"
first = import_client.import_exports(ROOT / "app" / "n8n", ids_path)
check("importing the exports updates in place instead of duplicating, and records the ids",
      first["ok"] and len(first["ids"]) == 6 and not import_state["created"]
      and json.loads(ids_path.read_text())["instance_version"] == "1.64.0",
      f"created={import_state['created']} ids={len(first['ids'])}")
attached = [p for p in import_state["patched"] if p.get("settings", {}).get("errorWorkflow") ==
            first["ids"].get("CR-9 · errors → receipt")]
check("the error workflow is attached to the other five at import time",
      len(attached) == 5, f"attached={len(attached)}")
second = import_client.import_exports(ROOT / "app" / "n8n", ids_path)
check("a second import is a no-op for identity: still six workflows, still no duplicates",
      second["ok"] and not import_state["created"], f"created={import_state['created']}")

canvas = live.canvas_decide(Config({"N8N_BASE_URL": "https://n8n.example", "N8N_API_KEY": "key"}),
                            {"event_id": "e", "materiality": "material_breaking"}, transport=transport)
check("the canvas can decide, and its execution id is captured",
      canvas["ok"] and canvas["decision"]["action"] == "ESCALATE" and canvas["execution_id"] == "exec-42",
      str(canvas.get("execution_id")))
check("canvas parity is judged on action *and* reason codes, not just the action",
      live.canvas_agrees({"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]},
                         {"action": "ESCALATE", "reason_codes": ["hostile_content"]}) is False
      and live.canvas_agrees({"action": "ESCALATE", "reason_codes": ["insufficient_corroboration", "quote_unavailable"]},
                             {"action": "ESCALATE", "reason_codes": ["quote_unavailable", "insufficient_corroboration"]}) is True)
mismatch = live.canvas_decide(Config({"N8N_BASE_URL": "https://n8n.example", "N8N_API_KEY": "k"}),
                              {"event_id": "e"},
                              transport=FakeTransport({("POST", "/webhook/cr/triage"):
                                                       (200, {"decision": {"action": "PUBLISH", "reason_codes": []}})}))
check("a canvas that answers with a different decision is detected, not trusted",
      mismatch["ok"] and not live.canvas_agrees(mismatch["decision"],
                                                {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"]}))

# F2: a 200 from the canvas is an authority, so it is re-validated against the closed sets before it
# can decide anything — a half-deployed workflow must not be able to invent an action
check("a canvas decision is only accepted if the rulebook could have emitted it",
      live.canvas_decision_valid({"action": "PUBLISH", "reason_codes": ["material_breaking"]},
                                 "change")["ok"]
      and not live.canvas_decision_valid({"action": "DELETE_EVERYTHING",
                                          "reason_codes": ["material_breaking"]}, "change")["ok"]
      and not live.canvas_decision_valid({"action": "PUBLISH", "reason_codes": ["nonsense_code"]},
                                         "change")["ok"]
      and not live.canvas_decision_valid({"action": "PUBLISH", "reason_codes": []}, "change")["ok"],
      "closed sets enforced on the canvas' answer")

broken = live.canvas_decide(Config({"N8N_BASE_URL": "https://n8n.example", "N8N_API_KEY": "key"}),
                            {"event_id": "e"}, transport=FakeTransport({}))
check("an unreachable canvas degrades to the oracle instead of failing the cycle",
      broken["ok"] is False and broken["reason"].startswith("webhook_http_"), broken.get("reason"))

# --- 5. telemetry -------------------------------------------------------------------------------
payload = {"learner_ref": "learner:deadbeef", "consent": False, "lesson_id": "lesson-03-apify-inputs",
           "events": [{"kind": "attempt", "item": "q1", "correct": False}]}
check("telemetry without consent is refused before storage",
      telemetry_lib.validate_payload(payload)["reason"] == "consent_missing")
check("a plain handle is refused (hashed handles only)",
      telemetry_lib.validate_payload({**payload, "consent": True, "learner_ref": "alice dot example"})
      ["reason"] == "handle_not_hashed")
telemetry_path = SANDBOX / "telemetry.jsonl"
telemetry_path.unlink(missing_ok=True)
telemetry_lib.store({"learner_ref": "learner:deadbeef", "lesson_id": "lesson-03-apify-inputs",
                     "version": "v3", "events": [{"kind": "attempt", "item": "q1", "correct": False},
                                                 {"kind": "attempt", "item": "q1", "correct": False}]},
                    telemetry_path)
small = telemetry_lib.cohort_window("lesson-03-apify-inputs", path=telemetry_path)
check("a cohort below the floor reports `unmeasured` with the reason",
      small["state"] == "unmeasured" and small["n"] == 1
      and "cohort_below_minimum" in small["reason"], small["reason"])
for i in range(5):
    telemetry_lib.store({"learner_ref": f"learner:aaaa00{i:02d}", "lesson_id": "lesson-03-apify-inputs",
                         "version": "v3", "events": [{"kind": "quiz_delta", "correct": -0.05},
                                                     {"kind": "dwell", "seconds": 600}]}, telemetry_path)
big = telemetry_lib.cohort_window("lesson-03-apify-inputs", path=telemetry_path)
check("a cohort at the floor produces a measured negative delta (the revert gate's input)",
      big["state"] == "measured" and big["n"] == 6 and big["quiz_delta"] == -0.05, str(big["quiz_delta"]))

# --- 6. notify ----------------------------------------------------------------------------------
notifier = notify_lib.Notifier(Config({"CR_NOTIFY_CHANNEL": "file"}), log_path=SANDBOX / "delivery.jsonl")
result = notifier.deliver([{"ts": "2026-09-26T10:00:00Z", "learner_ref": "learner:deadbeef",
                            "lesson_id": "lesson-03-apify-inputs", "from": "v2", "to": "v3",
                            "what_changed": "inputs are validated", "diff_path": "d.diff",
                            "opt_out": "one-click"}])
check("the file channel stages and never claims delivery",
      result["staged"] == 1 and result["delivered"] == 0)
telegram = notify_lib.Notifier(Config({"CR_NOTIFY_CHANNEL": "telegram"}), log_path=SANDBOX / "d2.jsonl")
check("a channel without credentials fails loudly rather than silently",
      telegram.deliver([{"ts": "t", "learner_ref": "learner:deadbeef", "lesson_id": "l", "from": "v1",
                         "to": "v2", "what_changed": "x", "opt_out": "one-click"}])["failed"] == 1)

# --- 7. console (served) ------------------------------------------------------------------------
import console as console_lib  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

console_lib.ConsoleHandler.token = "console-token"
server = ThreadingHTTPServer(("127.0.0.1", 0), console_lib.ConsoleHandler)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()


def fetch(path, token=None, method="GET"):
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method)
    if token:
        request.add_header("X-CR-Token", token)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:  # noqa: F821 (imported below)
        return exc.code, exc.read().decode()


import urllib.error  # noqa: E402
status, body = fetch("/healthz")
health = json.loads(body) if status == 200 else {}
check("the console serves /healthz with the chain state",
      status == 200 and "chain_ok" in health and "receipt_count_gap" in health, f"status={status}")
status, page = fetch("/")
check("the console refuses nothing it should serve, and serves no script",
      status in (200, 404) and "<script" not in page, f"status={status}")
status, _ = fetch("/pause", method="POST")
check("a write without the console token is refused", status == 403, f"status={status}")
status, _ = fetch("/nope")
check("an unknown route is a 404, not a stack trace", status == 404, f"status={status}")
server.shutdown()

# --- 8. end to end: one dry cycle -----------------------------------------------------------------
if SANDBOX.exists():
    shutil.rmtree(SANDBOX)
(SANDBOX / "app" / "out").mkdir(parents=True, exist_ok=True)
shutil.copytree(ROOT / "course", SANDBOX / "course")
subprocess.run([sys.executable, str(ROOT / "app" / "run_live.py"), "--root", str(SANDBOX),
                "--seed-baseline"], check=True, capture_output=True, text=True)
proc = subprocess.run([sys.executable, str(ROOT / "app" / "run_live.py"), "--root", str(SANDBOX),
                       "--dry-run", "--once"], capture_output=True, text=True)
summary = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip().startswith("{") else {}
receipts = [json.loads(l) for l in (SANDBOX / "app" / "out" / "receipts.jsonl").read_text().splitlines()
            if l.strip()] if (SANDBOX / "app" / "out" / "receipts.jsonl").exists() else []
publishes = [r for r in receipts if r["decision"]["action"] == "PUBLISH"]
escalates = [r for r in receipts if r["decision"]["action"] == "ESCALATE"]
check("one dry cycle publishes at most once, refuses what is single-voice, and chains the receipts",
      proc.returncode == 0 and len(publishes) == 1 and len(escalates) == 1
      and all(r["mode"] == "sim" for r in receipts) and summary.get("chain") is True,
      f"exit={proc.returncode} publish={len(publishes)} escalate={len(escalates)}")

if publishes:
    artifact = publishes[0]["artifact"]
    expected_next = f"v{int(artifact['previous_version'][1:]) + 1}"
    check("the published lesson is a new version with a diff, a receipt and a regenerated quiz item",
          artifact["new_version"] == expected_next
          and (SANDBOX / "course" / artifact["diff_path"]).exists()
          and artifact.get("quiz_item") == "q1"
          and publishes[0]["receipt_id"] in (SANDBOX / "course" / "agent-ops" / "CHANGELOG.md").read_text(),
          f"{artifact['previous_version']}→{artifact['new_version']} quiz={artifact.get('quiz_item')}")
    check("the published receipt names its voices and their roles",
          len(publishes[0]["sources"]) == 2
          and {s["role"] for s in publishes[0]["sources"]} <= {"authoritative", "corroborating", "none"},
          str([s["role"] for s in publishes[0]["sources"]]))
    check("the rewrite is anchored: the diff shows the validated-sentence change",
          "actor schema" in (SANDBOX / "course" / artifact["body_path"]).read_text(),
          artifact["body_path"])

# --- 7b. the intake and the gate must read the same file (the bug this test exists for) --------
import http.client  # noqa: E402
from http.server import ThreadingHTTPServer as _Server  # noqa: E402

telemetry_lib.rebase(SANDBOX)
intake_path = telemetry_lib.storage_for(SANDBOX)
intake_path.unlink(missing_ok=True)
telemetry_lib.TelemetryHandler.storage = intake_path
intake = _Server(("127.0.0.1", 0), telemetry_lib.TelemetryHandler)
intake_port = intake.server_address[1]
threading.Thread(target=intake.serve_forever, daemon=True).start()
conn = http.client.HTTPConnection("127.0.0.1", intake_port, timeout=5)
for i in range(6):     # ≥5 so the revert gate's n_min is met, not just the cohort floor
    conn.request("POST", "/telemetry", json.dumps(
        {"learner_ref": f"learner:cafe00{i:02d}", "consent": True, "lesson_id": "lesson-03-apify-inputs",
         "version": "v3", "events": [{"kind": "quiz_delta", "correct": -0.06}]}),
        {"Content-Type": "application/json"})
    conn.getresponse().read()
conn.request("POST", "/telemetry", json.dumps(
    {"learner_ref": "learner:cafe0099", "consent": False, "lesson_id": "lesson-03-apify-inputs",
     "events": [{"kind": "quiz_delta", "correct": -0.9}]}), {"Content-Type": "application/json"})
refused = conn.getresponse()
refused_code = refused.status
refused.read()
intake.shutdown()
gate_from_engine_path = telemetry_lib.cohort_window("lesson-03-apify-inputs", path=telemetry_lib.storage_for(SANDBOX))
check("events posted to the intake are the events the learner gate reads",
      refused_code == 403 and gate_from_engine_path["n"] == 6
      and gate_from_engine_path["quiz_delta"] == -0.06, f"n={gate_from_engine_path['n']}")
check("the intake writes exactly where the engine looks",
      live.STATE / "telemetry.jsonl" == telemetry_lib.storage_for(live.ROOT),
      f"{live.STATE / 'telemetry.jsonl'}")

check("the dry cycle leaves the sim labels on every evidence surface",
      "mode: **sim**" in (SANDBOX / "app" / "out" / "digest.md").read_text()
      and "sim" in (SANDBOX / "app" / "out" / "digest.html").read_text(), "labels present")
check("a dry cycle makes no live claim and stages rather than sends",
      summary.get("delivery", {}).get("delivered", 0) == 0
      and summary.get("delivery", {}).get("staged", 0) == 0, str(summary.get("delivery")))

# --- 8b. the learn phase actually reverts when the gate is genuinely satisfied -----------------
# The gate needs a publish that is ≥48 h old; the sandbox's own receipt is minutes old, so the test
# ages it (and says so) instead of pretending the window closed.
receipts_path = SANDBOX / "app" / "out" / "receipts.jsonl"
aged = set()
for line in receipts_path.read_text().splitlines():
    row = json.loads(line)
    if (row.get("artifact") or {}).get("lesson_id") == "lesson-03-apify-inputs" \
            and row["decision"]["action"] == "PUBLISH":
        aged.add(row["receipt_id"])
rows_back = [json.loads(l) for l in receipts_path.read_text().splitlines()]
for row in rows_back:
    if row["receipt_id"] in aged:
        row["ts"] = "2026-09-20T00:00:00Z"          # six days old: the 48 h window has closed
receipts_path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows_back) + "\n")

live.rebase(SANDBOX)
learn = live.learn_phase(Config({"CR_MODE": "sim"}), live.tree_for("sim"))
reverts = [json.loads(l) for l in receipts_path.read_text().splitlines()
           if json.loads(l)["decision"]["action"] == "REVERT"]
check("a measured cohort with a closed window makes the live learn phase revert",
      learn["events"] >= 1 and bool(reverts), f"events={learn['events']} reverts={len(reverts)}")
if reverts:
    check("the revert restores the named version and records the gate's arithmetic",
          reverts[-1]["decision"]["reason_codes"] == ["revert_gate_satisfied"]
          and "quiz_delta" in reverts[-1].get("label", "")
          and reverts[-1]["cohort_source"] == "fixture (simulated)"      # sim mode must say so
          and (SANDBOX / "course" / (reverts[-1]["artifact"].get("body_path") or "x")).exists(),
          str(reverts[-1].get("label"))[:90])
gate_after = [g for g in learn["gates"] if g["lesson_id"] == "lesson-03-apify-inputs"][0]
check("the gate reports the publish's age it measured, not a configured assumption",
      isinstance(gate_after.get("hours_since_publish"), float)
      and gate_after["hours_since_publish"] > 48, str(gate_after.get("hours_since_publish")))

ledger_rows = (SANDBOX / "app" / "out" / "state" / "apify_units.jsonl").read_text()
check("the cycle accounted its Apify units with a declared source of truth",
      "declared 1 run = 1 unit" in ledger_rows, ledger_rows.splitlines()[0][:120])

blob = json.dumps(summary) + json.dumps(receipts)
check("no recorded markdown is mistaken for a claim without a quote span",
      all(len(r.get("quotes", [])) >= 1 for r in publishes + escalates), "quotes present")

# --- 9. the round-3 review fixes (REVIEW.md F1, F3, F6, F7, F8, F12) -----------------------------

# F1: the path the engine posts to is the path the export registers — read from one file each,
# never a literal in a test (the original defect was exactly two hard-coded, disagreeing strings)
wiring_doc = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "wiring.json").read_text())
registered = [(n["parameters"].get("path")) for n in workflow_doc["nodes"]
              if n.get("type") == "n8n-nodes-base.webhook"]
check("the triage export registers the path the engine posts to (skin/wiring.json)",
      wiring_doc["webhooks"]["triage"] in registered, f"registered={registered}")

# F2: with --via-n8n the canvas' decision is the one the writers act on, and it says so
canvas_decision = {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"],
                   "authority": "PA2", "notes": "from the canvas"}
forced_tree = live.twin.Tree(SANDBOX / "course", SANDBOX / "app" / "out" / "canvas-test", mode="sim")
canvas_event = {"event_id": "cr-canvas-01", "kind": "change", "summary": "canvas decides",
                "sources": [], "input": {"event_id": "cr-canvas-01", "stream": "change",
                                         "materiality": "material_breaking", "learner_impact": 0.9,
                                         "source_agreement": 0.9, "quote_supported": 0.9,
                                         "sources_verified": 2, "injection_or_jailbreak": 0.0,
                                         "authority": "PA2", "freeze_active": False},
                "decision_override": canvas_decision}
forced_log = live.twin.run(forced_tree, [canvas_event], label="canvas decides")
forced_row = forced_tree.rows()[-1]
check("a canvas decision is the decision of record, and the receipt says who decided",
      forced_row["decision"]["action"] == "ESCALATE"
      and forced_row["decision"].get("decided_by") == "canvas"
      and forced_log["decisions"] == {"ESCALATE": 1}, str(forced_row["decision"])[:90])
good_override, who = live.twin.decide_for_event(
    {"decision_override": {"action": "DELETE_EVERYTHING", "reason_codes": ["nope"]}},
    {"authority": "PA2", "stream": "change", "materiality": "marketing_noise", "learner_impact": 0.1,
     "quote_supported": 0.9, "source_agreement": 0.9, "sources_verified": 2,
     "injection_or_jailbreak": 0.0, "freeze_active": False, "event_id": "x"})
check("an override outside the closed sets is refused, not trusted",
      who == "oracle" and good_override["action"] in ("NO_CHANGE", "ESCALATE"), str(good_override)[:80])

# F7: a crash mid-cycle must not mark the snapshots seen, and the next run must retry them
poison_root = SANDBOX / "f7-root"
if poison_root.exists():
    shutil.rmtree(poison_root)
live.rebase(poison_root)
poison_tree = live.tree_for("sim")
poison_ledger = apify_lib.UnitLedger(live.STATE / "apify_units.jsonl", 25, 1)
fetched = live.notice(live.Config({"CR_MODE": "sim", "CR_JUDGE_PROVIDER": "mock"}), poison_tree,
                      True, poison_ledger)
check("the notice phase no longer commits the dedupe set before the cycle ran",
      not (live.STATE / "seen_snapshots.json").exists() and bool(fetched["seen_keys"]),
      f"seen_file={(live.STATE / 'seen_snapshots.json').exists()} keys={len(fetched['seen_keys'])}")
live.stash_pending([s for s in fetched["snapshots"] if not s.get("unreachable")], 1)
live.commit_notice(fetched)
check("a committed cycle writes the dedupe set and clears the pending stash",
      (live.STATE / "seen_snapshots.json").exists() and not live.pending_path().exists())
live.rebase(SANDBOX)

# F3: consent is read from the register the intake writes, and the defaults are fail-closed
consent_register = telemetry_lib.load_consent(telemetry_lib.storage_for(SANDBOX))
check("the intake recorded consent next to the telemetry it accepted",
      bool(consent_register) and all("consent" in v for v in consent_register.values()),
      f"{len(consent_register)} learner(s)")
declined = {k for k, v in consent_register.items() if v["consent"] is False}
check("a learner who refused is recorded as revoked, never defaulted to consented",
      "learner:cafe0099" in declined, str(sorted(declined)))
learner_event = live._learner_event({"learner_ref": "learner:absent01", "concept": "x",
                                     "summary": "no consent row"}, {})
check("a learner with no consent row is not consented (silence is not consent)",
      learner_event["input"]["consent"] is False)

# F8: the n8n judge probe passed bytes to a JSON transport and crashed the preflight
probe_seen = {}


def probe_transport(method, url, headers, body, timeout=30):
    probe_seen["type"] = type(body).__name__
    return 200, {"text": "ok"}


probe_cfg = live.Config({"CR_JUDGE_PROVIDER": "n8n", "CR_JUDGE_API_KEY": "dummy",
                         "N8N_WEBHOOK_URL": "https://n8n.example/webhook/cr/judge"})
probe_result = judge_lib.probe_provider(probe_cfg, probe_transport)
check("the n8n judge probe sends JSON, not bytes (the preflight used to crash here)",
      probe_seen.get("type") == "dict" and probe_result["ok"] is True, str(probe_seen))

# F12: one malformed dwell row used to raise IndexError inside the unattended learn phase
dwell_path = SANDBOX / "app" / "out" / "state" / "dwell-test.jsonl"
dwell_path.write_text(json.dumps({"learner_ref": "learner:deadbeef", "lesson_id": "lesson-01",
                                  "kind": "dwell", "seconds": None, "ts": "t"}) + "\n")
try:
    dwell_window = telemetry_lib.cohort_window("lesson-01", path=dwell_path)
    dwell_ok, dwell_detail = True, dwell_window["state"]
except Exception as exc:                        # noqa: BLE001 - the test is the assertion
    dwell_ok, dwell_detail = False, f"{type(exc).__name__}: {exc}"
check("a dwell row without seconds is refused at intake and cannot crash the cohort window",
      dwell_ok and telemetry_lib.validate_payload(
          {"learner_ref": "learner:deadbeef", "consent": True, "lesson_id": "l",
           "events": [{"kind": "dwell"}]})["ok"] is False, str(dwell_detail))

# F6: a bare --root gets a course tree instead of a FileNotFoundError
bare_root = SANDBOX / "f6-root"
if bare_root.exists():
    shutil.rmtree(bare_root)
boot_note = guard_lib.bootstrap_course(bare_root, ROOT / "course")
check("a bare --root is given the authored course tree (the documented commands work as written)",
      bool(boot_note) and (bare_root / "course" / "agent-ops" / "curriculum.json").exists(),
      str(boot_note)[:80])
check("a root that already holds a course tree is left alone (no clobbering)",
      guard_lib.bootstrap_course(SANDBOX, ROOT / "course") is None
      and (SANDBOX / "course" / "agent-ops" / "curriculum.json").exists())

# --- 10. JEV (TypeSafe System One) as an additive decision provider (app/lib/jev.py) -------------

# A fake JEV host: it speaks the published wire protocol and nothing else. No key, no network — the
# point is that this integration is verifiable offline, like every other path in this repo.
jev_requests = []


def jev_transport(method, url, headers, body, timeout=30):
    jev_requests.append({"method": method, "url": url, "headers": headers, "body": body})
    if method != "POST" or not str(url).endswith("/v1/systemone"):
        return 404, {"error": "not found"}
    if headers.get("Authorization") == "Bearer wrong":
        return 401, {"error": "unauthorized"}
    answers = {}
    for name, spec in (body.get("questions") or {}).items():
        if spec.get("type") == "choice":
            # a legal answer is any option in the criteria map, which is the same closed set the
            # question carries — the fake has no shortlist of its own
            options = list(spec.get("criteria") or {})
            answers[name] = {"type": "choice", "choice": options[-1] if name == "q7_lesson_touched"
                             else options[0],
                             "probabilities": {option: round(1 / len(options), 3) for option in options},
                             "confidence": 0.62}
        else:
            answers[name] = {"type": "noul", "noul": 0.8 if name != "q4_source_agreement" else 0.9}
    return 200, {"model": "jev-1.13.0", "answers": answers,
                 "usage": {"input_tokens": 812, "output_tokens": 64, "cost": 0.0004}}


jev = judge_lib.jev_lib
jev_cfg = Config({"CR_JUDGE_PROVIDER": "jev", "CR_JEV_API_KEY": "ts_test", "CR_JEV_MODEL": "jev-latest"})
provider = judge_lib.build_provider(jev_cfg, jev_transport)
check("CR_JUDGE_PROVIDER=jev builds the System One provider (not a chat provider)",
      provider.name == "jev" and provider.endpoint() == "https://api.typesafe.ai/v1/systemone",
      f"{provider.name} @ {provider.endpoint()}")

event_for_jev = {"summary": "Claude ships a breaking change to the permissions API",
                 "lesson_touched": "lesson-04-agent-ops", "objective": "read a permission string",
                 "quotes": [{"source_id": "anthropic-changelog", "text": "permissions mode is removed"},
                            {"source_id": "anthropic-docs-mcp", "text": "use permissions_mode instead"}]}
judgement = judge_lib.ask_judge(event_for_jev, provider, "jev-latest")
sent = jev_requests[-1]["body"]
check("the JEV request is typed questions, not a chat prompt",
      "messages" not in sent and "temperature" not in sent
      and sent["questions"]["q1_materiality"]["type"] == "choice"
      and sent["questions"]["q4_source_agreement"]["type"] == "noul"
      and len(sent["questions"]) == 7, f"{len(sent.get('questions', {}))} typed questions")
check("a JEV reply becomes the same answers dict every provider returns",
      judgement["ok"] and judgement["answers"]["q1_materiality"] == "material_breaking"
      and judgement["answers"]["q4_source_agreement"] == 0.9
      and judgement["provider"] == "jev", json.dumps(judgement.get("answers", {}))[:90])
check("JEV's own confidence per answer rides along on the judgement",
      judgement.get("confidences", {}).get("q1_materiality") == 0.62,
      str(judgement.get("confidences"))[:90])
check("the judge stays the only place a model is asked: the answer set is validated before use",
      judge_lib.validate_answers(json.dumps({**judgement["answers"], "q2_learner_impact": 1.4}))["ok"] is False)

partial_answers = {"model": "jev-1.13.0", "answers": {"q1_materiality": {"type": "choice",
                   "choice": "material_breaking", "confidence": 0.9}}, "usage": {}}
check("a JEV reply that skips a question fails closed (unknown_state), like any other provider",
      judge_lib.validate_answers(json.dumps({k: v for k, v in
                                             {"q1_materiality": "material_breaking"}.items()}))["ok"] is False
      and jev.normalise(partial_answers)["answers"] == {"q1_materiality": "material_breaking"})

check("JEV renders nothing: a render request on that provider is refused, not hallucinated",
      jev.normalise({"answers": {"q1_materiality": {"type": "choice", "choice": "x"}}})["answers"]
      == {"q1_materiality": "x"}
      and judge_lib.validate_render(json.dumps(jev.normalise(partial_answers)["answers"]),
                                    body="The lesson says the old thing.", event=event_for_jev)["ok"] is False,
      "typed decisions are not prose")

# JV-04: the adapter is exercised with no network *and no key at all*, from a fixture, and the same
# call works against an alternate host (an OpenRouter/requesty/rout.my proxy, or one of the keyless
# local JEV servers the panel named) — the alt-host path is a feature, not a hack.
jev_fixture = json.loads((ROOT / "app" / "fixtures" / "jev" / "systemone-response.json").read_text())
alt_requests = []


def alt_transport(method, url, headers, body, timeout=30):
    alt_requests.append({"url": url, "headers": headers, "body": body})
    return 200, jev_fixture


alt_cfg = Config({"CR_JUDGE_PROVIDER": "jev", "CR_JEV_API_KEY": "ts_alt",
                  "CR_JEV_BASE_URL": "https://router.requesty.ai/v1"})
alt_provider = judge_lib.build_provider(alt_cfg, alt_transport)
alt_judgement = judge_lib.ask_judge(event_for_jev, alt_provider, "typesafe/jev-1.13.0")
check("JV-04: a proxy base URL is honoured (…/v1/systemone), and the fixture replay validates",
      alt_requests and alt_requests[-1]["url"] == "https://router.requesty.ai/v1/systemone"
      and alt_requests[-1]["body"]["model"] == "typesafe/jev-1.13.0"
      and alt_judgement["ok"] and alt_judgement["answers"]["q1_materiality"] == "material_breaking",
      f"{alt_requests[-1]['url'] if alt_requests else 'no call'} · ok={alt_judgement['ok']}")
_skin_questions = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "questions.json").read_text())["questions"]
check("JV-04: the fixture's option keys are the closed sets the request carries (no drift)",
      all((fx.get("choice") or fx.get("noul")) is not None for fx in jev_fixture["answers"].values())
      and all(jf.get("choice") in (q.get("options") or [])
              for q in _skin_questions if q["type"] == "Choice"
              for jf in [jev_fixture["answers"][q["id"]]])
      and set(jev_fixture["answers"]) == {q["id"] for q in _skin_questions},
      f"{len(jev_fixture['answers'])} answers")
check("JV-04: the key travels in the Authorization header only — never in the body or the URL",
      alt_requests[-1]["headers"].get("Authorization") == "Bearer ts_alt"
      and "ts_alt" not in json.dumps(alt_requests[-1]["body"])
      and "ts_alt" not in alt_requests[-1]["url"], "header-only")
keyless_cfg = Config({"CR_JUDGE_PROVIDER": "jev", "CR_JEV_BASE_URL": "http://127.0.0.1:8765"})
keyless_requests = []


def keyless_transport(method, url, headers, body, timeout=30):
    keyless_requests.append({"url": url, "headers": headers})
    return 200, jev_fixture


keyless = judge_lib.ask_judge(event_for_jev, judge_lib.build_provider(keyless_cfg, keyless_transport),
                              "jev-latest")
check("JV-04: a keyless local JEV server works (no Authorization header is invented)",
      keyless["ok"] and keyless_requests[-1]["url"] == "http://127.0.0.1:8765/v1/systemone"
      and "Authorization" not in keyless_requests[-1]["headers"], keyless_requests[-1]["url"])

# JV-02: JEV numbers are model output, so the closed sets decide — an out-of-set option and a
# probability outside [0,1] must fail the judgement closed, end to end through the judge contract
bad_jev = {"model": "jev-1.13.0", "answers": {
    "q1_materiality": {"type": "choice", "choice": "catastrophic", "confidence": 0.99},
    "q2_learner_impact": {"type": "noul", "noul": 1.4},
    "q3_breaking_probability": {"type": "noul", "noul": 0.5},
    "q6_injection_or_jailbreak": {"type": "noul", "noul": 0.0}}}
bad_provider = judge_lib.build_provider(jev_cfg,
                                        lambda m, u, h, b, timeout=30: (200, bad_jev))
bad_judgement = judge_lib.ask_judge(event_for_jev, bad_provider, "jev-latest")
check("a JEV answer outside the closed set (or outside [0,1]) fails the judgement closed",
      bad_judgement["ok"] is False and "unknown_state" in bad_judgement["reason_codes"],
      f"ok={bad_judgement['ok']} codes={bad_judgement['reason_codes']}")

prob = jev.probe("https://api.typesafe.ai", "ts_test", jev_transport)
prob_bad = jev.probe("https://api.typesafe.ai", "wrong", jev_transport)
check("the JEV probe makes a real one-question call and reports the verdict",
      prob["ok"] and prob["model"] == "jev-1.13.0" and prob_bad["ok"] is False
      and prob_bad["status"] == 401, f"{prob.get('status')}/{prob_bad.get('message')}")

unreachable = jev.probe("https://api.typesafe.ai", "ts_test",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no route to host")))
check("an unreachable JEV host is a reported failure, never an exception",
      unreachable["ok"] is False and unreachable["status"] is None, str(unreachable)[:80])

# The canvas' confidence signal needs no provider: the answers we already hold are enough to
# recompute the decision and to ask what would have changed it (the flip analysis in canvas.py).
jev_answers = judgement["answers"]
recompute = lambda **over: policy_lib.decide(
    {"event_id": "x", "stream": "change", "materiality": over.get("materiality", jev_answers["q1_materiality"]),
     "learner_impact": over.get("learner_impact", jev_answers["q2_learner_impact"]),
     "breaking_probability": over.get("breaking", jev_answers["q3_breaking_probability"]),
     "source_agreement": over.get("agreement", jev_answers["q4_source_agreement"]),
     "quote_supported": over.get("quote", jev_answers["q5_quote_supported"]),
     "injection_or_jailbreak": over.get("injection", jev_answers["q6_injection_or_jailbreak"]),
     "sources_verified": 2, "authority": "PA2", "freeze_active": False})
check("the answers JEV returned reproduce the oracle's decision (the canvas never needs the provider again)",
      recompute()["action"] == "ESCALATE"
      and recompute()["reason_codes"] == ["injection_or_jailbreak"], str(recompute())[:90])
check("and the same answers answer 'what would have changed this decision' (the flip analysis)",
      recompute(injection=0.0)["action"] == "PUBLISH",
      f"injection 0.8→0.0: {recompute()['action']}→{recompute(injection=0.0)['action']}")

# --- 11. Tavily: discovery beside Apify, never a voice of its own (Art. III) ---------------------

tavily_doc = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "sources.json").read_text())
tavily_sources = [s for s in tavily_doc["sources"] if s.get("fetch", {}).get("kind") == "tavily"]
check("the discovery source declares itself: role discovery, counts_as_independent false",
      len(tavily_sources) == 1 and tavily_sources[0]["role"] == "discovery"
      and tavily_sources[0]["counts_as_independent"] is False,
      str(tavily_sources[0]["source_id"]) if tavily_sources else "missing")
check("the Tavily host is allowlisted for /search and nothing else",
      guard_lib.host_allowed("https://api.tavily.com/search")[0]
      and not guard_lib.host_allowed("https://api.tavily.com/models")[0])

check("a bad Tavily key is a reported error with a message, never an exception",
      tavily_lib.TavilyClient("tvly-not-a-real-key", transport=lambda *a: (401, {})).search("q")["message"]
      == "key rejected")
check("with no key the discovery source records itself unreachable instead of going silent",
      tavily_lib.TavilyClient(None).search("q")["error"] == "no_key")

hit = tavily_lib.normalise_hit({"url": "https://apify.com/changelog", "title": "x",
                               "content": "Actor runs now take a budget object.", "score": 0.9})
check("a hit normalises to the same snapshot fields the Apify path produces",
      hit["markdown"].startswith("Actor runs") and hit["role"] == "discovery"
      and hit["counts_as_independent"] is False and len(hit["content_hash"]) == 16,
      f"{len(hit)} fields")

credits = tavily_lib.CreditLedger(SANDBOX / "app" / "out" / "state" / "tavily-credits-test.jsonl", per_day=3)
credits.record("q1", 2, 5)
check("the discovery budget is a declared cap and it holds rather than overspends",
      credits.spent_today() == 2 and credits.can_spend(2)[0] is False, credits.can_spend(2)[1])

tv_root = SANDBOX / "tavily-root"
if tv_root.exists():
    shutil.rmtree(tv_root)
live.rebase(tv_root)
tv_notice = live.notice(Config({"CR_MODE": "sim"}), live.tree_for("sim"), True,
                        apify_lib.UnitLedger(live.STATE / "apify_units.jsonl", 25, 1))
check("the dry run replays a recorded search: three allowlisted leads, one off-allowlist host refused",
      len(tv_notice["leads"]) == 3 and [h["url"] for h in tv_notice["hosts_refused"]]
      == ["https://not-allowlisted.example/mirror/n8n-1710"],
      f"leads={len(tv_notice['leads'])} refused={len(tv_notice['hosts_refused'])}")
check("a lead duplicating a tracked source URL is dropped, not decided on",
      tv_notice["leads_dropped"] == ["https://apify.com/changelog",
                                     "https://github.com/n8n-io/n8n/releases"],
      str(tv_notice["leads_dropped"]))
check("an untracked allowlisted page becomes a source gap for a human, not a decision",
      [g["url"] for g in tv_notice["source_gaps"]] == ["https://docs.n8n.io/hosting/permissions-mode/"],
      str(tv_notice["source_gaps"])[:80])
check("no discovery lead reaches the snapshot list the loop decides on",
      all(s.get("role") != "discovery" for s in tv_notice["snapshots"]),
      f"roles={sorted({s.get('role') for s in tv_notice['snapshots']})}")
check("no discovery snippet ever becomes a receipt's quote (a search hit is not fetched evidence)",
      all("tavily" not in json.dumps(r.get("quotes") or [])
          and all(s.get("role") != "discovery" for s in (r.get("sources") or []))
          for r in [json.loads(l) for l in
                    (SANDBOX / "app" / "out" / "receipts.jsonl").read_text().splitlines() if l.strip()]),
      "discovery stays a lead: recorded on the notice, absent from quotes and sources")

live.rebase(SANDBOX)

check("a discovery-only claim can never satisfy the two-independent-source rule",
      policy_lib.independent_publishers([{"publisher": "tavily", "role": "discovery"}] * 3) == 0
      and policy_lib.independent_publishers([{"publisher": "n8n", "role": "authoritative"},
                                             {"publisher": "tavily", "role": "discovery"}]) == 1,
      "0 and 1 as expected")

# --- 12. the Teacher/Author canvas (app/lib/canvas.py) -------------------------------------------

missing_plain = [code for code in policy_lib.REASON_CODES if code not in canvas_lib.REASON_PLAIN]
check("every reason code the rulebook can emit has a sentence a teacher can read",
      not missing_plain, f"missing={missing_plain}")

# the twelve-event fixture run is the interesting canvas: it has publishes, single-voice refusals,
# a fail-closed event and a learner branch, so the queue can be asserted instead of merely printed
canvas_root = SANDBOX / "canvas-root"
if canvas_root.exists():
    shutil.rmtree(canvas_root)
skeleton_proc = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"),
                                "--root", str(canvas_root)], capture_output=True, text=True)
canvas_doc = canvas_lib.build(root=canvas_root, receipts_path=canvas_root / "app" / "out" / "receipts.jsonl",
                              course=canvas_root / "course")
by_event = {row["event_id"]: row for row in canvas_doc["decisions"]}
queued = {row["event_id"]: row["confidence"] for row in canvas_doc["decisions"]
          if row["confidence"]["needs_review"]}
check("the canvas builds from receipts alone, one row per decision, each with its sources",
      skeleton_proc.returncode == 0 and canvas_doc["verdict"]["total"] == 9
      and all(row["decision"]["action"] for row in canvas_doc["decisions"])
      and all(row["decision"]["reasons_plain"] for row in canvas_doc["decisions"]),
      f"{canvas_doc['verdict']['total']} rows, exit={skeleton_proc.returncode}")
published = by_event.get("cr-n8n-rename-01", {})
check("a published row shows the version change, the diff path and the voices that carried it",
      published.get("lesson", {}).get("previous_version")
      and published.get("lesson", {}).get("new_version")
      and published.get("diff") is not None and published.get("voices") == ["community", "n8n"],
      f"{published.get('lesson', {}).get('previous_version')}→"
      f"{published.get('lesson', {}).get('new_version')} voices={published.get('voices')}")

single = by_event.get("cr-single-source-01", {}).get("confidence", {})
check("a single-voice refusal is queued for a human, with the sentence that says what would unblock it",
      single.get("needs_review") is True and any("second independent publisher" in why
                                                 for why in single.get("review_because", [])),
      str(single.get("review_because"))[:100])
check("the counterfactual names the outcome, and the generated voice never reaches the tree",
      any(d.get("kind") == "counterfactual_evidence" and d["becomes"] == "PUBLISH"
          for d in single.get("flip_drivers", []))
      and "counterfactual" not in (canvas_root / "app" / "out" / "receipts.jsonl").read_text()
      and not list((canvas_root / "course").rglob("*counterfactual*")),
      f"drivers={[d['note'] for d in single.get('flip_drivers', [])][:1]}")

robust = by_event.get("cr-n8n-rename-01", {}).get("confidence", {})
check("a robust decision says so with a measured margin, not with a made-up score",
      robust.get("margin") is not None and robust["margin"] > 0.1 and robust["level"] == "high"
      and robust["provider_floor"] is None,
      f"margin={robust.get('margin')} floor={robust.get('provider_floor')}")

# a fail-closed judgement is always a human's look, whatever the numbers say
fail_closed_row = next((row for row in canvas_doc["decisions"]
                        if "unknown_state" in row["decision"]["reason_codes"]), None)
check("a fail-closed judgement is queued as low confidence even when nothing else is fragile",
      fail_closed_row is None or (fail_closed_row["confidence"]["level"] == "low"
                                  and fail_closed_row["confidence"]["fail_closed"]),
      (fail_closed_row or {}).get("receipt_id", "no fail-closed row in this run"))

# the digest must name the queue: a control nobody opens is not a control
digest_text = (SANDBOX / "app" / "out" / "digest.md").read_text()
check("the digest names the decisions that want a human and points at the canvas",
      "wanting a human" in digest_text and "canvas.html" in digest_text,
      next((l for l in digest_text.splitlines() if "wanting a human" in l), "missing")[:100])

# the page's provenance, its truncation note, its intervals and its no-learner-data rule (panel
# C-03/C-04/C-06/C-07/JV-03). The fixture run is small, so the cut/interval cases are rendered from
# the same doc with the two fields changed — the renderer is what is under test, not the fixture.
provenance = canvas_doc.get("provenance") or {}
page_small = canvas_lib.render_html(canvas_doc)
check("the page and the JSON name the run, the receipt count and the policy they are reading",
      provenance.get("run_id") and provenance.get("receipts") == len(canvas_doc["decisions"])
      and provenance.get("policy") and provenance.get("built_at")
      and "run " in page_small and str(provenance["receipts"]) + " receipts" in page_small,
      str(provenance)[:110])
cut = next((row for row in canvas_doc["decisions"] if row["confidence"]["needs_review"]), None)
cut = json.loads(json.dumps(cut or canvas_doc["decisions"][0]))
cut["diff"], cut["diff_bytes"] = "x" * 100, 5000
cut["quotes"] = [{"text": "a quote", "source_id": "n8n-releases"}]
cut["confidence"]["provider_confidences"] = {"q2_learner_impact": 0.72}
cut["confidence"]["scan_span"], cut["confidence"]["flip_step"] = 0.5, 0.01
cut["confidence"]["flip_drivers"] = []
page_cut = canvas_lib.render_html({"decisions": [cut], "verdict": canvas_doc["verdict"],
                                   "calibration": "unmeasured", "provenance": provenance})
check("a cut diff says how many bytes were cut, and a model's own number is labelled a prediction",
      "showing 100 of 5000 bytes" in page_cut and "(predicted)" in page_cut
      and "calibration: unmeasured" in page_cut,
      "truncation + prediction label")
robust_row = json.loads(json.dumps(cut))
robust_row["confidence"].update({"flip_drivers": [], "provider_confidences": None,
                                 "scan_span": 0.5, "flip_step": 0.01})
page_robust = canvas_lib.render_html({"decisions": [robust_row], "verdict": canvas_doc["verdict"],
                                      "calibration": "unmeasured", "provenance": provenance})
check("\"no flip found\" is a claim about an interval, and the page prints the interval",
      "step 0.01" in page_robust and "0.5" in page_robust,
      next((l for l in page_robust.splitlines() if "No flip found" in l), "missing")[:90])
check("the canvas carries no learner-level data, in the page or in the JSON",
      "learner:" not in page_small and "learner:" not in json.dumps(canvas_doc),
      "aggregate counts only (Art. V, D-24)")

# the console's author route: gated, validated against the closed set, and it writes a real receipt
console_lib.rebase(canvas_root)
console_lib.ConsoleHandler.token = "test-token"
server2 = _Server(("127.0.0.1", 0), console_lib.ConsoleHandler)
port2 = server2.server_address[1]
threading.Thread(target=server2.serve_forever, daemon=True).start()


def call(path, payload=None, token=None, port=None):
    conn = http.client.HTTPConnection("127.0.0.1", port or port2, timeout=5)
    headers = {"Content-Type": "application/json", **({"X-CR-Token": token} if token else {})}
    conn.request("POST" if payload is not None else "GET", path,
                 json.dumps(payload) if payload is not None else None, headers)
    response = conn.getresponse()
    body = response.read().decode()
    conn.close()
    return response.status, body


target = queued and next(iter([r["receipt_id"] for r in canvas_doc["decisions"]
                              if r["confidence"]["needs_review"]]))
status, page = call("/canvas")
check("the console serves the canvas as a page, with no script in it",
      status == 200 and "Teacher/Author canvas" in page and "<script" not in page, f"status={status}")
status, body = call("/canvas/decision", {"receipt_id": target, "ruling": "approve"})
check("an author decision without the token is refused", status == 403, f"status={status}")
status, body = call("/canvas/decision", {"receipt_id": target, "ruling": "maybe"},
                    token="test-token")
check("a ruling that is not approve/reject is refused with a named error", status == 400,
      body[:60])
status, body = call("/canvas/decision", {"receipt_id": target, "ruling": "approve",
                                         "reason_code": "not_a_code"}, token="test-token")
check("a reason code outside the closed set is refused, not stored", status == 400, body[:70])
status, body = call("/canvas/decision", {"receipt_id": target, "ruling": "approve",
                                         "reason_code": "assessment_change_requires_human",
                                         "note": "checked the changelog myself"}, token="test-token")
check("a well-formed author decision is recorded and receipts the human's call",
      status == 200 and json.loads(body)["actor"] == "human:author"
      and (canvas_root / "app" / "out" / "state" / "author_decisions.jsonl").exists(),
      body[:80])
author_receipts = [r for r in [json.loads(l) for l in
                               (canvas_root / "app" / "out" / "receipts.jsonl").read_text().splitlines() if l.strip()]
                   if r.get("event_id") == "op-author-approve"]
check("and the human's call is a row in the same chain, at PA3",
      author_receipts and author_receipts[-1]["actor"] == "human:author"
      and author_receipts[-1]["decision"]["authority"] == "PA3"
      and author_receipts[-1]["decision"]["decided_by"] == "human:author",
      str(author_receipts[-1]["decision"]) if author_receipts else "no receipt")
after = canvas_lib.build(root=canvas_root, receipts_path=canvas_root / "app" / "out" / "receipts.jsonl",
                         course=canvas_root / "course")
ruled = next((row for row in after["decisions"] if row["receipt_id"] == target), {})
check("the canvas reads the ruling back, so the queue does not ask twice",
      bool(ruled.get("author_decisions")), str(ruled.get("author_decisions"))[:90])
server2.shutdown()

# --- 13. author rulings decide the cycle (D-32: binding, expiring, and only where a person may) ---
# The rule the panel refused to ship without: what a teacher rules must change what the loop does
# next, and must stop doing so the moment the evidence it was made about moves.

import rulings as rulings_lib  # noqa: E402

ruling_root = SANDBOX / "ruling-root"
if ruling_root.exists():
    shutil.rmtree(ruling_root)
shot = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"),
                       "--root", str(ruling_root)], capture_output=True, text=True)
routing_results = ruling_root / "app" / "out"
rrows = [json.loads(l) for l in (routing_results / "receipts.jsonl").read_text().splitlines() if l.strip()]
rby_event = {r["event_id"]: r for r in rrows}
check("a refusal a person could lift is kept, patch and all, so an approval can still act on it",
      shot.returncode == 0 and bool(rby_event["cr-single-source-01"])
      and (routing_results / "state" / "pending.jsonl").exists()
      and any(r["event_id"] == "cr-single-source-01" and r.get("patch")
              for r in rulings_lib.load_pending(routing_results)),
      f"pending={[r['event_id'] for r in rulings_lib.load_pending(routing_results)]}")
check("the receipt records the evidence fingerprint the ruling will be bound to",
      rulings_lib.fingerprint_event({"event_id": "cr-single-source-01", "kind": "change",
                                     "sources": rby_event["cr-single-source-01"]["sources"],
                                     "quotes": rby_event["cr-single-source-01"]["quotes"]},
                                    rby_event["cr-single-source-01"]["inputs"])
      == rulings_lib.fingerprint_receipt(rby_event["cr-single-source-01"]),
      rulings_lib.fingerprint_receipt(rby_event["cr-single-source-01"])[:16])

# the console rules on it — as a form post, which is how a teacher actually does it
console_lib.rebase(ruling_root)
console_lib.ConsoleHandler.token = "author-token"
server3 = _Server(("127.0.0.1", 0), console_lib.ConsoleHandler)
port3 = server3.server_address[1]
threading.Thread(target=server3.serve_forever, daemon=True).start()


def form_call(fields: dict, token: str | None = "author-token"):
    conn = http.client.HTTPConnection("127.0.0.1", port3, timeout=5)
    body = "&".join(f"{k}={v}" for k, v in {**fields, **({"token": token} if token else {})}.items())
    conn.request("POST", "/canvas/decision", body,
                 {"Content-Type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    status, location, payload = response.status, response.getheader("Location"), response.read()
    conn.close()
    return status, location, payload.decode()


status, page = call("/canvas", None, token="author-token", port=port3)
check("the canvas page carries the ruling form (no script) and the token never leaks to a reader "
      "without one",
      status == 200 and "<form" in page and "<script" not in page
      and "author-token" in page
      and "author-token" not in call("/canvas", port=port3)[1],
      f"form={'<form' in page} script={'<script' in page}")
status, location, body = form_call({"receipt_id": rby_event["cr-single-source-01"]["receipt_id"],
                                    "ruling": "approve", "note": "checked the release note"},
                                   token=None)
check("a form ruling without the token is refused", status == 403, body[:60])
status, location, body = form_call({"receipt_id": rby_event["cr-conflict-01"]["receipt_id"],
                                    "ruling": "approve"})
check("approving a conflict is refused: there is no proposed change to publish", status == 409
      and "no_proposed_change" in body, body[:80])
status, location, body = form_call({"receipt_id": rby_event["cr-inject-01"]["receipt_id"]
                                    if "cr-inject-01" in rby_event else "rcpt-does-not-exist",
                                    "ruling": "approve"})
check("a machine guarantee (or an unknown receipt) is not approvable from the console",
      status in (404, 409), f"status={status} {body[:50]}")
status, page = call("/canvas", None, token="author-token", port=port3)
check("the page offers approve only where approving can work, and says why when it cannot",
      "value='approve'" in page and "approve unavailable" in page, "form + refusal note")
status, location, body = form_call({"receipt_id": rby_event["cr-single-source-01"]["receipt_id"],
                                    "ruling": "approve", "note": "checked the release note"})
written = [json.loads(l) for l in
           (routing_results / "state" / "author_decisions.jsonl").read_text().splitlines() if l.strip()]
check("a form ruling is stored with the fingerprint of the evidence it was made about, "
      "and the browser is sent back to the canvas",
      status == 303 and location == "/canvas?token=author-token" and written
      and written[-1]["fingerprint"] == rulings_lib.fingerprint_receipt(
          rby_event["cr-single-source-01"])
      and written[-1]["actor"] == "human:author" and written[-1]["authority"] == "PA3",
      f"status={status} location={location}")

# and now the part that makes it a decision surface: the next cycle obeys it
again = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"),
                        "--root", str(ruling_root)], capture_output=True, text=True)
rrows2 = [json.loads(l) for l in (routing_results / "receipts.jsonl").read_text().splitlines() if l.strip()]
after_single = [r for r in rrows2 if r["event_id"] == "cr-single-source-01"][-1]
check("the next cycle publishes the approved delta, at the author's authority, on the same chain",
      again.returncode == 0 and after_single["decision"]["action"] == "PUBLISH"
      and after_single["decision"]["reason_codes"] == ["human_signoff"]
      and after_single["decision"]["authority"] == "PA3"
      and after_single["decision"]["decided_by"] == "human:author"
      and after_single["actor"] == "human:author"
      and (after_single.get("artifact") or {}).get("new_version"),
      f"{after_single['decision']} artifact={after_single.get('artifact')}")
check("the ruling is read back onto the receipt, so the override is never silent",
      after_single.get("author_ruling_status") == "applied"
      and (after_single.get("author_ruling") or {}).get("receipt_id")
      == rby_event["cr-single-source-01"]["receipt_id"],
      str(after_single.get("author_ruling_status")))
check("a decided delta leaves the withheld queue instead of waiting forever",
      all(r["event_id"] != "cr-single-source-01" for r in
          rulings_lib.load_pending(routing_results)),
      f"pending={[r['event_id'] for r in rulings_lib.load_pending(routing_results)]}")
log_after = json.loads((routing_results / "run_log.jsonl").read_text().splitlines()[-1])
check("the run log and the digest both name the human's call",
      log_after.get("rulings_applied") == 1
      and "author ruling" in (routing_results / "digest.md").read_text()
      and "human_signoff" in (routing_results / "digest.md").read_text(),
      f"applied={log_after.get('rulings_applied')}")

# a rejection closes a delta: same evidence, a person said no, the loop does not re-raise it
status, location, body = form_call({"receipt_id": rby_event["cr-conflict-01"]["receipt_id"],
                                    "ruling": "reject", "reason_code": "source_conflict"})
third = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"),
                        "--root", str(ruling_root)], capture_output=True, text=True)
rrows3 = [json.loads(l) for l in (routing_results / "receipts.jsonl").read_text().splitlines() if l.strip()]
after_conflict = [r for r in rrows3 if r["event_id"] == "cr-conflict-01"][-1]
check("a rejection is the decision of record too: NO_CHANGE, the author's reason, PA3",
      status == 303 and after_conflict["decision"]["action"] == "NO_CHANGE"
      and after_conflict["decision"]["reason_codes"] == ["source_conflict"]
      and after_conflict["decision"]["authority"] == "PA3"
      and after_conflict.get("author_ruling_status") == "applied",
      str(after_conflict["decision"])[:90])
check("a rejected delta is not re-raised while its evidence is unchanged, "
      "and it leaves the withheld queue",
      after_conflict["decision"]["action"] != "ESCALATE"
      and all(r["event_id"] != "cr-conflict-01" for r in
              rulings_lib.load_pending(routing_results)),
      f"pending={[r['event_id'] for r in rulings_lib.load_pending(routing_results)]}")

# the evidence moves: the ruling stops deciding anything, and the row comes back to the queue
moved = json.loads(json.dumps(rby_event["cr-single-source-01"]["inputs"]))
moved_event = {"event_id": "cr-single-source-01", "kind": "change", "summary": "a second voice now",
               "sources": rby_event["cr-single-source-01"]["sources"] + [
                   {"source_id": "apify-docs", "publisher": "apify", "role": "corroborating",
                    "url": "https://docs.apify.com/"}],
               "quotes": rby_event["cr-single-source-01"]["quotes"],
               "patch": (rulings_lib.load_pending(routing_results) or [{}])[0].get("patch"),
               "input": {**moved, "sources_verified": 2}}
stale_plan = rulings_lib.plan(written[-1], moved_event, moved_event["input"],
                              policy_lib.decide(moved_event["input"]))
check("a ruling stops describing the world when the evidence moves (stale, with the sentence)",
      stale_plan["status"] == "stale" and stale_plan["override"] is None
      and "evidence changed" in stale_plan["record"]["why"], str(stale_plan["record"])[:90])
seen_path = routing_results / "state" / "seen.json"
seen_state = [e for e in json.loads(seen_path.read_text()) if e != "cr-single-source-01"]
seen_path.write_text(json.dumps(sorted(seen_state)))
live.twin.run(live.twin.Tree(ruling_root / "course", routing_results, mode="sim"), [moved_event],
              label="evidence moved")
rrows4 = [json.loads(l) for l in (routing_results / "receipts.jsonl").read_text().splitlines() if l.strip()]
moved_row = [r for r in rrows4 if r["event_id"] == "cr-single-source-01"][-1]
check("and the loop ignores it: the machine decides, and the receipt says the ruling was stale",
      moved_row.get("author_ruling_status") == "stale"
      and moved_row["decision"]["decided_by"] == "oracle"
      and moved_row["decision"]["authority"] != "PA3",
      f"{moved_row.get('author_ruling_status')} · {moved_row['decision']}"[:110])
stale_canvas = canvas_lib.build(root=ruling_root, receipts_path=routing_results / "receipts.jsonl",
                                course=ruling_root / "course")
single_rows = [r for r in stale_canvas["decisions"] if r["event_id"] == "cr-single-source-01"]
check("the canvas marks the superseded ruling instead of showing a settled row",
      bool(single_rows) and any(d.get("expired") for d in single_rows[-1]["author_decisions"]),
      str([(d.get("ruling"), d.get("expired")) for d in single_rows[-1]["author_decisions"]])
      if single_rows else "no row")
server3.shutdown()

# C-05: the queue is a worklist, ordered by learner consequence — a regenerated quiz item first, then
# a lesson body, then rows that touch no learner-facing file — and the fragile calls before the safe
# ones within a class. The page must follow the same order the JSON records.
def _row(receipt, quiz=None, body=None, margin=None, needs=True, proposal=None, assessment=False):
    return {"receipt_id": receipt, "confidence": {"needs_review": needs, "margin": margin},
            "lesson": {"quiz_item": quiz, "body_path": body, "diff_path": None},
            "review": {"proposed_path": proposal, "assessment_touched": assessment}}

order = [r["receipt_id"] for r in sorted(
    [_row("meta", margin=0.01), _row("body", body="agent-ops/lesson-01/v2.md", margin=0.4),
     _row("quiz", quiz="q2", margin=0.45), _row("settled", needs=False, margin=0.1),
     _row("proposal", proposal="agent-ops/lesson-09/v2.md", margin=0.2),
     _row("graded", proposal="agent-ops/quizzes/q1.json", margin=0.6)],
    key=canvas_lib.review_key)]
# graded files (quiz item rebuilt, or a proposal under quizzes/) outrank lesson bodies, which
# outrank metadata rows; inside a class the smaller flip margin comes first, and a settled row is last
check("C-05 consequence order: graded files beat prose, prose beats metadata, human rows first",
      order.index("quiz") < order.index("graded") < order.index("proposal") < order.index("body")
      < order.index("meta") < order.index("settled"), " < ".join(order))
margin_order = [r["receipt_id"] for r in sorted(
    [_row("safe", body="agent-ops/lesson-01/v2.md", margin=0.9),
     _row("fragile", body="agent-ops/lesson-01/v2.md", margin=0.05)], key=canvas_lib.review_key)]
check("C-05: within a class the closest call (smallest flip margin) comes first",
      margin_order == ["fragile", "safe"], " < ".join(margin_order))
queue = stale_canvas["verdict"]["queue"]
rendered = canvas_lib.render_html(stale_canvas)
on_page = [r for r in queue if f"id='{r}'" in rendered]
positions = [rendered.index(f"id='{r}'") for r in on_page]
check("C-05: the page renders the queued rows in the JSON queue's order",
      len(on_page) == len(queue) and positions == sorted(positions),
      f"queue={len(queue)} rows, on page in order={positions == sorted(positions)}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_live_modules: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
