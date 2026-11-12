"""Market-performance scrapers (Tab 10 backbone): keyless stock data.

Sources (no API keys, in priority order):
  1. Yahoo Finance unofficial chart/search endpoints
  2. Stooq weekly CSV fallback
Pure stat functions live here too so the rise/fall math is testable
without any network.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from ..models import Evidence
from .client import Fetcher

SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=6&newsCount=0"
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1y&interval=1wk"
STOOQ_URL = "https://stooq.com/q/d/l/?s={sym}&i=w"

# tickers we accept, both from Yahoo search and EDGAR evidence
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9&.\-]{0,9}(\.(NS|BO|L|TO|AX|DE))?$", re.I)


def valid_ticker(sym: str) -> bool:
    return bool(_TICKER_RE.fullmatch((sym or "").strip()))


async def resolve_ticker(fetcher: Fetcher, name: str, ev: Evidence) -> Optional[dict]:
    """Find a ticker for the subject: EDGAR evidence first (already trusted),
    then Yahoo's keyless search. Returns {symbol, exchange?, source} or None."""
    # 1. evidence: the filings scraper stores ticker info when EDGAR matched
    for f in ev.financials:
        for key in ("ticker", "symbol"):
            sym = str(f.get(key) or "").strip().upper()
            if valid_ticker(sym):
                return {"symbol": sym, "source": "sec-edgar"}
    if fetcher.offline:
        return None
    data = await fetcher.try_json(SEARCH_URL.format(q=name.strip()[:60]), kind="markets")
    if isinstance(data, dict):
        for q in data.get("quotes", []) or []:
            sym = str(q.get("symbol") or "").strip()
            if valid_ticker(sym) and q.get("quoteType") in ("EQUITY", "ETF"):
                return {"symbol": sym.upper(), "exchange": q.get("exchDisp") or q.get("exchange"),
                        "name": q.get("shortname") or q.get("longname") or "", "source": "yahoo-search"}
    return None


def _parse_chart(data: Any) -> Optional[dict]:
    """Defensively pull (dates, closes, currency) from Yahoo's chart JSON."""
    try:
        result = data["chart"]["result"][0]
        stamps = result.get("timestamp") or []
        closes = result["indicators"]["quote"][0].get("close") or []
        pairs = [(datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"), float(c))
                 for ts, c in zip(stamps, closes) if c is not None]
        if len(pairs) < 8:
            return None
        meta = result.get("meta") or {}
        return {"closes": pairs, "currency": meta.get("currency", "USD"),
                "price": meta.get("regularMarketPrice")}
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def _parse_stooq_csv(text: str) -> Optional[dict]:
    rows: list[tuple[str, float]] = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",")
        if len(parts) >= 5:
            try:
                rows.append((parts[0], float(parts[4])))
            except ValueError:
                continue
    if len(rows) < 8:
        return None
    return {"closes": rows, "currency": "USD", "price": rows[-1][1]}


async def weekly_closes(fetcher: Fetcher, symbol: str) -> Optional[dict]:
    """1y of weekly closes for a symbol: Yahoo first, Stooq fallback."""
    if fetcher.offline:
        return None
    sym = symbol.upper()
    data = await fetcher.try_json(CHART_URL.format(sym=sym), kind="markets")
    parsed = _parse_chart(data) if data else None
    if parsed:
        return parsed
    text = await fetcher.try_text(STOOQ_URL.format(sym=sym.lower()), kind="markets")
    return _parse_stooq_csv(text) if text else None


# ------------------------------------------------------------- pure stats

def _pct(a: float, b: float) -> float:
    return round((a - b) / b * 100, 2) if b else 0.0


def performance_stats(closes: list[tuple[str, float]]) -> dict:
    """Rise/fall highlights from a weekly close series [(date, price)]."""
    if len(closes) < 8:
        return {}
    dates = [d for d, _ in closes]
    prices = [p for _, p in closes]
    current, first = prices[-1], prices[0]
    hi_i = max(range(len(prices)), key=lambda i: prices[i])
    lo_i = min(range(len(prices)), key=lambda i: prices[i])

    moves = [{"date": dates[i], "change_pct": _pct(prices[i], prices[i - 1]),
              "from": prices[i - 1], "to": prices[i]}
             for i in range(1, len(prices))]
    rises = sorted(moves, key=lambda m: -m["change_pct"])[:3]
    falls = sorted(moves, key=lambda m: m["change_pct"])[:3]

    # max drawdown: worst peak-to-trough fall across the year
    peak, drawdown, dd_when = prices[0], 0.0, ""
    for i, p in enumerate(prices):
        peak = max(peak, p)
        dd = _pct(p, peak)
        if dd < drawdown:
            drawdown, dd_when = dd, dates[i]

    # YTD: first close dated in the current calendar year
    year = dates[-1][:4]
    ytd_base = next((p for d, p in closes if d.startswith(year)), first)

    return {
        "current": current,
        "change_1y_pct": _pct(current, first),
        "high_52w": {"price": prices[hi_i], "date": dates[hi_i]},
        "low_52w": {"price": prices[lo_i], "date": dates[lo_i]},
        "ytd_pct": _pct(current, ytd_base),
        "max_drawdown": {"pct": drawdown, "date": dd_when},
        "best_weeks": rises,
        "worst_weeks": falls,
        "series": [{"date": d, "close": round(p, 2)} for d, p in closes],
    }


def index_for(geography: str) -> str:
    """Benchmark index for private/idea subjects, by geography."""
    return {"india": "^NSEI", "us": "^GSPC"}.get(geography, "^GSPC")
