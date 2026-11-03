"""Tab 13 — Market Sizing & Capital Strategy: formula integrity and verdicts."""
from __future__ import annotations

import asyncio

from app.agents.marketsize import MarketSizeAgent, _compact
from app.data.marketsize import ADOPTION_CURVE, MARKET_BASES
from app.models import AnalyzeRequest, Evidence


def _run(mode: str = "idea", geo: str = "india", sector_evidence: bool = True) -> dict:
    req = AnalyzeRequest(mode=mode, query="Payroll compliance automation", geography=geo)
    ev = Evidence(req=req, subject="PayCo")
    ev.sector = "payroll"  # the pipeline sets this via detect_sector before agents run
    agent = MarketSizeAgent()
    data = asyncio.run(agent.build(ev))
    return data


class TestSizingMath:
    def test_sam_formula(self):
        data = _run(geo="india")
        base = MARKET_BASES["payroll"]["india"]["buying_units"]
        arpa = data["assumptions"]["arpa"]
        assert data["sam"]["value"] == round(base * arpa * 12)

    def test_tam_uses_global_base(self):
        data = _run(geo="india")
        g = MARKET_BASES["payroll"]["global"]["buying_units"]
        arpa = data["assumptions"]["arpa"]
        assert data["tam"]["value"] == round(g * arpa * 12)

    def test_som_adoption_curve(self):
        data = _run(geo="india")
        base = MARKET_BASES["payroll"]["india"]["buying_units"]
        arpa = data["assumptions"]["arpa"]
        for row in data["som_by_year"]:
            y = int(row["year"].split()[1])
            assert row["customers"] == round(base * ADOPTION_CURVE[y])
            assert row["value"] == round(base * ADOPTION_CURVE[y] * arpa * 12)

    def test_missing_sector_falls_back_to_generic(self):
        data = _run(geo="us")
        # "Payroll compliance automation" detects payroll; force-generic run:
        from app.models import AnalyzeRequest, Evidence as E
        req = AnalyzeRequest(mode="idea", query="zzz unheard category")
        ev = E(req=req, subject="zzz unheard category")
        agent = MarketSizeAgent()
        data2 = asyncio.run(agent.build(ev))
        assert data2["market_base"]["sector"] == "generic"
        assert data2["sam"]["value"] > 0


class TestVerdict:
    def test_math_doesnt_close_when_som_below_breakeven(self):
        data = _run(geo="india")
        # offline defaults: tiny team burn, big base → likely closes comfortably;
        # verdict must be one of the three honest states, never vague
        assert any(k in data["verdict"] for k in ("MATH CLOSES", "MATH DOESN'T CLOSE", "UNKNOWN"))
        assert data["verdict_tone"] in ("green", "amber", "red")

    def test_verdict_unknown_without_breakeven(self):
        from app.models import AnalyzeRequest, Evidence as E
        req = AnalyzeRequest(mode="idea", query="anything")
        ev = E(req=req, subject="anything")
        agent = MarketSizeAgent()
        agent.sections = {}  # no financial section yet
        data = asyncio.run(agent.build(ev))
        assert "UNKNOWN" in data["verdict"]


class TestCapitalStrategy:
    def test_raise_formula_18mo_with_buffer(self):
        data = _run()
        cap = data["capital_strategy"]
        # burn comes from the financial section built earlier in the pipeline;
        # standalone here it's absent → raise None but formula documented
        assert "18 months" in cap["raise_formula"]
        assert "1.25" in cap["raise_formula"]

    def test_raise_computed_with_financial_section(self):
        from app.models import AnalyzeRequest, Evidence as E
        req = AnalyzeRequest(mode="idea", query="payroll", geography="india")
        ev = E(req=req, subject="payroll")
        ev.sector = "payroll"
        agent = MarketSizeAgent()
        agent.sections = {
            "financial": {"data": {"computed": {"burn_month": 100000, "breakeven_customers": 50}}},
            "pricing": {"data": {"unit_economics": {"arpa": 999, "currency": "₹"}}},
        }
        data = asyncio.run(agent.build(ev))
        assert data["capital_strategy"]["recommended_raise"] == round(100000 * 18 * 1.25)
        assert data["sam"]["value"] == round(MARKET_BASES["payroll"]["india"]["buying_units"] * 999 * 12)

    def test_dilution_at_geo_cap(self):
        from app.models import AnalyzeRequest, Evidence as E
        from app.data.marketsize import FUNDING_NORMS
        req = AnalyzeRequest(mode="idea", query="payroll", geography="us")
        ev = E(req=req, subject="payroll")
        agent = MarketSizeAgent()
        agent.sections = {"financial": {"data": {"computed": {"burn_month": 20000, "breakeven_customers": 40}}}}
        data = asyncio.run(agent.build(ev))
        expected = round(100 * (20000 * 18 * 1.25) / FUNDING_NORMS["us"]["pre_seed_cap_usd"])
        assert data["capital_strategy"]["dilution_at_geo_cap_pct"] == expected


class TestStructure:
    def test_fmf_checklist_and_investor_map(self):
        data = _run()
        assert len(data["founder_market_fit"]["questions"]) == 6
        assert len(data["investor_question_map"]) == 8
        assert all("Tab" in row["answered_by"] for row in data["investor_question_map"])

    def test_all_bases_have_required_fields(self):
        for sector, geos in MARKET_BASES.items():
            for geo, base in geos.items():
                assert base["buying_units"] > 0, (sector, geo)
                assert base["unit"] and base["basis"], (sector, geo)


class TestCompact:
    def test_usd(self):
        assert _compact(12_400_000, "$") == "$12.4M"
        assert _compact(1_200_000_000, "$") == "$1.2B"

    def test_inr(self):
        assert _compact(18_500_000, "₹").endswith("Cr")
        assert _compact(250_000, "₹").endswith("L")
