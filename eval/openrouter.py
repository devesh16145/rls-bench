"""OpenRouter chat completions with retries and a disk cache, so no sample is ever paid for twice."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from harness.db import ROOT

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"
CACHE_DIR = ROOT / "data" / "cache"
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "OPENROUTER_API_KEY":
                key = value.strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set (add it to .env)")
    return key


@dataclass
class Completion:
    text: str
    usage: dict[str, Any]
    cost_usd: float
    provider: str | None
    finish_reason: str | None
    cached: bool


def model_info(model: str) -> dict[str, Any]:
    r = httpx.get(MODELS_URL, timeout=30)
    r.raise_for_status()
    for m in r.json()["data"]:
        if m["id"] == model:
            return m
    raise KeyError(f"model {model!r} not listed on OpenRouter")


def _cache_path(key: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
    return CACHE_DIR / key["model"].replace("/", "__") / f"{digest}.json"


def complete(
    model: str,
    messages: list[dict[str, str]],
    *,
    prompt_hash: str,
    temperature: float,
    index: int,
    max_tokens: int,
    send_temperature: bool,
    reasoning: dict[str, Any] | None = None,
    client: httpx.Client | None = None,
) -> Completion:
    """One sample. Cached by (model, prompt hash, temperature, index, max_tokens)."""
    key = {
        "model": model,
        "prompt_hash": prompt_hash,
        "temperature": temperature,
        "index": index,
        "max_tokens": max_tokens,
    }
    if reasoning is not None:
        # only added when set, so cache keys of earlier default-reasoning samples stay valid
        key["reasoning"] = reasoning
    path = _cache_path(key)
    if path.exists():
        data = json.loads(path.read_text())
        return Completion(**{**data, "cached": True})

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "seed": index,
        "usage": {"include": True},
    }
    if send_temperature:
        body["temperature"] = temperature
    if reasoning is not None:
        body["reasoning"] = reasoning
    headers = {
        "Authorization": f"Bearer {load_api_key()}",
        "X-Title": "RLS-Bench",
    }
    own_client = client is None
    client = client or httpx.Client(timeout=600)
    try:
        for attempt in range(6):
            try:
                r = client.post(API_URL, json=body, headers=headers)
            except httpx.TransportError:
                if attempt == 5:
                    raise
                time.sleep(2**attempt)
                continue
            if r.status_code in RETRY_STATUS and attempt < 5:
                time.sleep(2**attempt)
                continue
            if r.status_code >= 400:
                # keep OpenRouter's explanation (e.g. "key limit exceeded"); it never contains the key
                raise httpx.HTTPStatusError(f"{r.status_code} from OpenRouter: {r.text[:300]}", request=r.request, response=r)
            payload = r.json()
            if "error" in payload:
                raise RuntimeError(f"OpenRouter error: {payload['error']}")
            break
    finally:
        if own_client:
            client.close()

    choice = payload["choices"][0]
    usage = payload.get("usage") or {}
    result = Completion(
        text=choice["message"].get("content") or "",
        usage=usage,
        cost_usd=float(usage.get("cost") or 0.0),
        provider=payload.get("provider"),
        finish_reason=choice.get("finish_reason"),
        cached=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in result.__dict__.items() if k != "cached"}
    path.write_text(json.dumps(data, indent=1))
    return result
