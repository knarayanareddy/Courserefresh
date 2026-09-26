#!/usr/bin/env python3
"""Containment primitives (TM04, TM05, TM06, TM16). One implementation, used by the twin, the tools
and the tests; production uses the same allowlist carried in `WIRING.md` §2 (mirrored to
`app/out/state/allowlist.json` at preflight).
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

MAX_BYTES = 2 * 1024 * 1024          # TM05: snapshots are truncated, not decompressed without bound
MAX_REDIRECTS = 0                    # TM04: no redirect chase off the allowlist
COURSE_ROOT = "course"               # TM06/TM16: the only writable tree

# Exact hosts (and, where a host serves many projects, exact path prefixes). Art. XIV.1.
ALLOWED: tuple[tuple[str, str], ...] = (
    ("docs.n8n.io", "/"),
    ("github.com", "/n8n-io/n8n/releases"),
    ("blog.n8n.io", "/"),
    ("apify.com", "/changelog"),
    ("docs.apify.com", "/"),
    ("github.com", "/modelcontextprotocol/"),
    ("blog.modelcontextprotocol.io", "/"),
    ("api.tavily.com", "/search"),   # discovery only: role "discovery", never counted (Art. III)
    ("example.invalid", "/"),        # fixture host: labelled fixtures only, never live
)


def host_allowed(url: str) -> tuple[bool, str]:
    """True only for an https URL whose exact host (and required path prefix) is allowlisted."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False, "unparseable"
    if parsed.scheme != "https":
        return False, "https-only"
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    for allowed_host, prefix in ALLOWED:
        if host == allowed_host and path.startswith(prefix):
            return True, f"{allowed_host}{prefix}"
    return False, f"host_not_allowlisted:{host}"


def within_size_cap(content: bytes | str) -> tuple[bool, int]:
    size = len(content.encode()) if isinstance(content, str) else len(content)
    return size <= MAX_BYTES, size


def safe_course_path(root: Path, relative: str, prefix: str = COURSE_ROOT) -> Path:
    """Resolve a write target, refusing anything outside `<root>/<prefix>/**` (TM06/TM16).

    `prefix=""` means the root itself is the course tree (how the offline twin is rooted).
    """
    target = (root / relative).resolve()
    base = (root / prefix).resolve() if prefix else root.resolve()
    if not str(target).startswith(str(base) + "/"):
        raise PermissionError(f"path escapes {prefix}/: {relative}")
    if any(part in (".git", ".github", "..") for part in Path(relative).parts):
        raise PermissionError(f"forbidden path segment: {relative}")
    return target


def bootstrap_course(root: Path, baseline: Path) -> str | None:
    """Give a bare `--root` a course tree to work on, because the documented commands assumed one.

    `python3 app/run_live.py --root app/out/e8 --dry-run --once` and
    `python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail` are the commands
    EVIDENCE.md cites as proof, and both used to die with a FileNotFoundError on a clean checkout:
    `--root` means "a complete tree", which no document said out loud (review F6). A root that
    already holds a course tree (or *is* one) is left untouched.
    """
    root, baseline = Path(root).resolve(), Path(baseline).resolve()
    if root == baseline or (root / "course").is_dir() or (root / "agent-ops").is_dir():
        return None
    if not (baseline / "agent-ops").is_dir():
        return None
    shutil.copytree(baseline, root / "course")
    return f"bootstrapped {root / 'course'} from the authored baseline ({baseline})"


def looks_like_secret(text: str) -> bool:
    """TM12: a receipt/log must never carry these shapes."""
    pattern = (r"gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|apify_api_[A-Za-z0-9]{20,}|"
               r"(?:token|secret|password|api[_-]?key)\s*[:=]\s*\S{8,}")
    return bool(re.search(pattern, text, re.IGNORECASE))
