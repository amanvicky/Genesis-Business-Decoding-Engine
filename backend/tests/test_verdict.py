"""Verdict Protocol v2: research-only gates (signal + fatals), no FMF quiz."""
from __future__ import annotations

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
            "adversary": {"data": {"fatal_count": 2}},
            "compliance": {"data": {"critical_count": 9}},
            "features": {"data": {"binary_roadmap": {"build_now": [{"feature": "The intake form"}]}}},
        },
    }
    base["sections"].update(over)
    return base


class TestGateRules:
    def test_all_pass_is_go(self):
        memo = build_memo(_report(), None)
        assert memo["decision"] == "GO"
        assert all(g["status"] == "pass" for g in memo["gates"])

    def test_structural_unknown_is_pending_not_fail(self):
        memo = build_memo(_report(structural={"data": {"verdict": "UNKNOWN — no evidence", "verdict_score": 0}}), None)
        assert memo["gates"][0]["status"] == "pending"
        assert memo["decision"] == "PENDING"
        assert "re-run the decode online" in memo["rationale"].lower()

    def test_measured_weak_signal_fails_problem_gate(self):
        memo = build_memo(_report(structural={"data": {"verdict": "Weak public signal", "verdict_score": 5}}), None)
        assert memo["gates"][0]["status"] == "fail"
        assert memo["decision"] == "NO-GO"
        assert "Do not write product code" in " ".join(memo["next_actions"])

    def test_fatal_burst_fails_death_gate(self):
        memo = build_memo(_report(adversary={"data": {"fatal_count": 7}}), None)
        assert memo["gates"][1]["status"] == "fail"
        assert memo["decision"] == "NO-GO"

    def test_caution_yields_conditional(self):
        memo = build_memo(_report(adversary={"data": {"fatal_count": 4}}), None)
        assert memo["gates"][1]["status"] == "caution"
        assert memo["decision"] == "CONDITIONAL"

    def test_fmf_answers_are_accepted_and_ignored(self):
        # the quiz died with the marketsize tab — old callers must not break
        memo = build_memo(_report(), [True, False, True])
        assert memo["founder_market_fit"] == {"score": None, "total": 0, "rows": []}
        assert memo["decision"] == "GO"

    def test_go_carries_next_actions(self):
        memo = build_memo(_report(), None)
        assert any("The intake form" in a for a in memo["next_actions"])
        assert any("compliance clock" in a for a in memo["next_actions"])

    def test_empty_report_never_crashes(self):
        memo = build_memo({})
        assert memo["decision"] == "PENDING"
        assert all(g["status"] == "pending" for g in memo["gates"])

    def test_protocol_version_2(self):
        assert build_memo(_report(), None)["protocol_version"] == 2


class TestMarkdown:
    def test_memo_markdown_complete(self):
        md = memo_to_markdown(build_memo(_report(), None))
        assert md.startswith("# GENESIS VERDICT — Payroll")
        assert "## Decision: **GO**" in md
        assert "## Gates" in md and "## Next Actions" in md
        assert "Founder-Market Fit" not in md  # the quiz is gone from the memo too


class TestEndpoint:
    def test_happy_path(self):
        r = client.post("/api/verdict", json={"report": _report()})
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "GO"
        assert len(body["gates"]) == 2

    def test_validation(self):
        assert client.post("/api/verdict", json={}).status_code == 422
        assert client.post("/api/verdict", json={"report": {}}).status_code == 200  # empty report → pending memo
        r = client.post("/api/verdict", content=b"{broken", headers={"Content-Type": "application/json"})
        assert r.status_code == 400

    def test_endpoint_reads_real_report_shape(self):
        # a payload straight from the pipeline's done event must work as-is
        done_report = {"subject": "X", "request": {"geography": "us"},
                       "sections": {sid: {"data": {}} for sid in ("structural", "adversary", "compliance", "features")}}
        r = client.post("/api/verdict", json={"report": done_report})
        assert r.status_code == 200
        assert r.json()["decision"] in ("GO", "CONDITIONAL", "PENDING", "NO-GO")
