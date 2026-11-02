"""Free web search via keyless public endpoints (no API key, no paid tier).

Cascade: DuckDuckGo lite → DuckDuckGo html → public SearXNG (JSON) → Mojeek
→ Google News RSS → Bing News RSS.
Any engine can block datacenter traffic; the cascade keeps recon alive.
News RSS is also queried directly for company subjects (see news_search).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from .client import Fetcher, UA, soup
from ..text import clean

# Engines that failed hard (blocked/off-air) this process are skipped afterwards.
_ENGINE_DEAD: set[str] = set()
_ENGINE_EMPTY: dict[str, int] = {}


async def ddg_search(fetcher: Fetcher, query: str, limit: int = 12) -> list[dict]:
    for name, backend in (
        ("ddg-lite", _lite),
        ("ddg-html", _html),
        ("searx", _searx),
        ("mojeek", _mojeek),
        ("gnews", _gnews_rss),
        ("bnews", _bnews_rss),
    ):
        if name in _ENGINE_DEAD:
            continue
        try:
            results = await backend(fetcher, query, limit)
        except Exception:
            _ENGINE_DEAD.add(name)
            continue
        if results:
            return results
        # A blocked challenge page returns 200 with zero results: allow a few
        # legitimate empty queries before retiring the engine for the session.
        _ENGINE_EMPTY[name] = _ENGINE_EMPTY.get(name, 0) + 1
        if _ENGINE_EMPTY[name] >= 3:
            _ENGINE_DEAD.add(name)
    return []


async def news_search(fetcher: Fetcher, query: str, limit: int = 10) -> list[dict]:
    """Direct news coverage (works even when general web engines block us)."""
    for name, backend in (("gnews", _gnews_rss), ("bnews", _bnews_rss)):
        if name in _ENGINE_DEAD:
            continue
        try:
            results = await backend(fetcher, query, limit)
        except Exception:
            _ENGINE_DEAD.add(name)
            continue
        if results:
            return results
    return []


def _unwrap(href: str) -> str:
    if "uddg=" in href:
        from urllib.parse import urlparse, parse_qs, unquote

        try:
            inner = parse_qs(urlparse(href).query).get("uddg", [href])
            return unquote(inner[0])
        except Exception:
            pass
    return href


async def _lite(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
    html = await fetcher.text(url, kind="search")
    s = soup(html)
    out: list[dict] = []
    for a in s.select("a.result-link"):
        href = _unwrap(a.get("href", ""))
        title = clean(a.get_text())
        snippet_el = a.find_parent("tr")
        snippet = ""
        if snippet_el:
            nxt = snippet_el.find_next_sibling("tr")
            if nxt:
                sn = nxt.select_one(".result-snippet")
                snippet = clean(sn.get_text()) if sn else ""
        if title and href.startswith("http"):
            out.append({"title": title, "url": href, "snippet": snippet})
        if len(out) >= limit:
            break
    return out


async def _html(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    html = await fetcher.text(url, kind="search")
    s = soup(html)
    out: list[dict] = []
    for a in s.select("a.result__a"):
        href = _unwrap(a.get("href", ""))
        title = clean(a.get_text())
        body = a.find_parent("div", class_="result")
        snippet = clean(body.select_one(".result__snippet").get_text()) if body and body.select_one(".result__snippet") else ""
        if title and href.startswith("http"):
            out.append({"title": title, "url": href, "snippet": snippet})
        if len(out) >= limit:
            break
    return out


# Public SearXNG instances that expose format=json. Best-effort; may be off air.
SEARX_INSTANCES = ["https://searx.be", "https://search.bus-hit.me", "https://priv.au"]


async def _searx(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    import httpx

    for base in SEARX_INSTANCES:
        try:
            async with httpx.AsyncClient(timeout=fetcher.settings.request_timeout, headers={"User-Agent": UA}) as client:
                r = await client.get(f"{base}/search", params={"q": query, "format": "json"})
            if r.status_code != 200:
                continue
            fetcher.evidence.add_source(f"{base}/search?q={quote_plus(query)}", kind="search")
            data = r.json()
            out = []
            for res in data.get("results", [])[:limit]:
                title, url = clean(res.get("title", "")), res.get("url", "")
                if title and url.startswith("http"):
                    out.append({"title": title, "url": url, "snippet": clean(res.get("content", ""))})
            if out:
                return out
        except Exception:
            continue
    return []


async def _mojeek(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    html = await fetcher.text(f"https://www.mojeek.com/search?q={quote_plus(query)}", kind="search")
    s = soup(html)
    out: list[dict] = []
    for a in s.select("a.title, li.results-standard a.ob, ul.results-standard h2 a"):
        href = a.get("href", "")
        title = clean(a.get_text())
        snippet = ""
        parent = a.find_parent("li")
        if parent:
            p = parent.select_one("p.s, p")
            snippet = clean(p.get_text()) if p else ""
        if title and href.startswith("http"):
            out.append({"title": title, "url": href, "snippet": snippet})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# News RSS (Google News + Bing News): keyless, bot-tolerant, reachable where
# HTML search engines block automated traffic.
# ---------------------------------------------------------------------------

async def _gnews_rss(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    xml_text = await fetcher.text(url, kind="news")
    return _parse_rss(xml_text, limit)


async def _bnews_rss(fetcher: Fetcher, query: str, limit: int) -> list[dict]:
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=RSS"
    xml_text = await fetcher.text(url, kind="news")
    return _parse_rss(xml_text, limit)


def _parse_rss(xml_text: str, limit: int) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out: list[dict] = []
    for item in root.iter("item"):
        title = clean(item.findtext("title") or "")
        link = (item.findtext("link") or "").strip()
        desc = clean(item.findtext("description") or "")
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not link.startswith("http"):
            continue
        # Google News appends " - Publisher" to titles; keep the headline part.
        if " - " in title:
            head, _, tail = title.rpartition(" - ")
            if head and len(tail.split()) <= 4:
                title = head
        out.append({"title": title[:200], "url": link, "snippet": desc[:260], "date": pub})
        if len(out) >= limit:
            break
    return out
