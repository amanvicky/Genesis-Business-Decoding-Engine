"""Cascade health: engines cool down instead of dying, counters reset on success."""
import asyncio
import time

import pytest

from app.scrapers import search

ENGINES = ("_lite", "_html", "_searx", "_mojeek", "_gnews_rss", "_bnews_rss")


def _reset():
    search._ENGINE_COOLDOWN.clear()
    search._ENGINE_EMPTY.clear()


class FakeFetcher:
    evidence = None


def _rows():
    return [{"title": "t", "url": "https://example.com/a", "snippet": "s"}]


@pytest.fixture
def all_empty(monkeypatch):
    async def impl(f, q, limit):
        return []
    for name in ENGINES:
        monkeypatch.setattr(search, name, impl)


@pytest.fixture
def lite_raises_rest_ok(monkeypatch):
    async def boom(f, q, limit):
        raise RuntimeError("403 blocked")
    async def ok(f, q, limit):
        return _rows()
    monkeypatch.setattr(search, "_lite", boom)
    for name in ENGINES[1:]:
        monkeypatch.setattr(search, name, ok)


class TestCascadeCooldown:
    def test_a_volley_of_empties_does_not_pause_before_the_limit(self, monkeypatch, all_empty):
        _reset()
        for _ in range(search._EMPTY_LIMIT - 1):
            assert asyncio.run(search.ddg_search(FakeFetcher(), "acme", 10)) == []
            assert not search._paused("ddg-lite")
        # one more empty crosses the limit → paused (not dead forever)
        asyncio.run(search.ddg_search(FakeFetcher(), "acme", 10))
        assert search._paused("ddg-lite")

    def test_paused_engines_are_skipped_but_not_permanently(self, monkeypatch, all_empty):
        _reset()
        search._pause("ddg-lite")
        # cooldown is time-based: rewind it and the engine is back in play
        search._ENGINE_COOLDOWN["ddg-lite"] = time.monotonic() - 1
        assert not search._paused("ddg-lite")

    def test_exception_pauses_that_engine_and_falls_through(self, monkeypatch, lite_raises_rest_ok):
        _reset()
        out = asyncio.run(search.ddg_search(FakeFetcher(), "acme", 10))
        assert out == _rows()          # ddg-html answered
        assert search._paused("ddg-lite")
        assert not search._paused("ddg-html")

    def test_success_resets_the_empty_counter(self, monkeypatch):
        _reset()
        state = {"n": 0}

        async def flaky(f, q, limit):
            state["n"] += 1
            return [] if state["n"] == 1 else _rows()

        async def empty(f, q, limit):
            return []

        monkeypatch.setattr(search, "_lite", flaky)
        for name in ENGINES[1:]:
            monkeypatch.setattr(search, name, empty)

        assert asyncio.run(search.ddg_search(FakeFetcher(), "acme", 10)) == []
        assert search._ENGINE_EMPTY["ddg-lite"] == 1
        assert asyncio.run(search.ddg_search(FakeFetcher(), "acme", 10)) == _rows()
        assert "ddg-lite" not in search._ENGINE_EMPTY
        assert not search._paused("ddg-lite")

    def test_news_search_skips_paused_gnews(self, monkeypatch):
        _reset()
        async def boom(f, q, limit):
            raise RuntimeError("off air")
        async def ok(f, q, limit):
            return _rows()
        monkeypatch.setattr(search, "_gnews_rss", boom)
        monkeypatch.setattr(search, "_bnews_rss", ok)
        out = asyncio.run(search.news_search(FakeFetcher(), "acme", 10))
        assert out == _rows()
        assert search._paused("gnews")
        assert not search._paused("bnews")
