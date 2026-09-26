#!/usr/bin/env python3
"""Serve the console and the telemetry intake for a demo (design/MASTER.md §4.1).

    python3 app/serve.py [--root DIR] [--console-port 8080] [--telemetry-port 8787]

Both servers bind 0.0.0.0 so a phone on the same network can post learner events during the pitch.
Nothing here writes to the course; the console's two write routes are the pause switch.
"""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "lib"))

import console as console_lib  # noqa: E402
import telemetry as telemetry_lib  # noqa: E402
from config import Config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Courserefresh console + telemetry")
    ap.add_argument("--root", default=str(ROOT), help="tree to serve (default: this checkout)")
    ap.add_argument("--console-port", type=int, default=None)
    ap.add_argument("--telemetry-port", type=int, default=None)
    args = ap.parse_args()
    cfg = Config()
    root = Path(args.root).resolve()
    console_port = args.console_port or cfg.int("CR_CONSOLE_PORT", 8080)
    telemetry_port = args.telemetry_port or cfg.int("CR_TELEMETRY_PORT", 8787)
    threading.Thread(target=telemetry_lib.serve,
                     kwargs={"port": telemetry_port, "root": root}, daemon=True).start()
    console_lib.serve(port=console_port, root=root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
