"""Reddit public JSON endpoints: unvarnished consumer complaints and demand signals.

Reddit aggressively rate-limits unauthenticated clients; every failure is soft.
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from .client import Fetcher, UA
from ..text import clean


async def reddit_search(fetcher: Fetcher, query: str, limit: int = 30) -> list[dict]:
    if fetcher.offline:
        return []
    url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&limit={limit}&sort=relevance&include_over_18=off"
    try:
        async with httpx.AsyncClient(
            timeout=fetcher.settings.request_timeout, headers={"User-Agent": UA}, follow_redirects=True
        ) as client:
            r = await client.get(url)
        if r.status_code != 200:
            return []
        fetcher.evidence.add_source(f"https://www.reddit.com/search/?q={quote_plus(query)}", kind="reddit")
        data = r.json()
    except Exception:
        return []
    out = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        title = clean(d.get("title"))
        selftext = clean(d.get("selftext"))[:500]
        if not title:
            continue
        out.append(
            {
                "title": title,
                "selftext": selftext,
                "subreddit": d.get("subreddit", ""),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "url": "https://www.reddit.com" + (d.get("permalink") or ""),
                "date": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).strftime("%Y-%m-%d"),
            }
        )
    return out
