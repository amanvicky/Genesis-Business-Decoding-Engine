"""Regression tests for the PricingAgent, post pure-research cut: the tab
renders what the company actually charges (tiers, history, psychology) —
no LTV:CAC math, no sandbox, no recommendations."""
from __future__ import annotations

import asyncio

from app.agents.pricing import PricingAgent
from app.models import AnalyzeRequest, Evidence


def _agent() -> PricingAgent:
    return PricingAgent()


def _tiers(*pairs: tuple[str, str]) -> list[dict]:
    return [{"name": n, "price": p, "context": ""} for n, p in pairs]


def _ev(geography: str = "us") -> Evidence:
    req = AnalyzeRequest(mode="company", query="TestCo", geography=geography)
    return Evidence(req=req, subject="TestCo")


class TestBuild:
    def test_build_with_tiers_completes(self):
        ev = _ev()
        ev.current_pricing = _tiers(("Starter", "$29"), ("Pro", "$99"), ("Enterprise", "$499"))
        data = asyncio.run(PricingAgent().build(ev))
        assert data["tiers"] == ev.current_pricing
        assert data["psychology"]  # free/anchoring drivers still detected
        # the planning layer is gone — no formulas, no sandbox, no advice
        assert "unit_economics" not in data
        assert "sandbox" not in data
        assert "recommendation" not in data

    def test_no_tiers_is_an_empty_honest_tab(self):
        data = asyncio.run(PricingAgent().build(_ev()))
        assert data["tiers"] == []
        assert data["history"] == []
        assert "psychology" in data

    def test_build_with_hostile_tier_shapes(self):
        ev = _ev()
        ev.current_pricing = [{"name": "Pro", "price": 99, "context": ""},   # int price
                              {"name": "", "price": ""},                     # empty everything
                              {"name": "Bad", "price": "not-a-price"}]       # garbage price
        data = asyncio.run(PricingAgent().build(ev))  # must not raise
        assert "tiers" in data

    def test_anchoring_detection(self):
        ev = _ev()
        ev.current_pricing = _tiers(("Starter", "$10"), ("Pro", "$20"), ("Enterprise", "$100"))
        data = asyncio.run(PricingAgent().build(ev))
        drivers = [p["driver"] for p in data["psychology"]]
        assert "Anchoring" in drivers  # 100 >= 3 * 20

    def test_free_tier_detection(self):
        ev = _ev()
        ev.current_pricing = _tiers(("Free", "$0"), ("Pro", "$29"))
        data = asyncio.run(PricingAgent().build(ev))
        drivers = [p["driver"] for p in data["psychology"]]
        assert "Freemium acquisition" in drivers

    def test_no_price_mining_methods_left_behind(self):
        # _arpa and _recommend died with the unit-economics layer; if anyone
        # re-adds price math here, this fails and the cut is being undone
        assert not hasattr(_agent(), "_arpa")
        assert not hasattr(_agent(), "_recommend")
