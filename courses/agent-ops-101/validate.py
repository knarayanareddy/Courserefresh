#!/usr/bin/env python3
"""Agent Ops 101 course validator (courses/agent-ops-101).

Same curriculum contract the live loop enforces on course/agent-ops (objectives,
prereqs, quiz alignment — test_curriculum.py), extended for the authored
expansion: 4 items per quiz, substantive explanations, frontmatter consistency,
body-length floors, and generated-answer-distribution sanity (86/96 on one
letter is a generated quiz's tell — shuffle options, remap answers).

This tree is authored (generated: false, PA3 throughout) and lives OUTSIDE
course/ so the live-loop machinery, evidence freezer and test sandboxes never
see it (their globs anchor to course/agent-ops, app/, specs/).

Run: python3 courses/agent-ops-101/validate.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cur = json.loads((ROOT / "curriculum.json").read_text())
lessons = {l["lesson_id"]: l for l in cur["lessons"]}
by_num = {f"lesson-{int(l['lesson_number']):02d}": l for l in cur["lessons"]}
CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), str(detail)))


# 1. structure & frontmatter ---------------------------------------------------------------
missing = []
for l in cur["lessons"]:
    p = ROOT / l["lesson_id"] / "v1.md"
    if not p.exists():
        missing.append(f"{l['lesson_id']}: no v1.md")
        continue
    fm = p.read_text().split("---")[1]
    for field, want in [
        ("lesson_id", f'"{l["lesson_id"]}"'), ("title", f'"{l["title"]}"'), ("version", '"v1"'),
        ("generated", "false"), ("authority", '"PA3"'), ("reviewed_by", '"author"'),
    ]:
        if not re.search(rf"^{field}:\s*{re.escape(want)}\s*$", fm, re.M):
            missing.append(f"{l['lesson_id']} frontmatter {field}!={want}")
check("24 lesson dirs with consistent PA3-authored frontmatter", not missing, f"{missing[:3]}")

# 2. prerequisites: linear chain, acyclic ---------------------------------------------------
bad = []
order = [l["lesson_id"] for l in sorted(cur["lessons"], key=lambda x: x["lesson_number"])]
for i, lid in enumerate(order):
    want = [] if i == 0 else [order[i - 1]]
    if lessons[lid]["prereqs"] != want:
        bad.append(f"{lid}: {lessons[lid]['prereqs']} != {want}")
check("prerequisites form the linear chain 1..24, acyclic", not bad, f"{bad[:3]}")

# 3. objectives: 2-3 per lesson, unique ids, real texts --------------------------------------
thin = [l["lesson_id"] for l in cur["lessons"] if not 2 <= len(l["objectives"]) <= 3]
allids = [o["id"] for l in cur["lessons"] for o in l["objectives"]]
dups = sorted({x for x in allids if allids.count(x) > 1})
short = [o["id"] for l in cur["lessons"] for o in l["objectives"] if len(o["text"]) < 30]
check("every lesson has 2-3 objectives, unique ids, real texts", not thin and not dups and not short,
      f"thin={thin} dups={dups} short={short[:2]}")

# 4. quizzes: alignment, well-formedness, explanations ---------------------------------------
unaligned, malformed, no_expl = [], [], []
for lid, l in by_num.items():
    q = json.loads((ROOT / "quizzes" / f"{lid}.json").read_text())
    if len(q["items"]) != 4:
        malformed.append(f"{lid}: {len(q['items'])} items")
    obj_ids = {o["id"] for o in l["objectives"]}
    covered = set()
    for it in q["items"]:
        if it["objective"] not in obj_ids:
            unaligned.append(f'{lid}:{it["id"]}')
        else:
            covered.add(it["objective"])
        if (not (0 <= it["answer"] < len(it["options"]))) or len(set(it["options"])) != len(it["options"]) \
                or len(it["options"]) < 3 or not it["prompt"].strip():
            malformed.append(f'{lid}:{it["id"]}')
        if len(it.get("explanation", "")) < 60:
            no_expl.append(f'{lid}:{it["id"]}')
    if covered != obj_ids:
        unaligned.append(f"{lid} uncovered: {sorted(obj_ids - covered)}")
check("24 quizzes × 4 items, objective-aligned, all objectives covered", not unaligned, f"{unaligned[:3]}")
check("items well-formed (≥3 unique options, in-range answers)", not malformed, f"{malformed[:3]}")
check("every item carries a substantive explanation", not no_expl, f"{no_expl[:3]}")

# 5. answer distribution (generated-quiz tell) ------------------------------------------------
dist = Counter(it["answer"] for lid in by_num
               for it in json.loads((ROOT / "quizzes" / f"{lid}.json").read_text())["items"])
check("answer indexes distributed across A-D (no mass on one letter)",
      max(dist.values()) <= 40 and set(dist) >= {0, 1, 2}, f"dist={dict(sorted(dist.items()))}")

# 6. bodies: floors and hygiene ----------------------------------------------------------------
body_probs, total_words = [], 0
for l in cur["lessons"]:
    t = (ROOT / l["lesson_id"] / "v1.md").read_text()
    body = t.split("---", 2)[2]
    total_words += len(body.split())
    if len(body.split()) < 700:
        body_probs.append(f"{l['lesson_id']} short body")
    if "**Learning objective.**" not in t or "## Recap" not in t:
        body_probs.append(f"{l['lesson_id']} missing objective line or recap")
    for junk in ("TODO", "TBD", "Lorem", "FIXME"):
        if junk in t:
            body_probs.append(f"{l['lesson_id']} contains {junk}")
    if re.search(r"[\uFFFD\u4e00-\u9fff]", t):
        body_probs.append(f"{l['lesson_id']} non-ASCII garbage")
check("bodies ≥700 words, objective lines, recaps, no junk", not body_probs, f"{body_probs[:3]}")

# 7. module wiring ------------------------------------------------------------------------------
modmap = []
for m in cur["course"]["modules"]:
    a, b = m["lessons"]
    for l in cur["lessons"]:
        if a <= l["lesson_number"] <= b and l.get("module") != m["id"]:
            modmap.append(l["lesson_id"])
check("module membership consistent with ranges", not modmap, f"{modmap[:3]}")

passed = sum(1 for _, ok, _ in CHECKS if ok)
width = max(len(c[0]) for c in CHECKS)
for name, ok, detail in CHECKS:
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
print(f"\nao101-validate: {passed}/{len(CHECKS)} checks passed · {total_words:,} words of lecture prose")
sys.exit(0 if passed == len(CHECKS) else 1)
