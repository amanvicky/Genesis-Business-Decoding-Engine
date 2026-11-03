"""The Verdict Protocol: deterministic gate rules, decision matrix, endpoint."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.verdict import build_memo, memo_to_markdown

client = TestClient(app)


def _report(**over) -> dict:
    base = {
        "subject": "Payroll compliance automation for Indian SMBs",
        "request": {"mode": "idea", "geography": "india"},
        "sections": {
            "structural": {"data": {"verdict": "Conditional: signals exist but thin.", "verdict_score": 40}},
            "marketsize": {"data": {
                "verdict": "MATH CLOSES COMFORTABLY: year-3 obtainable is 416× breakeven.",
                "verdict_tone": "green",
                "founder_market_fit": {"questions": [
                    {"q": "Felt this problem 6+ months?", "weight": "high"},
                    {"q": "20 reachable people with this problem?", "weight": "high"},
                    {"q": "Shipped in this domain before?", "weight": "medium"},
                    {"q": "Needs relationships you lack?", "weight": "high", "invert": True},
                    {"q": "Cloneable in one sprint?", "weight": "medium", "invert": True},
                    {"q": "3 years at below-market salary?", "weight": "high"},
                ]},
            }},
            "adversary": {"data": {"fatal_count": 2}},
            "compliance": {"data": {"critical_count": 9}},
            "financial": {"data": {"computed": {"burn_month": 240667, "breakeven_customers": 155, "arpa_assumption": 2499}}},
            "distribution": {"data": {"first_ten": [{"step": 1, "action": "List 30 NAMED prospects"}]}},
        },
    }
    base["sections"].update(over)
    return base


class TestGateRules:
    def test_all_pass_full_fmf_is_go(self):
        memo = build_memo(_report(), [True, True, True, False, False, True])
        assert memo["decision"] == "GO"
        assert all(g["status"] == "pass" for g in memo["gates"])
        assert memo["founder_market_fit"]["score"] == 6

    def test_invert_questions_score_no_as_good(self):
        # answering "no" to an invert question is the GOOD answer
        memo = build_memo(_report(), [True, True, True, False, False, True])
        assert memo["founder_market_fit"]["score"] == 6

    def test_structural_unknown_is_pending_gate_not_fail(self):
        memo = build_memo(_report(structural={"data": {"verdict": "UNKNOWN — no evidence", "verdict_score": 0}}), None)
        assert memo["gates"][0]["status"] == "pending"
        assert memo["decision"] in ("PENDING", "CONDITIONAL")

    def test_measured_weak_signal_fails_problem_gate(self):
        memo = build_memo(_report(structural={"data": {"verdict": "Weak public signal", "verdict_score": 5}}), None)
        assert memo["gates"][0]["status"] == "fail"
        assert memo["decision"] == "NO-GO"
        assert "Do not write product code" in " ".join(memo["next_actions"])

    def test_market_math_red_fails(self):
        memo = build_memo(_report(marketsize={"data": {
            "verdict": "MATH DOESN'T CLOSE", "verdict_tone": "red",
            "founder_market_fit": {"questions": []}}}), None)
        assert memo["decision"] == "NO-GO"

    def test_caution_yields_conditional(self):
        memo = build_memo(_report(adversary={"data": {"fatal_count": 4}}), None)
        assert memo["gates"][2]["status"] == "caution"
        assert memo["decision"] == "CONDITIONAL"

    def test_partial_fmf_does_not_score(self):
        memo = build_memo(_report(), [True, True, True])
        assert memo["founder_market_fit"]["score"] is None
        assert memo["decision"] == "PENDING"

    def test_gates_pass_but_weak_fmf_is_conditional(self):
        memo = build_memo(_report(), [True, False, False, False, False, False])
        assert memo["decision"] == "CONDITIONAL"
        assert any("co-founder" in c or "wedge" in c for c in memo["conditions"])

    def test_go_carries_next_actions(self):
        memo = build_memo(_report(), [True, True, True, False, False, True])
        assert any("List 30 NAMED prospects" in a for a in memo["next_actions"])
        assert any("compliance clock" in a for a in memo["next_actions"])

    def test_empty_report_never_crashes(self):
        memo = build_memo({})
        assert memo["decision"] in ("PENDING", "NO-GO", "CONDITIONAL")
        assert all(g["status"] == "pending" for g in memo["gates"])


class TestMarkdown:
    def test_memo_markdown_complete(self):
        md = memo_to_markdown(build_memo(_report(), [True, True, True, False, False, True]))
        assert md.startswith("# GENESIS VERDICT — Payroll")
        assert "## Decision: **GO**" in md
        assert "## Gates" in md and "## Founder-Market Fit (6/6)" in md
        assert "## Next Actions" in md


class TestEndpoint:
    def test_happy_path(self):
        r = client.post("/api/verdict", json={"report": _report(), "fmf_answers": [True, True, True, False, False, True]})
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "GO"
        assert len(body["gates"]) == 3

    def test_validation(self):
        assert client.post("/api/verdict", json={}).status_code == 422
        assert client.post("/api/verdict", json={"report": {}}).status_code == 200  # empty report → pending memo
        assert client.post("/api/verdict", json={"report": _report(), "fmf_answers": ["yes"] * 6}).status_code == 422
        assert client.post("/api/verdict", json={"report": _report(), "fmf_answers": [True] * 99}).status_code == 422
        r = client.post("/api/verdict", content=b"{broken", headers={"Content-Type": "application/json"})
        assert r.status_code == 400

    def test_endpoint_reads_real_report_shape(self):
        # a payload straight from the pipeline's done event must work as-is
        done_report = {"subject": "X", "request": {"geography": "us"},
                       "sections": {sid: {"data": {}} for sid in
                                    ("structural", "marketsize", "adversary", "compliance", "financial", "distribution")}}
        r = client.post("/api/verdict", json={"report": done_report, "fmf_answers": [True, True, True, False, False, True]})
        assert r.status_code == 200
        assert r.json()["decision"] in ("GO", "CONDITIONAL", "PENDING", "NO-GO")
