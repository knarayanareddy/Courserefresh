#!/usr/bin/env python3
"""Credential and configuration loading (constitution Art. XIV.3; WIRING.md §7).

Rules this module exists to enforce:
  * secrets come from the environment (or a gitignored `.env`) and never from the repository;
  * nothing here ever prints a secret value — only presence, length and a hash prefix;
  * `preflight()` says exactly what is missing, and a missing key degrades the mode instead of
    half-wiring it (`live` needs Apify + a judge; n8n is required to *claim* n8n powers the system).

Run: python3 -c "import sys; sys.path.insert(0,'app/lib'); import config; print(config.preflight())"
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

# Every knob, grouped by the platform it wires. Order matters for the printed preflight.
KEYS: dict[str, list[str]] = {
    "runtime": ["CR_MODE", "CR_LIVE_SCAN_MINUTES", "CR_BOT_BRANCH", "CR_REPO_REMOTE", "CR_DEMO_TOKEN",
                "CR_TELEMETRY_TOKEN", "CR_TELEMETRY_PORT", "CR_CONSOLE_PORT", "CR_CONSOLE_TOKEN",
                "CR_COMMIT", "CR_STATE_DIR"],
    "apify": ["APIFY_TOKEN", "APIFY_BASE_URL", "APIFY_TIMEOUT_S", "APIFY_MAX_RETRIES"],
    "judge": ["CR_JUDGE_PROVIDER", "CR_JUDGE_BASE_URL", "CR_JUDGE_API_KEY", "CR_JUDGE_MODEL",
              "CR_OBSERVE_MODEL", "CR_JUDGE_TIMEOUT_S"],
    "n8n": ["N8N_BASE_URL", "N8N_API_KEY", "N8N_WEBHOOK_URL", "N8N_INSTANCE_VERSION"],
    "notify": ["CR_NOTIFY_CHANNEL", "CR_TELEGRAM_BOT_TOKEN", "CR_TELEGRAM_CHAT_ID",
               "CR_NOTIFY_WEBHOOK_URL"],
}

# What each platform *needs* before the corresponding claim may be made in the video or the pitch.
REQUIRED: dict[str, list[str]] = {
    "apify": ["APIFY_TOKEN"],
    "judge": ["CR_JUDGE_API_KEY"],
    "n8n": ["N8N_BASE_URL", "N8N_API_KEY"],
    "notify": [],           # file channel is a legal default; telegram/webhook need their own keys
}

SECRET_MARKERS = ("TOKEN", "KEY", "SECRET", "PASSWORD")

DEFAULTS: dict[str, str] = {
    "CR_MODE": "auto",
    "CR_LIVE_SCAN_MINUTES": "60",
    "CR_BOT_BRANCH": "bot/courserefresh",
    "CR_REPO_REMOTE": "origin",
    "CR_TELEMETRY_PORT": "8787",
    "CR_CONSOLE_PORT": "8080",
    "APIFY_BASE_URL": "https://api.apify.com/v2",
    "APIFY_TIMEOUT_S": "300",
    "APIFY_MAX_RETRIES": "1",
    "CR_JUDGE_PROVIDER": "mock",
    "CR_JUDGE_BASE_URL": "https://api.openai.com/v1",
    "CR_JUDGE_MODEL": "gpt-4o-mini",
    "CR_OBSERVE_MODEL": "gpt-4o-mini",
    "CR_JUDGE_TIMEOUT_S": "60",
    "CR_NOTIFY_CHANNEL": "file",
    "CR_COMMIT": "0",
}


def load_env_file(path: Path | None = None) -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Values in the real environment always win."""
    path = path or ENV_FILE
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        pairs[key.strip()] = value.strip().strip('"').strip("'")
    return pairs


PREFIXES = ("APIFY_", "N8N_", "CR_", "OPENAI_", "ANTHROPIC_")


def environment(environ: dict[str, str] | None = None) -> dict[str, str]:
    """The process environment, filtered to the knobs this project owns.

    An unfiltered merge would drag PATH and HOME into every receipt; a filtered one still means
    `APIFY_TOKEN=… python3 app/run_live.py` works, which is how the user will paste keys.
    """
    environ = os.environ if environ is None else environ
    known = {k for keys in KEYS.values() for k in keys}
    return {k: v for k, v in environ.items() if k in known or k.startswith(PREFIXES)}


class Config:
    """Resolution order: explicit overrides > real environment > .env file > defaults."""

    def __init__(self, env: dict[str, str] | None = None, env_file: Path | None = None,
                 environ: dict[str, str] | None = None):
        file_values = load_env_file(env_file)
        shell = environment(environ)
        self.env: dict[str, str] = {**DEFAULTS, **file_values, **shell, **(env or {})}
        self.sources: dict[str, str] = {}
        for key in self.env:
            if (env or {}) and key in (env or {}):
                self.sources[key] = "explicit"
            elif key in shell:
                self.sources[key] = "environment"
            elif key in file_values:
                self.sources[key] = ".env"
            else:
                self.sources[key] = "default"

    # --- reads ---------------------------------------------------------------------------------
    def get(self, key: str, default: str | None = None) -> str | None:
        value = self.env.get(key, default)
        return value if value != "" else default

    def has(self, key: str) -> bool:
        return bool(self.env.get(key))

    def int(self, key: str, default: int = 0) -> int:
        try:
            return int(str(self.get(key, str(default))))
        except (TypeError, ValueError):
            return default

    def flag(self, key: str) -> bool:
        return str(self.get(key, "0")).lower() in ("1", "true", "yes", "on")

    def channel(self) -> str:
        return (self.get("CR_NOTIFY_CHANNEL", "file") or "file").lower()

    def masked(self, key: str) -> str:
        """A value's fingerprint: never the value itself."""
        value = self.env.get(key)
        if not value:
            return "absent"
        digest = hashlib.sha256(value.encode()).hexdigest()[:8]
        return f"set(len={len(value)}, sha256={digest})"

    # --- decisions -----------------------------------------------------------------------------
    def missing_for(self, platform: str) -> list[str]:
        return [k for k in REQUIRED.get(platform, []) if not self.has(k)]

    def platform_state(self) -> dict[str, dict]:
        state = {}
        for platform, keys in KEYS.items():
            required = REQUIRED.get(platform, [])
            present = [k for k in keys if self.has(k)]
            state[platform] = {
                "keys_present": present,
                "keys_missing_required": self.missing_for(platform),
                "wired": not self.missing_for(platform),
                "required": required,
            }
        return state

    def mode(self) -> str:
        """`live` only when the platforms that make the claim true are wired."""
        requested = (self.get("CR_MODE", "auto") or "auto").lower()
        if requested in ("sim", "live"):
            return requested
        return "live" if not self.missing_for("apify") and not self.missing_for("judge") else "sim"

    def preflight(self) -> dict:
        state = self.platform_state()
        blocking = [f"{p}:{k}" for p in ("apify", "judge") for k in self.missing_for(p)]
        return {
            "mode": self.mode(),
            "platforms": state,
            "blocking_for_live": blocking,
            "claims_allowed": {
                "apify powers the system": state["apify"]["wired"],
                "n8n runs the decisions": state["n8n"]["wired"],
                "live model calls": state["judge"]["wired"],
                "learner cards delivered": not self.missing_for("notify") and self.channel() != "file",
            },
            "channel": self.channel(),
            "secrets": {k: self.masked(k) for k in self.env if any(m in k for m in SECRET_MARKERS)},
        }


def preflight(env: dict[str, str] | None = None) -> dict:
    return Config(env).preflight()


if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2, sort_keys=True))
