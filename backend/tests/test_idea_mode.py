"""Idea-mode quality: honest verdicts when no evidence was gathered, and the
evidence-linked alternatives scan ("who already does this?")."""
from __future__ import annotations

import asyncio

from app.agents.features import FeaturesAgent
from app.agents.pricing import PricingAgent
from app.agents.structural import StructuralAgent
from app.models import AnalyzeRequest, Evidence


def _ev(mode: str = "idea", subject: str = "AI meeting notes for sales teams") -> Evidence:
    req = AnalyzeRequest(mode=mode, query=subject)
    return Evidence(req=req, subject=subject)


def _structural(ev: Evidence) -> dict:
    return asyncio.run(StructuralAgent().build(ev))


def _features(ev: Evidence) -> tuple[dict, str]:
    agent = FeaturesAgent()
    data = asyncio.run(agent.build(ev))
    return data, agent.summarize(ev, data)


class TestStructuralVerdictHonesty:
    def test_empty_evidence_says_unknown_not_weak(self):
        data = _structural(_ev())
        assert "UNKNOWN" in data["verdict"]
        assert "Weak public signal" not in data["verdict"]
        assert data["verdict_score"] == 0

    def test_with_evidence_normal_verdicts_apply(self):
        ev = _ev()
        ev.reddit = [{"title": "I hate manual meeting notes", "selftext": "x" * 80, "text": ""}]
        data = _structural(ev)
        assert "UNKNOWN" not in data["verdict"]

    def test_company_mode_unaffected(self):
        data = _structural(_ev("company"))
        assert "public record" in data["verdict"]


class TestAlternativesScan:
    def test_extracts_names_from_titles(self):
        ev = _ev(subject="voice notes app")
        ev.search = [
            {"title": "Best Alternatives to Fireflies for sales calls", "snippet": "", "url": "https://a.com"},
            {"title": "Otter vs Chorus: which is better", "snippet": "", "url": "https://b.com"},
        ]
        alts = FeaturesAgent()._alternatives(ev)
        lows = {c.lower() for c in alts["candidates"]}
        assert "fireflies" in lows
        assert "otter" in lows

    def test_subject_is_never_a_candidate(self):
        ev = _ev(subject="MeetingMind")
        ev.search = [{"title": "MeetingMind alternatives and competitors 2026", "snippet": "", "url": "https://a.com"}]
        alts = FeaturesAgent()._alternatives(ev)
        assert all("meetingmind" not in c.lower() for c in alts["candidates"])

    def test_chatter_carries_source_links(self):
        ev = _ev()
        ev.search = [{"title": "Looking for a Fathom alternative", "snippet": "switched from Otter last month",
                      "url": "https://x.com/post/1"}]
        alts = FeaturesAgent()._alternatives(ev)
        assert alts["chatter"] and alts["chatter"][0]["url"] == "https://x.com/post/1"
        assert "fathom" in {c.lower() for c in alts["candidates"]}

    def test_empty_evidence_empty_scan(self):
        alts = FeaturesAgent()._alternatives(_ev())
        assert alts == {"candidates": [], "chatter": []}

    def test_only_idea_mode_gets_alternatives(self):
        data, _ = _features(_ev("idea"))
        assert "alternatives" in data
        data_c, _ = _features(_ev("company"))
        assert "alternatives" not in data_c


class TestIdeaSummaries:
    def test_features_summary_leads_with_what_founder_gets(self):
        _, summary = _features(_ev())
        assert summary.startswith("Idea mode")
        assert "canonical zero-to-one build sequence" in summary
        assert "company mode" in summary

    def test_idea_usp_honest_when_no_phrases(self):
        data, _ = _features(_ev())
        assert "Insufficient corpus" not in data["true_usp"]

    def test_pricing_summary_marks_defaults_when_no_tiers(self):
        ev = _ev()
        agent = PricingAgent()
        data = asyncio.run(agent.build(ev))
        assert "no public pricing decoded" in agent.summarize(ev, data)
        
    def test_pricing_summary_decoded_when_tiers(self):
        ev = _ev()
        ev.current_pricing = [{"name": "Starter", "price": "$29", "context": ""}]
        agent = PricingAgent()
        data = asyncio.run(agent.build(ev))
        assert "1 tier(s) decoded" in agent.summarize(ev, data)
