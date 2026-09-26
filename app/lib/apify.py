#!/usr/bin/env python3
"""Apify client and dataset normaliser (interfaces.md §1; WIRING.md §1–§2b; harness §1 Notice).

What this module guarantees:
  * every actor call carries a pinned actor id and build, a run input and a charge cap;
  * a dataset row becomes a `SourceSnapshot` only if it has a url, markdown and an allowlisted host;
  * rejections are counted and reasoned (`host_not_allowlisted`, `no_url`, `no_markdown`, …) and the
    raw bytes are cached under `app/out/snapshots/` before anything is parsed;
  * units are accounted before spending, and the unit *source* is printed (`usd` when WIRING §5 has
    a price, otherwise the declared 1-run≈1-unit approximation from `skin/sources.json`);
  * a row missing a field the source promised is `source_stale`, never a silent null.

Everything talks through `transport`, a tiny callable `(method, url, headers, body) -> (status, json)`,
so the whole module is testable with no network.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app" / "lib"))
from guard import host_allowed, within_size_cap  # noqa: E402

SKIN = ROOT / "specs" / "courserefresh" / "skin"


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def load_sources() -> dict:
    return json.loads((SKIN / "sources.json").read_text())


def load_thresholds() -> dict:
    return json.loads((SKIN / "thresholds.json").read_text())


# --- transport ---------------------------------------------------------------------------------

def urllib_transport(method: str, url: str, headers: dict, body: dict | None, timeout: int = 60):
    """The only place in the codebase that opens a socket to Apify."""
    import urllib.error
    import urllib.request

    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:  # pragma: no cover - exercised live
        try:
            payload = json.loads(exc.read().decode() or "{}")
        except Exception:
            payload = {"error": {"message": str(exc)}}
        return exc.code, payload
    except urllib.error.URLError as exc:  # pragma: no cover - exercised live
        return 0, {"error": {"message": f"network: {exc.reason}"}}


class RecordingTransport:
    """Wraps a transport and keeps every request (never the token) for the evidence trail."""

    def __init__(self, inner):
        self.inner = inner
        self.calls: list[dict] = []

    def __call__(self, method, url, headers, body, timeout=60):
        status, payload = self.inner(method, url, headers, body, timeout)
        self.calls.append({"method": method, "url": url.split("?")[0], "status": status,
                           "bytes": len(json.dumps(payload)) if payload else 0,
                           "body_keys": sorted(body) if isinstance(body, dict) else []})
        return status, payload


# --- the client --------------------------------------------------------------------------------

class ApifyClient:
    def __init__(self, token: str | None, base_url: str = "https://api.apify.com/v2",
                 transport=urllib_transport, timeout: int = 300, max_retries: int = 1,
                 dry_run: bool = False, dry_dir: Path | None = None):
        self.token = token
        self.base = base_url.rstrip("/")
        self.transport = transport
        self.timeout = timeout
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.dry_dir = dry_dir or (ROOT / "app" / "fixtures" / "apify")

    # --- runs -------------------------------------------------------------------------------
    def run_actor(self, source: dict, budget_units: float | None = None) -> dict:
        """Start one actor run for a source. Returns {ok, run_id, dataset_id, usd, status, error}."""
        fetch = source["fetch"]
        if self.dry_run:
            return self._dry_run(source)
        if not self.token:
            return {"ok": False, "error": "no_token", "code": "actor_failed",
                    "message": "APIFY_TOKEN is not set"}
        actor = fetch["actor_id"]
        # `fetch.budget.max_total_charge_usd` (sources.json) is this actor's spend ceiling. Apify
        # enforces it as `maxTotalChargeUsd` on the run endpoints; the round-3 code pushed a
        # `budget` object into the actor *input*, where the platform ignores it (review F13f). The
        # unit ledger is still the control the loop acts on — this is the platform-side backstop.
        ceiling = (fetch.get("budget") or {}).get("max_total_charge_usd")
        url = (f"{self.base}/acts/{actor}/runs?token={self.token}"
               f"&build={fetch.get('build', 'latest')}&waitForFinish=180"
               + (f"&maxTotalChargeUsd={ceiling}" if isinstance(ceiling, (int, float)) else ""))
        payload = {"input": fetch["input"]}
        attempts, last = 0, {"ok": False, "error": "actor_failed"}
        while attempts <= self.max_retries:
            status, body = self.transport("POST", url, {}, payload, self.timeout)
            last = self._interpret_run(status, body)
            if last["ok"] or status in (400, 401, 403, 402):   # a bad request is not retryable
                break
            attempts += 1
            time.sleep(min(2 ** attempts, 8)) if not self.dry_run else None
        last["attempts"] = attempts + 1
        return last

    @staticmethod
    def _interpret_run(status: int, body: dict) -> dict:
        data = (body or {}).get("data") or {}
        if status in (200, 201) and data.get("id"):
            return {"ok": True, "run_id": data.get("id"), "dataset_id": data.get("defaultDatasetId"),
                    "status": data.get("status"), "usd": data.get("usageTotalUsd"),
                    "error": None}
        message = ((body or {}).get("error") or {}).get("message") or f"HTTP {status}"
        return {"ok": False, "error": "actor_failed", "code": "actor_failed", "message": message,
                "http_status": status}

    def dataset_items(self, dataset_id: str, limit: int = 100) -> list[dict]:
        if self.dry_run:
            return []
        url = f"{self.base}/datasets/{dataset_id}/items?token={self.token}&limit={limit}"
        status, body = self.transport("GET", url, {}, None, self.timeout)
        if status != 200 or not isinstance(body, list):
            return []
        return body

    def _dry_run(self, source: dict) -> dict:
        path = self.dry_dir / f"{source['source_id']}.json"
        if not path.exists():
            return {"ok": False, "error": "no_recorded_dataset", "code": "actor_failed",
                    "message": f"no recorded dataset for {source['source_id']}"}
        data = json.loads(path.read_text())
        return {"ok": True, "run_id": data.get("run_id", f"dry-{source['source_id']}"),
                "dataset_id": f"dry-dataset-{source['source_id']}",
                "status": "SUCCEEDED", "usd": data.get("usd", 0.0), "dry": True, "error": None,
                "items": data["items"]}


# --- normalisation ----------------------------------------------------------------------------

def normalise_row(row: dict, source: dict, max_bytes: int = 2 * 1024 * 1024) -> dict:
    """One dataset row → SourceSnapshot | a reasoned rejection. Never raises."""
    if not isinstance(row, dict) or not row.get("url"):
        return {"ok": False, "reason": "no_url"}
    if not row.get("markdown"):
        return {"ok": False, "reason": "no_markdown"}
    url = str(row["url"])
    allowed, why = host_allowed(url)          # TM04: exact host + required path prefix, https only
    if not allowed:
        return {"ok": False, "reason": "host_not_allowlisted", "detail": why, "url": url}
    markdown = str(row["markdown"])
    ok_size, size = within_size_cap(markdown)  # TM05: 2 MiB cap
    if not ok_size:
        return {"ok": False, "reason": "size_cap_exceeded", "url": url, "bytes": size}
    missing = [f for f in source.get("required_dataset_fields", ["url", "markdown"]) if not row.get(f)]
    if missing:
        return {"ok": False, "reason": "source_stale", "missing": missing, "url": url}
    return {"ok": True, "snapshot": {
        "source_id": source["source_id"], "publisher": source["publisher"],
        "independence_group": source["independence_group"], "role": source["role"],
        "url": url, "title": row.get("title") or url,
        "published_at": row.get("published_at"),
        "content_hash": row.get("content_hash") or sha256_text(markdown),
        "actor_run_id": row.get("actor_run_id") or row.get("run_id"),
        **({"fixture_key": row["fixture_key"]} if row.get("fixture_key") else {}),
        "status": int(row.get("http_status") or 200),
        "markdown": markdown,
    }}


def normalise_dataset(items: list[dict], source: dict, snapshots_dir: Path) -> dict:
    """All rows for one source → snapshots + a tally of everything that was thrown away and why."""
    accepted, rejected = [], []
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    for row in items:
        result = normalise_row(row, source)
        if not result["ok"]:
            rejected.append({"reason": result["reason"], "url": result.get("url"),
                             **({"missing": result["missing"]} if result.get("missing") else {})})
            continue
        snapshot = result["snapshot"]
        digest = snapshot["content_hash"].split(":")[-1][:16]
        raw = snapshots_dir / f"{source['source_id']}-{digest}.md"
        if not raw.exists():
            raw.write_text(snapshot["markdown"])
        try:                                  # keep paths repo-relative when we can, absolute otherwise
            snapshot["raw_path"] = str(raw.relative_to(ROOT))
        except ValueError:
            snapshot["raw_path"] = str(raw)
        accepted.append(snapshot)
    return {"snapshots": accepted, "rejected": rejected,
            "discarded": len(rejected),
            "rejected_reasons": sorted({r["reason"] for r in rejected})}


# --- budgeting ---------------------------------------------------------------------------------

class UnitLedger:
    """Spend before you call. Persisted so a restart cannot forget what was already spent."""

    def __init__(self, path: Path, per_day: float, units_per_run: float = 1.0):
        self.path = path
        self.per_day = per_day
        self.units_per_run = units_per_run
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def spent_today(self) -> float:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        return sum(r["units"] for r in self._rows() if r["day"] == today)

    def can_spend(self, units: float) -> tuple[bool, str]:
        spent = self.spent_today()
        if spent + units > self.per_day:
            return False, f"budget_hold: {spent}+{units} over {self.per_day} units/day"
        return True, f"{spent}+{units} of {self.per_day}"

    def record(self, source_id: str, run_id: str, usd: float | None, unit_price_eur: float | None = None) -> dict:
        if usd is not None and unit_price_eur:
            units = round(float(usd) / unit_price_eur, 4)
            units_source = f"usd/{unit_price_eur} EUR per unit (WIRING.md §5)"
        else:
            units = self.units_per_run
            units_source = "declared 1 run = 1 unit (skin/sources.json; WIRING.md §5 has no price)"
        row = {"day": time.strftime("%Y-%m-%d", time.gmtime()), "source_id": source_id,
               "run_id": run_id, "units": units, "usd": usd, "units_source": units_source,
               "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with self.path.open("a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        return row


def price_state() -> dict:
    """WIRING §5's table, read from app/prices.json. Empty → cost stays `unmeasured`."""
    path = ROOT / "app" / "prices.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    return {"priced": {k: v for k, v in data.items() if v}, "raw": data}
