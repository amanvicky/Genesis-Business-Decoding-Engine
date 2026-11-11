"""Optional bridge to a free local LLM via Ollama (zero-cost, no API keys).

Everything here fails soft: if Ollama is not installed or not running,
`enrich()` returns None and the pipeline continues with deterministic analysis.

Two silent breakages this layer used to have, now handled:
  - the availability probe cached one answer for the whole backend lifetime,
    so starting Ollama *after* Genesis meant "never available" until a
    restart — the probe now refreshes on a short TTL
  - the configured model (default llama3.2) may not be what the user has
    pulled — any pulled model now works: the configured one when present,
    otherwise whatever Ollama has
"""
from __future__ import annotations

import time

import httpx

from .config import get_settings

_PROBE_TTL = 60.0
_MODELS: list[str] = []
_MODELS_TS: float = 0.0
_TIMEOUT = httpx.Timeout(120.0, connect=5.0)


def pick_model(models: list[str], configured: str) -> str | None:
    """The configured model if the user has it pulled, else what they do have."""
    if not models:
        return None
    if configured in models:
        return configured
    # exact-name misses may still match with an implicit :latest tag
    for m in models:
        if m.split(":")[0] == configured.split(":")[0]:
            return m
    return models[0]


async def _known_models() -> list[str]:
    global _MODELS, _MODELS_TS
    now = time.monotonic()
    if _MODELS and now - _MODELS_TS < _PROBE_TTL:
        return _MODELS
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{s.ollama_url}/api/tags")
            r.raise_for_status()
            names = [m.get("name") or m.get("model") or "" for m in (r.json().get("models") or [])]
            _MODELS = [n for n in names if n]
            _MODELS_TS = now
    except Exception:
        # unreachable right now — remember the failure only for one TTL window,
        # so starting Ollama later needs no Genesis restart
        _MODELS = []
        _MODELS_TS = now
    return _MODELS


async def available() -> bool:
    if get_settings().genesis_offline:
        return False
    return bool(await _known_models())


async def resolve_model() -> str | None:
    if get_settings().genesis_offline:
        return None
    return pick_model(await _known_models(), get_settings().genesis_llm_model)


async def enrich(instruction: str, evidence: str, max_chars: int = 1200) -> str | None:
    """Return a short sharpened analysis from the local LLM, or None.

    The evidence window is deliberately small: on CPU-only machines prompt
    evaluation dominates (≈25s per 1k tokens), so a 6k-char dump made every
    section take minutes and the decode crawl. A tight window + a mechanical
    contract (bullets only, no questions, never refuse) keeps small local
    models fast AND on-format.
    """
    model = await resolve_model()
    if not model:
        return None
    system = (
        "You are Genesis, a brutally honest startup intelligence analyst. "
        "You write ONLY short lines that start with '- ' (max 25 words each). "
        "No introduction, no questions, no extra words, never refuse. "
        "Cite concrete mechanisms, numbers, or failure modes from the evidence. "
        "If the evidence is thin, one line must say exactly what is missing."
    )
    prompt = f"{instruction}\n\nEVIDENCE (scraped, may be partial):\n{evidence[:max_chars]}"
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 220, "stop": ["\n\n"]},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(f"{get_settings().ollama_url}/api/generate", json=payload)
            r.raise_for_status()
            return (r.json().get("response") or "").strip() or None
    except Exception:
        return None
