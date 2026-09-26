#!/usr/bin/env python3
"""The judge: the only place a language model is asked anything (harness §2; questions.json).

Rules this module enforces, because a model call is where honesty usually dies:
  * only the seven questions in `skin/questions.json` may be asked — the prompt is built from that
    file and from the event's own text, never from thresholds, never from the expected action;
  * temperature is 0 and the answer must be strict JSON; anything else is `payload_invalid`;
  * an answer outside the closed set, a missing question, or an unparsable response fails **closed**
    (`unknown_state`) — the policy then escalates, it never publishes;
  * providers are pluggable: `mock` (deterministic, offline), `openai` (any OpenAI-compatible base
    URL), `anthropic`, `n8n` (webhook), and `jev` (TypeSafe System One — a *typed decision* endpoint,
    not a chat model: it answers the seven closed questions and renders nothing, see jev.py);
  * tokens are counted per call and summed per change/day against `thresholds.budgets`.

Run: python3 app/lib/judge.py --selftest
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIN = ROOT / "specs" / "courserefresh" / "skin"
sys.path.insert(0, str(ROOT / "app" / "lib"))
import jev as jev_lib  # noqa: E402  (the System One decision provider; see jev.py)
from apify import urllib_transport  # noqa: E402  (the same no-dependency HTTP client)
from config import Config  # noqa: E402

QUESTIONS_PATH = SKIN / "questions.json"
THRESHOLDS = json.loads((SKIN / "thresholds.json").read_text())
QUESTIONS = json.loads(QUESTIONS_PATH.read_text())["questions"]

SYSTEM_PROMPT = (
    "You answer closed questions about a documentation change so a separate rule engine can decide "
    "what to do. Answer only from the text you are given. Never guess at policy, priorities or "
    "thresholds. Reply with one JSON object, keys exactly as named, no prose."
)


def prompt_for(event: dict) -> str:
    """The user prompt. Contains the questions, the quotes and the lesson's objective — nothing else."""
    lines = ["QUESTIONS (answer every one):"]
    for q in QUESTIONS:
        if q["type"] == "Choice":
            lines.append(f'- {q["id"]} (one of: {", ".join(q["options"])}): {q["proposition"]}')
        else:
            lines.append(f'- {q["id"]} (a probability between 0 and 1): {q["proposition"]}')
    lines.append("")
    lines.append("CHANGE UNDER CONSIDERATION:")
    lines.append(f"- source summary: {event.get('summary', '')}")
    lines.append(f"- lesson touched: {event.get('lesson_touched', '')}")
    lines.append(f"- lesson objective: {event.get('objective', '(not stated)')}")
    for i, quote in enumerate(event.get("quotes", []), 1):
        lines.append(f"- quote {i} ({quote.get('source_id', '?')}): \"{quote.get('text', '')}\"")
    lines.append("")
    lines.append("Reply with JSON only.")
    return "\n".join(lines)


def prompt_hash(event: dict) -> str:
    return "sha256:" + hashlib.sha256((SYSTEM_PROMPT + prompt_for(event)).encode()).hexdigest()


# --- providers ---------------------------------------------------------------------------------

class MockProvider:
    """Deterministic answers from the event itself (fixtures carry `judge_answers`).

    The mock exists so the whole loop, including the judge's schema validation, runs offline. It is
    labelled `mock` on every receipt, so nothing produced with it can be mistaken for a live call.
    """
    name = "mock"

    def complete(self, system: str, user: str, model: str) -> dict:
        answers = getattr(self, "answers", None)
        if answers is None:
            raise ValueError("MockProvider needs .answers")
        return {"text": json.dumps(answers), "prompt_tokens": len(user) // 4,
                "completion_tokens": len(json.dumps(answers)) // 4, "usd": None,
                "confidences": getattr(self, "confidences", None)}


class HttpProvider:
    """OpenAI-compatible chat completions (OpenAI, OpenRouter, vLLM, local gateways)."""

    name = "openai"

    def __init__(self, base_url: str, api_key: str, transport, timeout: int = 60):
        self.base_url, self.api_key, self.transport, self.timeout = base_url.rstrip("/"), api_key, transport, timeout

    def complete(self, system: str, user: str, model: str) -> dict:
        body = {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        status, payload = self.transport("POST", f"{self.base_url}/chat/completions",
                                         {"Authorization": f"Bearer {self.api_key}"}, body, self.timeout)
        if status != 200:
            raise RuntimeError(f"judge_http_{status}: {json.dumps(payload)[:200]}")
        choice = (payload.get("choices") or [{}])[0]
        usage = payload.get("usage") or {}
        return {"text": (choice.get("message") or {}).get("content", ""),
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "usd": None}


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, base_url: str, api_key: str, transport, timeout: int = 60):
        self.base_url, self.api_key, self.transport, self.timeout = base_url.rstrip("/"), api_key, transport, timeout

    def complete(self, system: str, user: str, model: str) -> dict:
        body = {"model": model, "max_tokens": 1024, "temperature": 0, "system": system,
                "messages": [{"role": "user", "content": user}]}
        status, payload = self.transport("POST", f"{self.base_url}/messages",
                                         {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}, body, self.timeout)
        if status != 200:
            raise RuntimeError(f"judge_http_{status}: {json.dumps(payload)[:200]}")
        text = "".join(block.get("text", "") for block in payload.get("content", []))
        usage = payload.get("usage") or {}
        return {"text": text, "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"), "usd": None}


class WebhookProvider:
    """The n8n route: a webhook answers exactly like the others. Keeps the canvas in the loop."""

    name = "n8n"

    def __init__(self, webhook_url: str, token: str | None, transport, timeout: int = 60):
        self.webhook_url, self.token, self.transport, self.timeout = webhook_url, token, transport, timeout

    def complete(self, system: str, user: str, model: str) -> dict:
        headers = {"X-CR-Token": self.token} if self.token else {}
        status, payload = self.transport("POST", self.webhook_url, headers,
                                         {"system": system, "user": user, "model": model}, self.timeout)
        if status not in (200, 201):
            raise RuntimeError(f"judge_webhook_{status}")
        return {"text": payload.get("text", ""), "prompt_tokens": payload.get("prompt_tokens"),
                "completion_tokens": payload.get("completion_tokens"), "usd": payload.get("usd")}


def probe_provider(cfg: Config, transport) -> dict:
    """Validate the pasted judge key with one cheap call. Never prints the key.

    openai-compatible and Anthropic both answer `GET {base}/models`, so one path covers both; the
    n8n webhook judge is probed with a tiny prompt through the workflow itself.
    """
    provider = (cfg.get("CR_JUDGE_PROVIDER", "mock") or "mock").lower()
    if provider == "mock":
        return {"ok": True, "provider": "mock", "note": "recorded answers — no key needed"}
    if provider == "jev":
        # GET /models proves nothing about a typed-decision endpoint (it has no models route), so the
        # probe is a real one-question call — the smallest thing a JEV host can answer.
        # The CR_JEV_* trio only: a provider never inherits another provider's credentials (falling
        # back to CR_JUDGE_BASE_URL would have posted typed-decision payloads to api.openai.com).
        return jev_lib.probe(cfg.get("CR_JEV_BASE_URL") or jev_lib.DEFAULT_BASE,
                             cfg.get("CR_JEV_API_KEY"),
                             transport, model=cfg.get("CR_JEV_MODEL") or jev_lib.DEFAULT_MODEL)
    base = (cfg.get("CR_JUDGE_BASE_URL") or "").rstrip("/")
    key = cfg.get("CR_JUDGE_API_KEY") or ""
    if not key:
        return {"ok": False, "provider": provider, "reason": "no_key"}
    if provider == "n8n":
        url = cfg.get("N8N_WEBHOOK_URL") or cfg.get("CR_JUDGE_BASE_URL")
        if not url:
            return {"ok": False, "provider": provider, "reason": "no_webhook_url"}
        token = cfg.get("CR_JUDGE_API_KEY") or cfg.get("CR_DEMO_TOKEN")
        headers = {"Content-Type": "application/json", **({"X-CR-Token": token} if token else {})}
        # a dict, not bytes: the transport serialises the body itself, and passing bytes made
        # `--preflight --probe` raise TypeError instead of printing a verdict (review F8)
        status, body = transport("POST", url, headers,
                                 {"system": "reply ok", "user": "ok", "model": cfg.get("CR_JUDGE_MODEL", "")}, 20)
        return {"ok": status == 200, "provider": provider, "status": status}
    headers = {"Authorization": f"Bearer {key}"} if provider != "anthropic" else \
        {"x-api-key": key, "anthropic-version": "2023-06-01"}
    status, body = transport("GET", f"{base}/models", headers, None, 20)
    models = []
    if isinstance(body, dict):
        data = body.get("data") or body.get("models") or []
        models = [m.get("id") or m.get("name") for m in data if isinstance(m, dict)][:5]
    configured = cfg.get("CR_JUDGE_MODEL")
    return {"ok": status == 200, "provider": provider, "status": status,
            "model_configured": configured, "model_listed": (configured in models) if models else None,
            "models_sample": models}


def build_provider(cfg: Config, transport, mock_answers: dict | None = None):
    provider = (cfg.get("CR_JUDGE_PROVIDER", "mock") or "mock").lower()
    if provider == "mock":
        instance = MockProvider()
        instance.answers = mock_answers or {}
        return instance
    if provider == "openai":
        return HttpProvider(cfg.get("CR_JUDGE_BASE_URL"), cfg.get("CR_JUDGE_API_KEY", ""), transport,
                            cfg.int("CR_JUDGE_TIMEOUT_S", 60))
    if provider == "anthropic":
        return AnthropicProvider(cfg.get("CR_JUDGE_BASE_URL", "https://api.anthropic.com/v1"),
                                 cfg.get("CR_JUDGE_API_KEY", ""), transport, cfg.int("CR_JUDGE_TIMEOUT_S", 60))
    if provider == "jev":
        # the additive decision provider. Its own trio, its own host: this is the one provider whose
        # protocol is nothing like a chat completion, so it never shares a base URL or a key
        return jev_lib.JevProvider(cfg.get("CR_JEV_BASE_URL") or jev_lib.DEFAULT_BASE,
                                   cfg.get("CR_JEV_API_KEY"),
                                   transport, model=cfg.get("CR_JEV_MODEL") or jev_lib.DEFAULT_MODEL)
    if provider == "n8n":
        return WebhookProvider(cfg.get("N8N_WEBHOOK_URL", "") or cfg.get("CR_JUDGE_BASE_URL", ""),
                               cfg.get("CR_JUDGE_API_KEY") or cfg.get("CR_DEMO_TOKEN"), transport)
    raise ValueError(f"unknown judge provider: {provider}")


# --- validation (fail closed) -------------------------------------------------------------------

SYSTEM_RENDER = (
    "You rewrite one lesson so it stops teaching something that is no longer true. You are given the "
    "lesson body and the corroborated quotes. Reply with one JSON object with exactly these keys: "
    "find (a sentence copied verbatim from the lesson body), replace (the corrected sentence, at most "
    "400 characters, introducing no number that is not in the quotes), learner_facing (at most 240 "
    "characters, plain language, no internal vocabulary) and optionally quiz "
    "({item_id, prompt, options[3], answer}) when an existing item tests the changed fact. No prose."
)

INTERNAL_WORDS = ("policy", "receipt", "escalat", "threshold", "reason code", "parity", "rollback gate")


def render_prompt(event: dict, body: str) -> str:
    lines = ["LESSON BODY (verbatim):", body, "", "CORROBORATED QUOTES:"]
    for quote in event.get("quotes", []):
        lines.append(f"- ({quote.get('source_id', '?')}) {quote.get('text', '')}")
    lines.append("")
    lines.append(f"CHANGE SUMMARY: {event.get('summary', '')}")
    lines.append("Reply with JSON only.")
    return "\n".join(lines)


def validate_render(raw: str, body: str, event: dict) -> dict:
    """A render is accepted only if it is anchored in the lesson and adds no unsupported number."""
    try:
        payload = json.loads(raw)
    except Exception as exc:
        return {"ok": False, "error": "payload_invalid", "reason_codes": ["claim_unanchored"],
                "message": f"not json: {exc}"}
    find, replace = str(payload.get("find", "")), str(payload.get("replace", ""))
    learner = str(payload.get("learner_facing", ""))
    problems = []
    if len(find) < 20 or find not in body:
        problems.append("find_not_in_lesson")
    if not replace.strip() or len(replace) > 400:
        problems.append("replace_empty_or_too_long")
    quote_text = " ".join(q.get("text", "") for q in event.get("quotes", []))
    for number in set(re.findall(r"\b\d+(?:\.\d+)*\b", replace)):
        if number not in quote_text:
            problems.append(f"unsupported_number:{number}")
    if len(learner) > 240 or not learner.strip():
        problems.append("learner_facing_length")
    if any(word in learner.lower() for word in INTERNAL_WORDS):
        problems.append("learner_facing_internal_vocabulary")
    quiz = payload.get("quiz")
    if quiz is not None:
        options = quiz.get("options") or []
        if (not quiz.get("item_id") or not quiz.get("prompt") or len(options) < 3
                or not isinstance(quiz.get("answer"), int) or not 0 <= quiz["answer"] < len(options)):
            problems.append("quiz_malformed")
    if problems:
        return {"ok": False, "error": "payload_invalid", "reason_codes": ["claim_unanchored"],
                "problems": problems}
    return {"ok": True, "patch": {"find": find, "replace": replace},
            "learner_facing": learner, "quiz": quiz}


def ask_renderer(event: dict, body: str, provider, model: str) -> dict:
    """The act-phase model call. Always anchored: an unanchored render is an escalation, not an edit."""
    try:
        result = provider.complete(SYSTEM_RENDER, render_prompt(event, body), model)
    except Exception as exc:
        return {"ok": False, "error": "judge_unavailable", "reason_codes": ["claim_unanchored"],
                "message": str(exc)[:200]}
    validated = validate_render(result.get("text", ""), body, event)
    if not validated["ok"]:
        return {**validated, "raw": result.get("text", "")[:400]}
    return {**validated, "tokens": (result.get("prompt_tokens") or 0) + (result.get("completion_tokens") or 0)}


def validate_answers(raw: str) -> dict:
    """Parse and validate the judge's reply against the closed questions. Never raises."""
    try:
        answers = json.loads(raw)
    except Exception as exc:
        return {"ok": False, "error": "payload_invalid", "reason_codes": ["unknown_state"],
                "message": f"not json: {exc}"}
    if not isinstance(answers, dict):
        return {"ok": False, "error": "payload_invalid", "reason_codes": ["unknown_state"],
                "message": "reply was not an object"}
    clean, problems = {}, []
    for question in QUESTIONS:
        qid, qtype = question["id"], question["type"]
        if qid not in answers:
            problems.append(f"{qid}:missing")
            continue
        value = answers[qid]
        if qtype == "Choice":
            if value not in question["options"]:
                problems.append(f"{qid}:not_in_closed_set")
            else:
                clean[qid] = value
        else:
            try:
                number = float(value)
            except (TypeError, ValueError):
                problems.append(f"{qid}:not_a_number")
                continue
            if not 0.0 <= number <= 1.0:
                problems.append(f"{qid}:outside_unit_interval")
            else:
                clean[qid] = round(number, 4)
    if problems:
        return {"ok": False, "error": "payload_invalid", "reason_codes": ["unknown_state"],
                "problems": problems}
    return {"ok": True, "answers": clean}


def ask_judge(event: dict, provider, model: str, ledger: "TokenLedger | None" = None) -> dict:
    """One judge call for one event. Returns answers + usage + the prompt hash, or a fail-closed error."""
    system, user = SYSTEM_PROMPT, prompt_for(event)
    try:
        result = provider.complete(system, user, model)
    except Exception as exc:
        return {"ok": False, "error": "judge_unavailable", "reason_codes": ["unknown_state"],
                "message": str(exc)[:200], "provider": provider.name, "prompt_hash": prompt_hash(event)}
    validated = validate_answers(result.get("text", ""))
    tokens = (result.get("prompt_tokens") or 0) + (result.get("completion_tokens") or 0)
    if ledger is not None and tokens:
        allowed, note = ledger.can_spend(tokens)
        if not allowed:
            return {"ok": False, "error": "over_budget", "reason_codes": ["over_budget"],
                    "message": note, "provider": provider.name, "prompt_hash": prompt_hash(event)}
        ledger.record(tokens, model)
    if not validated["ok"]:
        return {**validated, "provider": provider.name, "model": model, "tokens": tokens,
                "prompt_hash": prompt_hash(event), "raw": result.get("text", "")[:400]}
    return {"ok": True, "provider": provider.name, "model": model,
            "temperature": 0, "prompt_hash": prompt_hash(event), "tokens": tokens,
            "usd": result.get("usd"),
            # JEV answers carry their own confidence; a chat model's do not. The key always exists
            # (None when there is nothing to report), so a reader never has to guess.
            "confidences": result.get("confidences"), **validated}


# --- token ledger ------------------------------------------------------------------------------

class TokenLedger:
    def __init__(self, path: Path, per_change: int, per_day: int):
        self.path, self.per_change, self.per_day = path, per_change, per_day
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def spent_today(self) -> int:
        day = __import__("time").strftime("%Y-%m-%d", __import__("time").gmtime())
        return sum(r["tokens"] for r in self._rows() if r["day"] == day)

    def can_spend(self, tokens: int) -> tuple[bool, str]:
        if tokens > self.per_change:
            return False, f"single change needs {tokens} > {self.per_change}"
        spent = self.spent_today()
        if spent + tokens > self.per_day:
            return False, f"day: {spent}+{tokens} > {self.per_day}"
        return True, f"{spent}+{tokens} of {self.per_day}"

    def record(self, tokens: int, model: str) -> None:
        import time
        with self.path.open("a") as fh:
            fh.write(json.dumps({"day": time.strftime("%Y-%m-%d", time.gmtime()), "tokens": tokens,
                                 "model": model, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                sort_keys=True) + "\n")


def decision_input_from_judgement(event: dict, judgement: dict, snapshot_stats: dict,
                                  authority: str, freeze_active: bool, budgets: dict | None = None) -> dict:
    """The bridge: judge answers + snapshot facts → the policy's DecisionInput (data-model §5)."""
    answers = judgement.get("answers", {})
    return {
        "event_id": event["event_id"], "stream": event.get("kind", "change"),
        "materiality": answers.get("q1_materiality", "ambiguous"),
        "learner_impact": answers.get("q2_learner_impact", 0.0),
        "quote_supported": answers.get("q5_quote_supported", answers.get("q4_source_agreement", 0.0)),
        "source_agreement": answers.get("q4_source_agreement", 0.0),
        "sources_verified": snapshot_stats.get("sources_verified", 0),
        "injection_or_jailbreak": answers.get("q6_injection_or_jailbreak", 1.0),
        "authority": authority, "freeze_active": freeze_active,
        "lesson_touched": event.get("lesson_touched", ""),
        "previous_version_available": event.get("previous_version_available", True),
        "revert_gate_present": event.get("revert_gate_present", True),
        "assessment_touched": event.get("assessment_touched", False),
        "diff_lines": event.get("diff_lines", 0),
        "budgets": budgets or {},
        "sources": event.get("sources", []),
        "q3_breaking_probability": answers.get("q3_breaking_probability"),
        "q7_lesson_touched": answers.get("q7_lesson_touched"),
    }


def selftest() -> int:
    """The judge's own checks: prompt hygiene, validation, fail-closed, ledger."""
    checks: list[tuple[str, bool, str]] = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), str(detail)))

    event = {"event_id": "self-01", "summary": "a setting was renamed", "lesson_touched": "lesson-04",
             "objective": "write a least-privilege permission",
             "quotes": [{"source_id": "n8n-releases", "text": "renamed tool_permissions"}]}
    prompt = prompt_for(event)
    forbidden = ["min_sources", "source_agreement_min", "quote_supported_min", "injection_min",
                 "learner_impact_min", "publishes_per_day", "tokens_per_change", "PUBLISH", "ESCALATE",
                 "REVERT", "DISPATCH", "PA0", "PA1", "PA2", "PA3"]
    leaked = [f for f in forbidden if f in prompt]
    check("the prompt never leaks thresholds, reason codes or the expected action", not leaked,
          f"leaked={leaked}")
    check("the prompt asks every closed question",
          all(q["id"] in prompt for q in QUESTIONS), f"n={len(QUESTIONS)}")

    good = {q["id"]: (q["options"][0] if q["type"] == "Choice" else 0.5) for q in QUESTIONS}
    check("a well-formed answer validates", validate_answers(json.dumps(good))["ok"])
    check("a missing answer fails closed",
          validate_answers(json.dumps({k: v for k, v in good.items() if k != "q1_materiality"}))
          ["reason_codes"] == ["unknown_state"])
    bad = dict(good); bad["q1_materiality"] = "definitely_a_publish"
    check("an out-of-set choice fails closed",
          validate_answers(json.dumps(bad))["reason_codes"] == ["unknown_state"])
    bad2 = dict(good); bad2["q2_learner_impact"] = 7
    check("an out-of-range probability fails closed",
          validate_answers(json.dumps(bad2))["reason_codes"] == ["unknown_state"])
    check("prose instead of JSON fails closed",
          validate_answers("I think you should publish this")["reason_codes"] == ["unknown_state"])

    # the render contract: anchored, number-safe, plain-language
    body = "The tools are declared in `tool_permissions.tools` in the workflow settings."
    render_event = {"summary": "renamed", "quotes": [{"source_id": "s", "text": "renamed to permissions.mode in 1.85"}]}
    good_render = json.dumps({"find": "The tools are declared in `tool_permissions.tools` in the workflow settings.",
                              "replace": "The tools are declared in `permissions.mode.tools` since 1.85.",
                              "learner_facing": "One setting changed name; update the key you copied.",
                              "quiz": {"item_id": "q2", "prompt": "Which key?", "options": ["a", "b", "c"], "answer": 1}})
    check("an anchored render is accepted", validate_render(good_render, body, render_event)["ok"])
    unanchored = json.dumps({"find": "a sentence that is not in the lesson", "replace": "x",
                             "learner_facing": "y"})
    check("an unanchored render is refused as claim_unanchored",
          validate_render(unanchored, body, render_event)["reason_codes"] == ["claim_unanchored"])
    invented = json.dumps({"find": body, "replace": "It changed in version 9.9 exactly.",
                           "learner_facing": "A setting changed name."})
    check("a render that invents a version number is refused",
          not validate_render(invented, body, render_event)["ok"])
    jargon = json.dumps({"find": body, "replace": "The key is renamed.", "learner_facing":
                         "This affects the policy receipt and the escalation threshold."})
    check("learner copy with internal vocabulary is refused",
          not validate_render(jargon, body, render_event)["ok"])

    provider = MockProvider(); provider.answers = good
    result = ask_judge(event, provider, "mock-1")
    check("a mock call returns answers, a prompt hash and a token count",
          result["ok"] and result["prompt_hash"].startswith("sha256:") and result["tokens"] >= 0,
          f"tokens={result.get('tokens')}")

    ledger = TokenLedger(ROOT / "app" / "out" / "selftest-judge-ledger.jsonl",
                         THRESHOLDS["budgets"]["tokens_per_change"], THRESHOLDS["budgets"]["tokens_per_day"])
    ledger.path.unlink(missing_ok=True)
    allowed, _ = ledger.can_spend(1000)
    check("the token ledger allows a small spend and refuses an oversized one",
          allowed and not ledger.can_spend(THRESHOLDS["budgets"]["tokens_per_change"] + 1)[0])

    passed = sum(1 for _, ok, _ in checks if ok)
    width = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    print(f"\njudge selftest: {passed}/{len(checks)} checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
