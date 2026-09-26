#!/usr/bin/env python3
"""JEV (TypeSafe "System One") as a *decision* provider — additive, never a text model in a wiggle.

The product idea was written with JEV in mind (`Idea.md`: "Decide: Jev Noul ... and Choice ... Score
materiality"), and the build shipped an OpenAI-compatible chat model instead, with the docs telling
operators to point `CR_JUDGE_BASE_URL` at "a 'jev'-style key" (`judge.py`, `SETUP.md` §2,
`WIRING.md` §5, `HANDOFF.md`). That advice cannot work: JEV is not an OpenAI-compatible chat
endpoint and it generates no text. It answers *typed* questions in one call and returns typed
answers with their own probabilities. This module is the additive path the review asked for.

What maps onto what
-------------------
The seven closed questions in `skin/questions.json` are already a JEV schema, one for one:

    Choice (q1 materiality, q7 lesson touched)  →  JEV `choice`  (+ `criteria`: option → meaning)
    Noul   (q2–q6 probabilities)                →  JEV `noul`   (+ `criteria`: {true, false})
    (nothing in this repo asks a `score` question — that is the one JEV type left unused)

`JevProvider.complete()` normalises JEV's reply back into the exact `{"text": "<json>"}` shape every
other provider returns, so `validate_answers`, the policy oracle, the gold set and every receipt are
untouched by this integration. The answers' own confidences ride along separately (`confidences`),
which is what the Teacher/Author canvas uses to route the decisions worth a human's time.

Text stays with the text model
------------------------------
OBSERVE extraction, the renderer and the micro-lessons are prose and stay on the chat model
(`CR_JUDGE_PROVIDER=openai|anthropic`). The loop only needs a *decision* from JEV; asking it to
render would contradict what it is. So this provider is selected for the decision half only —
`build_provider()` in `judge.py` returns it when `CR_JUDGE_PROVIDER=jev`.

Keys and hosts
--------------
    CR_JEV_BASE_URL   the System One host. Default https://api.typesafe.ai (TypeSafe direct).
                      Any JEV-compatible host works: an OpenRouter/requesty/rout.my proxy, or a
                      *keyless local server* for offline verification (githubnext/localjev,
                      amithgc/local-jev) — point the base URL at it and leave the key empty.
    CR_JEV_API_KEY    the TypeSafe key (`TYPESAFE_API_KEY`). Never printed, never stored.
    CR_JEV_MODEL      `jev-latest` by default.

Wire contract (verified against the published API, not guessed):
    POST {base}/v1/systemone
    Authorization: Bearer <key>
    {"model": "jev-latest", "state": <the event text>, "questions": {name: {...}}}
  → {"model": "jev-1.13.0", "answers": {name: {"type": ..., ...}}, "usage": {...}}
    noul   → {"type": "noul", "noul": 0.0..1.0}          (the probability *is* the confidence)
    choice → {"type": "choice", "choice": "<option>", "probabilities": {...}, "confidence": 0..1}

Run: python3 app/tests/test_live_modules.py   (drives this module with a fake JEV transport, no key)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = json.loads((ROOT / "specs" / "courserefresh" / "skin" / "questions.json").read_text())["questions"]

DEFAULT_BASE = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"


def question_schema() -> dict:
    """The seven questions as JEV expects them: a name → definition map, one entry per question.

    `instructions` carries the proposition; `criteria` carries the closed set. For a Choice the
    criteria map option → short description (JEV caps a choice at 255 options; we pass 8 labels); for
    a Noul the criteria give the meaning of the two ends of the probability.
    """
    schema = {}
    for q in QUESTIONS:
        entry: dict = {"instructions": q["proposition"]}
        if q["type"] == "Choice":
            entry["type"] = "choice"
            entry["criteria"] = {option: option.replace("_", " ") for option in q["options"]}
        else:
            entry["type"] = "noul"
            entry["criteria"] = {"true": "the proposition is true for this change",
                                 "false": "the proposition is false for this change"}
        schema[q["id"]] = entry
    return schema


def build_request(state: str, model: str = DEFAULT_MODEL) -> dict:
    """The request body. `state` is the event's own text — never thresholds, never the expected act."""
    return {"model": model, "state": state, "questions": question_schema()}


def normalise(payload: dict) -> dict:
    """JEV's typed answers → the repo's flat answer dict plus per-question confidences.

    Strictly additive: an answer JEV did not give is *missing* (`validate_answers` then fails the
    judgement closed with `unknown_state`, exactly as it does for a chat model that skipped a
    question). Confidences are returned separately so nothing about the existing answer contract
    changes.
    """
    answers, confidences, types = {}, {}, {}
    for qid, answer in (payload.get("answers") or {}).items():
        if not isinstance(answer, dict):
            continue
        kind = answer.get("type")
        types[qid] = kind
        if kind == "choice":
            answers[qid] = answer.get("choice")
            confidences[qid] = answer.get("confidence")
        elif kind == "noul":
            value = answer.get("noul")
            answers[qid] = value
            # for a noul the probability is the answer *and* the confidence: how sure the model is
            # of the proposition. (For routing we care about distance from a policy threshold; the
            # canvas computes that with a flip analysis rather than a made-up cut-off.)
            confidences[qid] = value
        elif kind == "score":
            # no question in this repo asks for a score, but a JEV host may answer one anyway
            answers[qid] = answer.get("score")
            confidences[qid] = answer.get("confidence")
    return {"answers": answers, "confidences": confidences, "types": types,
            "model": payload.get("model"), "usage": payload.get("usage") or {}}


class JevProvider:
    """One JEV call per event. Same duck-type as MockProvider/HttpProvider: `complete(system, user, model)`.

    `system` is accepted and ignored on purpose: JEV takes one state string, and the repo's system
    prompt is instructions for a chat model. The state is the event prompt, so the judge still sees
    only the event — the same rule the other providers follow.
    """

    name = "jev"

    def __init__(self, base_url: str, api_key: str | None, transport, timeout: int = 60,
                 model: str = DEFAULT_MODEL):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self.api_key, self.transport, self.timeout, self.default_model = api_key, transport, timeout, model
        self.last_confidences: dict = {}

    def endpoint(self) -> str:
        # a host may be given with or without the version prefix; both are accepted
        return f"{self.base_url}/v1/systemone" if not self.base_url.endswith("/v1") else f"{self.base_url}/systemone"

    def complete(self, system: str, user: str, model: str) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = build_request(user, model or self.default_model)
        status, payload = self.transport("POST", self.endpoint(), headers, body, self.timeout)
        if status != 200:
            raise RuntimeError(f"judge_jev_{status}: {json.dumps(payload)[:200]}")
        normalised = normalise(payload)
        self.last_confidences = normalised["confidences"]
        usage = normalised["usage"] or {}
        return {"text": json.dumps(normalised["answers"]),
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
                "usd": usage.get("cost"),
                # additive passthrough: judge.ask_judge keeps these on the judgement
                "confidences": normalised["confidences"] or None,
                "jev_model": normalised["model"]}


def probe(base_url: str, api_key: str | None, transport, model: str = DEFAULT_MODEL,
          timeout: int = 20) -> dict:
    """One cheap, decisive JEV call: does this host answer the protocol at all?

    `GET /models` (the OpenAI/Anthropic probe) means nothing here, so the probe is a real one-question
    call — the smallest thing that can be answered. It never prints the key, and it reports what came
    back so a wrong base URL is distinguishable from a wrong key (401/403) or a bad request (422).
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {"model": model or DEFAULT_MODEL, "state": "Probe: reply with any probability.",
            "questions": {"probe_ok": {"type": "noul",
                                       "instructions": "Is this a live JEV endpoint?",
                                       "criteria": {"true": "yes", "false": "no"}}}}
    endpoint = f"{base_url.rstrip('/')}/v1/systemone" if not base_url.rstrip("/").endswith("/v1") \
        else f"{base_url.rstrip('/')}/systemone"
    try:
        status, payload = transport("POST", endpoint, headers, body, timeout)
    except Exception as exc:  # noqa: BLE001 - a probe reports, it never raises
        return {"ok": False, "provider": "jev", "status": None, "message": str(exc)[:160]}
    answered = bool((payload.get("answers") or {})) if isinstance(payload, dict) else False
    verdict = {"ok": status == 200 and answered, "provider": "jev", "status": status,
               "model": (payload or {}).get("model") if isinstance(payload, dict) else None,
               "answered": answered}
    if not verdict["ok"]:
        hint = {401: "key rejected", 403: "key not authorised for this host",
                422: "request shape rejected (check the base URL paths)",
                429: "rate limited", 500: "host error"}.get(status, "unexpected reply")
        verdict["message"] = hint
    return verdict
