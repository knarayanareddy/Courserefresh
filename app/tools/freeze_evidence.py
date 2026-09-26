#!/usr/bin/env python3
"""Freeze the evidence set before it is narrated (EVIDENCE.md §2).

Copies the artifacts of the latest run into app/out/evidence/<run_id>/ and writes MANIFEST.sha256.
Run: python3 app/tools/freeze_evidence.py
"""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "out"
PATTERNS = ["receipts.jsonl", "run_log.jsonl", "digest.md", "digest.html", "notifications.jsonl",
            "eval/**/report.txt", "selftest/**/receipts.jsonl", "micro-lessons/*.md",
            # the live path's own proof: what the engine thought was wired, and the one screen D-1 is
            # read from (E8/E10). Without these a live-engine bundle cannot say why it stayed in sim.
            "live/preflight.json", "live/preflight.txt", "live/last_cycle.json", "live/last_summary.json"]


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="freeze one run's evidence")
    ap.add_argument("--out", default=str(OUT), help="the run's output directory (default app/out)")
    ap.add_argument("--course", default=str(ROOT / "course"),
                    help="the course tree this run wrote to (a sandbox has its own)")
    ap.add_argument("--ship", action="store_true",
                    help="also copy the bundle into specs/evidence/<run_id>/ so the proof travels "
                         "with the repository (review F4: app/out is gitignored, so every "
                         "EVIDENCE.md pointer resolved to nothing on a clone)")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    runs = [json.loads(l) for l in (out / "run_log.jsonl").read_text().splitlines()] if (out / "run_log.jsonl").exists() else []
    OUT_LOCAL = out
    run_id = runs[-1]["run_id"] if runs else datetime.now(timezone.utc).strftime("cr-%Y%m%d-%H%M-manual")
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

    if args.ship:
        shipped = ROOT / "specs" / "evidence" / run_id
        if shipped.exists():
            shutil.rmtree(shipped)
        shipped.mkdir(parents=True)
        # the proof set, curated: the chains, the rendered surfaces, the eval, the changed lessons
        keep = ["receipts.jsonl", "run_log.jsonl", "digest.md", "digest.html", "notifications.jsonl",
                # the live path's own proof: what the engine thought was wired (E8) and the one screen
                # D-1 is read from (E10). A curated bundle that drops these cannot answer "why sim?".
                "live/preflight.json", "live/preflight.txt", "live/last_cycle.json"]
        for pattern in keep + ["eval/**/report.txt", "micro-lessons/*.md", "course/**/*.md", "course/**/*.diff"]:
            for path in sorted(dest.glob(pattern)):
                if path.is_file():
                    target = shipped / path.relative_to(dest)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
        (shipped / "README.md").write_text(
            f"# Frozen evidence — {run_id}\n\n"
            "Shipped with the repository on purpose: `app/out/` is gitignored, so a pointer into it\n"
            "resolves to nothing on a clone and the hashes in `specs/courserefresh/EVIDENCE.md`\n"
            "cannot be checked by anyone. Everything here is a copy of a real run's artifacts.\n\n"
            "- `MANIFEST.sha256` — every file, hashed. `app/tools/audit_claims.py` re-hashes it on\n"
            "  every battery run, so a bundle that no longer matches its manifest fails the build.\n"
            "- `receipts.jsonl` — the chained decision log (each row hashes the row before it).\n"
            "- `digest.md` / `digest.html` — the report and the console page, refusals first.\n"
            "- `course/**` — the lesson versions and diffs the run wrote.\n\n"
            f"Regenerate a local copy with the commands in `EVIDENCE.md` §4; the run id will differ\n"
            "(it is a timestamp), which is why the hashes here are the ones that travel.\n")
        shipped_manifest = []
        for path in sorted(shipped.rglob("*")):
            if path.is_file() and path.name != "MANIFEST.sha256":
                shipped_manifest.append(
                    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(shipped)}")
        (shipped / "MANIFEST.sha256").write_text("\n".join(shipped_manifest) + "\n")
        print(f"shipped {len(shipped_manifest)} files → {shipped.relative_to(ROOT)}")
    print((dest / 'MANIFEST.sha256').read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
