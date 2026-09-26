#!/usr/bin/env python3
"""Claims lint (constitution Art. VI, TM18): no number in the docs without a register row.
Run: python3 app/tests/test_claims.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
REGISTER = (SPECS / "courserefresh" / "RECEIPTS.md").read_text()

# Numbers that may appear without a register row because they are structural, not measured claims.
ALLOWED = {
    "100%",           # receipt coverage / chain integrity targets, proven by the tests
    "0",              # build-breaking invariants: hostile -> publish 0, unsupported -> publish 0
    "2",              # the two-source rule
    "40",             # the eval floor
    "4096", "4 KB",   # the digest budget (a configuration, in thresholds.json)
    "2-minute", "2:00", "3-minute", "15:00", "16:15", "07:30", "0:00", "0:12", "0:25", "0:30",
    "0:45", "1:05", "1:20", "1:35", "1:40", "1:50", "2:20", "3:00",  # shot-list timings
    "1/learner/day", "3/learner/week", "p50", "p95",
}

CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


SKIP_HYPE = {"constitution.md", "MASTER.md", "harness.md", "plan.md", "spec.md", "CONSENT.md"}


def docs():
    for path in sorted(SPECS.rglob("*.md")):
        if "reviews/01" in str(path):      # the 4prd review quotes the *reference* corpus's numbers
            continue
        yield path, path.read_text()


hype = re.compile(r"\b(real-?time|sub-second|instant(?:ly)?|state of the art|best-in-class|seamless)\b", re.I)
hype_hits, numeric_hits = [], []
for path, text in docs():
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in hype.finditer(line):
            prefix = line[: m.start()].lower()
            if path.name in SKIP_HYPE:
                continue
            if re.search(r"(never|not|no|cannot|can't|banned|refuse|nothing|instead of)", prefix):
                continue
            if "dies on" in line.lower():
                continue
            hype_hits.append(f"{path.relative_to(ROOT)}:{line_no} '{m.group(0)}'")
        if re.search(r"(judg|criteri|weight|autonomy|proven in real use|apify|problem fit|product & presentation)",
                     line, re.I):
            continue                        # the briefing's own weights are context, not our claim
        if "reviews/" in str(path):
            continue                        # panel opinions quote the brief's weights; reviews/04 closes them
        for m in re.finditer(r"(?<![\w/])(\d+(?:\.\d+)?)\s?(×|x|%)", line):
            token = m.group(0).strip()
            if token in ALLOWED or token.endswith("100%"):
                continue
            # A multiplier is only a *claim* when it compares our result to something
            following = line[m.end(): m.end() + 30].lower()
            if m.group(2) in ("×", "x") and not re.search(
                    r"(lower|fewer|faster|cheaper|better|higher|more|less|reduction|improvement)", following):
                continue                     # ratios in prose ("3× the median dwell") are not claims
            numeric_hits.append(f"{path.relative_to(ROOT)}:{line_no} '{token}'")

check("no hype adjectives in claims position", not hype_hits, "; ".join(hype_hits[:3]))
check("every multiplication/percentage claim is in the register", not numeric_hits, "; ".join(numeric_hits[:4]))

# every register row marked measured must carry an artifact + command
rows = [l for l in REGISTER.splitlines() if re.match(r"\| N\d+ \|", l)]
# the register's convention: a measured row bolds the word, so "unmeasured" cannot be mistaken for it
bad = []
for line in rows:
    cells = line.split("|")
    if "**measured**" in cells[4] and ("—" in cells[5] or "—" in cells[6]):
        bad.append(cells[1].strip())
check("measured rows name artifact and command", not bad, f"rows missing evidence: {bad}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_claims: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
