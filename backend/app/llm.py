"""Optional bridge to a free local LLM via Ollama (zero-cost, no API keys).

Everything here fails soft: if Ollama is not installed or not running,
`enrich()` returns None and the pipeline continues with deterministic analysis.
"""
from __future__ import annotations

import httpx

from .config import get_settings

_AVAILABLE: bool | None = None
_TIMEOUT = httpx.Timeout(120.0, connect=5.0)


async def available() -> bool:
    global _AVAILABLE
    s = get_settings()
    if s.genesis_offline:
        return False
    if _AVAILABLE is not None:
        return _AVAILABLE
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{s.ollama_url}/api/tags")
            _AVAILABLE = r.status_code == 200
    except Exception:
        _AVAILABLE = False
    return _AVAILABLE


async def enrich(instruction: str, evidence: str, max_chars: int = 6000) -> str | None:
    """Return a short sharpened analysis from the local LLM, or None."""
    if not await available():
        return None
    s = get_settings()
    system = (
        "You are Genesis, a brutally honest startup intelligence analyst. "
        "No fluff, no encouragement, no generic advice. Output 3-6 terse bullet "
        "points (max 25 words each) that a founder can act on today. "
        "Cite concrete mechanisms, numbers, or failure modes. "
        "If evidence is thin, say exactly what is missing and why it matters."
    )
    prompt = f"{instruction}\n\nEVIDENCE (scraped, may be partial):\n{evidence[:max_chars]}"
    payload = {
        "model": s.genesis_llm_model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 400},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(f"{s.ollama_url}/api/generate", json=payload)
            r.raise_for_status()
            return (r.json().get("response") or "").strip() or None
    except Exception:
        return None
