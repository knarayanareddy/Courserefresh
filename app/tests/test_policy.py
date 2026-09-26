#!/usr/bin/env python3
"""Policy unit checks: coercion, boundaries, rule order, determinism (constitution Art. VIII).
Run: python3 app/tests/test_policy.py
"""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "specs" / "courserefresh" / "skin"))
import policy  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


gold = policy.load_gold(ROOT / "specs" / "courserefresh" / "skin" / "gold.jsonl")
by_id = {r["row_id"]: r for r in gold}


def decide(row_id):
    return policy.decide(by_id[row_id]["input"])


# coercion: anything not a bounded number is unknown, not a pass
for value, label in [(float("nan"), "NaN"), (math.inf, "inf"), (-0.5, "negative"), ("high", "string"), (True, "bool")]:
    inp = dict(by_id["cr-breaking-01"]["input"], quote_supported=value)
    out = policy.decide(inp)
    check(f"coercion: {label} -> unknown_state", out["action"] == "ESCALATE" and "unknown_state" in out["reason_codes"], out["action"])

# boundaries (>= and <= are the rules, state them the same way everywhere)
check("threshold boundary: injection at exactly 0.5 escalates", decide("cr-ja-01")["action"] == "ESCALATE")
check("threshold boundary: quote at exactly 0.8 passes", decide("cr-quote-floor")["action"] == "PUBLISH")
check("threshold boundary: impact at exactly 0.4 passes", decide("cr-impact-floor")["action"] == "PUBLISH")

# rule order: earlier groups win even when later groups would also fire
check("rule order: safety beats evidence", "injection_or_jailbreak" in decide("cr-inject-01")["reason_codes"])
loud = policy.decide(dict(by_id["cr-conflict-01"]["input"], learner_impact=0.05, authority="PA0"))
check("rule order: evidence beats relevance and authority", "source_conflict" in loud["reason_codes"], loud["reason_codes"])
quiet = policy.decide(dict(by_id["cr-cosmetic-01"]["input"], authority="PA0"))
check("rule order: relevance beats authority", "low_learner_impact" in quiet["reason_codes"], quiet["reason_codes"])
check("rule order: authority beats integrity", decide("cr-pa0-01")["reason_codes"] == ["authority_insufficient"])

# ladder semantics
check("PA1 cannot ship a breaking change", decide("cr-pa1-breaking")["action"] == "DRAFT")
check("PA1 can ship an additive change", decide("cr-pa1-capability")["action"] == "PUBLISH")
check("PA2 ships the breaking change", decide("cr-breaking-01")["action"] == "PUBLISH")

# determinism + closed sets
a, b = policy.decide(by_id["cr-breaking-01"]["input"]), policy.decide(by_id["cr-breaking-01"]["input"])
check("the policy is deterministic", a == b)
codes = {c for group in policy.TAXONOMY["reason_codes"].values() for c in group}
bad = [r["row_id"] for r in gold if not set(policy.decide(r["input"])["reason_codes"]) <= codes]
check("every emitted reason code is in the taxonomy", not bad, ", ".join(bad[:3]))

# CLI
proc = subprocess.run([sys.executable, str(ROOT / "specs" / "courserefresh" / "skin" / "policy.py"),
                       "--dump"], input=json.dumps(by_id["cr-inject-01"]["input"]), capture_output=True, text=True)
ok = proc.returncode == 0 and json.loads(proc.stdout)["action"] == "ESCALATE"
check("--dump works and dispatches the hostile row", ok, proc.stdout.strip()[:60])

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_policy: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
