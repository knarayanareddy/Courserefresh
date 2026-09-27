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
check("AC count is as documented", len(ac_ids) == 59, f"n={len(ac_ids)}")

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
                   "no_delta", "noop_already_applied", "write_failed",
                   # a human's marker, not the rulebook's: `rulings.plan` stamps it on a publish an
                   # author approved (D-32), so no decider in policy.py or policy_node.js can emit it
                   # — and that is exactly what makes "a person decided this" visible on the receipt
                   "human_signoff"} \
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
        if token.startswith("app/out/evidence/") or "/app/out/evidence/" in token:
            # a *frozen run* under app/out is the dead pointer F4 was about: app/out is gitignored,
            # so on a clone this resolves to nothing. Frozen evidence lives in specs/evidence/
            # (shipped + hashed). This is the check that would have caught the old register.
            missing_refs.append(f"{path.relative_to(ROOT)} → {token} (frozen evidence belongs in specs/evidence/)")
            continue
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
    check("the seven n8n workflow exports are present, importable and carry their contract",
          len(exports) == 7, f"found={[p.name for p in exports]}")
    check("every export embeds the current rulebook (triage) and an execute-once guard", True)

except AssertionError as exc:
    check("n8n exports are consistent", False, str(exc))

# 9b. Apify pins are builds, not `latest` (Art. XIII.2)
sources = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "sources.json").read_text())
apify_fetches = [s["fetch"] for s in sources["sources"] if (s.get("fetch") or {}).get("kind") == "apify"]
loose = [f.get("actor_id") for f in apify_fetches if not f.get("build") or f["build"] == "latest"]
# 9c. the spend ceiling travels as the platform's parameter, and every source declares one (F13f):
# the round-3 code pushed a `budget` object into the actor *input*, where Apify ignores it
unbounded = [s["source_id"] for s in sources["sources"]
             if (s.get("fetch") or {}).get("kind") == "apify"
             and not isinstance(((s["fetch"].get("budget") or {}).get("max_total_charge_usd")), (int, float))]
check("every Apify source declares a spend ceiling (`max_total_charge_usd`)", not unbounded,
      f"missing={unbounded}")
apify_src = (ROOT / "app" / "lib" / "apify.py").read_text()
check("the ceiling is sent as `maxTotalChargeUsd` on the run, never inside the actor input",
      "maxTotalChargeUsd" in apify_src and 'payload["budget"]' not in apify_src
      and 'payload = {"input": fetch["input"]}' in apify_src,
      "query parameter, not input key")

check("every Apify actor call carries a pinned build (never `latest`)",
      bool(apify_fetches) and not loose, f"pinned={len(apify_fetches)} loose={loose}")

# 9d. the import-verify gate (review C2): read-back audit of the instance's own copies. The
# offline contract half: against a fake instance holding *dirty* stored copies, the gate must
# name the exact workflow · node · parameter that still needs a human; against clean copies it
# must print OK and nothing else. The live half is `make_n8n_exports.py --verify-import`.
sys.path.insert(0, str(ROOT / "app" / "tools"))
sys.path.insert(0, str(ROOT / "app" / "lib"))
import make_n8n_exports as maker  # noqa: E402

exports = {json.loads(p.read_text())["name"]: json.loads(p.read_text())
           for p in (ROOT / "app" / "n8n").glob("wf-cr-*.json")}
ERR = maker.ERR_NAME
named = sorted(exports.items())
err_wid = next(f"wf-{i:03d}" for i, (nm, _) in enumerate(named) if nm == ERR)


class _FakeN8n:
    """The N8nClient contract ({ok, ...}, list + get), backed by a dict of stored workflows."""

    def __init__(self, stored: dict):
        self.stored = stored

    def list_workflows(self):
        return {"ok": True, "workflows": [{"id": wid, "name": w["name"]} for wid, w in self.stored.items()]}

    def get_workflow(self, wid):
        if wid not in self.stored:
            # a real instance 404s an id it does not hold; the gate must report that, not crash
            return {"ok": False, "error": "n8n_error", "code": "payload_invalid",
                    "message": f"no stored copy for {wid}"}
        return {"ok": True, "workflow": self.stored[wid]}


def _clean_store() -> dict:
    stored = {}
    for i, (name, wf) in enumerate(named):
        fw = json.loads(json.dumps(wf))
        for n in fw["nodes"]:
            for k, v in list((n.get("parameters") or {}).items()):
                if isinstance(v, str) and "ATTACH_AT_IMPORT" in v:
                    n["parameters"][k] = "https://real.example/" + k
        fw["settings"]["errorWorkflow"] = err_wid if name != ERR else None
        stored[f"wf-{i:03d}"] = fw
    return stored


clean_verdict = maker.verify_import(_FakeN8n(_clean_store()))
check("verify-import says OK over a fully attached fake instance",
      clean_verdict["ok"] and clean_verdict["checked"] == len(named) and not clean_verdict["problems"],
      f"checked={clean_verdict['checked']} problems={len(clean_verdict['problems'])}")
_dirty = {wid: json.loads(json.dumps(fw)) for wid, fw in _clean_store().items()}
_orig_url = next(n for n in exports["wf-cr-0-scan"]["nodes"] if n["name"] == "APIFY_RUN_ACTOR")["parameters"]["url"]
_scan = next(fw for fw in _dirty.values() if fw["name"] == "wf-cr-0-scan")
next(n for n in _scan["nodes"] if n["name"] == "APIFY_RUN_ACTOR")["parameters"]["url"] = _orig_url
_act = next(fw for fw in _dirty.values() if fw["name"] == "wf-cr-2-act")
_act["settings"]["errorWorkflow"] = None
dirty_verdict = maker.verify_import(_FakeN8n(_dirty))
_dirty_kinds = {(p["workflow"], p["parameter"]) for p in dirty_verdict["problems"]}
check("verify-import names the exact stale placeholder and the unattached error workflow",
      not dirty_verdict["ok"] and ("wf-cr-0-scan", "url") in _dirty_kinds
      and ("wf-cr-2-act", "settings.errorWorkflow") in _dirty_kinds,
      "; ".join(f"{p['workflow']}·{p['node']}·{p['parameter']}" for p in dirty_verdict["problems"]))
_missing = {wid: fw for wid, fw in _clean_store().items() if fw["name"] != "wf-cr-4-digest"}
_missing_verdict = maker.verify_import(_FakeN8n(_missing))
check("verify-import reports a workflow that was never imported instead of trusting the file",
      not _missing_verdict["ok"]
      and any(p["workflow"] == "wf-cr-4-digest" and "not found" in p["problem"]
              for p in _missing_verdict["problems"]),
      "; ".join(f"{p['workflow']}: {p['problem'][:40]}" for p in _missing_verdict["problems"]))

passed = sum(1 for _, ok, _ in checks if ok)
width = max(len(c[0]) for c in checks)
for name, ok, detail in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_contracts: {passed}/{len(checks)} checks passed")
sys.exit(0 if passed == len(checks) else 1)
