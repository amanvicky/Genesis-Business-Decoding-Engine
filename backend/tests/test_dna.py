"""Tab 14 — Product DNA: pattern matching, per-feature breakdowns, glossaries."""
from __future__ import annotations

import asyncio

from app.agents.dna import DnaAgent
from app.data.dna import BUSINESS_GLOSSARY, PATTERNS, PSYCH_GLOSSARY
from app.models import AnalyzeRequest, Evidence


def _ev(mode: str = "company", subject: str = "Notion") -> Evidence:
    req = AnalyzeRequest(mode=mode, query=subject)
    return Evidence(req=req, subject=subject)


def _agent_with_features(feats: list[dict], mode: str = "company") -> tuple[dict, str]:
    ev = _ev(mode)
    agent = DnaAgent()
    agent.sections = {"features": {"data": {"features": feats}}}
    data = asyncio.run(agent.build(ev))
    return data, agent.summarize(ev, data)


class TestFeatureBreakdown:
    def test_freemium_feature_gets_full_breakdown(self):
        data, _ = _agent_with_features([
            {"feature": "Introduced free tier with 5 projects", "detail": "", "class": "day1", "source": "github-releases"}
        ])
        assert len(data["features"]) == 1
        pat = data["features"][0]["patterns"][0]
        assert pat["name"] == "Freemium / free tier"
        assert "philosophy" in pat and pat["philosophy"]
        assert pat["psychology"] and all(p["principle"] and p["explained"] for p in pat["psychology"])
        assert pat["business"] and pat["refine"]

    def test_no_match_means_no_breakdown(self):
        data, _ = _agent_with_features([
            {"feature": "Updated the login button color", "detail": "", "class": "day1", "source": "web-snippet"}
        ])
        assert data["features"] == []

    def test_breakdown_capped_at_ten_features(self):
        feats = [{"feature": f"added free tier integration template #{i}", "detail": "", "class": "day1", "source": ""}
                 for i in range(30)]
        data, _ = _agent_with_features(feats)
        assert len(data["features"]) <= 10

    def test_max_two_patterns_per_feature(self):
        feats = [{"feature": "free tier with streaks, referrals and templates", "detail": "", "class": "day1", "source": ""}]
        data, _ = _agent_with_features(feats)
        assert len(data["features"][0]["patterns"]) <= 2


class TestProductPhilosophy:
    def test_corpus_hits_drive_headline(self):
        ev = _ev("company")
        ev.search = [
            {"title": "notion launches free tier for students", "snippet": "freemium plan announced", "url": "https://a.co"},
            {"title": "notion templates marketplace grows", "snippet": "template library expansion", "url": "https://b.co"},
        ]
        data = asyncio.run(DnaAgent().build(ev))
        assert "optimizes for" in data["product_philosophy"]["headline"]
        assert data["product_philosophy"]["top_patterns"]

    def test_offline_empty_evidence_honest_headline(self):
        data = asyncio.run(DnaAgent().build(_ev("company")))
        assert "Not enough evidence" in data["product_philosophy"]["headline"]
        assert data["product_philosophy"]["top_patterns"] == []


class TestIdeaLens:
    def test_idea_mode_gets_sector_levers(self):
        data, summary = _agent_with_features([], mode="idea")
        # default sector generic
        assert data["idea_lens"] is not None
        assert len(data["idea_lens"]["recommended"]) >= 4
        assert "Pick TWO" in data["idea_lens"]["note"]
        assert "pick two" in summary.lower()

    def test_sector_specific_lens(self):
        ev = _ev("idea", subject="payroll automation")
        ev.sector = "payroll"  # pipeline sets this
        agent = DnaAgent()
        agent.sections = {}
        data = asyncio.run(agent.build(ev))
        names = {p["name"] for p in data["idea_lens"]["recommended"]}
        assert "Enterprise controls (SSO, audit, roles)" in names

    def test_company_mode_has_no_idea_lens(self):
        data, _ = _agent_with_features([], mode="company")
        assert data["idea_lens"] is None


class TestGlossaries:
    def test_used_principles_are_defined(self):
        data, _ = _agent_with_features([
            {"feature": "daily streaks and reminders", "detail": "", "class": "day1", "source": ""}
        ])
        principles_used = {ps["principle"] for fb in data["features"] for pat in fb["patterns"] for ps in pat["psychology"]}
        defined = set(data["glossary_psych"].keys())
        missing = principles_used - defined
        assert missing == set(), f"principles used but not defined: {missing}"

    def test_glossaries_are_plain_and_real(self):
        # every definition must be a sentence with a space (not placeholder junk)
        for t, d in BUSINESS_GLOSSARY.items():
            assert len(d) > 20 and " " in d, t
        for t, d in PSYCH_GLOSSARY.items():
            assert len(d) > 20 and " " in d, t

    def test_glossary_size_reasonable(self):
        assert len(BUSINESS_GLOSSARY) >= 15
        assert len(PSYCH_GLOSSARY) >= 12
        assert len(PATTERNS) >= 12
