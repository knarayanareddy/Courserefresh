#!/bin/sh
# Courserefresh — the whole battery. Any failure is a stop-the-line (Art. XII.3).
# Usage: sh app/check.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p app/out/evidence app/out/eval/gold-v0.3

echo "== 1/11 gold eval ========================================="
python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl | tee app/out/eval/gold-v0.3/report.txt
echo
echo "== 2/11 gate parity (node mirror vs python oracle) ========"
node app/tests/test_gate_parity.py
echo
echo "== 3/11 walking skeleton (offline twin) ==================="
python3 app/run_walking_skeleton.py --selftest
echo
echo "== 4/11 artifact integrity + learner contract ============="
python3 app/tests/test_artifacts.py
echo
echo "== 5/11 curriculum (objectives, quizzes, micro-lessons) ===="
python3 app/tests/test_curriculum.py
echo
echo "== 6/11 policy unit checks ================================"
python3 app/tests/test_policy.py
echo
echo "== 7/11 threat model ======================================"
python3 app/tests/test_threat_model.py
echo
echo "== 8/11 gold floor ========================================"
python3 app/tests/test_gold_floor.py
echo
echo "== 9/11 contracts ========================================="
python3 app/tests/test_contracts.py
echo
echo "== 10/11 claims ============================================"
python3 app/tests/test_claims.py
echo
echo "== 11/11 hygiene + design ================================="
python3 app/tests/test_hygiene.py
python3 app/tests/test_design.py
echo
echo "ALL GREEN"
printf "battery green\n" > app/out/evidence/LAST-GREEN.txt
