"""Polite HTTP client shared by every scraper.

- Honest User-Agent identifying the tool.
- Limited retries with backoff, hard timeouts.
- Offline mode (GENESIS_OFFLINE=1) raises OfflineError instead of touching the network.
- Optional SOCKS5 proxy routing (used by the Tor module).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models import Evidence

UA = "GenesisResearchBot/1.0 (local zero-cost business research tool; automated, polite)"


class OfflineError(RuntimeError):
    pass


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class Fetcher:
    def __init__(self, evidence: Evidence, proxy: str | None = None):
        self.evidence = evidence
        self.proxy = proxy
        self.settings = get_settings()
        self._sem = asyncio.Semaphore(6)

    @property
    def offline(self) -> bool:
        return self.settings.genesis_offline

    async def _request(self, url: str, *, headers: dict | None = None) -> httpx.Response:
        if self.offline:
            raise OfflineError(f"offline mode: skipped {url}")
        h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
        if headers:
            h.update(headers)
        timeout = httpx.Timeout(self.settings.request_timeout, connect=10.0)
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with self._sem:
                    async with httpx.AsyncClient(timeout=timeout, proxy=self.proxy, follow_redirects=True) as client:
                        r = await client.get(url, headers=h)
                if r.status_code in (429, 503) and attempt < 2:
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                return r
            except (httpx.HTTPError, OSError) as exc:
                last_exc = exc
                if attempt < 2:
                    await asyncio.sleep(0.8 * (attempt + 1))
        raise last_exc or RuntimeError(f"fetch failed: {url}")

    async def json(self, url: str, *, kind: str = "api", headers: dict | None = None) -> Any:
        r = await self._request(url, headers=headers)
        r.raise_for_status()
        self.evidence.add_source(url, kind=kind)
        return r.json()

    async def text(self, url: str, *, kind: str = "web", headers: dict | None = None) -> str:
        r = await self._request(url, headers=headers)
        r.raise_for_status()
        self.evidence.add_source(url, kind=kind)
        return r.text

    async def try_json(self, url: str, *, kind: str = "api", headers: dict | None = None) -> Optional[Any]:
        try:
            return await self.json(url, kind=kind, headers=headers)
        except Exception:
            return None

    async def try_text(self, url: str, *, kind: str = "web", headers: dict | None = None) -> Optional[str]:
        try:
            return await self.text(url, kind=kind, headers=headers)
        except Exception:
            return None


def as_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")
