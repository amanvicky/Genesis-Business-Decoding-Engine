"""Polite HTTP client shared by every scraper.

- Honest User-Agent identifying the tool.
- Limited retries with backoff, hard timeouts.
- Offline mode (GENESIS_OFFLINE=1) raises OfflineError instead of touching the network.
- Optional SOCKS5 proxy routing (used by the Tor module).
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models import Evidence

UA = "GenesisResearchBot/1.0 (local zero-cost business research tool; automated, polite)"

# Hard cap on any single response body — a hostile or misbehaving endpoint must
# not be able to stream gigabytes into the user's RAM.
_MAX_BODY = 5_000_000
_BLOCKED_HOSTS = {"localhost"}


def safe_public_http_url(url: str) -> bool:
    """SSRF gate for URLs that arrived from UNTRUSTED data (search results,
    API responses). Requires http(s), no embedded credentials, and a host that
    is neither localhost-style nor a private/link-local/reserved IP literal.
    Domain names are accepted at face value — DNS-rebirth to private space is
    a documented limitation, not silently ignored."""
    try:
        u = urlparse(url)
        if u.scheme not in ("http", "https") or not u.hostname:
            return False
        if u.username or u.password:
            return False
        host = u.hostname.lower()
        if host in _BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
            return False
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return True  # a domain name, not an IP literal
        return not (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified)
    except Exception:
        return False


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
                        async with client.stream("GET", url, headers=h) as resp:
                            if resp.status_code in (429, 503) and attempt < 2:
                                await asyncio.sleep(1.2 * (attempt + 1))
                                continue
                            chunks: list[bytes] = []
                            total = 0
                            async for chunk in resp.aiter_bytes(65536):
                                total += len(chunk)
                                if total > _MAX_BODY:
                                    raise RuntimeError(f"response body exceeds {_MAX_BODY} bytes: {url}")
                                chunks.append(chunk)
                            # rebuild a concrete Response so .json()/.text/.raise_for_status work.
                            # aiter_bytes yields DECODED bytes — drop content-encoding/length
                            # headers or httpx re-decompresses and fails (DecodingError)
                            hdrs = {k: v for k, v in resp.headers.multi_items()
                                    if k.lower() not in ("content-encoding", "content-length")}
                            r = httpx.Response(resp.status_code, headers=hdrs, content=b"".join(chunks),
                                               request=resp.request)
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
