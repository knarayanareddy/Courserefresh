#!/usr/bin/env python3
"""The author console — read-only, one page, no scripts (interfaces.md §6; design/MASTER.md §4.1).

Routes (all GET unless noted):
    /                       the latest digest page (falls back to digest.md as plain text)
    /healthz                {mode, freeze, chain_ok, last_run, receipt_count_gap}
    /api/preflight          what is wired and what is missing (never a secret value)
    /api/receipts           every receipt row, refusals first
    /api/run_log            every run
    /lesson/{lesson_id}     versions, current body path, sources block, gate state
    /receipt/{receipt_id}   one row, pretty-printed, plus the chain verdict
    /eval                   the last eval report
    /pause  (POST)          kill switch on;         /resume (POST, {"confirm":"RESUME"}) off

The console never renders model output as markup (the digest page is already escaped by the twin),
never serves an external asset, and refuses writes without `CR_CONSOLE_TOKEN` when one is set.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "out"
sys.path.insert(0, str(ROOT / "app" / "lib"))
sys.path.insert(0, str(ROOT / "app"))
from config import Config  # noqa: E402

spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)


def rebase(root: Path) -> None:
    """Serve a different tree (a rehearsal sandbox, a demo root) without touching the repo."""
    global ROOT, OUT, twin
    ROOT = Path(root).resolve()
    OUT = ROOT / "app" / "out"
    spec_path = ROOT / "app" / "run_walking_skeleton.py"
    if spec_path.exists():
        s = importlib.util.spec_from_file_location("twin", spec_path)
        twin = importlib.util.module_from_spec(s)
        s.loader.exec_module(twin)


def receipts() -> list[dict]:
    path = OUT / "receipts.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def run_log() -> list[dict]:
    path = OUT / "run_log.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def state() -> dict:
    tree = twin.Tree(ROOT / "course", OUT, mode="live")
    ok, rows = tree.verify_chain()
    runs = run_log()
    expected = sum(len(runs[-1]["decisions"].values()) if runs else 0 for _ in (0,))
    return {"mode": runs[-1]["mode"] if runs else "sim",
            "freeze": tree.frozen(),
            "chain_ok": ok,
            "chain_rows": rows,
            "last_run": runs[-1]["run_id"] if runs else None,
            "receipt_count_gap": max(0, expected - len(receipts())),
            "receipts": len(receipts())}


class ConsoleHandler(BaseHTTPRequestHandler):
    server_version = "CourserefreshConsole/1.0"
    token: str | None = None

    # --- helpers -------------------------------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload) -> None:
        self._send(status, json.dumps(payload, indent=2, sort_keys=True, default=str).encode())

    def _authorised(self) -> bool:
        return not self.token or self.headers.get("X-CR-Token") == self.token

    # --- routes --------------------------------------------------------------------------------
    def do_GET(self):  # noqa: N802
        route = urlparse(self.path).path.rstrip("/") or "/"
        if route == "/":
            page = OUT / "digest.html"
            if page.exists():
                self._send(200, page.read_bytes(), "text/html; charset=utf-8")
            elif (OUT / "digest.md").exists():
                self._send(200, (OUT / "digest.md").read_text().encode(), "text/plain; charset=utf-8")
            else:
                self._json(404, {"ok": False, "error": "no_digest_yet"})
            return
        if route == "/healthz":
            self._json(200, state())
            return
        if route == "/api/preflight":
            self._json(200, Config().preflight())
            return
        if route == "/api/receipts":
            rows = receipts()
            order = {"ESCALATE": 0, "REVERT": 1, "PUBLISH": 2, "DISPATCH": 3, "NO_CHANGE": 4}
            self._json(200, sorted(rows, key=lambda r: order.get(r["decision"]["action"], 9)))
            return
        if route == "/api/run_log":
            self._json(200, run_log())
            return
        if route == "/eval":
            reports = sorted(OUT.glob("eval/*/report.txt"))
            self._send(200, reports[-1].read_text().encode() if reports else b"no eval report yet",
                       "text/plain; charset=utf-8")
            return
        if route.startswith("/receipt/"):
            receipt_id = unquote(route.split("/", 2)[2])
            row = next((r for r in receipts() if r["receipt_id"] == receipt_id), None)
            if not row:
                self._json(404, {"ok": False, "error": "no_such_receipt"})
                return
            chain = state()
            self._json(200, {"receipt": row, "chain_ok": chain["chain_ok"], "chain_rows": chain["chain_rows"]})
            return
        if route.startswith("/lesson/"):
            lesson_id = unquote(route.split("/", 2)[2])
            folder = ROOT / "course" / "agent-ops" / lesson_id
            if not folder.exists():
                self._json(404, {"ok": False, "error": "no_such_lesson"})
                return
            versions = sorted(p.name for p in folder.glob("v*.md"))
            current = versions[-1] if versions else None
            rows = [r for r in receipts() if (r.get("artifact") or {}).get("lesson_id") == lesson_id]
            gates = [r["artifact"].get("revert_gate") for r in rows if r.get("artifact")]
            self._json(200, {"lesson_id": lesson_id, "versions": versions, "current": current,
                             "diff_paths": sorted(p.name for p in folder.glob("diffs/*.diff")),
                             "sources_block": True, "gates": [g for g in gates if g],
                             "decisions": [{"action": r["decision"]["action"], "receipt_id": r["receipt_id"]}
                                           for r in rows]})
            return
        self._json(404, {"ok": False, "error": "unknown_route"})

    def do_POST(self):  # noqa: N802
        route = urlparse(self.path).path.rstrip("/")
        if route not in ("/pause", "/resume"):
            self._json(404, {"ok": False, "error": "unknown_route"})
            return
        if not self._authorised():
            self._json(403, {"ok": False, "error": "bad_token"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length).decode() or "{}")
        except Exception:
            body = {}
        tree = twin.Tree(ROOT / "course", OUT, mode=state()["mode"])
        if route == "/pause":
            tree.freeze_path.write_text("paused by console")
            tree.append_receipt({"ts": twin.now(), "run_id": twin.run_id(), "event_id": "op-pause",
                                 "mode": tree.mode, "stream": "change",
                                 "decision": {"action": "NO_CHANGE", "reason_codes": ["freeze_active"],
                                              "authority": "PA1"},
                                 "artifact": None, "cost": None, "actor": "human:console",
                                 "label": "kill switch from the console"})
            self._json(200, {"ok": True, "freeze": True})
            return
        if body.get("confirm") != "RESUME":
            self._json(400, {"ok": False, "error": "confirm_required"})
            return
        if not tree.frozen():
            self._json(409, {"ok": False, "error": "not_paused"})
            return
        tree.freeze_path.unlink()
        tree.append_receipt({"ts": twin.now(), "run_id": twin.run_id(), "event_id": "op-resume",
                             "mode": tree.mode, "stream": "change",
                             "decision": {"action": "NO_CHANGE", "reason_codes": ["no_delta"], "authority": "PA1"},
                             "artifact": None, "cost": None, "actor": "human:console",
                             "label": "kill switch released from the console"})
        self._json(200, {"ok": True, "freeze": False})

    def log_message(self, *args):
        return


def serve(port: int | None = None, token: str | None = None, root: Path | None = None) -> None:
    cfg = Config()
    if root:
        rebase(root)
    port = port or cfg.int("CR_CONSOLE_PORT", 8080)
    ConsoleHandler.token = token if token is not None else cfg.get("CR_CONSOLE_TOKEN")
    server = ThreadingHTTPServer(("0.0.0.0", port), ConsoleHandler)
    print(f"console serving {ROOT} · listening on 0.0.0.0:{port} · writes "
          f"{'require a token' if ConsoleHandler.token else 'are open (set CR_CONSOLE_TOKEN to gate them)'}",
          flush=True)
    server.serve_forever()


if __name__ == "__main__":
    serve()
