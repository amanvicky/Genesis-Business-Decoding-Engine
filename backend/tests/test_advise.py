"""Real-time advisor: intent routing + report-grounded answers + the endpoint."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.advise import MAX_QUESTION, advise, detect_intent
from app.main import app

client = TestClient(app)


def _report() -> dict:
    return {
        "subject": "Payroll compliance automation for Indian SMBs",
        "request": {"mode": "idea", "geography": "india"},
        "sections": {
            "structural": {"data": {"verdict": "Conditional: signals exist but thin — validate with 20 user interviews before building."}},
            "features": {
                "data": {
                    "mvp_sequence": [{"order": 1, "build": "Auth + minimal identity (email OTP)"}, {"order": 2, "build": "The single core action"}],
                    "binary_roadmap": {"never_for_mvp": [{"feature": "SSO / SAML / SCIM", "gate": "after 3 enterprise procurement requests"}]},
                    "alternatives": {
                        "candidates": ["greytHR", "Zoho Payroll"],
                        "chatter": [{"text": "switched from Excel to greytHR last quarter", "url": "https://x.com/1"}],
                    },
                }
            },
            "compliance": {"data": {"checklist": [{"item": "Company incorporation (MCA)", "cost": "₹7k–₹20k", "time": "1–3 weeks"}], "critical_count": 9}},
            "pricing": {"data": {"unit_economics": {"arpa": 999, "currency": "₹", "ltv_cac_ratio": 0.52}, "tiers": []}},
            "financial": {"data": {"computed": {"burn_month": 240667, "capital_needed": 2888000, "breakeven_customers": 155, "arpa_assumption": 2499}, "team_size": 2, "runway_target_months": 12}},
            "distribution": {"data": {"channels": [{"name": "Reddit value-first participation"}, {"name": "Programmatic SEO"}], "first_ten": [{"step": 1, "action": "List 30 NAMED prospects"}]}},
            "premortem": {"data": {
                "common_failure_modes": [{"mode": "Unit economics never closed", "counter": "Write the contribution-margin-per-user equation on one page."}],
                "analogs": [{"name": "Zenefits", "root_cause": "Growth led compliance: unlicensed brokers sold insurance."}],
            }},
            "adversary": {"data": {"fatal_count": 5, "personas": [{"role": "skeptical VC", "challenges": [{"challenge": "distribution is unproven"}]}]}},
            "marketsize": {
                "data": {
                    "verdict": "MATH CLOSES COMFORTABLY: year-3 obtainable (240,000) is 416× breakeven.",
                    "verdict_tone": "green",
                    "assumptions": {"arpa": 999, "currency": "₹"},
                    "tam": {"display": "₹786.3Cr", "basis": "global base"},
                    "sam": {"display": "₹74.3Cr", "basis": "india wedge"},
                    "som_by_year": [{"year": "Year 3", "customers": 18600, "value": 223000000, "display": "₹22.3Cr", "adoption": "3.0%"}],
                    "capital_strategy": {
                        "recommended_raise": 5415008,
                        "raise_formula": "burn × 18 months × 1.25 buffer",
                        "raise_when": "NOT now. Raise after timeline gate G1.",
                        "dilution_at_geo_cap_pct": 361,
                        "dilution_formula": "raise ÷ geo-typical pre-seed cap",
                        "bootstrap_note": "keep the equity",
                    },
                }
            },
        },
    }


class TestIntentRouting:
    @pytest.mark.parametrize(("q", "intent"), [
        ("Should I raise or bootstrap?", "capital"),
        ("How much dilution at a 2M cap?", "capital"),
        ("Is my market big enough?", "market"),
        ("Who already does this?", "competitors"),
        ("What do I build first?", "mvp"),
        ("Do I need a license for payroll in India?", "compliance"),
        ("What should I charge?", "pricing"),
        ("What's my burn and runway?", "burn"),
        ("How do I get my first 10 customers?", "customers"),
        ("What kills companies like this?", "risk"),
        ("What will investors say?", "redteam"),
        ("hello", "hello"),
        ("Tell me something about the weather in Bioshock", "next"),
    ])
    def test_routing(self, q, intent):
        assert detect_intent(q) == intent


class TestGroundedAnswers:
    def test_capital_quotes_real_raise(self):
        out = advise("Should I raise?", _report())
        assert "5,415,008" in out["answer"] or "54.2L" in out["answer"] or "₹" in out["answer"]
        assert any("18 months" in b for b in out["bullets"])
        assert "marketsize" in out["open_tabs"]

    def test_competitors_name_evidence_brands(self):
        out = advise("Who already does this?", _report())
        assert "greytHR" in " ".join(out["bullets"])
        assert any("x.com/1" in b for b in out["bullets"])

    def test_mvp_lists_sequence_and_bloat(self):
        out = advise("What do I build first?", _report())
        assert any("Auth + minimal identity" in b for b in out["bullets"])
        assert any("SSO" in b and "gate" in b for b in out["bullets"])

    def test_compliance_quotes_costs(self):
        out = advise("What compliance do I need?", _report())
        assert any("MCA" in b and "₹7k–₹20k" in b for b in out["bullets"])
        assert "9" in out["answer"]  # critical count

    def test_burn_quotes_numbers(self):
        out = advise("What's my burn?", _report())
        assert any("₹2.4L" in b or "240,667" in b for b in out["bullets"])
        assert any("155" in b for b in out["bullets"])

    def test_risk_names_failure_modes_and_fatal_count(self):
        out = advise("What's my biggest risk?", _report())
        assert any("Unit economics never closed" in b for b in out["bullets"])   # mode + counter
        assert any("Zenefits" in b for b in out["bullets"])                      # matched analog
        assert any("5" in b and "FATAL" in b for b in out["bullets"])            # red-team count

    def test_next_composes_decision_list(self):
        out = advise("What now?", _report())
        assert len(out["bullets"]) >= 3
        assert any("compliance clock" in b for b in out["bullets"])  # critical_count=9 present

    def test_unknown_question_still_actionable(self):
        out = advise("Tell me about penguins", _report())
        assert out["answer"] and out["bullets"] and out["followups"]

    def test_empty_report_never_crashes(self):
        out = advise("Should I raise?", {})
        assert out["answer"]


class TestEndpoint:
    def test_stream_shape(self):
        r = client.post("/api/advise/stream", json={"question": "Should I raise?", "report": _report()})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/x-ndjson")
        events = [json.loads(ln) for ln in r.text.splitlines() if ln.strip()]
        types = [e["type"] for e in events]
        assert "log" in types and "answer" in types and "error" not in types
        answer = [e for e in events if e["type"] == "answer"][0]
        assert answer["answer"] and isinstance(answer["bullets"], list)

    def test_validation(self):
        assert client.post("/api/advise/stream", json={"report": {}}).status_code == 422
        assert client.post("/api/advise/stream", json={"question": "x" * (MAX_QUESTION + 1), "report": {}}).status_code == 422
        assert client.post("/api/advise/stream", json={"question": "hi"}).status_code == 422
