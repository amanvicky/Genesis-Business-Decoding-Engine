"""Tab 16 — Stock Performance: the rise and fall, with the highlights.

Public company: ticker resolution, 1-year weekly closes, 52-week high/low,
biggest weekly rises and falls with dates, max drawdown. Private company or
idea mode: the relevant market index as context, honestly labeled. Everything
keyless (Yahoo chart JSON, Stooq fallback); offline degrades to pending.
"""
from __future__ import annotations

from ..models import Evidence
from ..scrapers import markets as MK
from ..scrapers.client import Fetcher
from .base import Agent


def _fmt_price(p: float, currency: str) -> str:
    sym = "₹" if currency == "INR" else "$"
    return f"{sym}{p:,.2f}"


class MarketsAgent(Agent):
    id = "markets"
    title = "Stock Performance — Rise & Fall"
    icon = "▲"
    tab = 10

    async def build(self, ev: Evidence) -> dict:
        from ..text import clean as _clean
        f = Fetcher(ev)
        if f.offline:
            return {"traded": None, "note": "Offline run — market data needs the network. Re-run online.",
                    "highlights": {"rises": [], "falls": []}}

        name = _clean(ev.subject) or ev.sector
        resolved = await MK.resolve_ticker(f, name, ev)

        # public company path
        if resolved:
            series = await MK.weekly_closes(f, resolved["symbol"])
            if series and series.get("closes"):
                stats = MK.performance_stats(series["closes"])
                currency = series.get("currency") or "USD"
                return {
                    "traded": True,
                    "symbol": resolved["symbol"],
                    "company_name": resolved.get("name") or name,
                    "source": resolved.get("source", ""),
                    "currency_display": currency,
                    "performance": stats,
                    "sparkline": [p["close"] for p in stats["series"]],
                    "summary": (
                        f"{resolved['symbol']} at {_fmt_price(stats['current'], currency)} — "
                        f"{stats['change_1y_pct']:+.1f}% over 1y, {stats['ytd_pct']:+.1f}% YTD. "
                        f"52w range {_fmt_price(stats['low_52w']['price'], currency)}–{_fmt_price(stats['high_52w']['price'], currency)}. "
                        f"Max drawdown {stats['max_drawdown']['pct']:.1f}%."
                    ),
                    "note": "Weekly closes, keyless public endpoints. Not investment advice.",
                }

        # private / unresolved: benchmark index for the geography they'd launch into
        index_sym = MK.index_for(ev.req.geography.value)
        series = await MK.weekly_closes(f, index_sym)
        index_name = {"^NSEI": "Nifty 50", "^GSPC": "S&P 500"}.get(index_sym, index_sym)
        if series and series.get("closes"):
            stats = MK.performance_stats(series["closes"])
            currency = series.get("currency") or "USD"
            return {
                "traded": False,
                "index": {"symbol": index_sym, "name": index_name},
                "currency_display": currency,
                "performance": stats,
                "sparkline": [p["close"] for p in stats["series"]],
                "summary": (
                    f"{name} is not publicly traded, so here's the market you'd be launching into: "
                    f"{index_name} {stats['change_1y_pct']:+.1f}% over 1y. "
                    "When you raise or benchmark, this is the tide your numbers swim against."
                ),
                "note": "Index context only — the subject itself has no public market.",
            }

        return {"traded": None, "note": "No market data found for this subject (and no index fallback succeeded).",
                "highlights": {"rises": [], "falls": []}}

    def summarize(self, ev: Evidence, data: dict) -> str:
        return data.get("summary") or data.get("note", "")

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. Given the 1-year performance stats and the biggest weekly rises and "
            "falls, name the most plausible business reason for the single largest move and the one thing "
            "a founder in this category should learn from it. One short paragraph."
        )
