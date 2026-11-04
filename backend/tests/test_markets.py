"""Tab 16 — Stock Performance: pure stats math + ticker validation + agent shape."""
from __future__ import annotations

import asyncio

from app.agents.markets import MarketsAgent
from app.models import AnalyzeRequest, Evidence
from app.scrapers.markets import (
    index_for,
    performance_stats,
    valid_ticker,
    weekly_closes,
)


def _series(n: int = 30, base: float = 100.0) -> list[tuple[str, float]]:
    return [(f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", round(base + i * 1.5, 2)) for i in range(n)]


class TestPerformanceStats:
    def test_rise_fall_highlights(self):
        closes = _series(10)
        closes[5] = (closes[5][0], 260.0)   # big spike
        closes[9] = (closes[9][0], 40.0)    # big crash, at the end so no recovery week outranks it
        stats = performance_stats(closes)
        assert stats["best_weeks"][0]["change_pct"] > 50
        assert stats["worst_weeks"][0]["change_pct"] < -50
        assert stats["best_weeks"][0]["date"] == closes[5][0]
        assert stats["worst_weeks"][0]["date"] == closes[9][0]

    def test_52w_high_low_and_current(self):
        closes = _series(12)
        closes[3] = (closes[3][0], 300.0)
        closes[9] = (closes[9][0], 10.0)
        stats = performance_stats(closes)
        assert stats["high_52w"]["price"] == 300.0 and stats["high_52w"]["date"] == closes[3][0]
        assert stats["low_52w"]["price"] == 10.0
        assert stats["current"] == closes[-1][1]

    def test_ytd_uses_current_year_base(self):
        closes = [("2025-09-01", 100.0), ("2025-10-01", 110.0), ("2025-11-01", 100.0), ("2025-12-01", 150.0),
                  ("2026-01-05", 120.0), ("2026-02-01", 130.0), ("2026-03-01", 140.0), ("2026-04-01", 180.0)]
        stats = performance_stats(closes)
        assert stats["ytd_pct"] == 50.0  # 180 vs 120 (first close of 2026)

    def test_max_drawdown_peak_to_trough(self):
        closes = [("2026-01-01", 100.0), ("2026-02-01", 200.0), ("2026-03-01", 50.0), ("2026-04-01", 80.0),
                  ("2026-05-01", 90.0), ("2026-06-01", 100.0), ("2026-07-01", 110.0), ("2026-08-01", 120.0)]
        stats = performance_stats(closes)
        assert stats["max_drawdown"]["pct"] == -75.0
        assert stats["max_drawdown"]["date"] == "2026-03-01"

    def test_short_series_empty(self):
        assert performance_stats(_series(5)) == {}

    def test_no_crash_on_flat_series(self):
        closes = [("2026-01-01", 50.0), ("2026-01-08", 50.0), ("2026-01-15", 50.0), ("2026-01-22", 50.0),
                  ("2026-01-29", 50.0), ("2026-02-05", 50.0), ("2026-02-12", 50.0), ("2026-02-19", 50.0)]
        stats = performance_stats(closes)
        assert stats["max_drawdown"]["pct"] == 0.0


class TestTickerValidation:
    def test_valid_symbols(self):
        assert valid_ticker("AAPL")
        assert valid_ticker("M&M.NS")
        assert valid_ticker("TSLA")

    def test_rejects_injection_shapes(self):
        assert not valid_ticker("AAPL?range=1y")
        assert not valid_ticker("../../etc/passwd")
        assert not valid_ticker("")
        assert not valid_ticker("A" * 30)


class TestAgentShape:
    def test_offline_reports_pending_without_network(self):
        req = AnalyzeRequest(mode="company", query="Apple")
        ev = Evidence(req=req, subject="Apple")
        data = asyncio.run(MarketsAgent().build(ev))
        assert data["traded"] is None
        assert "Offline" in data["note"]

    def test_public_company_full_path_with_fake_fetcher(self):
        # patch the Fetcher the AGENT constructs, so the whole build path runs:
        # resolve via fake search -> real weekly_closes parse -> stats
        import app.agents.markets as AM
        closes = [(f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", 100.0 + i) for i in range(30)]

        class FakeFetcher:
            offline = False

            async def try_json(self, url, **kw):
                if "search?" in url:
                    return {"quotes": [{"symbol": "AAPL", "quoteType": "EQUITY", "shortname": "Apple Inc."}]}
                return {"chart": {"result": [{
                    "meta": {"currency": "USD", "regularMarketPrice": closes[-1][1]},
                    "timestamp": list(range(len(closes))),
                    "indicators": {"quote": [{"close": [c for _, c in closes]}]},
                }]}}

            async def try_text(self, url, **kw):
                return None

        orig = AM.Fetcher
        AM.Fetcher = lambda ev: FakeFetcher()  # type: ignore[misc]
        try:
            req = AnalyzeRequest(mode="company", query="Apple", geography="us")
            ev = Evidence(req=req, subject="Apple")
            data = asyncio.run(MarketsAgent().build(ev))
        finally:
            AM.Fetcher = orig
        assert data["traded"] is True
        assert data["symbol"] == "AAPL"
        assert data["performance"]["current"] == closes[-1][1]
        assert len(data["sparkline"]) == 30

    def test_private_company_gets_index_context(self):
        import app.agents.markets as AM
        closes = [(f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", 20000.0 + i * 10) for i in range(30)]

        class NoTickerFetcher:
            offline = False

            async def try_json(self, url, **kw):
                if "search?" in url:
                    return {"quotes": []}
                return {"chart": {"result": [{
                    "meta": {"currency": "INR", "regularMarketPrice": closes[-1][1]},
                    "timestamp": list(range(len(closes))),
                    "indicators": {"quote": [{"close": [c for _, c in closes]}]},
                }]}}

            async def try_text(self, url, **kw):
                return None

        orig = AM.Fetcher
        AM.Fetcher = lambda ev: NoTickerFetcher()  # type: ignore[misc]
        try:
            req = AnalyzeRequest(mode="idea", query="tiffin service", geography="india")
            ev = Evidence(req=req, subject="tiffin service")
            data = asyncio.run(MarketsAgent().build(ev))
        finally:
            AM.Fetcher = orig
        assert data["traded"] is False
        assert data["index"]["symbol"] == "^NSEI"
        assert "not publicly traded" in data["summary"]


def _fake_weekly(closes):
    async def _inner(f, sym):
        return {"closes": closes, "currency": "USD", "price": closes[-1][1]}
    return _inner


def test_index_by_geography():
    assert index_for("india") == "^NSEI"
    assert index_for("us") == "^GSPC"
    assert index_for("global") == "^GSPC"


def test_offline_weekly_closes_returns_none():
    req = AnalyzeRequest(mode="idea", query="x y")
    ev = Evidence(req=req, subject="x")
    f = FetcherOffline()
    assert asyncio.run(weekly_closes(f, "AAPL")) is None


class FetcherOffline:
    offline = True

    def __getattr__(self, name):
        raise RuntimeError("network touched in offline mode")
