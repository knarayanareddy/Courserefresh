#!/usr/bin/env python3
"""One place for the numbers (RECEIPTS.md refers here instead of eight one-off scripts).

Usage: python3 app/tools/metrics.py [--out DIR]
Prints JSON: receipts, chain, decisions, publishes, digest bytes, cadence, unmeasured cost fields.
Nothing is invented: a field with no evidence prints null.
"""
import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("twin", ROOT / "app" / "run_walking_skeleton.py")
twin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twin)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "app" / "out"))
    args = ap.parse_args()
    out = Path(args.out)
    tree = twin.Tree(ROOT / "course", out, mode="sim")
    rows = tree.rows()
    ok, n = tree.verify_chain()
    log_lines = [json.loads(l) for l in tree.run_log_path.read_text().splitlines()] if tree.run_log_path.exists() else []
    decisions: dict[str, int] = {}
    for row in rows:
        decisions[row["decision"]["action"]] = decisions.get(row["decision"]["action"], 0) + 1
    costs = [r["cost"] for r in rows if r.get("cost")]
    digest = tree.digest_path.read_text() if tree.digest_path.exists() else ""
    metrics = {
        "run_id": log_lines[-1]["run_id"] if log_lines else None,
        "mode": log_lines[-1]["mode"] if log_lines else None,
        "runs": len(log_lines),
        "receipts": len(rows),
        "chain_ok": ok,
        "chain_rows": n,
        "decisions": decisions,
        "publishes": decisions.get("PUBLISH", 0),
        "digest_bytes": len(digest.encode()) if digest else None,
        "cost_eur": None if all(c.get("eur") is None for c in costs) else [c["eur"] for c in costs],
        "tokens": sum(c.get("tokens") or 0 for c in costs),
        "apify_units": sum(c.get("apify_units") or 0 for c in costs),
        "cadence_min_configured": twin.THRESHOLDS["scan"]["every_min"],
        "cadence_measured": None,   # requires ≥5 live runs; stays null until the loop is live
        "generated_at": datetime.now(timezone.utc).strftime("%Y.%m.%dT%H:%M:%SZ"),
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
