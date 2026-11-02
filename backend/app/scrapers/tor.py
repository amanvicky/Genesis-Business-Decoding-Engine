"""Deep/Dark Web OSINT module (Tab 11) — lawful-use, passive, read-only.

Design constraints (intentional, not optional):
- ONLY passive reading of publicly indexed OSINT content: Ahmia (legal onion
  search index), public paste-site search results, and the free HIBP breach
  corpus. No marketplaces, no credentials, no purchases, no interaction.
- Tor (socks5://127.0.0.1:9050) is used when available for user privacy;
  without Tor the module degrades to Ahmia's clearnet interface + HIBP.
- Queries containing clearly illegal intent are refused outright.
"""
from __future__ import annotations

import time

import httpx

from .client import Fetcher, soup
from ..config import get_settings
from ..text import clean

# Probe result cache: health checks shouldn't pay a 20s connect timeout
# against a dead proxy on every request.
_PROBE_TTL = 60.0
_last_probe: tuple[float, dict] | None = None

# Refuse anything that looks like an attempt to source illegal goods/services.
REFUSE_TERMS = [
    "buy drugs", "buy weapons", "gun for sale", "hitman", "hit man",
    "counterfeit passport", "fake passport", "buy cc", "card dumps", "cvv shop",
    "child", "cp video", "hitlist", "buy rcs", "shell rdp with admin",
]

AHMIA = "https://ahmia.fi/search/?q="
HIBP_BREACHES = "https://haveibeenpwned.com/api/v3/breaches"


async def tor_status(proxy: str) -> dict:
    """Check whether the local Tor SOCKS5 proxy is alive and exiting properly."""
    global _last_probe
    s = get_settings()
    if s.genesis_offline:
        return {"available": False, "reason": "offline mode"}
    now = time.monotonic()
    if _last_probe and now - _last_probe[0] < _PROBE_TTL:
        return _last_probe[1]
    result = {"available": False, "reason": "unknown"}
    try:
        async with httpx.AsyncClient(timeout=20, proxy=proxy, follow_redirects=True) as client:
            r = await client.get("https://check.torproject.org/api/ip")
            data = r.json()
        result = {"available": bool(data.get("IsTor")), "exit_ip": data.get("IP"), "proxy": proxy}
    except Exception as exc:
        result = {"available": False, "reason": f"Tor not reachable on {proxy} ({type(exc).__name__})"}
    _last_probe = (now, result)
    return result


async def probe(fetcher: Fetcher) -> dict:
    return await tor_status(get_settings().tor_proxy)


def check_query_legal(query: str) -> bool:
    low = query.lower()
    return not any(t in low for t in REFUSE_TERMS)


async def ahmia_search(fetcher: Fetcher, query: str, tor: dict, limit: int = 10) -> list[dict]:
    """Search the Ahmia index. Routed through Tor when Tor is available."""
    proxy = get_settings().tor_proxy if tor.get("available") else None
    try:
        if proxy:
            async with httpx.AsyncClient(timeout=35, proxy=proxy, follow_redirects=True) as client:
                r = await client.get(AHMIA + query.replace(" ", "+"), headers={"User-Agent": "GenesisResearchBot/1.0"})
        else:
            html = await fetcher.text(AHMIA + query.replace(" ", "+"), kind="tor-ahmia")
            r = None
        if r is not None:
            html = r.text
        fetcher.evidence.add_source(AHMIA + query.replace(" ", "+"), kind="ahmia")
    except Exception:
        return []
    s = soup(html)
    out: list[dict] = []
    for li in s.select("li.result"):
        a = li.select_one("h4 a, a")
        if not a:
            continue
        href = a.get("href", "")
        title = clean(a.get_text())
        desc_el = li.select_one("p")
        if title and href:
            out.append({"title": title, "url": href, "snippet": clean(desc_el.get_text()) if desc_el else ""})
        if len(out) >= limit:
            break
    return out


async def breach_intel(fetcher: Fetcher, subject: str) -> list[dict]:
    """Free HIBP corpus: breaches whose names intersect the subject/sector."""
    data = await fetcher.try_json(HIBP_BREACHES, kind="hibp", headers={"User-Agent": "GenesisResearchBot"})
    if not data:
        return []
    keys = [w for w in subject.lower().split() if len(w) > 3]
    out = []
    for b in data:
        name = (b.get("Name") or "").lower()
        title = (b.get("Title") or "").lower()
        if any(k in name or k in title for k in keys):
            out.append(
                {
                    "name": b.get("Title"),
                    "date": b.get("BreachDate"),
                    "accounts": b.get("PwnCount"),
                    "data_classes": (b.get("DataClasses") or [])[:6],
                    "description": clean(b.get("Description") or "")[:300],
                }
            )
    return sorted(out, key=lambda x: x.get("date") or "", reverse=True)[:6]
