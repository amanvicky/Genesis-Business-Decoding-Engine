"""Regression tests for the uncommitted structural-agent fixes:
word-boundary markers, web-headline exclusion from pains, headline-fragment
filter + dedupe on moat evidence.
"""
from __future__ import annotations

import asyncio

from app.agents.structural import StructuralAgent, _is_headline_fragment
from app.models import AnalyzeRequest, Evidence


def _ev(mode: str = "idea") -> Evidence:
    req = AnalyzeRequest(mode=mode, query="payroll for small teams")
    return Evidence(req=req, subject="TestCo")


def _run(ev: Evidence) -> dict:
    return asyncio.run(StructuralAgent().build(ev))


class TestPainDemandClassification:
    def test_substring_excellent_is_not_excel_pain(self):
        ev = _ev()
        ev.reddit = [{"title": "ADP Sports is rated Excellent by the fans",
                      "selftext": "The stadium review says the team is excellent this season, really.", "text": ""}]
        data = _run(ev)
        assert data["pain_points"] == []

    def test_real_excel_pain_still_matches(self):
        ev = _ev()
        ev.reddit = [{"title": "payroll in excel is killing us",
                      "selftext": "We run everything in excel and spreadsheet chaos costs us days every month.", "text": ""}]
        data = _run(ev)
        assert len(data["pain_points"]) == 1
        assert data["pain_points"][0]["source"] == "reddit"

    def test_web_headlines_never_become_pains(self):
        ev = _ev()
        ev.search = [{"title": "Why is everyone hating payroll software", "snippet": "manual spreadsheet waste"}]
        data = _run(ev)
        assert data["pain_points"] == []
        assert data["demand_triggers"] == []

    def test_demand_marker_via_hn(self):
        ev = _ev()
        ev.hn_comments = [{"text": "Looking for an alternative to ADP for a 10-person company, any tool?"}]
        data = _run(ev)
        assert len(data["demand_triggers"]) == 1

    def test_pain_takes_precedence_over_demand(self):
        ev = _ev()
        ev.reddit = [{"title": "looking for help",
                      "selftext": "I hate how painful this manual process is, absolute waste of time daily.", "text": ""}]
        data = _run(ev)
        assert len(data["pain_points"]) == 1
        assert data["demand_triggers"] == []

    def test_cap_limits(self):
        ev = _ev()
        ev.reddit = [{"title": f"hate this pain number {i}", "selftext": "x" * 80, "text": ""} for i in range(30)]
        data = _run(ev)
        assert len(data["pain_points"]) <= 12


class TestMoats:
    def test_network_effect_evidence_found(self):
        ev = _ev("company")
        ev.hn_comments = [{"text": "The marketplace connects buyers and sellers in a two-sided network."}]
        data = _run(ev)
        types = [m["type"] for m in data["moats"]]
        assert "Network effects" in types

    def test_publisher_tail_is_not_evidence(self):
        ev = _ev("company")
        ev.search = [{"title": "", "snippet": "They built compliance and license infrastructure across states Economic Times."}]
        data = _run(ev)
        assert data["moats"] == []

    def test_one_sentence_cannot_fill_two_moats(self):
        ev = _ev("company")
        sentence = ("The platform integrates with existing workflow tools and builds a proprietary data "
                    "advantage from every transaction processed through the system of record they maintain.")
        ev.hn_comments = [{"text": sentence}]
        data = _run(ev)
        evidences = [m["evidence"][:90].lower() for m in data["moats"]]
        assert len(evidences) == len(set(evidences))

    def test_keyword_boundary_no_false_network_hit(self):
        ev = _ev("company")
        # "networking event" must not trigger the "network effect" family the old
        # substring match did; note "network" alone isn't a keyword — only
        # "network effect"/"two-sided"/"marketplace" etc. are.
        ev.hn_comments = [{"text": "People met at a networking event last week downtown."}]
        data = _run(ev)
        assert data["moats"] == []


class TestVerdicts:
    def test_idea_mode_empty_evidence_is_unknown_not_weak(self):
        data = _run(_ev("idea"))
        assert data["mode"] == "idea"
        assert "UNKNOWN" in data["verdict"]
        assert "Weak public signal" not in data["verdict"]
        assert 0 <= data["verdict_score"] <= 100

    def test_company_mode_speaks_about_record(self):
        data = _run(_ev("company"))
        assert "public record" in data["verdict"]

    def test_evidence_volume_counts(self):
        ev = _ev()
        ev.search = [{"title": "a", "snippet": "b"}]
        data = _run(ev)
        assert data["evidence_volume"]["search_results"] == 1


def test_headline_fragment_direct():
    assert _is_headline_fragment("ADP expands payroll reach Economic Times")
    assert _is_headline_fragment("Big move announced, reports Reuters.")
    assert not _is_headline_fragment("A founder in Reuters regions built compliance tooling")
    assert not _is_headline_fragment("payroll costs are rising everywhere")
