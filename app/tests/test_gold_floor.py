#!/usr/bin/env python3
"""Gold-set floor and trap checks (constitution Art. VII).
Run: python3 app/tests/test_gold_floor.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "specs" / "courserefresh" / "skin" / "gold.jsonl"
TRAPS = {
    "cr-inject-01": "injection_or_jailbreak",
    "cr-single-01": "insufficient_corroboration",
    "cr-conflict-01": "source_conflict",
    "cr-paywall-01": "unverifiable",
    "cr-assess-01": "assessment_change_requires_human",
    "cr-ambiguous-01": "ambiguous_change",
    "cr-cosmetic-01": "low_learner_impact",
    "cr-seeded-01": "seeded_rehearsal",
}
checks: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), str(detail)))


meta, rows = {}, []
for line in GOLD.read_text().splitlines():
    if not line.strip():
        continue
    obj = json.loads(line)
    if "_meta" in obj:
        meta = obj["_meta"]
    else:
        rows.append(obj)

check("gold set meets the floor of 40", len(rows) >= 40, f"n={len(rows)}")
check("gold_version is recorded", bool(meta.get("gold_version")), meta.get("gold_version", ""))
check("every row carries its label provenance", all(r.get("label_author") and r.get("label_notes") for r in rows))

missing = [t for t in TRAPS if not any(r["row_id"] == t for r in rows)]
bad_expected = [t for t, reason in TRAPS.items()
                if not any(r["row_id"] == t and reason in r["expected"]["reason_codes"] for r in rows)]
check("all eight named traps exist", not missing, ", ".join(sorted(missing)) or "present")
check("traps expect their named reason", not bad_expected, ", ".join(bad_expected) or "ok")

# Art. VII: a trap's free-text must not name its own trap (enumerated fields are inputs, not hints)
BANNED_HINTS = ("injection", "jailbreak", "single source", "contradict", "paywall", "assessment change",
                "trap", "escalate because", "should publish", "expected action")
leaks = []
for row in rows:
    if row["row_id"] not in TRAPS:
        continue
    free = [v for k, v in row["input"].items()
            if isinstance(v, str) and k not in ("materiality", "authority", "stream", "event_id",
                                               "lesson_touched", "concept")]
    blob = " ".join(free).lower()
    if any(h in blob for h in BANNED_HINTS):
        leaks.append(row["row_id"])
check("trap labels are not written into the input", not leaks, ", ".join(leaks) or "no free-text hints")

unpublished = []
for row in rows:
    for source in row["input"].get("sources", []):
        if not source.get("publisher"):
            unpublished.append(f"{row['row_id']}:{source.get('source_id')}")
check("every source names its publisher (independence is code-decided)", not unpublished,
      ", ".join(unpublished[:3]) or "ok")

streams = {r["input"]["stream"] for r in rows}
check("all three streams are covered", streams >= {"change", "learner", "revert"}, ", ".join(sorted(streams)))

passed = sum(1 for _, ok, _ in checks if ok)
width = max(len(c[0]) for c in checks)
for name, ok, detail in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_gold_floor: {passed}/{len(checks)} checks passed (n={len(rows)}, gold_version={meta.get('gold_version')})")
sys.exit(0 if passed == len(checks) else 1)
