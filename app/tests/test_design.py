#!/usr/bin/env python3
"""Design lockfile checks (constitution Art. XV).
Run: python3 app/tests/test_design.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
master = (ROOT / "specs" / "design" / "MASTER.md").read_text()
shots = (ROOT / "specs" / "courserefresh" / "VIDEO-SHOTLIST.md").read_text()
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


tokens = set(re.findall(r"(--[a-z0-9-]+):", master))
required = {"--paper", "--ink", "--accent", "--status-publish", "--status-queue", "--status-revert",
            "--status-nochange", "--status-unknown", "--radius", "--measure"}
check("the lockfile defines every status token", required <= tokens, f"missing={sorted(required - tokens)}")
check("the banned list exists and names the clichés",
      "Banned, on sight" in master and all(w in master for w in ("gradients", "glow", "sparkle")))
check("accessibility floor is specified",
      "prefers-reduced-motion" in master and "AA" in master and "colour alone" in master)
labels = ["SEEDED SOURCE", "RECORDED", "DEGRADED", "OFFLINE TWIN"]
check("every fallback has an on-screen label in the shot list", all(l in shots for l in labels),
      f"missing={[l for l in labels if l not in shots]}")
check("status is a word plus a colour (not colour alone)",
      "word plus a colour" in master or "colour alone" in master)

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_design: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
