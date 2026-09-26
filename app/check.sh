#!/bin/sh
# Courserefresh — the whole battery. Any failure is a stop-the-line (Art. XII.3).
# Usage: sh app/check.sh
#
# Every stage runs through `run_stage`, which shows the output, appends it to
# app/out/evidence/battery.log and exits non-zero when the stage fails. The previous version piped
# stages into `tee`, and a pipeline's status is the status of `tee`: a failing gold eval printed its
# mismatches and the battery still said ALL GREEN (review F7's class: green while the run was broken).
#
# Stage 13 summarises that log; stage 14 audits the numbers in specs/courserefresh/RECEIPTS.md
# against the files they describe (review F5: the register could drift while the battery stayed green).
set -e
cd "$(dirname "$0")/.."
mkdir -p app/out/evidence app/out/eval/gold-v0.3
LOG=app/out/evidence/battery.log
: > "$LOG"

stage() { echo "== $1/$TOTAL $2" | tee -a "$LOG"; }

run_stage() {   # run, show, log, and stop the line on a non-zero exit
  OUT=$(mktemp)
  if "$@" >"$OUT" 2>&1; then STATUS=0; else STATUS=$?; fi
  tee -a "$LOG" <"$OUT"
  rm -f "$OUT"
  if [ "$STATUS" -ne 0 ]; then
    echo "!! STOP THE LINE: $* exited $STATUS"
    exit "$STATUS"
  fi
}

run_stage_report() {   # same, and keep the output as a named artifact
  REPORT="$1"; shift
  OUT=$(mktemp)
  if "$@" >"$OUT" 2>&1; then STATUS=0; else STATUS=$?; fi
  cp "$OUT" "$REPORT"
  tee -a "$LOG" <"$OUT"
  rm -f "$OUT"
  if [ "$STATUS" -ne 0 ]; then
    echo "!! STOP THE LINE: $* exited $STATUS"
    exit "$STATUS"
  fi
}

TOTAL=14

stage 1 "gold eval ========================================="
run_stage_report app/out/eval/gold-v0.3/report.txt \
  python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl
echo

stage 2 "gate parity (node mirror vs python oracle) ======="
run_stage node app/tests/test_gate_parity.py
echo

stage 3 "walking skeleton (offline twin) =================="
run_stage python3 app/run_walking_skeleton.py --selftest
echo

stage 4 "artifact integrity + learner contract ============"
run_stage python3 app/tests/test_artifacts.py
echo

stage 5 "curriculum (objectives, quizzes, micro-lessons) =="
run_stage python3 app/tests/test_curriculum.py
echo

stage 6 "live path (apify · judge · n8n · telemetry · console)"
run_stage python3 app/lib/judge.py --selftest
run_stage python3 app/tests/test_live_modules.py
echo

stage 7 "policy unit checks ==============================="
run_stage python3 app/tests/test_policy.py
echo

stage 8 "threat model ====================================="
run_stage python3 app/tests/test_threat_model.py
echo

stage 9 "gold floor ======================================="
run_stage python3 app/tests/test_gold_floor.py
echo

stage 10 "contracts ======================================="
run_stage python3 app/tests/test_contracts.py
echo

stage 11 "claims =========================================="
run_stage python3 app/tests/test_claims.py
echo

stage 12 "hygiene + design ================================"
run_stage python3 app/tests/test_hygiene.py
run_stage python3 app/tests/test_design.py
echo

stage 13 "handoff collector (redaction + manifest) ========"
run_stage python3 app/tests/test_handoff.py
echo

# the numbers the audit checks are frozen before the audit runs, so its own output cannot move them
python3 app/tools/battery_summary.py "$LOG" > app/out/evidence/battery-summary.json
stage 14 "claims audit (register vs the files) ============"
run_stage python3 app/tools/audit_claims.py --summary app/out/evidence/battery-summary.json
echo
echo "ALL GREEN"
printf "battery green\n" > app/out/evidence/LAST-GREEN.txt
