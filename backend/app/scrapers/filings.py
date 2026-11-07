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


def registration_from_submissions(submissions: dict) -> dict:
    """Public registration fields of an EDGAR filer, from the submissions
    payload (pure — testable offline)."""
    j = submissions or {}
    reg: dict = {
        "entity_type": j.get("entityType"),
        "state_of_incorporation": j.get("stateOfIncorporation"),
        "sic": j.get("sic"),
        "sic_description": j.get("sicDescription"),
        "exchanges": [str(x) for x in (j.get("exchanges") or [])],
        "fiscal_year_end": j.get("fiscalYearEnd"),
        "former_names": [str(f.get("name")) for f in (j.get("formerNames") or []) if f.get("name")][:3],
        "addresses": [],
    }
    for a in (j.get("addresses") or {}).values():
        if isinstance(a, dict) and a.get("street1"):
            reg["addresses"].append(", ".join(
                str(a.get(p)) for p in ("street1", "street2", "city", "stateOrCountry", "zip")
                if a.get(p)))
    return {k: v for k, v in reg.items() if v not in (None, "", [])}


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
            j = r.json()
            profile["registration"] = registration_from_submissions(j)
            recent = (j.get("filings") or {}).get("recent") or {}
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
