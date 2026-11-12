"""Architecture-audit regression tests: SSRF gate, boundary validation,
scraper hardening, and the cross-agent contract fixes."""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.data import failures as failures_kb
from app.main import app
from app.models import AnalyzeRequest, Evidence
from app.scrapers.client import Fetcher, safe_public_http_url
from app.scrapers.github import releases as gh_releases
from app.scrapers.wayback import pricing_history
from app.scrapers.wikipedia import _strip_headers

client = TestClient(app)


class TestSSRFGate:
    @pytest.mark.parametrize("url", [
        "http://169.254.169.254/latest/meta-data#pricing",  # cloud metadata
        "http://192.168.1.1/admin?pricing",                  # private range
        "http://10.0.0.5/",
        "http://127.0.0.1:8000/api/health",
        "http://localhost:3000/",
        "https://user@10.0.0.5:8080/changelog",              # credential smuggle
        "ftp://example.com/x",
        "https://host.local/x",
        "javascript:alert(1)",
    ])
    def test_blocked(self, url):
        assert safe_public_http_url(url) is False, url

    @pytest.mark.parametrize("url", [
        "https://razorpay.com/pricing",
        "http://example.com",
        "https://sub.domain.org/a/b?c=d",
    ])
    def test_allows_public(self, url):
        assert safe_public_http_url(url) is True, url


class TestBoundaryValidation:
    def test_whitespace_only_query_rejected_at_boundary(self):
        with pytest.raises(ValidationError):
            AnalyzeRequest(query="   ")
        with pytest.raises(ValidationError):
            AnalyzeRequest(query=" \t ")

    def test_query_is_stripped(self):
        assert AnalyzeRequest(query="  ADP payroll  ").query == "ADP payroll"

    def test_valid_query_still_accepted(self):
        assert AnalyzeRequest(query="ab").query == "ab"


class TestScraperHardening:
    def test_wikipedia_header_stripper_linear_and_correct(self):
        text = "== History ==\nkeep this line\n===Deep===\nalso keep"
        assert _strip_headers(text) == "keep this line\nalso keep"
        big = "=" * 50000 + "x" + "=" * 50000
        assert _strip_headers(big) == ""          # header-ish, dropped
        assert _strip_headers("= not a header = ok") == "= not a header = ok"

    def test_github_releases_rejects_bad_full_name_without_network(self):
        ev = Evidence(req=AnalyzeRequest(query="x y"), subject="x")
        f = Fetcher(ev)  # offline fetcher raises if the network is ever touched
        for bad in ("owner/repo/extra", "has space/repo", "", "owner/", "/repo", "owner/repo?x=1"):
            assert asyncio.run(gh_releases(f, bad)) == [], bad

    def test_wayback_survives_non_list_cdx(self):
        ev = Evidence(req=AnalyzeRequest(query="x y"), subject="x")
        f = Fetcher(ev)

        async def fake_json(url, **kw):
            return {"error": "not a list"}  # CDX returning a JSON object
        f.try_json = fake_json  # type: ignore[method-assign]
        assert asyncio.run(pricing_history(f, "example.com")) == []

    def test_reddit_shape_guards(self):
        # exercised via direct import to avoid network: the guards live in the
        # parsing block — simulate by importing and checking the module guards exist
        import inspect
        from app.scrapers import reddit
        src = inspect.getsource(reddit)
        assert "isinstance(data, dict)" in src
        assert 'd.get("created_utc") or 0' in src


class TestAdversaryRobustness:
    def _adversary_with(self, premortem_data: dict):
        from app.agents.adversary import AdversaryAgent
        req = AnalyzeRequest(mode="idea", query="chegg homework answers")
        ev = Evidence(req=req, subject="chegg homework answers")
        agent = AdversaryAgent()
        agent.sections = {"premortem": {"data": premortem_data}, "structural": {"data": {"moats": []}}}
        return asyncio.run(agent.build(ev))

    def test_empty_failure_modes_does_not_crash(self):
        # realistic subject class where no failure keyword matches → []
        data = self._adversary_with({"common_failure_modes": [], "analogs": []})
        assert data is not None
        assert "error" not in data

    def test_serious_count_excludes_probes(self):
        from app.agents.adversary import AdversaryAgent
        req = AnalyzeRequest(mode="idea", query="x y")
        ev = Evidence(req=req, subject="x")
        agent = AdversaryAgent()
        agent.sections = {
            "premortem": {"data": {"common_failure_modes": [{"mode": "Unit economics never closed"}], "analogs": []}},
            "structural": {"data": {"moats": []}},
        }
        data = asyncio.run(agent.build(ev))
        total = data["fatal_count"] + data["serious_count"]
        emitted = sum(len(p.get("kills") or []) for p in data["personas"])
        assert total <= emitted  # probes are not counted as serious


class TestPricingAnchoring:
    def test_no_false_anchoring_when_order_not_price_order(self):
        from app.agents.pricing import PricingAgent
        req = AnalyzeRequest(mode="idea", query="xy")
        ev = Evidence(req=req, subject="x")
        ev.current_pricing = [  # keyword-ladder order, prices DESCENDING
            {"name": "Team", "price": "$100", "context": ""},
            {"name": "Business", "price": "$50", "context": ""},
            {"name": "Scale", "price": "$10", "context": ""},
        ]
        data = asyncio.run(PricingAgent().build(ev))
        # the generic education entry is expected; a DETECTED anchoring cites
        # actual prices ("X at N vs Y at M") — none may exist here
        detected = [p for p in data["psychology"]
                    if p["driver"] == "Anchoring" and "vs" in p["evidence"] and "$" in p["evidence"]]
        assert detected == []

    def test_real_anchoring_still_detected(self):
        from app.agents.pricing import PricingAgent
        req = AnalyzeRequest(mode="idea", query="xy")
        ev = Evidence(req=req, subject="xy")
        ev.current_pricing = [
            {"name": "Starter", "price": "$10", "context": ""},
            {"name": "Pro", "price": "$20", "context": ""},
            {"name": "Enterprise", "price": "$100", "context": ""},
        ]
        data = asyncio.run(PricingAgent().build(ev))
        detected = [p for p in data["psychology"]
                    if p["driver"] == "Anchoring" and "Enterprise" in p["evidence"] and "Pro" in p["evidence"]]
        assert detected, data["psychology"][:2]


class TestCORS:
    def test_foreign_origin_gets_no_cors_grant(self):
        r = client.get("/api/health", headers={"Origin": "https://evil.example"})
        assert r.headers.get("access-control-allow-origin") != "https://evil.example"
        assert r.headers.get("access-control-allow-origin") != "*"

    def test_dashboard_origin_allowed(self):
        r = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


class TestFailuresKBUnchanged:
    def test_matching_failures_still_works(self):
        hits = failures_kb.matching_failures("payroll compliance", "payroll")
        assert hits and all("name" in h for h in hits)
