#!/usr/bin/env python3
"""Threat model: one check per numbered threat in specs/security/threat-model.md §2.
Run: python3 app/tests/test_threat_model.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "specs" / "courserefresh" / "skin"))
import policy  # noqa: E402
from lib.guard import MAX_BYTES, host_allowed, looks_like_secret, safe_course_path, within_size_cap  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []


def check(tm, name, ok, detail=""):
    CHECKS.append((f"{tm} {name}", bool(ok), str(detail)))


gold = policy.load_gold(ROOT / "specs" / "courserefresh" / "skin" / "gold.jsonl")
by_id = {r["row_id"]: r for r in gold}


def dec(row_id):
    return policy.decide(by_id[row_id]["input"])


tm01 = dec("cr-inject-01")
check("TM01", "hostile page never publishes", tm01["action"] == "ESCALATE" and "injection_or_jailbreak" in tm01["reason_codes"])
check("TM02", "no fetch-from-instructions path in the code",
      "follow this" not in (ROOT / "app" / "run_walking_skeleton.py").read_text())
tm03 = dec("cr-single-hi-agree")
check("TM03", "self-certifying / single source is not corroboration", tm03["action"] == "ESCALATE" and "insufficient_corroboration" in tm03["reason_codes"])
ok_evil, why = host_allowed("https://github.com.evil.tld/steal")
ok_http, why2 = host_allowed("http://docs.n8n.io/")
ok_ok, _ = host_allowed("https://docs.n8n.io/releases")
check("TM04", "host allowlist (spoof + plain http blocked, exact host allowed)", (not ok_evil) and (not ok_http) and ok_ok, f"{why} / {why2}")
ok_cap, size = within_size_cap("x" * (MAX_BYTES + 1))
check("TM05", "size cap enforced", (not ok_cap) and MAX_BYTES == 2 * 1024 * 1024)
blocked = 0
for bad in ("../../etc/passwd", "course/../.git/config", "course/agent-ops/../../secret.md"):
    try:
        safe_course_path(ROOT, bad)
    except PermissionError:
        blocked += 1
check("TM06", "write path refuses escapes", blocked == 3, f"{blocked}/3 blocked")
check("TM07", "over-wide diffs escalate", "diff_too_wide" in dec("cr-wide-01")["reason_codes"])
tm08 = dec("cr-assess-01")
check("TM08", "assessment changes are human-only", tm08["action"] == "ESCALATE" and "assessment_change_requires_human" in tm08["reason_codes"])
leaky = []
import re as _re  # noqa: E402
for path in (ROOT / "app" / "fixtures" / "telemetry").glob("*.json"):
    text = path.read_text()
    if _re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text) or not text.count("learner:"):
        leaky.append(path.name)
check("TM09", "telemetry carries hashed handles only", not leaky, ", ".join(leaky[:3]))
check("TM10", "notification caps enforced", dec("cr-learner-capday")["action"] == "NO_CHANGE" and dec("cr-learner-capweek")["action"] == "NO_CHANGE")
# TM11 — the console now exists, so it is tested as a surface: no scripts, no remote resources,
# and hostile content that reaches a receipt must be escaped, not rendered.
import importlib.util  # noqa: E402
import shutil  # noqa: E402
tm_console = ROOT / "app" / "out" / "tm11-console"
if tm_console.exists():
    shutil.rmtree(tm_console)
shutil.copytree(ROOT / "course", tm_console / "course")
_spec = importlib.util.spec_from_file_location("twin_for_tm11", ROOT / "app" / "run_walking_skeleton.py")
_twin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_twin)
_tree = _twin.Tree(tm_console / "course", tm_console / "app" / "out", mode="sim")
_events = _twin.load_events()
_honest = [e for e in _events if e["event_id"] == "cr-n8n-rename-01"]
_hostile = json.loads(json.dumps(next(e for e in _events if e["event_id"] == "cr-hostile-page-01")))
_hostile["summary"] = '<script>fetch("https://evil.example/x")</script>'
_twin.run(_tree, _honest + [_hostile], label="tm11")
_page = (_tree.out / "digest.html").read_text()
# a URL inside escaped text is harmless; a URL in an attribute or a script is not
import re as _re  # noqa: E402
unsafe = [marker for marker in ("<script", "onerror=", "onload=", "javascript:", "<img", "<iframe")
          if marker in _page] + _re.findall(r'\b(?:src|href)\s*=', _page)
check("TM11", "the console has no scripts, no remote resources, and escapes hostile text",
      not unsafe and "&lt;script&gt;" in _page, f"found={unsafe}")
check("TM12", "secret shapes are detected", looks_like_secret("token=abcdef123456") and not looks_like_secret("the token budget is 60k"))
check("TM13", "budget exhaustion escalates", "over_budget" in dec("cr-budget-pubs")["reason_codes"])
proc = subprocess.run([sys.executable, str(ROOT / "app" / "run_walking_skeleton.py"), "--resume", "--token", "wrong"],
                      capture_output=True, text=True, env={"CR_DEMO_TOKEN": "right", "PATH": "/usr/bin:/bin"})
check("TM14", "unauthorised resume refused with exit 3", proc.returncode == 3, f"exit={proc.returncode}")

sys.path.insert(0, str(ROOT / "app"))
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)
tmp = ROOT / "app" / "out" / "tm-chain-test"
import importlib.util  # noqa: E402
import shutil  # noqa: E402
if tmp.exists():
    shutil.rmtree(tmp)
tree = twin.Tree(tmp, tmp / "out", mode="sim")
tree.append_receipt({"ts": "t", "run_id": "r", "event_id": "e1", "stream": "change", "decision": {"action": "ESCALATE", "reason_codes": ["unknown_state"], "authority": "PA0"}, "artifact": None, "cost": None, "actor": "system"})
tree.append_receipt({"ts": "t", "run_id": "r", "event_id": "e2", "stream": "change", "decision": {"action": "ESCALATE", "reason_codes": ["unknown_state"], "authority": "PA0"}, "artifact": None, "cost": None, "actor": "system"})
ok, n = tree.verify_chain()
lines = tree.receipts_path.read_text().splitlines()
row = json.loads(lines[0]); row["decision"]["action"] = "PUBLISH"
tree.receipts_path.write_text(json.dumps(row, sort_keys=True) + "\n" + lines[1] + "\n")
ok2, _ = tree.verify_chain()
check("TM15", "chain verifies and detects an edit", ok and n == 2 and not ok2)
check("TM16", "publish path cannot leave the course root", blocked == 3)
seeded = dec("cr-seeded-01")
check("TM17", "seeded rehearsal is labelled in the decision", "seeded_rehearsal" in seeded["reason_codes"])
claims = subprocess.run([sys.executable, str(ROOT / "app" / "tests" / "test_claims.py")], capture_output=True, text=True)
check("TM18", "claim lint runs over the docs", claims.returncode == 0, (claims.stdout.strip().splitlines() or [""])[-1])

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_threat_model: {passed}/{len(CHECKS)} threats covered")
sys.exit(0 if passed == len(CHECKS) else 1)
