"""Real-time advisor, post pure-research cut: the coaching intents (capital,
burn, market sizing, first-ten customers) are gone; what's left routes to the
research tabs only. Grounded answers come from the brief's own evidence."""
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
            "pricing": {"data": {"tiers": [{"name": "Starter", "price": "₹499"}, {"name": "Pro", "price": "₹1,999"}],
                                  "psychology": [{"driver": "Anchoring", "evidence": "Pro at ₹1,999 vs Starter at ₹499"}]}},
            "premortem": {"data": {
                "common_failure_modes": [{"mode": "Distribution assumed, never tested", "counter": "Name the ten prospects before writing code."}],
                "analogs": [{"name": "Zenefits", "root_cause": "Growth led compliance: unlicensed brokers sold insurance."}],
            }},
            "adversary": {"data": {"fatal_count": 5, "personas": [{"role": "skeptical VC", "challenges": [{"challenge": "distribution is unproven"}]}]}},
        },
    }


class TestIntentRouting:
    @pytest.mark.parametrize(("q", "intent"), [
        ("Who already does this?", "competitors"),
        ("What do I build first?", "mvp"),
        ("Do I need a license for payroll in India?", "compliance"),
        ("What should I charge?", "pricing"),
        ("What kills companies like this?", "risk"),
        ("What will investors say?", "redteam"),
        ("How is the stock doing?", "markets"),
        ("hello", "hello"),
        # the coaching intents are gone — their questions fall to the
        # evidence-first default instead of a calculator
        ("Should I raise or bootstrap?", "next"),
        ("What's my burn and runway?", "next"),
        ("How do I get my first 10 customers?", "next"),
        ("Tell me something about the weather in Bioshock", "next"),
    ])
    def test_routing(self, q, intent):
        assert detect_intent(q) == intent


class TestGroundedAnswers:
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

    def test_pricing_quotes_observed_tiers_not_formulas(self):
        out = advise("What should I charge?", _report())
        assert any("₹499" in b for b in out["bullets"])
        assert any("Anchoring" in b for b in out["bullets"])
        assert not any("LTV" in b or "CAC" in b for b in out["bullets"])

    def test_pricing_absence_is_a_fact_not_advice(self):
        empty = {"subject": "GhostCo", "request": {}, "sections": {"pricing": {"data": {"tiers": []}}}}
        out = advise("What should I charge?", empty)
        assert "nothing visible" in out["answer"]
        assert not any("Recommended" in b for b in out["bullets"])

    def test_risk_names_failure_modes_and_fatal_count(self):
        out = advise("What's my biggest risk?", _report())
        assert any("Distribution assumed" in b for b in out["bullets"])         # mode + counter
        assert any("Zenefits" in b for b in out["bullets"])                      # matched analog
        assert any("5" in b and "FATAL" in b for b in out["bullets"])            # red-team count

    def test_next_composes_decision_list(self):
        out = advise("What now?", _report())
        assert len(out["bullets"]) >= 3
        assert any("launch-blocking" in b for b in out["bullets"])  # critical_count=9 present

    def test_unknown_question_still_actionable(self):
        out = advise("Tell me about penguins", _report())
        assert out["answer"] and out["bullets"] and out["followups"]

    def test_empty_report_never_crashes(self):
        out = advise("Should I raise?", {})
        assert out["answer"]

    def test_capital_question_never_invents_math(self):
        # the raise calculator is gone — the honest answer routes to the brief
        out = advise("Should I raise or bootstrap?", _report())
        assert "Recommended raise" not in out["answer"]
        assert "Dilution" not in " ".join(out["bullets"])


class TestEndpoint:
    def test_stream_shape(self):
        r = client.post("/api/advise/stream", json={"question": "What should I charge?", "report": _report()})
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
