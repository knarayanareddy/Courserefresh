#!/usr/bin/env python3
"""Learner telemetry endpoint and the cohort window (interfaces.md §5; constitution Art. V, XI.4).

The endpoint is deliberately small and paranoid:
  * `consent` is checked **before** anything is stored; a false or missing consent is 403 and the
    rejection is counted (`telemetry_rejected`), never stored;
  * handles must look like `learner:<8 hex>` — anything else is refused as `payload_invalid`;
  * rows are append-only JSONL; there is no read route and no learner-facing surface;
  * the cohort window is computed from stored rows: attempts, correctness, dwell, and a quiz delta
    that only exists when the cohort is at or above `thresholds.learner.cohort_min`.

Run (live): python3 app/lib/telemetry.py            # binds 0.0.0.0:$CR_TELEMETRY_PORT
"""
from __future__ import annotations

import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "lib"))
from config import Config  # noqa: E402

# One canonical location, shared by the intake server and the engine's learner gate. If these two
# ever disagree, consent-checked events silently never reach the cohort and the gate says
# `no_telemetry` while real learners are posting — round 3 shipped exactly that bug once.
STORAGE = ROOT / "app" / "out" / "state" / "telemetry.jsonl"
THRESHOLDS = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "thresholds.json").read_text())
HANDLE = re.compile(r"^learner:[0-9a-f]{8}$")


def validate_payload(payload: dict) -> dict:
    """Returns {ok, reason} — the same shape the console and the tests use."""
    if not isinstance(payload, dict):
        return {"ok": False, "reason": "payload_invalid"}
    handle = str(payload.get("learner_ref", ""))
    if not HANDLE.match(handle):
        return {"ok": False, "reason": "handle_not_hashed"}
    if payload.get("consent") is not True:
        return {"ok": False, "reason": "consent_missing", "status": 403}
    if not payload.get("lesson_id"):
        return {"ok": False, "reason": "payload_invalid"}
    if not isinstance(payload.get("events"), list) or not payload["events"]:
        return {"ok": False, "reason": "payload_invalid"}
    for event in payload["events"]:
        if event.get("kind") not in ("attempt", "dwell", "quiz_delta", "complete"):
            return {"ok": False, "reason": "payload_invalid"}
    return {"ok": True, "reason": "accepted", "status": 200}


def store(payload: dict, path: Path | None = None) -> int:
    path = path or STORAGE
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("a") as fh:
        for event in payload["events"]:
            fh.write(json.dumps({"ts": event.get("t") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 "learner_ref": payload["learner_ref"], "lesson_id": payload["lesson_id"],
                                 "kind": event["kind"], "item": event.get("item"),
                                 "correct": event.get("correct"), "seconds": event.get("seconds"),
                                 "version": payload.get("version")}, sort_keys=True) + "\n")
            written += 1
    return written


def cohort_window(lesson_id: str, version: str | None = None, path: Path | None = None,
                  window_h: int | None = None) -> dict:
    """The gate's input. `n` is distinct learners; the delta is `unmeasured` below the cohort floor."""
    path = path or STORAGE
    window_h = window_h or THRESHOLDS["budgets"].get("revert_window_h", 48)
    if not path.exists():
        return {"lesson_id": lesson_id, "n": 0, "state": "unmeasured", "reason": "no_telemetry"}
    now = time.time()
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r.get("lesson_id") == lesson_id
            and (version is None or r.get("version") in (None, version))]
    learners = {r["learner_ref"] for r in rows}
    attempts = [r for r in rows if r.get("kind") == "attempt"]
    deltas = [r for r in rows if r.get("kind") == "quiz_delta" and isinstance(r.get("correct"), (int, float))]
    youngest = max((r.get("ts", "") for r in rows), default="")
    gate = {"lesson_id": lesson_id, "version": version, "n": len(learners),
            "attempts": len(attempts),
            "accuracy": round(sum(1 for a in attempts if a.get("correct")) / len(attempts), 4) if attempts else None,
            "dwell_median_s": sorted([a["seconds"] for a in rows if a.get("kind") == "dwell" and a.get("seconds")],
                                     reverse=False)[len([a for a in rows if a.get("kind") == "dwell"]) // 2]
            if any(a.get("kind") == "dwell" for a in rows) else None,
            "window_h": window_h, "last_event": youngest, "cohort_source": "telemetry"}
    if len(learners) < THRESHOLDS["learner"]["cohort_min"]:
        gate.update({"quiz_delta": None, "state": "unmeasured",
                     "reason": f"cohort_below_minimum ({len(learners)}<{THRESHOLDS['learner']['cohort_min']})"})
    else:
        delta = round(sum(d["correct"] for d in deltas) / len(deltas), 4) if deltas else None
        gate.update({"quiz_delta": delta, "state": "measured" if delta is not None else "unmeasured",
                     "reason": None if delta is not None else "no_quiz_delta_rows"})
    gate["computed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    return gate


class TelemetryHandler(BaseHTTPRequestHandler):
    server_version = "CourserefreshTelemetry/1.0"
    token: str | None = None
    storage: Path = STORAGE

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (http.server API)
        if self.path == "/healthz":
            self._json(200, {"ok": True, "storage": str(self.storage), "accepts": ["POST /telemetry"]})
        else:
            self._json(404, {"ok": False, "error": "no_read_routes"})

    def do_POST(self):  # noqa: N802 (http.server API)
        if self.path != "/telemetry":
            self._json(404, {"ok": False, "error": "unknown_route"})
            return
        if self.token and self.headers.get("X-CR-Token") != self.token:
            self._json(403, {"ok": False, "reason": "bad_token"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode() or "{}")
        except Exception:
            self._json(400, {"ok": False, "reason": "payload_invalid"})
            return
        verdict = validate_payload(payload)
        if not verdict["ok"]:
            self._json(verdict.get("status", 400), {"ok": False, "reason": verdict["reason"]})
            return
        written = store(payload, self.storage)
        self._json(200, {"ok": True, "stored": written})

    def log_message(self, *args):   # keep the console clean; the endpoint writes no access log
        return


def rebase(root: Path) -> None:
    """Point telemetry at another tree's storage (a sandbox rehearsal, a demo)."""
    global STORAGE
    STORAGE = Path(root).resolve() / "app" / "out" / "state" / "telemetry.jsonl"


def storage_for(root: Path | None = None) -> Path:
    """The single place a root becomes a telemetry path (the engine and the server both call this)."""
    if root is None:
        return STORAGE
    return Path(root).resolve() / "app" / "out" / "state" / "telemetry.jsonl"


def serve(port: int | None = None, token: str | None = None, storage: Path | None = None,
          root: Path | None = None) -> None:
    cfg = Config()
    if root:
        rebase(root)
    port = port or cfg.int("CR_TELEMETRY_PORT", 8787)
    TelemetryHandler.token = token if token is not None else cfg.get("CR_TELEMETRY_TOKEN")
    TelemetryHandler.storage = storage or STORAGE
    server = ThreadingHTTPServer(("0.0.0.0", port), TelemetryHandler)
    print(f"telemetry listening on 0.0.0.0:{port} · storage {TelemetryHandler.storage} · "
          f"token {'required' if TelemetryHandler.token else 'not required'}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    serve()
