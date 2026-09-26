#!/usr/bin/env node
/**
 * Parity: the n8n production rulebook (app/n8n/policy_node.js) must agree with the oracle
 * (specs/courserefresh/skin/policy.py) on every gold row (constitution Art. VIII.3).
 *
 * Run: node app/tests/test_gate_parity.py        (this is a Node script; the .py name is the
 * contract name used across the docs — spec.md AC-3.1, WIRING.md §3, harness.md §11.)
 */
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const GOLD = path.join(ROOT, "specs", "courserefresh", "skin", "gold.jsonl");
const NODE_MIRROR = path.join(ROOT, "app", "n8n", "policy_node.js");
const PY_ORACLE = path.join(ROOT, "specs", "courserefresh", "skin", "policy.py");

const { decide } = require(NODE_MIRROR);

const rows = fs.readFileSync(GOLD, "utf8").split("\n").filter(Boolean).map(JSON.parse)
  .filter((r) => r.row_id);

// Named probes: branches the gold set does not exercise. Same code path as gold rows.
const learnerBase = rows.find((r) => r.input.stream === "learner").input;
const probes = [
  { row_id: "probe-concept-cap", input: { ...learnerBase, concept_recently_dispatched: true } },
  { row_id: "probe-frozen-learner", input: { ...learnerBase, freeze_active: true } },
];
const cases = rows.concat(probes);
fs.mkdirSync(path.join(ROOT, "app", "out"), { recursive: true });
const CASES = path.join(ROOT, "app", "out", "parity-cases.json");
fs.writeFileSync(CASES, JSON.stringify(cases.map((r) => ({ row_id: r.row_id, input: r.input }))));

const pySnippet = `
import json, sys
sys.path.insert(0, sys.argv[1])
import policy
rows = json.load(open(sys.argv[2]))
print(json.dumps([{ "row_id": r["row_id"], "decision": policy.decide(r["input"]) } for r in rows if "row_id" in r]))
`;

const pythonOut = JSON.parse(execFileSync("python3", ["-c", pySnippet, path.dirname(PY_ORACLE), CASES], { encoding: "utf8" }));
const byId = Object.fromEntries(pythonOut.map((r) => [r.row_id, r.decision]));

const bad = [];
for (const row of cases) {
  const js = decide(row.input);
  const py = byId[row.row_id];
  if (!py) { bad.push(`${row.row_id}: missing python decision`); continue; }
  const same = js.action === py.action &&
    JSON.stringify([...js.reason_codes].sort()) === JSON.stringify([...py.reason_codes].sort());
  if (!same) bad.push(`${row.row_id}: js=${js.action}${JSON.stringify(js.reason_codes)} py=${py.action}${JSON.stringify(py.reason_codes)}`);
}

console.log(`gate parity — rows=${rows.length} probes=${probes.length} checked against the Python oracle`);
bad.slice(0, 10).forEach((line) => console.log("  MISMATCH", line));
console.log(bad.length === 0 ? "PASS" : `FAIL (${bad.length} mismatches)`);
process.exit(bad.length === 0 ? 0 : 1);
