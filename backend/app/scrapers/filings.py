"""SEC EDGAR (free, keyless): company filings + XBRL annual revenue history.

This is the open-financial-filings layer of source triangulation. US-listed
subjects get real revenue decodes; private/Indian companies have no free
structured equivalent and are reported as such.
"""
from __future__ import annotations

import re

import httpx

from ..text import clean

UA = {"User-Agent": "GenesisResearchBot/1.0 (local research tool; contact: local@localhost)"}
_tickers_cache: list[dict] | None = None

_SUFFIXES = re.compile(r"\b(inc|incorporated|corp|corporation|llc|ltd|limited|plc|co|company|group|holdings?)\b", re.I)


def _norm(value: str) -> str:
    return _SUFFIXES.sub("", re.sub(r"[^a-z ]", " ", value.lower())).strip()


async def _load_tickers(fetcher) -> list[dict]:
    global _tickers_cache
    if _tickers_cache is not None:
        return _tickers_cache
    try:
        async with httpx.AsyncClient(timeout=30, headers=UA, follow_redirects=True) as client:
            r = await client.get("https://www.sec.gov/files/company_tickers.json")
        r.raise_for_status()
        rows = list(r.json().values())
        _tickers_cache = [
            {"cik": int(x["cik_str"]), "ticker": x["ticker"], "norm": _norm(x["title"]), "title": x["title"]}
            for x in rows
        ]
    except Exception:
        _tickers_cache = []
    return _tickers_cache


def _match(rows: list[dict], *names: str) -> dict | None:
    cands = [_norm(n) for n in names if n]
    for norm in cands:
        if not norm:
            continue
        for row in rows:
            if row["norm"] == norm:
                return row
    for norm in cands:
        if len(norm) < 4:
            continue
        for row in rows:
            if row["norm"].startswith(norm):
                return row
    return None


async def _annual_revenues(cik: int) -> list[dict]:
    """Annual (10-K, FY) revenue history from the free XBRL companyconcept API."""
    out: list[dict] = []
    for concept in ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"):
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/{concept}.json"
        try:
            async with httpx.AsyncClient(timeout=25, headers=UA, follow_redirects=True) as client:
                r = await client.get(url)
            if r.status_code != 200:
                continue
            units = (r.json().get("units") or {}).get("USD") or []
            seen: dict[str, dict] = {}
            for u in units:
                if u.get("form") == "10-K" and u.get("fp") == "FY" and u.get("val"):
                    seen.setdefault(u["end"], {"fy_end": u["end"], "revenue_usd": u["val"]})
            out = [seen[k] for k in sorted(seen)][-10:]
            if out:
                break
        except Exception:
            continue
    return out


async def edgar_profile(fetcher, subject: str, wiki_name: str | None = None, expansion: str | None = None) -> dict:
    """Resolve the subject on EDGAR. Tries the wiki canonical name, the raw
    subject, and the triangulated acronym expansion ("automatic data processing")
    — bare acronyms alone can't match EDGAR's registered names."""
    if fetcher.offline:
        return {}
    rows = await _load_tickers(fetcher)
    if not rows:
        return {}
    match = _match(rows, wiki_name or "", subject, expansion or "")
    if not match:
        return {}
    cik = match["cik"]
    profile: dict = {"cik": cik, "name": match["title"], "ticker": match["ticker"], "revenues": [], "filings": []}

    try:
        async with httpx.AsyncClient(timeout=25, headers=UA, follow_redirects=True) as client:
            r = await client.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if r.status_code == 200:
            recent = (r.json().get("filings") or {}).get("recent") or {}
            forms, dates, accessions, docs = (
                recent.get("form") or [],
                recent.get("filingDate") or [],
                recent.get("accessionNumber") or [],
                recent.get("primaryDocument") or [],
            )
            for i in range(min(len(forms), 400)):
                if forms[i] in ("10-K", "10-K/A") and len(profile["filings"]) < 4:
                    acc = (accessions[i] or "").replace("-", "")
                    doc = docs[i] if i < len(docs) else ""
                    profile["filings"].append(
                        {
                            "form": forms[i],
                            "date": dates[i] if i < len(dates) else "",
                            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}" if doc else "",
                        }
                    )
    except Exception:
        pass

    profile["revenues"] = await _annual_revenues(cik)
    return profile
