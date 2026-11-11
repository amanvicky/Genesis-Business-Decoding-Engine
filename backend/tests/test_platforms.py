"""Wider platform lanes (LinkedIn/essays/GDELT press) and the local-LLM
model resolver."""
from __future__ import annotations

import asyncio

import pytest

from app.llm import pick_model
from app.scrapers import platforms


@pytest.fixture(autouse=True)
def _no_throttle_waits(monkeypatch):
    """The GDELT spacing exists for real rate limits; tests must stay fast."""
    monkeypatch.setattr(platforms, "_GDELT_MIN_GAP", 0.01)
    monkeypatch.setattr(platforms, "_GDELT_RETRY_WAIT", 0.01)
    platforms._last_gdelt_call = 0.0


class TestPickModel:
    def test_configured_model_wins(self):
        assert pick_model(["llama3.2", "mistral"], "llama3.2") == "llama3.2"

    def test_falls_back_to_what_the_user_has(self):
        models = ["richardyoung/llama-3.1-8b-instruct-abliterated:latest"]
        assert pick_model(models, "llama3.2") == models[0]

    def test_implicit_latest_tag_matches(self):
        assert pick_model(["llama3.2:latest", "mistral"], "llama3.2") == "llama3.2:latest"

    def test_nothing_pulled_is_none(self):
        assert pick_model([], "llama3.2") is None


class _PressFetcher:
    """GDELT-shaped try_json stub."""

    def __init__(self, payload):
        self.payload = payload

    async def try_json(self, url, *, kind="api", headers=None):
        self.url = url
        return self.payload


def _gdelt_payload():
    return {"articles": [
        {"url": "https://www.business-standard.com/x", "title": "Razorpay launches RAY",
         "domain": "business-standard.com", "seendate": "20260903T124500Z"},
        {"url": "https://techcrunch.com/y", "title": "Razorpay raises $100M",
         "domain": "techcrunch.com", "seendate": "20260801T090000Z"},
        {"url": "", "title": "no url row must be skipped", "domain": "d", "seendate": ""},
        {"url": "https://www.business-standard.com/x", "title": "duplicate url row", "domain": "d", "seendate": ""},
    ]}


class TestPress:
    def test_gdelt_rows_mapped_with_source(self):
        f = _PressFetcher(_gdelt_payload())
        rows = asyncio.run(platforms.press(f, "razorpay"))
        assert len(rows) == 2
        assert all(r["platform"] == "press" for r in rows)
        assert rows[0]["title"].startswith("Razorpay launches")
        assert "business-standard.com" in rows[0]["snippet"]

    def test_gdelt_query_is_quoted_and_bounded(self):
        f = _PressFetcher({"articles": []})
        asyncio.run(platforms.press(f, "rapid skill"))
        assert "%22rapid%20skill%22" in f.url
        assert "maxrecords=25" in f.url and "sourcelang=eng" in f.url

    def test_gdelt_unreachable_is_empty_not_fatal(self):
        class Dead:
            async def try_json(self, url, *, kind="api", headers=None):
                return None
        assert asyncio.run(platforms.press(Dead(), "anything")) == []


class _SearchStub:
    """Monkeypatches search.ddg_search with canned per-query rows."""

    def __init__(self, by_query):
        self.by_query = by_query

    async def __call__(self, f, q, limit):
        return self.by_query.get(q, [])


class TestSiteScopedLanes:
    def test_linkedin_lane_keeps_only_linkedin(self, monkeypatch):
        from app.scrapers import search as search_mod
        rows = [
            {"title": "Post about Razorpay", "url": "https://www.linkedin.com/posts/foo_razorpay-activity-1", "snippet": "our payroll takes days"},
            {"title": "Not linkedin", "url": "https://example.com/x", "snippet": "junk"},
        ]
        monkeypatch.setattr(search_mod, "ddg_search", _SearchStub({
            'site:linkedin.com/posts "Razorpay"': rows,
        }))
        out = asyncio.run(platforms.linkedin_posts(None, "Razorpay"))
        assert len(out) == 1
        assert out[0]["platform"] == "linkedin"
        assert "linkedin.com" in out[0]["url"]

    def test_essays_lane_keeps_medium_and_substack(self, monkeypatch):
        from app.scrapers import search as search_mod
        monkeypatch.setattr(search_mod, "ddg_search", _SearchStub({
            "site:medium.com Zoho": [
                {"title": "Zoho teardown", "url": "https://medium.com/@a/zoho-teardown", "snippet": "deep dive"},
            ],
            "site:substack.com Zoho": [
                {"title": "Zoho essay", "url": "https://somebody.substack.com/p/zoho", "snippet": "analysis"},
                {"title": "junk", "url": "https://example.com/z", "snippet": ""},
            ],
        }))
        out = asyncio.run(platforms.essays(None, "Zoho"))
        assert {("medium.com" in r["url"] or "substack.com" in r["url"]) for r in out} == {True}
        assert len(out) == 2

    def test_engine_failure_is_empty_not_fatal(self, monkeypatch):
        from app.scrapers import search as search_mod

        async def boom(f, q, limit):
            raise RuntimeError("rate limited")
        monkeypatch.setattr(search_mod, "ddg_search", boom)
        assert asyncio.run(platforms.linkedin_posts(None, "ADP")) == []
        assert asyncio.run(platforms.essays(None, "ADP")) == []
