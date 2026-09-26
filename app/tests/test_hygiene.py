#!/usr/bin/env python3
"""Hygiene (TM09, TM12, review 01 H11): the repo must not ship secrets, junk, or dated prose.
Run: python3 app/tests/test_hygiene.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


gitignore = (ROOT / ".gitignore").read_text() if (ROOT / ".gitignore").exists() else ""
for needed in ("app/out/", "__pycache__/", "*.pyc", ".env"):
    check(f".gitignore covers {needed}", needed in gitignore)

secret_patterns = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI-style key"),
    (re.compile(r"apify_api_[A-Za-z0-9]{20,}", re.I), "Apify token"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "email address"),
]
hits = []
for path in list((ROOT / "app").rglob("*")) + list(SPECS.rglob("*")):
    if not path.is_file() or path.suffix not in (".py", ".js", ".json", ".md", ".sh", ".jsonl"):
        continue
    if "out/" in str(path) or path.name == "CONSENT.md":   # CONSENT.md is the consent text itself
        continue
    text = path.read_text(errors="ignore")
    for pattern, label in secret_patterns:
        for m in pattern.finditer(text):
            if label == "email address" and ("example.invalid" in m.group(0) or "learner:" in m.group(0)):
                continue
            hits.append(f"{path.relative_to(ROOT)}: {label}")
check("no secrets or emails in app/ or specs/", not hits, "; ".join(sorted(set(hits))[:4]))

dated = []
for path in SPECS.rglob("*.md"):
    if path.name == "PREREGISTRATION.md":
        continue
    for line_no, line in enumerate(path.read_text().splitlines(), 1):
        if re.search(r"\b20\d\d[-/]\d\d[-/]\d\d\b", line):
            dated.append(f"{path.relative_to(ROOT)}:{line_no}")
check("wall-clock dates only in the pre-registration", not dated, "; ".join(dated[:4]))


def git(args: list[str]) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


if (ROOT / ".git").exists():
    tracked = git(["ls-files"])
    check("no build/output artifacts tracked", not re.search(r"(app/out/|__pycache__|\.pyc$|egg-info)", tracked),
          "see git ls-files" if tracked else "no commits yet")
else:
    check("no build/output artifacts tracked", True, "no git checkout")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_hygiene: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
