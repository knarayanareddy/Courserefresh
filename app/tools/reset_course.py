#!/usr/bin/env python3
"""Reset the course artifact to its authored baseline (lesson 04 at v3, everything else at v1).

The loop is not idempotent for revert/learner events (only change events dedupe), so a demo or a
fresh evidence run starts from a known state. This script is the honest way to say "the loop wrote
those versions" — it deletes only versions the loop wrote, never the authored v1/v3 bodies.

Run: python3 app/tools/reset_course.py [--course DIR] [--out DIR]
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = {"lesson-04-tool-permissions": 3}
README_HEAD = "| Lesson | Title | Version |"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", default=str(ROOT / "course"))
    ap.add_argument("--out", default=str(ROOT / "app" / "out"))
    args = ap.parse_args()
    course = Path(args.course)
    out = Path(args.out)
    removed = []
    for lesson in sorted((course / "agent-ops").glob("lesson-*")):
        keep = BASELINE.get(lesson.name, 1)
        for path in sorted(lesson.glob("v*.md")):
            n = int(path.stem[1:])
            if n > keep:
                path.unlink()
                removed.append(path.relative_to(course))
        diffs = lesson / "diffs"
        if diffs.exists():
            shutil.rmtree(diffs)
    changelog = course / "agent-ops" / "CHANGELOG.md"
    changelog.write_text("# Changelog — Agent Ops\n\n## v1 / v3 — initial\nSix lessons authored; lesson 04 at v3 after two author edits.\n")
    readme = course / "agent-ops" / "README.md"
    if readme.exists():
        titles = {}
        for lesson in sorted((course / "agent-ops").glob("lesson-*")):
            num = lesson.name.split("-")[1]
            keep = BASELINE.get(lesson.name, 1)
            fm = (lesson / f"v{keep}.md").read_text().split("---")[1]
            title = [l for l in fm.splitlines() if l.startswith("title:")][0].split(":", 1)[1].strip().strip('"')
            titles[num] = (title, f"v{keep}")
        lines = []
        for line in readme.read_text().splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")] if line.startswith("|") else []
            if len(cells) == 3 and cells[0] in titles:
                title, version = titles[cells[0]]
                line = f"| {cells[0]} | {title} | {version} |"
            lines.append(line)
        readme.write_text("\n".join(lines) + "\n")
    for name in ("receipts.jsonl", "run_log.jsonl", "digest.md", "notifications.jsonl"):
        path = out / name
        if path.exists():
            path.unlink()
    state = out / "state"
    if state.exists():
        shutil.rmtree(state)
    print(f"reset: removed {len(removed)} loop-written versions; state cleared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
