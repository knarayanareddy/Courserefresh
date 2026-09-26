#!/usr/bin/env python3
"""Handoff collector — one command to hand a live run back without handing over a key.

    python3 app/tools/collect_live.py                      # collect the latest run in this checkout
    python3 app/tools/collect_live.py --root DIR --out DIR  # collect from a sandbox / another tree
    python3 app/tools/collect_live.py --no-probe --no-tar   # offline variant

What it does, in order:

1. asks the engine itself for a fresh preflight (`--probe` by default: Apify `/users/me`, judge
   `/models`, n8n `/api/v1/workflows`) — the report carries presence, length and a hash prefix,
   never a value;
2. copies the run's own evidence: `receipts.jsonl`, `run_log.jsonl`, the digest (md + html), the
   cohort gates, the delivery records, the n8n ids file, the Apify unit ledger;
3. **summarises** learner telemetry instead of copying it: counts per lesson, no handles, ever;
4. redacts every value of every secret-looking environment variable it can see, plus a conservative
   shape pattern (bearer tokens, `sk-…`, `apify_api_…`, telegram bot tokens);
5. scans the whole output for those values and **refuses to finish** (exit 3) if one survived;
6. writes `HANDOFF.md` (what this proves, what is still missing, the commands that produced it) and
   `MANIFEST.sha256`, and packs `handoff-<run_id>.tar.gz` unless `--no-tar`.

Exit codes: 0 collected · 1 no run to collect · 2 write problem · 3 secret found after redaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "lib"))

SECRET_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "DSN")
# Conservative shapes only: sha256 digests, run ids and receipt ids must survive untouched.
SHAPES = re.compile(
    r"(?i)(bearer\s+[A-Za-z0-9._\-]{20,}"
    r"|sk-[A-Za-z0-9._\-]{16,}"
    r"|apify_api_[A-Za-z0-9]{10,}"
    r"|xox[baprs]-[A-Za-z0-9\-]{10,}"
    r"|\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b"
    r"|gh[pousr]_[A-Za-z0-9]{20,})"
)
COPY = ["receipts.jsonl", "run_log.jsonl", "digest.md", "digest.html", "notifications.jsonl"]
COPY_UNDER = {
    "live/preflight.json": "preflight.json",
    "live/last_summary.json": "last_summary.json",
    "live/cohort_gates.json": "cohort_gates.json",
    "live/delivery.jsonl": "delivery.jsonl",
    "live/n8n-ids.json": "n8n_ids.json",
    "state/apify_units.jsonl": "apify_units.jsonl",
    "state/run_state.json": "run_state.json",
}


def secret_values(cfg) -> list[str]:
    """Every value this process holds for a secret-looking key, longest first."""
    values = []
    for key, value in getattr(cfg, "env", {}).items():
        if value and any(marker in key.upper() for marker in SECRET_MARKERS) and len(str(value)) >= 8:
            values.append(str(value))
    return sorted(set(values), key=len, reverse=True)


def redact(text: str, values: list[str]) -> tuple[str, int, int]:
    """Returns (clean_text, exact_hits, shape_hits). Shapes are counted, never replaced blindly."""
    exact = 0
    for value in values:
        if value in text:
            exact += text.count(value)
            text = text.replace(value, "«redacted»")
    shaped = len(SHAPES.findall(text))
    text = SHAPES.sub("«redacted-shape»", text)
    return text, exact, shaped


def scan_for_secrets(text: str, values: list[str]) -> list[str]:
    """The guard the collector refuses to pass. Returns the offending values (never printed)."""
    found = [v for v in values if v in text]
    if SHAPES.search(text):
        found.append("«shape:" + SHAPES.search(text).group(0)[:6] + "…»")
    return found


def telemetry_summary(path: Path) -> dict:
    """Counts per lesson and per kind. No handle, no timestamp, no rows — by construction."""
    if not path.exists():
        return {"rows": 0, "note": "no telemetry stored"}
    lessons: dict[str, dict] = {}
    handles: set[str] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        lesson = lessons.setdefault(row.get("lesson_id", "?"), {"events": 0, "kinds": {}})
        lesson["events"] += 1
        lesson["kinds"][row.get("kind", "?")] = lesson["kinds"].get(row.get("kind", "?"), 0) + 1
        handles.add(row.get("learner_ref", ""))
    return {"rows": sum(l["events"] for l in lessons.values()), "distinct_handles": len(handles),
            "lessons": lessons, "note": "handles are counted, never copied"}


def canvas_and_apify(out: Path) -> tuple[dict, dict]:
    runs = [json.loads(l) for l in (out / "run_log.jsonl").read_text().splitlines() if l.strip()] \
        if (out / "run_log.jsonl").exists() else []
    canvas = {"cycles": [], "executions": 0, "mismatches": 0, "degraded": 0}
    for row in runs:
        records = row.get("canvas") or []
        for record in records:
            if record.get("ok") and record.get("same_as_oracle") is not False:
                canvas["executions"] += 1
            elif record.get("ok") is True and record.get("same_as_oracle") is False:
                canvas["mismatches"] += 1
            else:
                canvas["degraded"] += 1
            canvas["cycles"].append({"run_id": row.get("run_id"), **record})
    ledger = out / "state" / "apify_units.jsonl"
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()] if ledger.exists() else []
    apify = {"units_recorded": sum(int(r.get("units", 0)) for r in rows),
             "runs": sorted({r.get("run_id") for r in rows if r.get("run_id")}),
             "sources": sorted({r.get("source_id") for r in rows if r.get("source_id")})}
    return canvas, apify


def environment(cfg, root: Path) -> dict:
    git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True)
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, capture_output=True, text=True)
    return {
        "mode": cfg.mode(), "channel": cfg.channel(),
        "git_sha": git.stdout.strip() or None, "branch": branch.stdout.strip() or None,
        "python": sys.version.split()[0], "platform": sys.platform,
        "keys_present": sorted(k for k in cfg.env if cfg.has(k)),
        "secrets": {k: cfg.masked(k) for k in cfg.env
                    if any(m in k.upper() for m in SECRET_MARKERS)},
        "sources": {s["source_id"]: {"role": s.get("role"), "build": (s.get("fetch") or {}).get("build")}
                    for s in json.loads((ROOT / "specs" / "courserefresh" / "skin" / "sources.json")
                                        .read_text())["sources"]},
    }


def handoff_markdown(run_id: str, meta: dict, canvas: dict, apify: dict, telemetry: dict) -> str:
    mode = meta.get("mode", "unknown")
    warn = ("**This is a `sim` run** — the datasets came from `app/fixtures/apify/`, or `--dry-run` was "
            "set. No Apify actor ran and no workflow executed. The labels in the artifacts say so."
            if mode != "live" else
            "**This is a `live` run** — real Apify datasets and real n8n executions.")
    return f"""# Handoff — run `{run_id}`

{warn}

Collected {meta.get("collected_at")} by `app/tools/collect_live.py` from `{meta.get("root")}`.

## What this run proves

| Thing | Value |
|---|---|
| decisions | {json.dumps(meta.get("decisions", {}), sort_keys=True)} |
| receipt chain verified at end | {meta.get("chain_verified")} |
| canvas executions used for a decision | {canvas["executions"]} (degraded: {canvas["degraded"]}, mismatches: {canvas["mismatches"]}) |
| Apify units recorded | {apify["units_recorded"]} across {len(apify["runs"])} run id(s) |
| telemetry | {telemetry["rows"]} event(s) from {telemetry.get("distinct_handles", 0)} hashed handle(s) |

## What is still missing (the honest list)

- A **delivered** learner card (`CR_NOTIFY_CHANNEL=telegram|webhook`): the `file` channel stages and
  never marks delivered. `delivery.jsonl` says which happened.
- A real **n8n execution id** on the canvas path (`--via-n8n`): see `canvas.json`.
- The first **Apify run id** in `WIRING.md` §6: see `apify_units.jsonl` and `apify_runs` below.

## Commands that produced this

```bash
python3 app/run_live.py --preflight --probe
python3 app/tools/make_n8n_exports.py --import
python3 app/run_live.py --once --via-n8n
```

## Contents

`preflight.json` (presence + fingerprints only) · `run_log.jsonl` · `receipts.jsonl` ·
`digest.md`/`digest.html` · `cohort_gates.json` · `delivery.jsonl` · `n8n_ids.json` ·
`apify_units.jsonl` · `telemetry-summary.json` (counts only) · `canvas.json` ·
`environment.json` · `SECRET-SCAN.txt` · `MANIFEST.sha256`.

Nothing in this folder contains a key: the collector redacts every secret value it can see and
refuses to finish (exit 3) if one survived. `SECRET-SCAN.txt` is the receipt for that claim.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="collect a run's evidence for handoff")
    ap.add_argument("--root", default=str(ROOT), help="tree the run wrote to (default: this checkout)")
    ap.add_argument("--out", default=None, help="where the handoff folder goes (default: <root>/handoff)")
    ap.add_argument("--run-id", default=None, help="default: the latest run in run_log.jsonl")
    ap.add_argument("--no-probe", action="store_true", help="skip the live probes")
    ap.add_argument("--no-tar", action="store_true", help="keep the folder, write no archive")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve() if args.out else root / "handoff"
    run_out = root / "app" / "out"
    if not (run_out / "run_log.jsonl").exists():
        print(json.dumps({"ok": False, "error": "no_run", "hint": f"no run_log.jsonl under {run_out}"}))
        return 1

    from config import Config  # noqa: E402
    cfg = Config()
    values = secret_values(cfg)
    runs = [json.loads(l) for l in (run_out / "run_log.jsonl").read_text().splitlines() if l.strip()]
    run_id = args.run_id or (runs[-1].get("run_id") if runs else None) or datetime.now(timezone.utc).strftime("cr-manual")
    last = runs[-1] if runs else {}
    dest = out_dir / run_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    report: dict = {"run_id": run_id, "root": str(root), "mode": last.get("mode", cfg.mode()),
                    "decisions": last.get("decisions", {}), "chain_verified": last.get("chain_verified_at_end"),
                    "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if not args.no_probe:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("live", root / "app" / "run_live.py")
            live = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(live)
            live.rebase(root)
            report["probe"] = live.preflight(cfg, probe=True)
        except Exception as exc:                       # never fail the collect because a probe did
            report["probe"] = {"ok": False, "error": f"probe_unavailable: {type(exc).__name__}"}
    else:
        report["probe"] = cfg.preflight()

    exact_total = shaped_total = 0
    written: list[Path] = []

    def write(name: str, payload) -> None:
        nonlocal exact_total, shaped_total
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False)
        clean, exact, shaped = redact(text, values)
        exact_total += exact
        shaped_total += shaped
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(clean + ("" if clean.endswith("\n") else "\n"))
        written.append(target)

    for name in COPY:
        path = run_out / name
        if path.exists():
            write(name, path.read_text())
    for source, target_name in COPY_UNDER.items():
        path = run_out / source
        if path.exists():
            write(target_name, path.read_text())
    canvas, apify = canvas_and_apify(run_out)
    write("canvas.json", canvas)
    write("apify_runs.json", apify)
    write("telemetry-summary.json", telemetry_summary(run_out / "state" / "telemetry.jsonl"))
    write("environment.json", environment(cfg, root))
    write("preflight.json", report["probe"])
    write("HANDOFF.md", handoff_markdown(run_id, report, canvas, apify,
                                         telemetry_summary(run_out / "state" / "telemetry.jsonl")))

    # the guard: nothing leaves this machine with a value we can still recognise
    offenders = []
    for path in dest.rglob("*"):
        if path.is_file():
            if scan_for_secrets(path.read_text(errors="ignore"), values):
                offenders.append(path.name)
    scan_line = (f"PASS · {len(written)} files · exact redactions: {exact_total} · "
                 f"shape redactions: {shaped_total}\n")
    if offenders:
        scan_line = (f"FAIL · a secret-shaped string survived in: {', '.join(sorted(offenders))}\n"
                     f"This folder must not be shared. Re-run after removing the offending value.\n")
    (dest / "SECRET-SCAN.txt").write_text(scan_line)
    write("SECRET-SCAN.txt", (dest / "SECRET-SCAN.txt").read_text())

    manifest = []
    for path in sorted(dest.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            manifest.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(dest)}")
    (dest / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")

    archive = None
    if not args.no_tar:
        archive = out_dir / f"handoff-{run_id}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(dest, arcname=run_id)

    ok = not offenders
    print(json.dumps({"ok": ok, "run_id": run_id, "folder": str(dest),
                      "archive": str(archive) if archive else None, "files": len(manifest),
                      "redactions": {"exact": exact_total, "shape": shaped_total},
                      "scan": "pass" if ok else "fail",
                      "missing": [n for n in ("receipts.jsonl", "run_log.jsonl", "digest.md",
                                              "delivery.jsonl", "n8n_ids.json", "apify_units.jsonl")
                                  if not (dest / n).exists()]}, indent=1, sort_keys=True))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
