#!/usr/bin/env python3
"""Claims audit — re-derive the numbers the register claims, and fail the battery on drift (F5).

`test_claims.py` checks the *shape* of a claim (has it an artifact? a command?). Nothing checked the
*value*: the register said `34/57 naive inclinations`, `57 gold rows` and a sha256 for the frozen gold
set while the files said `36/59`, `59` and a different hash — and the battery stayed green. A register
nobody re-derives is prose with a table around it, so this tool re-derives it.

It reads the fenced `json` block under `## 6. Machine-checked counts` in
`specs/courserefresh/RECEIPTS.md` and compares every value against the thing itself:

  * gold          the file's rows, sha256 and version, plus the eval report it produces right now
  * battery       PASS lines and stage headers in `app/out/evidence/battery.log`
  * suites        each suite's `passed/total` from that same log
  * evidence      every file under `specs/evidence/<run>/` re-hashed against its MANIFEST.sha256
                  (review F4: a hash that nobody can check is not evidence)
  * digest        the shipped digest's byte count

It runs as the last stage of `sh app/check.sh`, so a number that drifts fails the build instead of
sitting in a document. Exit 0 = everything still describes the file it names. Exit 1 = drift, printed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "specs" / "courserefresh" / "RECEIPTS.md"
GOLD = ROOT / "specs" / "courserefresh" / "skin" / "gold.jsonl"
LOG = ROOT / "app" / "out" / "evidence" / "battery.log"
EVIDENCE = ROOT / "specs" / "evidence"

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(ok), str(detail)))


def registered() -> dict:
    """The machine-checked block: a fenced json object between the audit markers."""
    text = REGISTER.read_text()
    match = re.search(r"<!--\s*claims-audit:begin\s*-->\s*```json\s*(.*?)```\s*<!--\s*claims-audit:end\s*-->",
                      text, re.S)
    if not match:
        return {}
    return json.loads(match.group(1))


def derive_gold() -> dict:
    rows = [l for l in GOLD.read_text().splitlines() if l.strip()]
    meta = next((json.loads(l)["_meta"] for l in rows if "_meta" in l), {})
    report = subprocess.run([sys.executable, str(ROOT / "specs" / "courserefresh" / "skin" / "policy.py"),
                             "--eval", str(GOLD)], capture_output=True, text=True).stdout
    def field(pattern: str) -> str | None:
        found = re.search(pattern, report)
        return found.group(1) if found else None
    return {"n": len([l for l in rows if "_meta" not in l]),
            "sha256": hashlib.sha256(GOLD.read_bytes()).hexdigest(),
            "gold_version": meta.get("gold_version"),
            "action_match": field(r"action match:\s*([\d.]+)"),
            "unknown_state": int(field(r"unknown_state rows:\s*(\d+)") or -1),
            "naive_inclinations": field(r"naive publish inclinations (\d+/\d+)")}


def derive_battery() -> dict:
    text = LOG.read_text() if LOG.exists() else ""
    suites = {name: [int(a), int(b)] for name, a, b in
              re.findall(r"^(\w+):\s*(\d+)/(\d+) checks passed", text, re.M)}
    stages = re.findall(r"^== (\d+)/(\d+) ", text, re.M)
    return {"pass_lines": len(re.findall(r"^\s+PASS", text, re.M)),
            "stages": len(stages), "suites": suites}


def derive_evidence() -> dict:
    bundles, problems = {}, []
    for manifest in sorted(EVIDENCE.glob("*/MANIFEST.sha256")):
        files = 0
        for line in manifest.read_text().splitlines():
            if not line.strip():
                continue
            digest, _, name = line.partition("  ")
            target = manifest.parent / name.strip()
            files += 1
            if not target.exists():
                problems.append(f"{manifest.parent.name}/{name.strip()}: missing")
            elif hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                problems.append(f"{manifest.parent.name}/{name.strip()}: hash changed")
        bundles[manifest.parent.name] = files
    return {"bundles": bundles, "problems": problems,
            # per bundle, not "the first digest alphabetically": two shipped runs is the normal state
            # (the offline twin's hero and the live engine's dry cycle), and a scalar would silently
            # start describing whichever one sorted first
            "digests": {m.parent.name: (m.parent / "digest.md").stat().st_size
                        for m in sorted(EVIDENCE.glob("*/MANIFEST.sha256"))
                        if (m.parent / "digest.md").exists()}}


def main() -> int:
    # check.sh freezes the battery summary before this stage runs, so the numbers being audited are
    # "everything except the audit itself" — which is what makes the totals unambiguous
    summary_path = None
    if "--summary" in sys.argv:
        summary_path = Path(sys.argv[sys.argv.index("--summary") + 1])
    summary = json.loads(summary_path.read_text()) if summary_path and summary_path.exists() else None
    want = registered()
    check("the register carries the machine-checked block", bool(want),
          "RECEIPTS.md §6" if want else "block missing")
    if not want:
        return report_and_exit()

    gold = derive_gold()
    for key in ("n", "sha256", "gold_version", "action_match"):
        claimed = (want.get("gold") or {}).get(key)
        check(f"gold {key} still describes the frozen set", str(claimed) == str(gold[key]),
              f"register={claimed} file={gold[key]}")
    claimed_unknown = (want.get("gold") or {}).get("unknown_state")
    check("the eval's unknown_state count is what the register says",
          claimed_unknown == gold["unknown_state"], f"register={claimed_unknown} now={gold['unknown_state']}")
    claimed_naive = (want.get("gold") or {}).get("naive_inclinations")
    check("the naive-inclination column (b) figure is what the eval prints",
          claimed_naive == gold["naive_inclinations"],
          f"register={claimed_naive} now={gold['naive_inclinations']}")

    battery = summary or derive_battery()
    check("the battery log exists for the audit to read", battery["stages"] > 0, str(LOG))
    if battery["stages"]:
        wb = want.get("battery") or {}
        check("the stage count matches the register",
              wb.get("stages_before_audit") == battery["stages"],
              f"register={wb.get('stages_before_audit')} log={battery['stages']}")
        check("the PASS-line count matches the register",
              wb.get("pass_lines_before_audit") == battery["pass_lines"],
              f"register={wb.get('pass_lines_before_audit')} log={battery['pass_lines']}")
        if battery.get("parity"):
            check("the parity row/probe count matches the register",
                  wb.get("parity") == battery["parity"],
                  f"register={wb.get('parity')} log={battery['parity']}")
    for suite, claimed in (want.get("suites") or {}).items():
        actual = battery["suites"].get(suite)
        check(f"suite {suite} still passes {claimed[0]}/{claimed[1]}",
              actual == claimed, f"register={claimed} log={actual}")
    missing = sorted(set(battery["suites"]) - set((want.get("suites") or {})))
    check("every suite that ran is recorded in the register", not missing, f"missing={missing}")

    evidence = derive_evidence()
    check("every shipped evidence bundle re-hashes against its manifest",
          not evidence["problems"], f"{len(evidence['bundles'])} bundle(s) · {evidence['problems'][:3]}")
    claimed_run = (want.get("evidence") or {}).get("run_id")
    check("the register names the bundle that is actually shipped",
          claimed_run in evidence["bundles"], f"register={claimed_run} shipped={sorted(evidence['bundles'])}")
    claimed_bundles = (want.get("evidence") or {}).get("bundles") or {}
    for name, claimed_files in claimed_bundles.items():
        check(f"the shipped bundle {name} still has {claimed_files} file(s)",
              evidence["bundles"].get(name) == claimed_files,
              f"register={claimed_files} now={evidence['bundles'].get(name)}")
    for name, claimed_bytes in ((want.get("evidence") or {}).get("digests") or {}).items():
        actual_bytes = evidence["digests"].get(name)
        check(f"the shipped digest of {name} is the size the register claims",
              actual_bytes == claimed_bytes, f"register={claimed_bytes} file={actual_bytes}")
    missing_digest_rows = sorted(set(evidence["digests"]) - set((want.get("evidence") or {}).get("digests") or {}))
    check("every shipped bundle has a digest size in the register", not missing_digest_rows,
          f"missing={missing_digest_rows}")

    check("the audit's own check count matches the register (add a row when you add a check)",
          (want.get("battery") or {}).get("audit_checks") == len(CHECKS) + 1,
          f"register={(want.get('battery') or {}).get('audit_checks')} running={len(CHECKS) + 1}")
    return report_and_exit()


def report_and_exit() -> int:
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    width = max(len(name) for name, _, _ in CHECKS)
    for name, ok, detail in CHECKS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print(f"\naudit_claims: {passed}/{len(CHECKS)} checks passed — "
          f"every number above was re-derived from the file it names")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
