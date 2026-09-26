#!/usr/bin/env python3
"""Tavily — discovery and corroboration beside Apify, never a voice of its own (Art. III).

Apify answers "what does this page say now?". It cannot answer "where else did this change land?"
or "which page of the docs actually moved?" — that is a search-engine question, and today the six
sources in `skin/sources.json` are pinned by hand with cadences. Tavily is added for exactly that
gap, in the one way that cannot corrupt the corroboration rule:

    a Tavily hit is a **lead**, not a source.

The engine still publishes only on `skin/thresholds.json → evidence.min_sources` *independent
publishers* (`policy.py` counts distinct publishers, not documents). So:

  * `sources.json` gives the Tavily source `role: "discovery"` and `counts_as_independent: false`;
  * `policy.py` / `policy_node.js` count voices with `role not in ("none", "discovery")`, which is the
    same rule mirrors already had — a discovery hint can be quoted, it cannot vote;
  * quotes found through Tavily are anchored to the page they came from, and that page is fetched
    and attributed to its own publisher before it can vote (the allowlist still gates every fetch);
  * the engine keeps working with no `TAVILY_API_KEY`: the call reports `no_key` and the discovery
    source records itself `unreachable`, an honest gap rather than silence.

`search()` mirrors the published API: `POST https://api.tavily.com/search`, `Authorization: Bearer
tvly-…`, `{query, search_depth, max_results, topic, include_domains, include_raw_content}` →
`{query, answer, results: [{title, url, content, score}], usage}`. Offline, `dry_run=True` replays
`app/fixtures/tavily/search.json`, so this path is verifiable with no key and no egress, like every
other path in this repo.

Run: python3 app/tests/test_live_modules.py
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "app" / "fixtures" / "tavily"
DEFAULT_BASE = "https://api.tavily.com"
DEFAULT_CREDITS_PER_DAY = 30          # Tavily's free tier is 1 000 credits/month; 30/day keeps it
SEARCH_CREDITS = {"basic": 1, "advanced": 2}


def normalise_hit(hit: dict, source: dict | None = None) -> dict | None:
    """One Tavily result → the same snapshot fields the Apify path produces. Never raises.

    The field names are deliberately identical (`markdown`, `content_hash`, `role`, `publisher`) so
    the verify stage needs no branch for discovery: it is one more snapshot, with one difference
    that matters — `role` is `discovery` and `counts_as_independent` is `False`, hard-coded *here*
    rather than in the caller, because the honesty of the independence count must not depend on a
    caller remembering it.
    """
    if not isinstance(hit, dict) or not hit.get("url"):
        return None
    body = (hit.get("raw_content") or hit.get("content") or "").strip()
    if not body:
        return None
    source = source or {}
    markdown = body[: 2 * 1024 * 1024]
    return {"source_id": source.get("source_id", "tavily-discovery"),
            "publisher": hit.get("publisher") or source.get("publisher") or "tavily",
            "independence_group": source.get("independence_group", "search-engine"),
            "role": "discovery",                      # a lead: quoted, never counted
            "counts_as_independent": False,
            "discovered_by": "tavily",
            "search_score": hit.get("score"),
            "url": hit["url"], "title": (hit.get("title") or hit["url"])[:200],
            "published_at": hit.get("published_date"),
            "status": 200,
            "content_hash": hashlib.sha256(body.encode()).hexdigest()[:16],
            "markdown": markdown}


class TavilyClient:
    """The smallest useful client: one search call, a credit ledger, and a dry-run path."""

    def __init__(self, token: str | None, base_url: str = DEFAULT_BASE, transport=None,
                 timeout: int = 60, dry_run: bool = False, dry_dir: Path | None = None):
        self.token, self.base = token, (base_url or DEFAULT_BASE).rstrip("/")
        self.transport, self.timeout = transport, timeout
        self.dry_run, self.dry_dir = dry_run, (dry_dir or FIXTURES)

    def search(self, query: str, *, depth: str = "advanced", max_results: int = 5,
               topic: str = "general", include_domains: list[str] | None = None,
               include_raw_content: bool = True, days: int | None = None) -> dict:
        """One search. Returns {ok, answer, results, credits, usage, error, message} — never raises."""
        credits = SEARCH_CREDITS.get(depth, 1)
        if self.dry_run:
            fixture = self.dry_dir / "search.json"
            if not fixture.exists():
                return {"ok": False, "error": "no_recorded_search", "credits": 0, "results": [],
                        "message": f"no recorded search at {fixture}"}
            recorded = json.loads(fixture.read_text())
            return {"ok": True, "dry": True, "answer": recorded.get("answer"),
                    "results": recorded.get("results", []), "credits": 0,
                    "usage": {"requested": 1, "replayed": 1}}
        if not self.token:
            return {"ok": False, "error": "no_key", "credits": 0, "results": [],
                    "message": "TAVILY_API_KEY is not set; the discovery source records itself unreachable"}
        body: dict = {"query": query, "search_depth": depth, "max_results": max_results,
                      "topic": topic, "include_answer": "basic", "include_raw_content": include_raw_content}
        if include_domains:
            body["include_domains"] = include_domains
        if days:
            body["days"] = days
        status, payload = self.transport("POST", f"{self.base}/search",
                                         {"Authorization": f"Bearer {self.token}",
                                          "Content-Type": "application/json"}, body, self.timeout)
        if status != 200:
            message = {"401": "key rejected", "400": "bad request", "429": "rate limited",
                       "432": "plan limit", "433": "paygo limit"}.get(str(status), f"HTTP {status}")
            return {"ok": False, "error": f"tavily_http_{status}", "message": message,
                    "credits": credits, "results": [], "retryable": status in (429, 500, 502, 503)}
        return {"ok": True, "answer": payload.get("answer"), "results": payload.get("results", []),
                "credits": credits, "usage": payload.get("usage") or {}}


class CreditLedger:
    """Tavily credits per day, declared and printed — the same shape as the Apify unit ledger."""

    def __init__(self, path: Path, per_day: int = DEFAULT_CREDITS_PER_DAY):
        self.path, self.per_day = path, per_day

    def _rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def spent_today(self) -> int:
        day = time.strftime("%Y-%m-%d", time.gmtime())
        return sum(int(r.get("credits", 0)) for r in self._rows()
                   if str(r.get("ts", "")).startswith(day))

    def can_spend(self, credits: int) -> tuple[bool, str]:
        spent = self.spent_today()
        if spent + credits > self.per_day:
            return False, f"tavily credit cap: {spent}/{self.per_day} used today"
        return True, f"{spent + credits}/{self.per_day} credits after this search"

    def record(self, query: str, credits: int, results: int) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "query": query[:120],
               "credits": credits, "results": results, "cap_per_day": self.per_day}
        with self.path.open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        return row


def query_for(source: dict, concepts: list[str] | None = None) -> str:
    """The search string a discovery source asks for: its own query, or its subject + concepts."""
    fetch = source.get("fetch", {})
    if fetch.get("query"):
        return fetch["query"]
    subject = source.get("subject") or source.get("publisher") or "changelog"
    terms = ", ".join(concepts or source.get("concepts") or [])
    return f"{subject} changelog breaking change {terms}".strip()
