"""Wider platform lanes for recon: LinkedIn posts, long-form essays
(Medium/Substack), and global magazine/press coverage via the keyless GDELT
database.

Everything here is snippet/title-level evidence with its source link kept —
walled gardens are never scraped directly, only what the open web indexes of
them (which is exactly where professionals and magazines speak publicly).
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from . import search
from ..text import clean, domain_of

_GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
# GDELT enforces one request per 5 seconds per IP and answers 429 otherwise —
# enforce the gap ourselves, faster retries just burn the window
_GDELT_MIN_GAP = 5.5
_GDELT_RETRY_WAIT = 6.0
_last_gdelt_call = 0.0


def _row(title: str, url: str, snippet: str = "", platform: str = "web") -> dict:
    return {"title": clean(title)[:200], "url": url, "snippet": clean(snippet)[:400], "platform": platform}


async def linkedin_posts(f, subject: str, limit: int = 10) -> list[dict]:
    """Public LinkedIn posts and pulse articles as the open web indexes them.
    LinkedIn itself is authwalled — the honest keyless layer is exactly the
    posts professionals published publicly, which is where work complaints
    and wins surface."""
    rows: list[dict] = []
    queries = (f'site:linkedin.com/posts "{subject}"', f'site:linkedin.com/pulse {subject}')
    for q in queries:
        if len(rows) >= limit:
            break
        try:
            results = await search.ddg_search(f, q, 8)
        except Exception:
            results = []
        for r in results:
            if "linkedin.com" in domain_of(r["url"]):
                rows.append(_row(r.get("title", ""), r["url"], r.get("snippet", ""), "linkedin"))
    return rows[:limit]


async def essays(f, subject: str, limit: int = 8) -> list[dict]:
    """Long-form analysis: Medium posts and Substack essays that mention the
    subject — usually deeper than forum chatter."""
    rows: list[dict] = []
    queries = (f'site:medium.com {subject}', f'site:substack.com {subject}')
    for q in queries:
        try:
            results = await search.ddg_search(f, q, 8)
        except Exception:
            results = []
        for r in results:
            d = domain_of(r["url"])
            if "medium.com" in d or "substack.com" in d:
                rows.append(_row(r.get("title", ""), r["url"], r.get("snippet", ""), "essays"))
    return rows[:limit]


async def press(f, subject: str, limit: int = 15) -> list[dict]:
    """Global magazine and press coverage — the keyless GDELT 2.0 DOC API
    indexes hundreds of thousands of outlets; eng-language slice stays
    minable. Titles carry the signal; every row keeps its outlet and link."""
    global _last_gdelt_call
    start = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y%m%d%H%M%S")
    query = quote(f'"{subject}"')
    url = (f"{_GDELT}?query={query}&mode=artlist&format=json&maxrecords=25"
           f"&sourcelang=eng&startdatetime={start}")
    data = None
    for attempt in range(2):
        gap = time.monotonic() - _last_gdelt_call
        if gap < _GDELT_MIN_GAP:
            await asyncio.sleep(_GDELT_MIN_GAP - gap)
        _last_gdelt_call = time.monotonic()
        data = await f.try_json(url, kind="press")
        if isinstance(data, dict) and data.get("articles"):
            break
        if attempt == 0:
            # a 429 window just opened — wait it out once, then give up quietly
            await asyncio.sleep(_GDELT_RETRY_WAIT)
    rows: list[dict] = []
    seen: set[str] = set()
    for a in ((data or {}).get("articles") if isinstance(data, dict) else None) or []:
        title = clean(a.get("title") or "")
        url = (a.get("url") or "").strip()
        if not title or not url or url in seen:
            continue
        seen.add(url)
        rows.append(_row(title, url, f"{a.get('domain', '')} · seen {a.get('seendate', '')}", "press"))
    return rows[:limit]
