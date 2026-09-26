#!/usr/bin/env python3
"""The handoff collector's own proof (SETUP.md §6): it must carry a run and it must drop a key.

Two properties matter and both are tested end to end here, in a sandbox, with a fake secret in the
environment that the collector is *supposed* to find and remove:

1. collected — the folder has the run's evidence, a manifest that re-hashes, canvas execution ids,
   Apify run ids, and a telemetry summary that contains counts but no handles;
2. sealed — the literal secret value appears nowhere in the output, the scan says PASS, and the
   guard (the same function) does catch a planted secret when one is placed where redaction cannot
   reach it, so the test cannot pass vacuously.

Run: python3 app/tests/test_handoff.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SANDBOX = ROOT / "app" / "out" / "handoff-test"
# assembled at runtime on purpose: the hygiene test scans this file for key-shaped strings, and a
# test that needs a fake secret must not look like a real one on disk
SECRET = "apify" + "_api_" + "SUPER" + "SECRET" + "value123456"
JUDGE_SECRET = "s" + "k-" + "test-" + "SUPER" + "SECRET" + "value-abcdefghijklmno"

spec = importlib.util.spec_from_file_location("collect_live", ROOT / "app" / "tools" / "collect_live.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)

CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


# --- 1. the guard itself (so the end-to-end pass cannot be vacuous) -----------------------------
planted = f"token={SECRET} and key={JUDGE_SECRET}"
clean, exact, shaped = collector.redact(planted, [SECRET, JUDGE_SECRET])
check("redaction removes the exact values it knows", SECRET not in clean and JUDGE_SECRET not in clean
      and exact == 2, f"exact={exact} shaped={shaped}")
check("the scanner catches a value that redaction did not touch",
      bool(collector.scan_for_secrets(f"x {SECRET} y", [SECRET]))
      and bool(collector.scan_for_secrets("Authorization: Bearer abcdEFGH1234567890ijkl", []))
      and not collector.scan_for_secrets("sha256:" + "a" * 64, [SECRET]),
      "shape + exact detection, digests untouched")

# --- 2. a sandbox run to collect ----------------------------------------------------------------
if SANDBOX.exists():
    shutil.rmtree(SANDBOX)
out = SANDBOX / "app" / "out"
(out / "live").mkdir(parents=True)
(out / "state").mkdir(parents=True)
run_id = "cr-20990101-0000-777"
(out / "run_log.jsonl").write_text(json.dumps({"run_id": run_id, "mode": "live",
                                               "decisions": {"PUBLISH": 1, "ESCALATE": 1},
                                               "chain_verified_at_end": True,
                                               "canvas": [{"event_id": "cr-1", "ok": True,
                                                           "same_as_oracle": True,
                                                           "execution_id": "exec-4711"}],
                                               "sources_scanned": 6}) + "\n")
(out / "receipts.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"receipt_id": "rcpt-777-000", "event_id": "cr-1", "ts": "2026.09.26T00:00:00Z", "stream": "change",
     "decision": {"action": "PUBLISH", "reason_codes": ["material_breaking"], "authority": "PA2"},
     # a deliberately sloppy receipt: this is the leak the collector must scrub
     "label": f"publisher echoed the token {SECRET} in a log line"},
    {"receipt_id": "rcpt-777-001", "event_id": "cr-2", "ts": "2026.09.26T00:00:01Z", "stream": "change",
     "decision": {"action": "ESCALATE", "reason_codes": ["insufficient_corroboration"], "authority": "PA2"},
     "label": "one voice only"},
]) + "\n")
(out / "digest.md").write_text(f"# digest\n\nmode: **live**\n\nrefusal: one voice only\n")
(out / "digest.html").write_text("<!doctype html><title>digest</title><p>mode: live</p>")
(out / "live" / "preflight.json").write_text(json.dumps({"mode": "live", "blocking_for_live": []}))
(out / "live" / "cohort_gates.json").write_text(json.dumps([{"lesson_id": "lesson-03-apify-inputs", "n": 6,
                                                             "state": "measured", "quiz_delta": -0.08}]))
(out / "live" / "delivery.jsonl").write_text(json.dumps({"learner_ref": "learner:deadbeef",
                                                         "status": "delivered", "channel": "telegram"}) + "\n")
(out / "live" / "n8n-ids.json").write_text(json.dumps({"instance_version": "1.64.0",
                                                       "ids": {"wf-cr-1-triage": "wf-1"}}))
(out / "state" / "apify_units.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"day": "2026-09-26", "source_id": "n8n-releases", "run_id": "apify-run-abc123", "units": 1},
    {"day": "2026-09-26", "source_id": "apify-changelog", "run_id": "apify-run-def456", "units": 1},
]) + "\n")
(out / "state" / "telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"learner_ref": "learner:deadbeef", "lesson_id": "lesson-03-apify-inputs", "kind": "quiz_delta", "correct": -0.08},
    {"learner_ref": "learner:feedface", "lesson_id": "lesson-03-apify-inputs", "kind": "attempt", "correct": False},
]) + "\n")

env = {**os.environ, "APIFY_TOKEN": SECRET, "CR_JUDGE_API_KEY": JUDGE_SECRET, "CR_JUDGE_PROVIDER": "mock"}
proc = subprocess.run([sys.executable, str(ROOT / "app" / "tools" / "collect_live.py"),
                       "--root", str(SANDBOX), "--no-probe", "--no-tar"],
                      capture_output=True, text=True, env=env)
summary = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}
folder = Path(summary.get("folder", SANDBOX / "handoff" / run_id))

check("the collector exits 0 and names the folder it wrote",
      proc.returncode == 0 and summary.get("ok") is True and folder.exists(),
      f"exit={proc.returncode} {summary.get('folder', proc.stderr[-120:])}")
check("it found and scrubbed the leaked token (exact redaction, not luck)",
      summary.get("redactions", {}).get("exact", 0) >= 1
      and summary.get("scan") == "pass", json.dumps(summary.get("redactions", {})))
check("the literal secret appears nowhere in the collected set",
      all(SECRET not in p.read_text(errors="ignore") and JUDGE_SECRET not in p.read_text(errors="ignore")
          for p in folder.rglob("*") if p.is_file()))
check("SECRET-SCAN.txt is the receipt for that claim",
      "PASS" in (folder / "SECRET-SCAN.txt").read_text(),
      (folder / "SECRET-SCAN.txt").read_text().strip()[:60])

manifest_lines = (folder / "MANIFEST.sha256").read_text().splitlines()
mismatched = [line for line in manifest_lines if hashlib.sha256(
    (folder / line.split("  ", 1)[1]).read_bytes()).hexdigest() != line.split("  ", 1)[0]]
check("every collected file re-hashes against the manifest", not mismatched, f"bad={mismatched[:3]}")

names = {p.name for p in folder.iterdir() if p.is_file()}
check("the folder carries the run's own artifacts",
      {"run_log.jsonl", "receipts.jsonl", "digest.md", "digest.html", "cohort_gates.json",
       "delivery.jsonl", "n8n_ids.json", "apify_units.jsonl", "canvas.json", "apify_runs.json",
       "telemetry-summary.json", "environment.json", "HANDOFF.md", "MANIFEST.sha256"} <= names,
      str(sorted(names)))
canvas = json.loads((folder / "canvas.json").read_text())
apify = json.loads((folder / "apify_runs.json").read_text())
check("canvas execution ids and Apify run ids survive the trip",
      canvas["executions"] == 1 and canvas["cycles"][0]["execution_id"] == "exec-4711"
      and "apify-run-abc123" in apify["runs"] and apify["units_recorded"] == 2, json.dumps(apify["runs"]))
telemetry = json.loads((folder / "telemetry-summary.json").read_text())
check("telemetry is summarised, never copied: counts survive, handles do not",
      telemetry["rows"] == 2 and telemetry["distinct_handles"] == 2
      and "learner:" not in (folder / "telemetry-summary.json").read_text(),
      f"rows={telemetry['rows']} handles={telemetry['distinct_handles']}")
env_doc = json.loads((folder / "environment.json").read_text())
check("environment.json lists names and fingerprints, never values",
      "APIFY_TOKEN" in env_doc["keys_present"] and env_doc["secrets"]["APIFY_TOKEN"].startswith("set(")
      and SECRET not in (folder / "environment.json").read_text(),
      env_doc["secrets"].get("APIFY_TOKEN", "missing"))
check("HANDOFF.md says what the run proves and what is still missing",
      "still missing" in (folder / "HANDOFF.md").read_text()
      and "live` run" in (folder / "HANDOFF.md").read_text())

# --- 3. the archive, and the exit code when there is nothing to collect --------------------------
proc2 = subprocess.run([sys.executable, str(ROOT / "app" / "tools" / "collect_live.py"),
                        "--root", str(SANDBOX), "--no-probe"],
                       capture_output=True, text=True, env=env)
archive = (SANDBOX / "handoff" / f"handoff-{run_id}.tar.gz")
check("the tar archive is written for a push/paste handoff",
      proc2.returncode == 0 and archive.exists() and archive.stat().st_size > 1000,
      f"{archive.stat().st_size if archive.exists() else 0} B")
empty = SANDBOX / "empty"
(empty / "app" / "out").mkdir(parents=True)
proc3 = subprocess.run([sys.executable, str(ROOT / "app" / "tools" / "collect_live.py"),
                        "--root", str(empty), "--no-probe"], capture_output=True, text=True, env=env)
check("a tree with no run is refused, not faked", proc3.returncode == 1 and "no_run" in proc3.stdout,
      f"exit={proc3.returncode}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_handoff: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
