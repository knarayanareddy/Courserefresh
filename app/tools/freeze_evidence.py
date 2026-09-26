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
PATTERNS = ["receipts.jsonl", "run_log.jsonl", "digest.md", "notifications.jsonl",
            "eval/**/report.txt", "selftest/**/receipts.jsonl", "micro-lessons/*.md"]


def main() -> int:
    runs = [json.loads(l) for l in (OUT / "run_log.jsonl").read_text().splitlines()] if (OUT / "run_log.jsonl").exists() else []
    run_id = runs[-1]["run_id"] if runs else datetime.utcnow().strftime("cr-%Y%m%d-%H%M-manual")
    dest = OUT / "evidence" / run_id
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for pattern in PATTERNS:
        for path in OUT.glob(pattern):
            if path.is_file() and "evidence" not in path.parts:
                target = dest / path.relative_to(OUT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied.append(target)
    course = ROOT / "course"
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
