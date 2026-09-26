#!/usr/bin/env python3
"""Delivery of learner cards and micro-lessons (interfaces.md §4; constitution Art. IV, XIV).

The file channel stages rows (which is what a sim run may claim); telegram and webhook deliver. Every
attempt writes a delivery record — `delivered`, `staged`, or `notification_failed` with the reason —
so a failed send is never mistaken for a sent one, and the digest can print the difference.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "lib"))
from config import Config  # noqa: E402

DELIVERY_LOG = ROOT / "app" / "out" / "notifications_delivery.jsonl"


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
            return response.status, json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:  # pragma: no cover - exercised live
        return exc.code, {"message": str(exc)}
    except urllib.error.URLError as exc:  # pragma: no cover - exercised live
        return 0, {"message": f"network: {exc.reason}"}


def delivery_log_for(root: Path | None = None) -> Path:
    """The delivery log for a tree. A `--root` run must not write its delivery record into the
    checkout while the collector looks for it inside the run's own tree (review F13a)."""
    if root is None:
        return DELIVERY_LOG
    return Path(root).resolve() / "app" / "out" / "delivery.jsonl"


def card_text(row: dict) -> str:
    """Three lines + a link + an opt-out (design/MASTER.md §4). Plain language only."""
    rehearsal = "This is a labelled rehearsal, not a vendor release.\n" if row.get("rehearsal") else ""
    return (f"{rehearsal}What changed: {row['what_changed']}\n"
            f"Lesson: {row['lesson_id']} {row['from']} → {row['to']}\n"
            f"See the diff: {row.get('diff_path', '(in the repo)')}\n"
            f"Stop these messages: {row.get('opt_out', 'one-click')}")


class Notifier:
    def __init__(self, cfg: Config | None = None, transport=urllib_transport, log_path: Path | None = None):
        self.cfg = cfg or Config()
        self.channel = self.cfg.channel()
        self.transport = transport
        self.log_path = log_path or DELIVERY_LOG

    def deliver(self, rows: list[dict]) -> dict:
        """Deliver every staged row on the configured channel. Returns a summary + records."""
        records = []
        for row in rows:
            records.append(self._deliver_one(row))
        delivered = [r for r in records if r["status"] == "delivered"]
        failed = [r for r in records if r["status"] == "notification_failed"]
        self._append(records)
        return {"channel": self.channel, "attempted": len(records), "delivered": len(delivered),
                "failed": len(failed), "staged": sum(1 for r in records if r["status"] == "staged"),
                "records": records}

    def _deliver_one(self, row: dict) -> dict:
        base = {"ts": row.get("ts"), "learner_ref": row.get("learner_ref"),
                "lesson_id": row.get("lesson_id"), "channel": self.channel}
        if self.channel == "file":
            return {**base, "status": "staged",
                    "note": "channel=file: the card exists as a row and is not sent anywhere"}
        if not row.get("consent", True):        # defence in depth: consent is checked upstream too
            return {**base, "status": "notification_failed", "error": "consent_missing"}
        text = card_text(row)
        if self.channel == "telegram":
            token, chat = self.cfg.get("CR_TELEGRAM_BOT_TOKEN"), self.cfg.get("CR_TELEGRAM_CHAT_ID")
            if not token or not chat:
                return {**base, "status": "notification_failed", "error": "not_configured"}
            status, body = self.transport("POST", f"https://api.telegram.org/bot{token}/sendMessage",
                                          {}, {"chat_id": chat, "text": text, "disable_web_page_preview": True})
            if status == 200 and (body or {}).get("ok"):
                return {**base, "status": "delivered", "message_id": (body.get("result") or {}).get("message_id")}
            return {**base, "status": "notification_failed", "error": f"telegram_http_{status}"}
        if self.channel == "webhook":
            url = self.cfg.get("CR_NOTIFY_WEBHOOK_URL")
            if not url:
                return {**base, "status": "notification_failed", "error": "not_configured"}
            headers = {"X-CR-Token": self.cfg.get("CR_DEMO_TOKEN", "")} if self.cfg.has("CR_DEMO_TOKEN") else {}
            status, body = self.transport("POST", url, headers, {"kind": "learner_card", "row": row, "text": text})
            if status in (200, 201):
                return {**base, "status": "delivered", "response_id": (body or {}).get("id")}
            return {**base, "status": "notification_failed", "error": f"webhook_http_{status}"}
        return {**base, "status": "notification_failed", "error": f"unknown_channel:{self.channel}"}

    def _append(self, records: list[dict]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as fh:
            for record in records:
                fh.write(json.dumps(record, sort_keys=True) + "\n")


def delivery_summary(path: Path | None = None) -> dict:
    path = path or DELIVERY_LOG
    if not path.exists():
        return {"delivered": 0, "staged": 0, "failed": 0}
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return {"delivered": sum(1 for r in rows if r["status"] == "delivered"),
            "staged": sum(1 for r in rows if r["status"] == "staged"),
            "failed": sum(1 for r in rows if r["status"] == "notification_failed")}
