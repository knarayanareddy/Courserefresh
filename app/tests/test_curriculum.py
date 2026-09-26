#!/usr/bin/env python3
"""Curriculum integrity: objectives, prerequisites, quiz alignment, micro-lesson contract.

The teacher seat's finding (review 05, T-01…T-04): the subject course was a set of lesson files with
quiz items bolted on, and the agent could "regenerate the quiz" without any test saying what the quiz
was for. This file makes the curriculum a checked artifact: a lesson without objectives, an item
without an objective, a prerequisite cycle, or a micro-lesson that is not two minutes is a defect.

Run: python3 app/tests/test_curriculum.py
"""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)

COURSE = ROOT / "course" / "agent-ops"
curriculum = json.loads((COURSE / "curriculum.json").read_text())
lessons = curriculum["lessons"]
by_id = {l["lesson_id"]: l for l in lessons}
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


# 1. objectives and prerequisites ---------------------------------------------------------------
thin, bad_prereq, cycles = [], [], []
for lesson in lessons:
    if len(lesson.get("objectives", [])) < 2:
        thin.append(lesson["lesson_id"])
    for p in lesson["prereqs"]:
        if p not in by_id:
            bad_prereq.append(f"{lesson['lesson_id']}→{p}")
seen: set[str] = set()
def visit(node: str, path: list[str]) -> None:
    if node in path:
        cycles.append("→".join(path + [node]))
        return
    if node in seen:
        return
    for p in by_id[node]["prereqs"]:
        visit(p, path + [node])
    seen.add(node)
for lesson in lessons:
    visit(lesson["lesson_id"], [])
check("every lesson has ≥2 objectives", not thin, f"thin={thin}")
check("prerequisites point at real lessons, acyclically", not bad_prereq and not cycles,
      f"dangling={bad_prereq} cycles={cycles}")

# 2. quiz items are aligned with objectives ------------------------------------------------------
unaligned, orphaned, malformed = [], [], []
for lesson in lessons:
    quiz_path = COURSE / "quizzes" / f"lesson-{int(lesson['lesson_number']):02d}.json"
    if not quiz_path.exists():
        orphaned.append(f"{lesson['lesson_id']}: no quiz file")
        continue
    quiz = json.loads(quiz_path.read_text())
    obj_ids = {o["id"] for o in lesson["objectives"]}
    mapped = set()
    for item in quiz["items"]:
        target = lesson["quiz_items"].get(item["id"])
        if target not in obj_ids:
            unaligned.append(f"{lesson['lesson_id']}:{item['id']}")
        else:
            mapped.add(target)
        if not (0 <= item["answer"] < len(item["options"])) or len(set(item["options"])) != len(item["options"]) \
                or len(item["options"]) < 3 or not item["prompt"].strip():
            malformed.append(f"{lesson['lesson_id']}:{item['id']}")
    missing = obj_ids - mapped
    if missing:
        unaligned.append(f"{lesson['lesson_id']} objectives without items: {sorted(missing)}")
check("every quiz item maps to a real objective", not unaligned, "; ".join(unaligned[:3]))
check("every lesson has a quiz whose items are well-formed", not orphaned and not malformed,
      f"orphaned={orphaned[:2]} malformed={malformed[:3]}")

# 3. a regenerated item stays aligned when the loop writes it ------------------------------------
sandbox = ROOT / "app" / "out" / "curriculum-test"
if sandbox.exists():
    shutil.rmtree(sandbox)
shutil.copytree(ROOT / "course", sandbox / "course")
tree = twin.Tree(sandbox / "course", sandbox / "app" / "out", mode="sim")
event = next(e for e in twin.load_events() if e["event_id"] == "cr-n8n-rename-01")
twin.apply_patch(tree, event, {"authority": "PA2"}, "curriculum-test")
written = json.loads((tree.root / "agent-ops" / "quizzes" / "lesson-04.json").read_text())
item = next(i for i in written["items"] if i["id"] == event["quiz_patch"]["item_id"])
check("the regenerated quiz item is well-formed and traceable",
      0 <= item["answer"] < len(item["options"]) and item.get("regenerated_by") == event["event_id"],
      f"answer={item['answer']} by={item.get('regenerated_by')}")

# 4. the micro-lesson contract ------------------------------------------------------------------
contract = curriculum["micro_lesson_contract"]
stuck = next(e for e in twin.load_events() if e["event_id"] == "cr-learner-stuck-01")
record = twin.dispatch_micro_lesson(tree, stuck, "curriculum-test")
text = (tree.out / record["path"]).read_text()
parts_ok = all(p in text for p in ("1. What it is", "2. Worked example", "3. Practice"))
check("a dispatched micro-lesson names the concept, has the three parts, and fits two minutes",
      stuck["input"]["concept"] in text and parts_ok and len(text.split()) <= contract["max_words"]
      and "graded" not in text.lower(),
      f"words={len(text.split())} parts={parts_ok}")

# 5. learner-facing copy exists for anything that actually notified, and it is human --------------
sandbox2 = ROOT / "app" / "out" / "curriculum-test-2"
if sandbox2.exists():
    shutil.rmtree(sandbox2)
shutil.copytree(ROOT / "course", sandbox2 / "course")
tree2 = twin.Tree(sandbox2 / "course", sandbox2 / "app" / "out", mode="sim")
twin.run(tree2, twin.load_events(), label="curriculum-test")
fixtures = {e["event_id"]: e for e in twin.load_events()}
notified = [r for r in tree2.rows() if (r["artifact"] or {}).get("notified")]
missing_copy = [r["event_id"] for r in notified if not fixtures[r["event_id"]].get("learner_facing")]
opaque = [r["event_id"] for r in notified
          if "policy" in fixtures[r["event_id"]]["learner_facing"].lower()
          or "receipt" in fixtures[r["event_id"]]["learner_facing"].lower()]
copy_too_long = [e["event_id"] for e in fixtures.values() if len(e.get("learner_facing", "")) > 240]
check("every change that notified carries learner-facing copy (≤240 chars, no internal jargon)",
      bool(notified) and not missing_copy and not opaque and not copy_too_long,
      f"notified={len(notified)} missing={missing_copy} jargon={opaque} long={copy_too_long}")

# 6. downstream lessons are named, never silently rewritten --------------------------------------
downstream = twin.downstream_lessons("lesson-04-tool-permissions")
check("a change names the downstream lessons to revisit", downstream == ["lesson-05-receipts-and-reverts",
                                                                        "lesson-06-evals-that-survive"],
      f"downstream={downstream}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\ntest_curriculum: {passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
