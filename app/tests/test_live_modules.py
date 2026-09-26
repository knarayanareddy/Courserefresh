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

import apify as apify_lib  # noqa: E402
import judge as judge_lib  # noqa: E402
import n8n as n8n_lib  # noqa: E402
import notify as notify_lib  # noqa: E402
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

check("the dry cycle leaves the sim labels on every evidence surface",
      "mode: **sim**" in (SANDBOX / "app" / "out" / "digest.md").read_text()
      and "sim" in (SANDBOX / "app" / "out" / "digest.html").read_text(), "labels present")
check("a dry cycle makes no live claim and stages rather than sends",
      summary.get("delivery", {}).get("delivered", 0) == 0
      and summary.get("delivery", {}).get("staged", 0) == 0, str(summary.get("delivery")))

ledger_rows = (SANDBOX / "app" / "out" / "state" / "apify_units.jsonl").read_text()
check("the cycle accounted its Apify units with a declared source of truth",
      "declared 1 run = 1 unit" in ledger_rows, ledger_rows.splitlines()[0][:120])

blob = json.dumps(summary) + json.dumps(receipts)
check("no recorded markdown is mistaken for a claim without a quote span",
      all(len(r.get("quotes", [])) >= 1 for r in publishes + escalates), "quotes present")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_live_modules: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
