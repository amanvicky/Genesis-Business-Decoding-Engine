"""Wayback Machine: historical pricing-page snapshots via the free CDX API.

This is how Genesis reverse-engineers pricing evolution without paid archives:
find archived /pricing pages, pull a spread of snapshots, extract money tokens.
"""
from __future__ import annotations

import asyncio

from .client import Fetcher
from ..text import clean, money_values

CDX = "https://web.archive.org/cdx/search/cdx"


async def pricing_history(fetcher: Fetcher, domain: str, max_snapshots: int = 6) -> list[dict]:
    if not domain or fetcher.offline:
        return []
    cdx = await fetcher.try_json(
        f"{CDX}?url={domain}/pricing&output=json&fl=timestamp,statuscode&filter=statuscode:200"
        f"&collapse=timestamp:6&limit=40",
        kind="archive",
    )
    if not cdx or len(cdx) < 2:
        cdx = await fetcher.try_json(
            f"{CDX}?url={domain}&output=json&fl=timestamp,statuscode&filter=statuscode:200"
            f"&collapse=timestamp:6&limit=40",
            kind="archive",
        )
    rows = cdx[1:] if cdx else []
    if not rows:
        return []
    # spread snapshots evenly across the archive's history
    step = max(1, len(rows) // max_snapshots)
    chosen = [r[0] for r in rows[::step]][:max_snapshots]
    out: list[dict] = []
    for ts in chosen:
        url = f"https://web.archive.org/web/{ts}/https://{domain}/pricing"
        html = await fetcher.try_text(url, kind="archive")
        if not html or "<title" not in html:
            url = f"https://web.archive.org/web/{ts}/https://{domain}/"
            html = await fetcher.try_text(url, kind="archive")
        if not html:
            continue
        text = clean(html)
        prices = money_values(text)[:8]
        if not prices:
            continue
        out.append(
            {
                "date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
                "snapshot": url,
                "prices": [{"raw": p["raw"], "context": p["context"][:110]} for p in prices],
            }
        )
        await asyncio.sleep(0.4)  # be polite to the archive
    return out
