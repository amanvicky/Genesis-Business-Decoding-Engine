"""Regression tests for the PricingAgent — including the live-only crash the
E2E stream test caught: _arpa unpacked a float whenever any paid tier existed.
Offline mode never produced tiers, so the offline suite couldn't see it."""
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


class TestArpa:
    def test_median_of_paid_tiers(self):
        # Free $0 is excluded (amount 0); median of [29, 99, 499] = 99
        assert _agent()._arpa(_tiers(("Free", "$0"), ("Starter", "$29"), ("Pro", "$99"), ("Enterprise", "$499"))) == 99.0

    def test_free_named_tiers_with_real_prices(self):
        # every tier name contains "free" → paid pool empty → must fall back
        # to vals without crashing on the float/tuple mix (the live bug)
        assert _agent()._arpa(_tiers(("Free trial", "$5"), ("Free plus", "$15"))) == 15.0

    def test_no_tiers_returns_none(self):
        assert _agent()._arpa([]) is None

    def test_zero_price_tiers_ignored(self):
        assert _agent()._arpa(_tiers(("Free", "$0"), ("Free starter", "$0.00"))) is None


class TestBuild:
    def test_build_with_tiers_completes(self):
        ev = _ev()
        ev.current_pricing = _tiers(("Starter", "$29"), ("Pro", "$99"), ("Enterprise", "$499"))
        data = asyncio.run(PricingAgent().build(ev))
        assert data["unit_economics"]["arpa"] == 99.0
        assert data["unit_economics"]["ltv_cac_ratio"] is not None
        assert data["tiers"] == ev.current_pricing

    def test_cac_payback_is_months_not_years(self):
        # the field is named cac_payback_months: CAC / monthly net margin.
        # A ×12 slip once shipped 12×-overstated months to the advisor.
        ev = _ev()
        ev.current_pricing = _tiers(("Starter", "$29"), ("Pro", "$99"), ("Enterprise", "$499"))
        ue = asyncio.run(PricingAgent().build(ev))["unit_economics"]
        expected = round(180 / (ue["arpa"] * ue["assumed_gross_margin"]), 1)
        assert ue["cac_payback_months"] == expected

    def test_build_without_tiers_uses_geo_default(self):
        data = asyncio.run(PricingAgent().build(_ev("india")))
        assert data["unit_economics"]["arpa"] == 999
        data_us = asyncio.run(PricingAgent().build(_ev("us")))
        assert data_us["unit_economics"]["arpa"] == 29

    def test_build_with_hostile_tier_shapes(self):
        ev = _ev()
        ev.current_pricing = [{"name": "Pro", "price": 99, "context": ""},   # int price
                              {"name": "", "price": ""},                     # empty everything
                              {"name": "Bad", "price": "not-a-price"}]       # garbage price
        data = asyncio.run(PricingAgent().build(ev))  # must not raise
        assert isinstance(data["unit_economics"]["arpa"], (float, int)) or data["unit_economics"]["arpa"] is None

    def test_anchoring_detection(self):
        ev = _ev()
        ev.current_pricing = _tiers(("Starter", "$10"), ("Pro", "$20"), ("Enterprise", "$100"))
        data = asyncio.run(PricingAgent().build(ev))
        drivers = [p["driver"] for p in data["psychology"]]
        assert "Anchoring" in drivers  # 100 >= 3 * 20
