"""Hacker News (Algolia public API): developer-community sentiment, free."""
from __future__ import annotations

from urllib.parse import quote_plus

from .client import Fetcher
from ..text import clean


async def hn_stories(fetcher: Fetcher, query: str, limit: int = 20) -> list[dict]:
    data = await fetcher.try_json(
        f"https://hn.algolia.com/api/v1/search?query={quote_plus(query)}&tags=story&hitsPerPage={limit}",
        kind="hn",
    )
    out = []
    for hit in (data or {}).get("hits", []):
        out.append(
            {
                "title": clean(hit.get("title") or hit.get("story_title") or ""),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "points": hit.get("points") or 0,
                "comments": hit.get("num_comments") or 0,
                "date": (hit.get("created_at") or "")[:10],
            }
        )
    return [s for s in out if s["title"]]


async def hn_comments(fetcher: Fetcher, query: str, limit: int = 25) -> list[dict]:
    data = await fetcher.try_json(
        f"https://hn.algolia.com/api/v1/search?query={quote_plus(query)}&tags=comment&hitsPerPage={limit}",
        kind="hn",
    )
    out = []
    for hit in (data or {}).get("hits", []):
        text = clean(hit.get("comment_text") or "")
        if len(text) < 40:
            continue
        out.append(
            {
                "text": text[:600],
                "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "date": (hit.get("created_at") or "")[:10],
            }
        )
    return out
