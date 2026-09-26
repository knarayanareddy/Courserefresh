#!/usr/bin/env python3
"""Author rulings — a person's call on a queued row, bound to the evidence they saw (D-32, Art. IX).

The canvas (`app/lib/canvas.py`) *shows* a teacher the diff, the sources and how fragile the decision
is; the console's `POST /canvas/decision` records their ruling. Until this module existed the ruling
was a record and nothing more: it was stored, it was shown back, and the loop did exactly what it
would have done anyway. A decision surface that decisions do not change is a report, so:

* the console writes the ruling **and the fingerprint of the evidence it was made about**;
* the loop, before it acts on an event, looks for the latest ruling for that event
  (`state/author_decisions.jsonl`, read from the run's own `app/out`);
* the ruling is the decision of record **only if it still describes the world**: same evidence
  fingerprint *and* the machine would still make the same decision it made when the author ruled.
  Otherwise it is ignored, the row returns to the queue, and both the receipt and the canvas say why
  (an approval that survives the evidence changing underneath it is a blank cheque, not a decision).

**What a person may override is a closed set** (`APPROVABLE`): the evidence-class refusals, where the
question is "is this publisher good enough for us?" and a person is the right authority. What a person
may **not** override is the machine's own guarantees — hostile input, missing consent, an over-budget
run, a fail-closed judgement, a write that failed. Those are not judgement calls about content, they
are the rules that keep the product safe, and a human approval must not be able to switch them off
(Art. III, IV, V, XIV). Widening the set is an amendment, not a config change.

Precedence when more than one authority speaks for one event: **human > canvas > oracle** (D-32,
AC-16.1). The oracle still runs on every event and its verdict stays on the receipt, so a human
override is visible to whoever audits the chain, never silent.

Output: nothing of its own. `plan()` is pure; `run()` in `app/run_walking_skeleton.py` applies it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# The reason codes whose refusal a human may lift. Both are evidence-class: the facts are known, the
# question is whether they are enough. Nothing here is "the model was unsure" (that is a judgement to
# re-run, not to overrule) and nothing here bypasses a safety, consent, budget or integrity rule.
APPROVABLE = ("insufficient_corroboration", "source_conflict")

# The reason code a human approval stamps on the publish. It is in `change_taxonomy.json` (the closed
# vocabulary every runtime shares); the oracle can never emit it, and that is the point — the receipt
# says a person decided, and `decided_by` says which person.
APPROVED_REASON = "human_signoff"

# The evidence half of a DecisionInput: everything the decision was *about*. Run state (`budgets`,
# `freeze_active`, `caps`, `concept_recently_dispatched`) is deliberately outside the fingerprint —
# publishes spent, a pause switch and per-learner caps change between runs without the evidence
# changing, and those are policed separately (the machine's verdict is compared too, see `plan`).
EVIDENCE_FIELDS = (
    "materiality", "learner_impact", "breaking_probability", "source_agreement", "quote_supported",
    "injection_or_jailbreak", "sources_verified", "authority", "stream", "event_id", "stuck",
    "concept", "grade_impacting", "consent",
)

REJECT_DEFAULT_REASON = "immaterial_change"


def evidence_of(inp: dict) -> dict:
    """The decision-relevant slice of an input dict (engine `inp` or a receipt's recorded `inputs`)."""
    return {k: (inp or {}).get(k) for k in EVIDENCE_FIELDS if k in (inp or {})}


def fingerprint(kind: str, event_id: str, evidence: dict, sources, quotes) -> str:
    """A stable hash of *what the decision was made about*.

    Hashed with sorted keys and no whitespace so the engine and the console — which compute it from
    different objects (a live event, a stored receipt row) — cannot disagree by accident.
    """
    payload = {"kind": kind, "event_id": event_id, "evidence": evidence,
               "sources": sources or [], "quotes": quotes or []}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def fingerprint_event(event: dict, inp: dict) -> str:
    """The fingerprint as the loop computes it, from the event and the inputs it is deciding on."""
    return fingerprint(event.get("kind") or (inp or {}).get("stream") or "",
                       event.get("event_id") or (inp or {}).get("event_id") or "",
                       evidence_of(inp), event.get("sources"), event.get("quotes"))


def fingerprint_receipt(row: dict) -> str:
    """The same fingerprint as the console computes it, from the receipt the human ruled on."""
    return fingerprint(row.get("stream") or (row.get("inputs") or {}).get("stream") or "",
                       row.get("event_id") or (row.get("inputs") or {}).get("event_id") or "",
                       evidence_of(row.get("inputs") or {}), row.get("sources"), row.get("quotes"))


def load(path: Path) -> list[dict]:
    """Every ruling on disk, oldest first. A malformed line is skipped, never fatal."""
    if not Path(path).exists():
        return []
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:  # noqa: BLE001 - a corrupt ruling line must not stop the loop
            continue
        if isinstance(row, dict) and row.get("receipt_id"):
            rows.append(row)
    return rows


def for_event(rows: list[dict], event_id: str) -> dict | None:
    """The latest ruling about this event, or None. Latest wins: a person may change their mind."""
    matches = [r for r in rows if r.get("event_id") == event_id]
    return matches[-1] if matches else None


def ruling_payload(row: dict, ruling: str, reason_code: str, note: str, actor: str) -> dict:
    """The record the console writes: the call, plus the evidence it was made about (D-32)."""
    return {"ts": None, "run_id": None, "receipt_id": row["receipt_id"], "event_id": row.get("event_id"),
            "ruling": ruling, "reason_code": reason_code, "note": note, "actor": actor,
            "authority": "PA3", "action_under_review": (row.get("decision") or {}).get("action"),
            "reason_codes_under_review": (row.get("decision") or {}).get("reason_codes") or [],
            "fingerprint": fingerprint_receipt(row)}


def plan(ruling: dict | None, event: dict, inp: dict, machine: dict) -> dict:
    """Would this ruling decide this event? Pure; never raises.

    Returns `{"status", "override", "record"}`:

      * `applied`         — the override is the decision of record (`authority: PA3`);
      * `stale`           — the evidence changed since the author ruled;
      * `superseded`      — same evidence, but the machine's verdict changed anyway (spend, freeze,
                            caps): a different question from the one the author answered;
      * `not_approvable`  — the refusal is a machine guarantee, not a judgement call;
      * `unknown`         — no ruling for this event.
    """
    if not ruling:
        return {"status": "unknown", "override": None, "record": None}
    record = {"receipt_id": ruling.get("receipt_id"), "ruling": ruling.get("ruling"),
              "reason_code": ruling.get("reason_code"), "actor": ruling.get("actor"),
              "ts": ruling.get("ts"), "fingerprint": ruling.get("fingerprint")}
    known_everywhere = ruling.get("fingerprint") in (None, "")
    now = fingerprint_event(event, inp)
    if known_everywhere or now != ruling.get("fingerprint"):
        # a ruling written before fingerprints existed cannot be bound to anything; treat it as stale
        record["stale"] = True
        record["why"] = ("this ruling predates evidence fingerprints, so nothing can bind it"
                         if known_everywhere else
                         "the evidence changed after this ruling (a new fact, a new source or a new judgement)")
        return {"status": "stale", "override": None, "record": record}
    under_review = ruling.get("reason_codes_under_review") or []
    if not under_review or any(r not in APPROVABLE for r in under_review):
        record["why"] = ("this refusal is not a judgement call: "
                         + ", ".join(under_review or ["(no reason codes recorded)"]))
        return {"status": "not_approvable", "override": None, "record": record}
    if machine.get("action") != ruling.get("action_under_review") or \
            sorted(machine.get("reason_codes") or []) != sorted(under_review):
        record["why"] = (f"the machine's verdict changed since the ruling "
                         f"({machine.get('action')}({', '.join(machine.get('reason_codes') or [])}) "
                         f"now, {ruling.get('action_under_review')}({', '.join(under_review)}) then)")
        return {"status": "superseded", "override": None, "record": record}
    if ruling.get("ruling") == "approve":
        override = {"action": "PUBLISH", "reason_codes": [APPROVED_REASON], "authority": "PA3",
                    "notes": f"author {ruling.get('actor')} approved {ruling.get('receipt_id')}: "
                             f"{ruling.get('reason_code')}"}
    elif ruling.get("ruling") == "reject":
        override = {"action": "NO_CHANGE",
                    "reason_codes": [ruling.get("reason_code") or REJECT_DEFAULT_REASON],
                    "authority": "PA3",
                    "notes": f"author {ruling.get('actor')} declined {ruling.get('receipt_id')}"
                             + (f": {ruling.get('note')}" if ruling.get("note") else "")}
    else:
        record["why"] = f"unknown ruling {ruling.get('ruling')!r}"
        return {"status": "not_approvable", "override": None, "record": record}
    record["applied"] = True
    return {"status": "applied", "override": override, "record": record}


# --- the withheld-delta queue -------------------------------------------------------------------
# A refused change leaves no artifact: the patch that would have published it lived in the scan
# result, and the receipt records only the *inputs* the decision was made from. So when the loop
# refuses a delta for an approvable reason it keeps the delta itself here, patch and all. Without
# this, an author's "approve" could never act on anything: the next scan of an unchanged source
# produces no delta (nothing changed), and the refusal would stand forever. With it, the ruling is
# applied by the next cycle, which is what "the ruling binds the cycle" has to mean in practice.

PENDING_DEFAULT_CAP = 20          # overridden by `thresholds.review.pending_cap`


def pending_path(out: Path) -> Path:
    return Path(out) / "state" / "pending.jsonl"


def load_pending(out: Path, cap: int = PENDING_DEFAULT_CAP) -> list[dict]:
    """The deltas the loop refused but a person could still approve, oldest first. Never raises."""
    rows = []
    for line in (pending_path(out).read_text().splitlines() if pending_path(out).exists() else []):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:  # noqa: BLE001 - a corrupt queue line must not stop the loop
            continue
        if isinstance(row, dict) and row.get("event_id"):
            rows.append(row)
    return rows[-cap:]


def save_pending(out: Path, rows: list[dict], cap: int = PENDING_DEFAULT_CAP) -> None:
    path = pending_path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    kept = rows[-cap:]
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in kept))


def remember(out: Path, event: dict, decision: dict, cap: int = PENDING_DEFAULT_CAP) -> bool:
    """Keep this refused delta so a later author ruling can still act on it. Returns whether it did.

    Only the evidence-class refusals are kept (`APPROVABLE`): there is nothing a person can usefully
    do about `over_budget` or `write_failed` here, and a queue of things nobody can decide is how a
    queue stops being read.
    """
    codes = decision.get("reason_codes") or []
    if decision.get("action") != "ESCALATE" or not codes or any(c not in APPROVABLE for c in codes):
        return False
    rows = [r for r in load_pending(out, cap) if r.get("event_id") != event.get("event_id")]
    rows.append(json.loads(json.dumps(event, default=str)))     # a copy: the caller mutates `event`
    save_pending(out, rows, cap)
    return True


def resolve(out: Path, event_ids, cap: int = PENDING_DEFAULT_CAP) -> int:
    """Drop deltas a person has ruled on (their call is now the record). Returns how many went."""
    decided = set(event_ids)
    rows = load_pending(out, cap)
    kept = [r for r in rows if r.get("event_id") not in decided]
    if len(kept) != len(rows):
        save_pending(out, kept, cap)
    return len(rows) - len(kept)


def replays(pending: list[dict], ruling_rows: list[dict]) -> list[dict]:
    """The withheld deltas a live ruling now decides — to be re-decided this cycle.

    Both rulings come back: an approval so the change can publish at the author's authority, a
    rejection so the event's own row records "closed by a person" instead of leaving the refusal as
    the last word. Either way the delta then leaves the withheld queue (`resolve`), so the replay
    happens once per ruling, not once per cycle.
    """
    out = []
    for row in pending:
        ruling = for_event(ruling_rows, row.get("event_id"))
        if ruling and ruling.get("ruling") in ("approve", "reject"):
            clone = json.loads(json.dumps(row, default=str))
            clone["ruling_replay"] = True
            out.append(clone)
    return out


def expired(ruling: dict | None, row: dict) -> dict | None:
    """Has a ruling for this receipt stopped describing the world? (What the canvas shows a teacher.)

    `None` when there is nothing to say; otherwise `{"status", "why"}`. Used by the canvas so a row
    the author ruled on does not look settled after the evidence moved underneath it.
    """
    if not ruling:
        return None
    if (ruling.get("fingerprint") or "") != fingerprint_receipt(row):
        return {"status": "stale",
                "why": "the evidence changed after your ruling — the row is back in the queue"}
    return None
