"""Tab 17 — Company Deep-Dive: the four layers + KB integrity + advisor routing."""
from __future__ import annotations

import asyncio

from app.agents.deepdive import DeepDiveAgent
from app.data.deepdive import MARKETING_MECHANICS, REALITY_CHECKS, USER_ISSUES
from app.advise import advise, detect_intent
from app.models import AnalyzeRequest, Evidence


def _ev(mode: str = "company", subject: str = "Notion") -> Evidence:
    req = AnalyzeRequest(mode=mode, query=subject)
    return Evidence(req=req, subject=subject)


def _agent(sections: dict | None = None, mode: str = "company") -> tuple[dict, str]:
    ev = _ev(mode)
    agent = DeepDiveAgent()
    agent.sections = sections or {}
    data = asyncio.run(agent.build(ev))
    return data, agent.summarize(ev, data)


class TestWhatTheyDo:
    def test_company_mode_names_the_subject(self):
        data, _ = _agent()
        wtd = data["what_they_do"]
        assert "Notion" in wtd["the_problem"] or "Notion" in wtd["the_solution"]
        assert wtd["the_problem"] and wtd["the_solution"] and wtd["founder_logic"]

    def test_idea_mode_framed_for_the_builder(self):
        data, _ = _agent(mode="idea")
        wtd = data["what_they_do"]
        assert "dossier" in wtd["the_problem"].lower() or "friction" in wtd["the_problem"].lower()

    def test_origin_from_timeline_when_no_wiki(self):
        agent = DeepDiveAgent()
        agent.sections = {"timeline": {"data": {"events": [{"date": "2013", "what": "founded after college frustration"}]}}}
        data = asyncio.run(agent.build(_ev()))
        assert "founded after college frustration" in data["what_they_do"]["the_trigger"]

    def test_solution_names_top_features(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "block editor", "detail": "drag-and-drop pages"},
            {"feature": "team workspaces", "detail": "shared space"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        assert "block editor" in data["what_they_do"]["the_solution"]


class TestFeatureInventory:
    def test_every_entry_has_the_four_layers(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "free tier with 5 projects", "detail": "try before paying", "class": "day1"},
            {"feature": "templates gallery", "detail": "starter pages", "class": "growth"},
        ]}, },
        }
        data = asyncio.run(agent.build(_ev()))
        assert len(data["feature_inventory"]) == 2
        for f in data["feature_inventory"]:
            assert f["the_issue_before"] and f["the_trigger"] and f["the_impact"]
            assert f["what_it_does"] and f["feature"]

    def test_freemium_feature_gets_the_user_issue(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "free tier with 5 projects", "detail": "", "class": "day1"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        issue = data["feature_inventory"][0]["the_issue_before"]
        assert "sales call" in issue  # from USER_ISSUES["Freemium / free tier"]

    def test_capped_at_fourteen_and_deduped(self):
        feats = [{"feature": f"free tier integration template thing number {i}", "detail": "", "class": "day1"}
                 for i in range(40)]
        feats.append({"feature": "free tier integration template thing number 3", "detail": "", "class": "day1"})
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": feats}}}
        data = asyncio.run(agent.build(_ev()))
        assert len(data["feature_inventory"]) == 14

    def test_streaks_feature_gets_evolution_lens(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "daily streaks with reminders", "detail": "", "class": "day1"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        f = data["feature_inventory"][0]
        assert f["psych_basis"] and f["evolution"]  # social proof/loss aversion family

    def test_impact_pulled_from_dna_played_out(self):
        agent = DeepDiveAgent()
        agent.sections = {
            "features": {"data": {"features": [{"feature": "referral program", "detail": "", "class": "growth"}]}},
            "dna": {"data": {"features": [{"feature": "referral program", "patterns": [
                {"name": "Referrals & invites", "played_out": [{"kind": "growth", "text": "signups doubled in a quarter", "url": "https://x"}]},
            ]}]}},
        }
        data = asyncio.run(agent.build(_ev()))
        assert "doubled" in data["feature_inventory"][0]["the_impact"]

    def test_trigger_correlates_with_timeline_date(self):
        agent = DeepDiveAgent()
        agent.sections = {
            "features": {"data": {"features": [{"feature": "mobile app", "detail": "", "class": "growth", "date": "2016-05"}]}},
            "timeline": {"data": {"events": [{"date": "2016-04", "what": "raised Series B to expand"}]}},
        }
        data = asyncio.run(agent.build(_ev()))
        assert "Series B" in data["feature_inventory"][0]["the_trigger"]

    def test_trigger_not_circular_when_event_is_the_feature_sentence(self):
        agent = DeepDiveAgent()
        agent.sections = {
            "features": {"data": {"features": [
                {"feature": "it was first released in 2016 and is available on the web", "detail": "", "date": "2016-05"}]}},
            "timeline": {"data": {"events": [
                {"date": "2016-05", "what": "it was first released in 2016 and is available on the web"},
                {"date": "2016-06", "what": "raised seed round"}]}},
        }
        data = asyncio.run(agent.build(_ev()))
        trigger = data["feature_inventory"][0]["the_trigger"]
        assert "raised seed round" in trigger or "Shipped around 2016" in trigger

    def test_solution_line_never_ends_mid_word(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "it was first released in 2016 and is available on the web and desktop apps everywhere", "detail": ""},
            {"feature": "SSO", "detail": ""},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        sol = data["what_they_do"]["the_solution"]
        assert "everywher " not in sol and not sol.rstrip(".").endswith("everywher")
        # one product-like name + event-style entries → build-sequence framing
        assert "build sequence" in sol

    def test_event_style_evidence_gets_build_sequence_not_fake_stack(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "In March 2018, Notion 2.0 was released to the public", "detail": ""},
            {"feature": "Notion acquired Skiff in February 2024 for infrastructure", "detail": ""},
            {"feature": "Notion 1.0 released in August 2016 quickly adopted", "detail": ""},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        sol = data["what_they_do"]["the_solution"]
        assert "build sequence" in sol
        assert "The solution is a stack" not in sol

    def test_impact_drops_doubled_title_echo(self):
        agent = DeepDiveAgent()
        agent.sections = {
            "features": {"data": {"features": [{"feature": "ai agents", "detail": "", "class": "growth"}]}},
            "dna": {"data": {"features": [{"feature": "ai agents", "patterns": [
                {"name": "AI copilots & auto-magic", "played_out": [
                    {"kind": "press", "text": "Notion AI Used by Millions Notion AI Used by Millions TechCrunch", "url": "https://x"}]},
            ]}]}},
        }
        data = asyncio.run(agent.build(_ev()))
        assert data["feature_inventory"][0]["the_impact"].count("Used by Millions") == 1


class TestRealityCheck:
    def test_default_eight_observations(self):
        data, _ = _agent()
        items = data["reality_check"]["items"]
        assert len(items) == 8
        assert all(i["area"] and i["what"] for i in items)

    def test_compliance_count_injected(self):
        agent = DeepDiveAgent()
        agent.sections = {"compliance": {"data": {"critical_count": 5}}}
        data = asyncio.run(agent.build(_ev()))
        target = next(i for i in data["reality_check"]["items"] if "Compliance arrives" in i["area"])
        assert "5" in target["what"]

    def test_failure_modes_injected(self):
        agent = DeepDiveAgent()
        agent.sections = {"premortem": {"data": {"common_failure_modes": [{"mode": "nobody wants it"}]}}}
        data = asyncio.run(agent.build(_ev()))
        target = next(i for i in data["reality_check"]["items"] if "Growth" in i["area"])
        assert "nobody wants it" in target["what"]

    def test_breakeven_injected(self):
        agent = DeepDiveAgent()
        agent.sections = {"financial": {"data": {"computed": {"breakeven_customers": 420}}}}
        data = asyncio.run(agent.build(_ev()))
        target = next(i for i in data["reality_check"]["items"] if "Cash" in i["area"])
        assert "420" in target["what"]


class TestMarketing:
    def test_mechanics_detected_from_snippets(self):
        ev = _ev()
        ev.search = [
            {"title": "notion launches free tier", "snippet": "the free plan includes unlimited pages for personal use", "url": "https://a"},
            {"title": "notion vs evernote comparison", "snippet": "notion alternative to evernote is the best pick", "url": "https://b"},
        ]
        data = asyncio.run(DeepDiveAgent().build(ev))
        names = {m["mechanic"] for m in data["marketing"]["mechanics"]}
        assert any("freemium" in n.lower() or "product is the ad" in n.lower() for n in names)
        assert any("comparative" in n.lower() or "category" in n.lower() for n in names)

    def test_mechanic_fields_are_complete(self):
        ev = _ev()
        ev.search = [{"title": "t", "snippet": "sign up for the free trial today", "url": "https://a"}]
        data = asyncio.run(DeepDiveAgent().build(ev))
        m = data["marketing"]["mechanics"][0]
        assert m["mechanic"] and m["signals"] and m["what_they_promote"] and m["psych"]

    def test_channel_ranking_from_distribution(self):
        agent = DeepDiveAgent()
        agent.sections = {"distribution": {"data": {"channels": [
            {"name": "Community loops", "score": 9}, {"name": "SEO content", "score": 7},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        assert data["marketing"]["channel_ranking"] == ["Community loops", "SEO content"]

    def test_dna_confirmation_flag(self):
        agent = DeepDiveAgent()
        agent.sections = {"dna": {"data": {"product_philosophy": {"top_patterns": [{"name": "Search real estate (SEO engine)"}]}}}}
        data = asyncio.run(agent.build(_ev()))
        # dna cross-ref alone is enough to surface the mechanic
        assert any(m["dna_confirmed"] for m in data["marketing"]["mechanics"])

    def test_hook_falls_back_to_core_workflow(self):
        data, _ = _agent()
        assert data["marketing"]["the_hook"]  # always a string, never None


class TestKBIntegrity:
    def test_mechanics_are_concrete_not_filler(self):
        assert len(MARKETING_MECHANICS) >= 10
        for m in MARKETING_MECHANICS:
            assert m["kw"] and m["how"] and m["promotes"] and m["psych"], m["name"]
            assert "digital marketing" not in m["how"].lower()
            assert len(m["how"]) > 80, m["name"]

    def test_reality_checks_are_observations(self):
        assert len(REALITY_CHECKS) >= 8
        for rc in REALITY_CHECKS:
            assert rc["area"] and len(rc["what"]) > 60, rc["area"]

    def test_user_issues_cover_dna_patterns(self):
        from app.data.dna import PATTERNS
        assert len(USER_ISSUES) >= 12
        names = {p["name"] for p in PATTERNS}
        missing = {n for n in USER_ISSUES if n not in names}
        assert missing == set(), f"USER_ISSUES keys not matching DNA patterns: {missing}"


class TestSummary:
    def test_summary_counts_the_layers(self):
        data, summary = _agent()
        assert "14" in summary or str(len(data["feature_inventory"])) in summary
        assert "8" in summary
        assert "reality" in summary.lower() and "marketing" in summary.lower()


class TestAdvisorRouting:
    def test_marketing_question_routes_to_deepdive(self):
        assert detect_intent("how did they market the company?") == "deepdive"
        assert detect_intent("what is their marketing?") == "deepdive"

    def test_what_do_they_do_routes_to_deepdive(self):
        assert detect_intent("what does this company do?") == "deepdive"

    def test_reality_check_routes_to_deepdive(self):
        assert detect_intent("what is the reality check here?") == "deepdive"

    def test_feature_breakdown_routes_to_deepdive(self):
        assert detect_intent("give me the feature breakdown") == "deepdive"

    def test_handler_answers_from_the_section(self):
        report = {"subject": "Notion", "sections": {"deepdive": {"data": {
            "what_they_do": {"the_problem": "P", "the_solution": "S", "the_trigger": "T", "founder_logic": "F"},
            "feature_inventory": [{"feature": "free tier", "the_issue_before": "sales call", "the_impact": "growth"}],
            "reality_check": {"items": [{"area": "Churn is silent", "what": "users leave quietly"}]},
            "marketing": {"mechanics": [{"mechanic": "Press & launch moments", "signals": ["launch"],
                                          "what_they_promote": "the milestone", "psych": "authority"}],
                          "the_hook": "the free tier", "channel_ranking": ["Community loops"]},
        }}}}
        for q in ("how did they market it?", "what is the reality check?", "feature breakdown please", "what do they do?"):
            out = advise(q, report)
            assert out["bullets"] and "deepdive" in out["open_tabs"], q
        assert "Press" in advise("how did they market it?", report)["bullets"][0]

    def test_handler_without_section_is_honest(self):
        out = advise("what does this company do?", {"subject": "x", "sections": {}})
        assert "re-run" in out["answer"].lower()
