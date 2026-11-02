"""Review-platform intelligence via search-snippet aggregation.

Genesis never scrapes behind review sites' paywalls or violates their ToS —
it aggregates what public search engines already expose (snippets from
Trustpilot, G2, Capterra, Product Hunt, and complaint-oriented queries).
"""
from __future__ import annotations

from .client import Fetcher
from .search import ddg_search

REVIEW_QUERIES = [
    ('site:trustpilot.com "{q}"', "trustpilot"),
    ('site:g2.com "{q}" reviews', "g2"),
    ('site:capterra.com "{q}" reviews', "capterra"),
    ('"{q}" review worst complaint "switched from"', "complaints"),
    ('"{q}" "canceled" OR "cancelled" OR "churned" why', "churn"),
]


async def review_intel(fetcher: Fetcher, subject: str, per_query: int = 5) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for tmpl, kind in REVIEW_QUERIES:
        results = await ddg_search(fetcher, tmpl.format(q=subject), per_query)
        for r in results:
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            r["kind"] = kind
            out.append(r)
    return out
