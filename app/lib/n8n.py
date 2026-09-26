#!/usr/bin/env python3
"""n8n client — import the workflows, run them, read their executions (WIRING.md §3–§3.1, §6).

Design decisions that come from the spec, not from taste:
  * the client never edits a workflow's decision logic; it imports what
    `app/tools/make_n8n_exports.py` generated and records the resulting ids;
  * `import_exports` is idempotent: a workflow with the same name is updated in place;
  * every call returns `{ok, ...}` with an error code from interfaces.md §2 — the caller turns that
    into a receipt, so a broken canvas is visible in the digest rather than silent;
  * `N8N_INSTANCE_VERSION` is recorded with the import (WIRING §3.1, instance pin).

Everything talks through `transport`, so this module is testable with no network.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "app" / "n8n"
IDS_PATH = ROOT / "app" / "out" / "live" / "n8n-ids.json"


def urllib_transport(method: str, url: str, headers: dict, body: dict | None, timeout: int = 30):
    import urllib.error
    import urllib.request

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode() or "{}"
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as exc:  # pragma: no cover - exercised live
        try:
            payload = json.loads(exc.read().decode() or "{}")
        except Exception:
            payload = {"message": str(exc)}
        return exc.code, payload
    except urllib.error.URLError as exc:  # pragma: no cover - exercised live
        return 0, {"message": f"network: {exc.reason}"}


class N8nClient:
    def __init__(self, base_url: str | None, api_key: str | None, transport=urllib_transport,
                 timeout: int = 30, instance_version: str | None = None):
        self.base = (base_url or "").rstrip("/")
        self.key = api_key or ""
        self.transport = transport
        self.timeout = timeout
        self.instance_version = instance_version

    def _headers(self) -> dict:
        return {"X-N8N-API-KEY": self.key}

    def configured(self) -> bool:
        return bool(self.base and self.key)

    # --- workflows ---------------------------------------------------------------------------
    def list_workflows(self) -> dict:
        if not self.configured():
            return {"ok": False, "error": "not_configured", "code": "payload_invalid",
                    "message": "N8N_BASE_URL / N8N_API_KEY missing"}
        status, body = self.transport("GET", f"{self.base}/api/v1/workflows", self._headers(), None, self.timeout)
        if status != 200:
            return {"ok": False, "error": "n8n_error", "code": "payload_invalid",
                    "message": (body or {}).get("message", f"HTTP {status}")}
        return {"ok": True, "workflows": (body or {}).get("data", [])}

    def upsert_workflow(self, workflow: dict) -> dict:
        """Create or update by name. Returns {ok, id, created}."""
        if not self.configured():
            return {"ok": False, "error": "not_configured", "code": "payload_invalid",
                    "message": "N8N_BASE_URL / N8N_API_KEY missing"}
        listing = self.list_workflows()
        if not listing["ok"]:
            return listing
        existing = next((w for w in listing["workflows"] if w.get("name") == workflow.get("name")), None)
        payload = {k: v for k, v in workflow.items() if k in ("name", "nodes", "connections", "settings", "staticData")}
        # n8n Cloud's schema rejects `errorWorkflow: null` ("Expected string, received null") — the
        # exports carry the null as a placeholder, and import_exports PATCHes the real wf-cr-9 id on
        # after that workflow exists, so the null must never travel in the create/update payload
        settings = dict(payload.get("settings") or {})
        if settings.get("errorWorkflow", "missing") is None:
            settings.pop("errorWorkflow", None)
            payload["settings"] = settings
        if existing:
            status, body = self.transport("PUT", f"{self.base}/api/v1/workflows/{existing['id']}",
                                          self._headers(), payload, self.timeout)
            if status != 200:
                return {"ok": False, "error": "n8n_error", "code": "write_failed",
                        "message": (body or {}).get("message", f"HTTP {status}")}
            return {"ok": True, "id": existing["id"], "created": False,
                    "instance_version": self.instance_version}
        status, body = self.transport("POST", f"{self.base}/api/v1/workflows", self._headers(), payload, self.timeout)
        if status not in (200, 201):
            return {"ok": False, "error": "n8n_error", "code": "write_failed",
                    "message": (body or {}).get("message", f"HTTP {status}")}
        # n8n Cloud returns the created workflow at the top level (its OSS/self-host shape wraps in
        # `data`); accept both so the ids file is never empty on the one instance that matters
        created = body if isinstance(body, dict) and body.get("id") else \
            (body or {}).get("data", {}) if isinstance(body, dict) else {}
        return {"ok": True, "id": (created or {}).get("id"), "created": True,
                "instance_version": self.instance_version}

    def activate(self, workflow_id: str, active: bool = True) -> dict:
        if not self.configured():
            return {"ok": False, "error": "not_configured", "code": "payload_invalid"}
        status, body = self.transport("PATCH", f"{self.base}/api/v1/workflows/{workflow_id}",
                                      self._headers(), {"active": active}, self.timeout)
        return {"ok": status == 200, "active": active,
                "message": (body or {}).get("message", "") if status != 200 else ""}

    def get_workflow(self, workflow_id: str) -> dict:
        """Read one workflow's live copy back from the instance — what the verify gate audits.

        The public API returns the stored object, so this is the canvas as n8n actually holds it:
        nodes, parameters, connections and settings -- not what the export file says it sent.
        """
        if not self.configured():
            return {"ok": False, "error": "not_configured", "code": "payload_invalid",
                    "message": "N8N_BASE_URL / N8N_API_KEY missing"}
        status, body = self.transport("GET", f"{self.base}/api/v1/workflows/{workflow_id}",
                                      self._headers(), None, self.timeout)
        if status != 200:
            return {"ok": False, "error": "n8n_error", "code": "payload_invalid",
                    "message": (body or {}).get("message", f"HTTP {status}")}
        workflow = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
        return {"ok": True, "workflow": workflow}

    def executions(self, workflow_id: str, limit: int = 5) -> dict:
        if not self.configured():
            return {"ok": False, "error": "not_configured", "code": "payload_invalid"}
        url = f"{self.base}/api/v1/executions?workflowId={workflow_id}&limit={limit}&includeData=true"
        status, body = self.transport("GET", url, self._headers(), None, self.timeout)
        if status != 200:
            return {"ok": False, "error": "n8n_error", "code": "payload_invalid",
                    "message": (body or {}).get("message", f"HTTP {status}")}
        return {"ok": True, "executions": (body or {}).get("data", [])}

    def call_webhook(self, path: str, payload: dict) -> dict:
        """Trigger a workflow the way the scan does. `path` is the webhook path, e.g. 'cr/triage'."""
        if not self.base:
            return {"ok": False, "error": "not_configured", "code": "payload_invalid"}
        headers = {"X-CR-Token": self.key} if self.key else {}
        status, body = self.transport("POST", f"{self.base}/webhook/{path.lstrip('/')}", headers, payload, self.timeout)
        return {"ok": status in (200, 201), "status": status,
                "response": body if isinstance(body, (dict, list)) else None}

    # --- import ------------------------------------------------------------------------------
    def autofill_webhook_hosts(self, workflow: dict) -> dict:
        """Cross-workflow HTTP nodes: point `ATTACH_AT_IMPORT/webhook/<path>` at this instance.

        The host is not a secret and not a decision — it is wherever this import is landing, which
        is `self.base`. Leaving it a placeholder made the canvas state a working import while the
        first live POST silently went to a host named `ATTACH_AT_IMPORT` (review C3). Credentials,
        chat ids and repo names stay placeholders: those are choices a human makes in the UI
        (SETUP §3) and the verify gate names them until then.
        """
        for node in workflow.get("nodes", []):
            url = (node.get("parameters") or {}).get("url")
            if isinstance(url, str) and url.startswith("ATTACH_AT_IMPORT/webhook/"):
                node["parameters"]["url"] = f"{self.base}/webhook/" + url.split("ATTACH_AT_IMPORT/webhook/", 1)[1]
        return workflow

    def import_exports(self, export_dir: Path | None = None, ids_path: Path | None = None) -> dict:
        """Push every generated workflow to the instance, remember the ids, attach the error workflow."""
        export_dir = export_dir or EXPORT_DIR
        ids_path = ids_path or IDS_PATH
        ids_path.parent.mkdir(parents=True, exist_ok=True)
        results, ids = [], {}
        files = sorted(export_dir.glob("wf-cr-*.json"))
        error_file = export_dir / "wf-cr-9-errors.json"
        for path in [p for p in files if p != error_file] + ([error_file] if error_file.exists() else []):
            workflow = self.autofill_webhook_hosts(json.loads(path.read_text()))
            result = self.upsert_workflow(workflow)
            results.append({"file": path.name, "name": workflow.get("name"), **result})
            if result.get("ok") and result.get("id"):
                ids[workflow["name"]] = result["id"]
        error_id = ids.get("CR-9 · errors → receipt")
        if error_id:
            for name, workflow_id in ids.items():
                if name == "CR-9 · errors → receipt":
                    continue
                # n8n Cloud: PATCH /workflows/{id} is 405 for settings; the attach is a PUT (full
                # update) with the current nodes/connections plus the merged settings — never a
                # bare {errorWorkflow} payload, which would replace the whole settings object and
                # silently drop executionOrder on every re-import
                current = self.get_workflow(workflow_id)
                stored = current.get("workflow") or {}
                settings = {**(stored.get("settings") or {}), "errorWorkflow": error_id}
                payload = {k: stored.get(k) for k in ("name", "nodes", "connections", "staticData")}
                self.transport("PUT", f"{self.base}/api/v1/workflows/{workflow_id}",
                               self._headers(), {**payload, "settings": settings}, self.timeout)
        ids_path.write_text(json.dumps({"instance_version": self.instance_version, "ids": ids,
                                        "results": results}, indent=2, sort_keys=True) + "\n")
        ok = all(r.get("ok") for r in results) and bool(results)
        return {"ok": ok, "ids": ids, "results": results, "path": str(ids_path)}
