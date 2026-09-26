#!/usr/bin/env python3
"""Summarise a battery log into the JSON the claims audit checks against (Art. VI; review F5).

    python3 app/tools/battery_summary.py app/out/evidence/battery.log > app/out/evidence/battery-summary.json

Counts what actually ran: PASS lines, stage headers, every suite's `passed/total`, and the parity
row/probe count. `check.sh` writes this before the audit stage so the numbers the register claims are
frozen at "everything except the audit itself", which is what makes them unambiguous.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUITE = re.compile(r"^(\w+):\s*(\d+)/(\d+) checks passed", re.M)
SELFTEST = re.compile(r"^(\w+ selftest|selftest):\s*(\d+)/(\d+) checks passed", re.M)
PASS = re.compile(r"^\s+PASS", re.M)
STAGE = re.compile(r"^== (\d+)/(\d+)", re.M)
PARITY = re.compile(r"gate parity — rows=(\d+) probes=(\d+)")


def summarise(text: str) -> dict:
    suites = {name: [int(a), int(b)] for name, a, b in SUITE.findall(text)}
    for name, a, b in SELFTEST.findall(text):
        suites[name.replace(" ", "_")] = [int(a), int(b)]
    parity = PARITY.search(text)
    return {"pass_lines": len(PASS.findall(text)),
            "stages": len(STAGE.findall(text)),
            "suites": suites,
            "parity": [int(parity.group(1)), int(parity.group(2))] if parity else None}


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app/out/evidence/battery.log")
    summary = summarise(source.read_text())
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
