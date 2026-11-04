"""Founder School: curriculum integrity + personalization + teach routing."""
from __future__ import annotations

import asyncio

from app.advise import detect_intent, advise
from app.agents.school import SchoolAgent
from app.data.school import LESSONS, PHASES
from app.models import AnalyzeRequest, Evidence


def _build(**sections) -> dict:
    ev = Evidence(req=AnalyzeRequest(mode="idea", query="payroll for smb", geography="india"), subject="PayCo")
    ev.sector = "payroll"
    agent = SchoolAgent()
    agent.sections = sections
    return asyncio.run(agent.build(ev))


class TestCurriculum:
    def test_six_phases_eighteen_lessons(self):
        assert len(PHASES) == 6
        assert len(LESSONS) == 18
        all_ids = {lid for p in PHASES for lid in p["lesson_ids"]}
        assert all_ids == set(LESSONS.keys())

    def test_every_lesson_is_complete(self):
        for lid, l in LESSONS.items():
            assert len(l["lesson"]) > 200, f"{lid} lesson too thin"
            assert l["truth"] and l["action"] and l["title"], lid

    def test_terms_are_defined_in_vocabulary(self):
        # the vocabulary ships with the school, so no term goes undefined
        from app.data.dna import BUSINESS_GLOSSARY, PSYCH_GLOSSARY
        vocab = {k.lower().split(" ")[0] for k in list(BUSINESS_GLOSSARY) + list(PSYCH_GLOSSARY)}
        vocab |= {"painkiller", "vitamin", "positioning"}  # taught inline in lessons
        for lid, l in LESSONS.items():
            for t in l["terms"]:
                head = t.lower().split(" ")[0]
                assert head in vocab, f"{lid} uses undefined term: {t}"


class TestPersonalization:
    def test_money_lessons_use_report_numbers(self):
        data = _build(financial={"data": {"computed": {
            "burn_month": 240667, "breakeven_customers": 155, "capital_needed": 2888000,
            "gross_margin_assumption": 0.62, "arpa_assumption": 2499}}},
            marketsize={"data": {"assumptions": {"arpa": 2499, "currency": "₹"}}})
        personal = {}
        for p in data["phases"]:
            for l in p["lessons"]:
                if l.get("with_your_numbers"):
                    personal[l["id"]] = l["with_your_numbers"]
        assert {"the_one_equation", "cac_ltv", "oxygen", "runway_discipline"} <= set(personal)
        assert "₹2.5K" in personal["the_one_equation"] or "2,499" in personal["the_one_equation"]
        assert "155" in personal["the_one_equation"]

    def test_no_numbers_no_personalization(self):
        data = _build()
        for p in data["phases"]:
            for l in p["lessons"]:
                assert l.get("with_your_numbers") is None


class TestTeachRouting:
    def test_term_questions_route_to_teach(self):
        for q in ("what is churn", "explain CAC", "what is runway"):
            assert detect_intent(q) == "teach", q

    def test_possessive_stays_dossier_question(self):
        assert detect_intent("what's my burn and runway?") == "burn"
        assert detect_intent("what is my runway") == "burn"

    def test_teach_answer_defines_term(self):
        out = advise("what is churn", {"subject": "X", "sections": {}})
        assert "customers" in out["answer"].lower()
        assert out["open_tabs"] == ["school"]

    def test_teach_returns_lesson_for_topic(self):
        out = advise("how do startups work", {"subject": "X", "sections": {}})
        assert "A startup is not a small company" in out["answer"]
        assert any("uncomfortable truth" in b.lower() for b in out["bullets"])
