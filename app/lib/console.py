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
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "out"
sys.path.insert(0, str(ROOT / "specs" / "courserefresh" / "skin"))
sys.path.insert(0, str(ROOT / "app" / "lib"))
sys.path.insert(0, str(ROOT / "app"))
import canvas as canvas_lib  # noqa: E402
import policy  # noqa: E402
import rulings as rulings_lib  # noqa: E402
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


def author_decisions_path() -> Path:
    return OUT / "state" / "author_decisions.jsonl"


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

    def _supplied_token(self, body: dict | None = None) -> str | None:
        """Where a token may arrive: header, `?token=` (for a browser opening the page), form field."""
        if self.headers.get("X-CR-Token"):
            return self.headers["X-CR-Token"]
        query = parse_qs(urlparse(self.path).query)
        if query.get("token"):
            return query["token"][0]
        return (body or {}).get("token")

    def _authorised(self, body: dict | None = None) -> bool:
        """A token, when one is configured, must arrive one of three ways (no scripts on the page).

        With no `CR_CONSOLE_TOKEN` the console is open — it is a loopback tool (TM09) — and every
        write says so at startup, which is the only thing that keeps "no token configured" from
        reading like "secured".
        """
        return not self.token or self._supplied_token(body) == self.token

    # --- routes --------------------------------------------------------------------------------
    def do_GET(self):  # noqa: N802
        route = urlparse(self.path).path.rstrip("/") or "/"
        if route == "/canvas":
            # the Teacher/Author canvas: the same document the CLI writes, rendered on demand, so a
            # teacher reads the tree as it is rather than a page that may be a run behind. With the
            # reader authorised the page carries the ruling form (D-32); without, it is a read-only
            # copy — a token is never handed to a request that could not already write.
            doc = canvas_lib.build(root=ROOT, receipts_path=OUT / "receipts.jsonl",
                                   course=ROOT / "course")
            form = self._authorised()
            self._send(200, canvas_lib.render_html(
                doc, action_url="/canvas/decision" if form else None,
                token=self.token if form else None).encode(), "text/html; charset=utf-8")
            return
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
        if route not in ("/pause", "/resume", "/canvas/decision"):
            self._json(404, {"ok": False, "error": "unknown_route"})
            return
        if route == "/canvas/decision":
            self._author_decision()
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

    def _author_decision(self) -> None:
        """The author's ruling on a row the canvas queued for a human (Art. IX, D-32: a person decides).

        Accepts JSON (the API) or `application/x-www-form-urlencoded` (the form on `/canvas`, so the
        surface a teacher reads does not need a script to act). Three writes, all append-only: the
        ruling itself (`state/author_decisions.jsonl`, carrying the *fingerprint* of the evidence it
        was made about, so the loop can tell whether it still describes the world), a receipt row at
        `authority: PA3` / `actor: human:author`, and — for a form post — a 303 back to the canvas, so
        the browser shows the updated queue rather than a JSON blob. The reason code must come from
        the closed set; a free-text reason is a note, not a code.
        """
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode() if length else ""
        form_post = "application/x-www-form-urlencoded" in (self.headers.get("Content-Type") or "")
        if form_post:
            parsed = parse_qs(raw)
            body = {k: v[0] for k, v in parsed.items()}
            # HTML forms send `ruling` from the clicked submit button; `_send`/`_json` stay identical
            body["ruling"] = (parsed.get("ruling") or [""])[0]
        else:
            try:
                body = json.loads(raw or "{}")
            except Exception:
                body = {}
        if not self._authorised(body):
            if form_post:
                self._send(403, b"No. A token is required (open the page with ?token=...).",
                           "text/plain; charset=utf-8")
            else:
                self._json(403, {"ok": False, "error": "bad_token"})
            return
        receipt_id = str(body.get("receipt_id") or "")
        ruling = str(body.get("ruling") or "")
        reason = str(body.get("reason_code") or "")
        note = str(body.get("note") or "")[:400]
        def refuse(status: int, error: str) -> None:
            if form_post:
                self._send(status, f"Refused: {error}".encode(), "text/plain; charset=utf-8")
            else:
                self._json(status, {"ok": False, "error": error})

        if ruling not in ("approve", "reject"):
            refuse(400, "ruling_must_be_approve_or_reject")
            return
        if reason and reason not in policy.REASON_CODES:
            refuse(400, "reason_code_not_in_closed_set")
            return
        if not reason:
            reason = rulings_lib.REJECT_DEFAULT_REASON if ruling == "reject" \
                else rulings_lib.APPROVED_REASON
        rows = {r.get("receipt_id"): r for r in receipts()}
        target = rows.get(receipt_id)
        if not target:
            refuse(404, "unknown_receipt")
            return
        if ruling == "approve":
            under = (target.get("decision") or {}).get("reason_codes") or []
            if not under or any(r not in rulings_lib.APPROVABLE for r in under):
                # a person may lift an evidence-class refusal, never a machine guarantee (D-32)
                refuse(409, "not_approvable: " + (", ".join(under) or "no reason codes on the receipt"))
                return
            withheld = next((r for r in rulings_lib.load_pending(OUT)
                             if r.get("event_id") == target.get("event_id")), None)
            if not (withheld or {}).get("patch"):
                # "approve" has to mean something. For a conflict there is no proposed change to
                # publish — the loop never wrote one — so the honest answer is "close it instead".
                refuse(409, "no_proposed_change: nothing was ever written for this delta; "
                            "close it (reject) or add a second source")
                return
        decision = rulings_lib.ruling_payload(target, ruling, reason, note, "human:author")
        decision["ts"], decision["run_id"] = twin.now(), twin.run_id()
        path = author_decisions_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            handle.write(json.dumps(decision, sort_keys=True) + "\n")
        tree = twin.Tree(ROOT / "course", OUT, mode=state()["mode"])
        tree.append_receipt({"ts": twin.now(), "run_id": twin.run_id(),
                             "event_id": f"op-author-{ruling}", "mode": tree.mode, "stream": "change",
                             "decision": {"action": "PUBLISH" if ruling == "approve" else "NO_CHANGE",
                                          "reason_codes": [reason], "authority": "PA3",
                                          "decided_by": "human:author"},
                             "artifact": {"reviewed_receipt": receipt_id, "reviewed_event": decision.get("event_id"),
                                          "lesson_id": (target.get("artifact") or {}).get("lesson_id")},
                             "cost": None, "actor": "human:author",
                             "label": f"author {ruling}d {receipt_id}" + (f": {note}" if note else "")})
        if form_post:
            self.send_response(303)
            self.send_header("Location", "/canvas" + (f"?token={self.token}" if self.token else ""))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._json(200, {"ok": True, **decision})

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
