#!/usr/bin/env python3
"""Loop behaviour checks against the offline twin (constitution Art. XII; spec AC-1…AC-11).
Run: python3 app/tests/test_walking_skeleton.py
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)

SANDBOX = ROOT / "app" / "out" / "loop-test"
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


if SANDBOX.exists():
    shutil.rmtree(SANDBOX)
shutil.copytree(ROOT / "course", SANDBOX / "course")
course_out = SANDBOX / "app" / "out"
course_out.mkdir(parents=True, exist_ok=True)
tree = twin.Tree(SANDBOX / "course", course_out, mode="sim")
before_files = {p.relative_to(SANDBOX) for p in SANDBOX.rglob("*") if p.is_file()}

events = twin.load_events(include_seed=True)
log = twin.run(tree, events, label="loop-test")
rows = tree.rows()
ok, n = tree.verify_chain()

publishes = [r for r in rows if r["decision"]["action"] == "PUBLISH"]
reverts = [r for r in rows if r["decision"]["action"] == "REVERT"]
check("the loop publishes, refuses, dispatches and reverts in one run",
      bool(publishes) and bool(reverts) and bool([r for r in rows if r["decision"]["action"] == "DISPATCH"])
      and log["decisions"].get("ESCALATE", 0) >= 2,
      json.dumps(log["decisions"]))
check("the chain verifies after the run", ok and n == len(rows), f"{n} rows")
check("receipt coverage is 100%", len(rows) == sum(log["decisions"].values()), f"{len(rows)} receipts")
art = publishes[0]["artifact"]
check("a publish wrote a version, a diff and promised its undo",
      (SANDBOX / "course" / art["body_path"]).exists() and (SANDBOX / "course" / art["diff_path"]).exists()
      and art["revert_gate"]["window_h"] == 48,
      f"{art['previous_version']} → {art['new_version']}")
check("nothing was written outside course/** and the out dir",
      all(str(f).startswith(("course/", "app/")) for f in {p.relative_to(SANDBOX) for p in SANDBOX.rglob("*") if p.is_file()} - before_files),
      "write surface")

after_first = len(tree.rows())
twin.run(tree, events, label="loop-test-2")
second = tree.rows()[after_first:]
check("dedupe: a second run re-decides nothing it already saw",
      not [r for r in second if r["decision"]["action"] == "PUBLISH"],
      f"{len(second)} new rows, 0 publishes")

digest = (course_out / "digest.md").read_text()
i_refuse, i_change, i_learn = digest.find("## 1. What it refused"), digest.find("## 2. What changed"), digest.find("## 3. Learners")
check("digest sections are in the fixed order", 0 <= i_refuse < i_change < i_learn)
check("digest names the mode and stays under the byte cap",
      "mode: **sim**" in digest and len(digest.encode()) <= 4096, f"{len(digest.encode())} bytes")
check("every receipt costs `unmeasured` rather than a guess",
      all(r["cost"]["eur"] is None for r in rows))
check("hostile, single-source and contradiction rows are present and escalated",
      {r["event_id"] for r in rows if r["decision"]["action"] == "ESCALATE"} >=
      {"cr-hostile-page-01", "cr-single-source-01", "cr-conflict-01"})

# pause / resume through the CLI (the kill switch a human actually touches)
proc = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"), "--pause",
                       "--root", str(SANDBOX)], capture_output=True, text=True)
freeze = SANDBOX / "app" / "out" / "state" / "FREEZE"
check("--pause freezes writes", proc.returncode == 0 and freeze.exists())
frozen_log = twin.run(tree, events, label="frozen-live")
check("frozen runs never publish", all(r["decision"]["action"] != "PUBLISH" for r in tree.rows()[len(rows) + len(second):]))
proc = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"), "--resume",
                       "--root", str(SANDBOX)], capture_output=True, text=True)
check("--resume restores writes with a receipt", proc.returncode == 0 and not freeze.exists(),
      f"exit={proc.returncode}")

report = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"), "--report",
                         "--root", str(SANDBOX)], capture_output=True, text=True)
check("--report renders the digest", report.returncode == 0 and "digest" in report.stdout.lower())

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_walking_skeleton: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
