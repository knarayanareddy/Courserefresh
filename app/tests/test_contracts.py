#!/usr/bin/env python3
"""Contracts: the docs, the closed sets, and the code must agree (constitution Art. VIII.3, XVI.2).
Run: python3 app/tests/test_contracts.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIN = ROOT / "specs" / "courserefresh" / "skin"
checks: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), str(detail)))


taxonomy = json.loads((SKIN / "change_taxonomy.json").read_text())
thresholds = json.loads((SKIN / "thresholds.json").read_text())
spec = (ROOT / "specs" / "courserefresh" / "spec.md").read_text()
trace = (ROOT / "specs" / "courserefresh" / "TRACEABILITY.md").read_text()
data_model = (ROOT / "specs" / "shared" / "data-model.md").read_text()
harness = (ROOT / "specs" / "shared" / "harness.md").read_text()
interfaces = (ROOT / "specs" / "shared" / "interfaces.md").read_text()
tasks = (ROOT / "specs" / "courserefresh" / "tasks.md").read_text()
receipts = (ROOT / "specs" / "courserefresh" / "RECEIPTS.md").read_text()

# 1. every AC in spec.md is traced, and every traced AC exists
ac_ids = set(re.findall(r"\*\*(AC-\d+\.\d+)\*\*", spec))
trace_ids = set(re.findall(r"\b(AC-\d+\.\d+)\b", trace))
check("every AC in spec.md is traced", not (ac_ids - trace_ids), f"missing={sorted(ac_ids - trace_ids)}")
check("no traced AC is orphaned", not (trace_ids - ac_ids), f"orphans={sorted(trace_ids - ac_ids)}")
check("AC count is as documented", len(ac_ids) == 57, f"n={len(ac_ids)}")

# 2. closed sets: data-model §4 tables vs change_taxonomy.json
row_codes = {}
for line in data_model.splitlines():
    m = re.match(r"\| `(Materiality|ChangeAction|LearnerAction|NotifyScope)` \| (.+) \|", line)
    if m:
        row_codes[m.group(1)] = set(re.findall(r"`([a-zA-Z0-9_:<>]+)`", m.group(2)))
row_codes["Materiality"] = set(re.findall(r"`(material_\w+|cosmetic|marketing_noise|ambiguous|contradictory|unverifiable)`", data_model))
check("materiality matches between doc and taxonomy",
      row_codes.get("Materiality", set()) == set(taxonomy["materiality"]),
      f"doc={len(row_codes.get('Materiality', []))} taxonomy={len(taxonomy['materiality'])}")

# 3. rule order is identical in harness.md and the taxonomy
order_line = next((l for l in harness.splitlines() if "Rule order is normative" in l), "")
doc_order = [w for w in re.findall(r"[a-z]+", order_line) if w in taxonomy["rule_order"]]
check("harness rule order matches taxonomy",
      doc_order[:6] == taxonomy["rule_order"][:6],
      f"doc={doc_order[:6]} taxonomy={taxonomy['rule_order'][:6]}")

# 4. documented CLI flags exist in the offline twin
skeleton = (ROOT / "app" / "run_walking_skeleton.py").read_text()
documented = set(re.findall(r"--([a-z][a-z-]+)", interfaces))
implemented = set(re.findall(r'add_argument\("--([a-z][a-z-]+)"', skeleton))
missing_flags = sorted(documented - implemented - {"confirm", "actor", "token", "event", "dry-run", "seed-demo"})
check("documented CLI flags exist in the skeleton", not missing_flags, f"documented={sorted(documented)} missing={missing_flags}")

# 5. every reason code in the taxonomy is emitted by at least one of the three deciders, or is a
#    declared lifecycle marker (which the docs must name)
policy = (SKIN / "policy.py").read_text()
used = set(re.findall(r'"([a-z_]+)"\]', policy)) | set(re.findall(r'out\("(?:ESCALATE|DRAFT|NO_CHANGE|PUBLISH|REVERT|DISPATCH)", \["([a-z_]+)"', policy))
declared_unused = {"source_stale", "fallback_used", "budget_hold", "cadence_degraded", "consent_revoked",
                   "no_delta", "noop_already_applied", "write_failed"} \
    | set(taxonomy["publishable_materialities"]) | {"seeded_rehearsal"}   # emitted by the publish branch
tax_codes = {c for group in taxonomy["reason_codes"].values() for c in group}
never = sorted(tax_codes - used - declared_unused)
check("no reason code is dead weight", not never, f"unused={never}")

# 6. tasks.md may not claim a path that does not exist (review 01, H3), and may not hide state
open_tasks = [l for l in tasks.splitlines() if l.strip().startswith("- [ ]")]
missing_paths = []
for line in open_tasks:
    for path in re.findall(r"`([^`]+\.(?:py|json|md|jsonl|diff))`", line):
        if path.startswith("<") or "…" in path:
            continue
        if not (ROOT / path).exists() and not (ROOT / "specs" / path).exists():
            missing_paths.append(path)
check("todo tasks do not promise existing proofs", not missing_paths, f"missing={missing_paths[:4]}")

# 7. thresholds the docs cite exist in thresholds.json
cited = {"injection_min", "min_sources", "n_min", "window_h", "publishes_per_day", "digest_bytes"}
have = set()
def walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            have.add(k)
            walk(v)
walk(thresholds)
check("thresholds cited by the docs exist", cited <= have, f"missing={sorted(cited - have)}")

# 8. receipts register: every `unmeasured` row keeps a placeholder value
bad_rows = [l for l in receipts.splitlines() if "unmeasured" in l and l.startswith("|") and "`<" not in l and "configuration" not in l]
check("unmeasured rows keep placeholders", len(bad_rows) <= 2, f"rows={len(bad_rows)}")

# 8b. every code/test/spec path a document names must exist (review 01 H3, the reference's defect)
PATTERN = re.compile(r"`((?:specs|app|course)/[A-Za-z0-9_./-]+\.(?:py|js|json|jsonl|md|sh|diff))`")
missing_refs = []
for path in sorted((ROOT / "specs").rglob("*.md")) + [ROOT / "README.md", ROOT / "AGENTS.md"]:
    if "reviews/01" in str(path):
        continue    # the 4prd review quotes paths inside the *reference* repository
    for token in PATTERN.findall(path.read_text()):
        if "<" in token or "..." in token or token.endswith("report.txt") or token.startswith("app/out/"):
            continue    # runtime evidence or abbreviated path: produced by running, checked in EVIDENCE.md
        # loop-written lesson versions do not exist on a fresh clone: the authored bodies do, and the
        # written ones are proven by the frozen run (EVIDENCE.md §4, reviews/04 §3.6)
        loop_written = re.match(r"course/agent-ops/(lesson-\d+)[^/]*/v(\d+)\.md$", token)
        if loop_written:
            baselines = dict(re.findall(r'"(lesson-\d+)[^"]*":\s*(\d+)',
                                        (ROOT / "app" / "tools" / "reset_course.py").read_text()))
            if int(loop_written.group(2)) > int(baselines.get(loop_written.group(1), 1)):
                continue
        if not (ROOT / token).exists():
            missing_refs.append(f"{path.relative_to(ROOT)} → {token}")
check("every path named in the docs exists", not missing_refs, "; ".join(sorted(set(missing_refs))[:5]))

# 9. n8n exports exist, are importable JSON, and embed the *current* policy node byte-for-byte
import hashlib
node_src = (ROOT / "app" / "n8n" / "policy_node.js").read_text()
wf_dir = ROOT / "app" / "n8n"
exports = sorted(wf_dir.glob("wf-cr-*.json"))
checks_names = []
try:
    for path in exports:
        doc = json.loads(path.read_text())
        assert isinstance(doc["nodes"], list) and doc["nodes"], path.name
        # a name may be a human label ("CR-9 · errors → receipt"); the workflow number is the contract
        number = path.stem.replace("wf-cr-", "").split("-")[0]
        assert number in doc["name"], f"{path.name} names the wrong workflow: {doc['name']}"
        assert any(n.get("type") == "n8n-nodes-base.stickyNote" for n in doc["nodes"]), \
            f"{path.name} carries no contract note"
        if "triage" in path.name:
            policy_nodes = [n for n in doc["nodes"] if n["name"] == "POLICY"]
            assert policy_nodes and policy_nodes[0]["parameters"]["jsCode"] == node_src, "POLICY node drifted"
        if path.name != "wf-cr-9-errors.json":
            guards = [n for n in doc["nodes"] if n["type"] == "n8n-nodes-base.code"
                      and "execute-once" in n.get("parameters", {}).get("jsCode", "")]
            assert len(guards) == 1, f"{path.name} has no execute-once guard"
    check("the six n8n workflow exports are present, importable and carry their contract",
          len(exports) == 6, f"found={[p.name for p in exports]}")
    check("every export embeds the current rulebook (triage) and an execute-once guard", True)

except AssertionError as exc:
    check("n8n exports are consistent", False, str(exc))

# 9b. Apify pins are builds, not `latest` (Art. XIII.2)
sources = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "sources.json").read_text())
apify_fetches = [s["fetch"] for s in sources["sources"] if (s.get("fetch") or {}).get("kind") == "apify"]
loose = [f.get("actor_id") for f in apify_fetches if not f.get("build") or f["build"] == "latest"]
check("every Apify actor call carries a pinned build (never `latest`)",
      bool(apify_fetches) and not loose, f"pinned={len(apify_fetches)} loose={loose}")

passed = sum(1 for _, ok, _ in checks if ok)
width = max(len(c[0]) for c in checks)
for name, ok, detail in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_contracts: {passed}/{len(checks)} checks passed")
sys.exit(0 if passed == len(checks) else 1)
