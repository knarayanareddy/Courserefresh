#!/usr/bin/env python3
"""Freeze the evidence set before it is narrated (EVIDENCE.md §2).

Copies the artifacts of the latest run into app/out/evidence/<run_id>/ and writes MANIFEST.sha256.
Run: python3 app/tools/freeze_evidence.py
"""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "out"
PATTERNS = ["receipts.jsonl", "run_log.jsonl", "digest.md", "digest.html", "notifications.jsonl",
            "eval/**/report.txt", "selftest/**/receipts.jsonl", "micro-lessons/*.md"]


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="freeze one run's evidence")
    ap.add_argument("--out", default=str(OUT), help="the run's output directory (default app/out)")
    ap.add_argument("--course", default=str(ROOT / "course"),
                    help="the course tree this run wrote to (a sandbox has its own)")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    runs = [json.loads(l) for l in (out / "run_log.jsonl").read_text().splitlines()] if (out / "run_log.jsonl").exists() else []
    OUT_LOCAL = out
    run_id = runs[-1]["run_id"] if runs else datetime.utcnow().strftime("cr-%Y%m%d-%H%M-manual")
    dest = out / "evidence" / run_id
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for pattern in PATTERNS:
        for path in OUT_LOCAL.glob(pattern):
            if path.is_file() and "evidence" not in path.parts:
                target = dest / path.relative_to(OUT_LOCAL)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied.append(target)
    course = Path(args.course).resolve()
    for path in course.rglob("*.md"):
        target = dest / "course" / path.relative_to(course)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(target)
    manifest = []
    for path in sorted(copied):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(f"{digest}  {path.relative_to(dest)}")
    (dest / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")
    print(f"froze {len(copied)} files → {dest.relative_to(ROOT)}")
    print((dest / 'MANIFEST.sha256').read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
