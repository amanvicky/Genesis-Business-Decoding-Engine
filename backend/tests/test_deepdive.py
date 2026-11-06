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
        assert "friction" in wtd["the_problem"].lower()

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

    def test_capped_at_twenty_four_and_deduped(self):
        feats = [{"feature": f"free tier integration template thing number {i}", "detail": "", "class": "day1"}
                 for i in range(40)]
        feats.append({"feature": "free tier integration template thing number 3", "detail": "", "class": "day1"})
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": feats}}}
        data = asyncio.run(agent.build(_ev()))
        assert len(data["feature_inventory"]) == 24

    def test_dedupe_prefers_row_with_real_description(self):
        agent = DeepDiveAgent()
        site_rows = [{"feature": "Databases", "detail": "relational tables with multiple views and rollups",
                      "class": "on-site", "source": "company-site", "url": "https://x", "date": ""},
                     {"feature": "databases", "detail": "", "class": "day1", "source": "web-snippet"}]
        inventory, _ = agent._inventory(site_rows, [], {}, {})
        db = next(f for f in inventory if f["feature"].lower() == "databases")
        assert "relational tables" in db["what_it_does"]

    def test_event_rows_go_to_milestones_not_inventory(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "Notion 1.0 released in August 2016", "detail": "", "date": "2016-08", "source": "wikipedia-history"},
            {"feature": "Notion acquired Skiff in February 2024", "detail": "", "date": "2024-02"},
            {"feature": "databases with multiple views", "detail": "", "class": "day1"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        names = {f["feature"] for f in data["feature_inventory"]}
        assert "databases with multiple views" in names
        assert not any("released" in n or "acquired" in n for n in names)
        ms = data["product_milestones"]
        assert len(ms) == 2
        assert any("Skiff" in m["what"] for m in ms)
        assert ms[0]["when"]  # dated milestones ranked first

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

    def test_event_feature_sentence_never_enters_inventory(self):
        # an event-like row IS a milestone now - so it can't collide with the
        # timeline inside the inventory at all
        agent = DeepDiveAgent()
        agent.sections = {
            "features": {"data": {"features": [
                {"feature": "it was first released in 2016 and is available on the web", "detail": "", "date": "2016-05"}]}},
            "timeline": {"data": {"events": [
                {"date": "2016-05", "what": "it was first released in 2016 and is available on the web"},
                {"date": "2016-06", "what": "raised seed round"}]}},
        }
        data = asyncio.run(agent.build(_ev()))
        assert data["feature_inventory"] == []
        assert len(data["product_milestones"]) == 1

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


SITE_HTML = """
<html><head><meta name="description" content="Notion is the connected workspace
for docs, projects and teams."></head><body>
<nav><h3>Log in</h3><h3>Get started</h3></nav>
<main><h1>Notion 2.0 released with connected databases</h1>
<h2>Notion AI</h2><h2>Databases &amp; views</h2><h2>Templates gallery</h2>
<h3>Sign up</h3><h3>Download the app everywhere</h3></main>
<footer><h4>careers</h4></footer></body></html>
"""


class TestSiteMining:
    def _with_fetcher(self, html_by_url: dict):
        import app.agents.deepdive as AD

        class FakeFetcher:
            offline = False

            async def try_text(self, url, **kw):
                return html_by_url.get(url)

        orig = AD.Fetcher
        AD.Fetcher = lambda ev: FakeFetcher()  # type: ignore[misc]
        try:
            ev = _ev()
            ev.wiki_domain_hint = "notion.so"
            data = asyncio.run(DeepDiveAgent().build(ev))
        finally:
            AD.Fetcher = orig
        return data

    def test_site_headings_become_on_site_features(self):
        data = self._with_fetcher({"https://notion.so": SITE_HTML})
        names = {f["feature"]: f for f in data["feature_inventory"]}
        assert "Notion AI" in names
        assert "Databases & views" in names
        assert names["Notion AI"]["kind"] == "on-site"

    def test_nav_junk_and_events_filtered(self):
        data = self._with_fetcher({"https://notion.so": SITE_HTML})
        names = {f["feature"] for f in data["feature_inventory"]}
        assert "Log in" not in names and "Sign up" not in names
        assert not any("released" in n for n in names)

    def test_meta_description_feeds_the_solution(self):
        data = self._with_fetcher({"https://notion.so": SITE_HTML})
        sol = data["what_they_do"]["the_solution"]
        assert "connected workspace" in sol

    def test_offline_skips_mining_gracefully(self):
        data, _ = _agent()
        assert data["feature_inventory"] == [] or all(
            f["kind"] != "on-site" for f in data["feature_inventory"])

    def test_domain_found_from_evidence_urls_when_hint_empty(self):
        agent = DeepDiveAgent()
        ev = _ev()
        ev.wiki_domain_hint = ""
        ev.search = [
            {"title": "s", "url": "https://news.google.com/rss/articles/notion-abc"},
            {"title": "s", "url": "https://www.notion.so/help/databases"},
            {"title": "s", "url": "https://trustpilot.com/review/notion"},
        ]
        d = agent._domain_scan(ev.search, ["notion"])
        assert d == "notion.so"

    def test_domain_scan_rejects_non_domain_urls(self):
        agent = DeepDiveAgent()
        assert agent._domain_scan([{"url": "https://user@10.0.0.5:8080/x"}], ["notion"]) == ""
        assert agent._domain_scan([{"url": "not a url"}], ["notion"]) == ""


class TestUserWords:
    def test_problem_quotes_real_voices(self):
        agent = DeepDiveAgent()
        agent.sections = {"friction": {"data": {"representative_voices": [
            {"source": "r/startups", "text": "we switched three times because the export always broke halfway",
             "url": "https://reddit/x"},
            {"source": "Trustpilot", "text": "support never answered my tickets for weeks", "url": "https://tp/x"},
            {"source": "G2", "text": "too expensive for small teams like ours", "url": "https://g2/x"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        uw = data["what_they_do"]["the_problem_in_user_words"]
        assert len(uw) == 3
        assert uw[0]["source"] == "r/startups"
        assert "export always broke" in uw[0]["quote"]

    def test_dedupes_and_drops_tiny_quotes(self):
        agent = DeepDiveAgent()
        agent.sections = {"structural": {"data": {"pain_points": [
            {"source": "HN", "text": "short", "url": ""},
            {"source": "HN", "text": "the onboarding took hours and most people quit before finishing", "url": ""},
            {"source": "HN", "text": "the onboarding took hours and most people quit before finishing", "url": ""},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        uw = data["what_they_do"]["the_problem_in_user_words"]
        assert len(uw) == 1

    def test_rating_boilerplate_and_doubled_echo_dropped(self):
        agent = DeepDiveAgent()
        agent.sections = {"friction": {"data": {"representative_voices": [
            {"source": "Trustpilot",
             "text": "Notion is rated \"Average\" with 3.1/5 on Trustpilot. Notion is rated \"Average\" with 3.1/5 on Trustpilot Trustpilot",
             "url": "https://tp"},
            {"source": "r/saas", "text": "we moved off it after the import wizard ate our whole workspace twice", "url": "https://rd"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        uw = data["what_they_do"]["the_problem_in_user_words"]
        assert len(uw) == 1
        assert "moved off it" in uw[0]["quote"]


class TestRealityPersonalization:
    def test_tiers_and_alternatives_injected(self):
        agent = DeepDiveAgent()
        agent.sections = {
            "pricing": {"data": {"tiers": [{"name": "Free"}, {"name": "Plus"}, {"name": "Business"}]}},
            "features": {"data": {"alternatives": {"candidates": ["Coda", "ClickUp"]}}},
        }
        data = asyncio.run(agent.build(_ev()))
        items = {i["area"]: i["what"] for i in data["reality_check"]["items"]}
        comp = [w for a, w in items.items() if "Competition" in a]
        assert comp and "Coda" in comp[0] and "3 tiers" in comp[0]

    def test_support_line_counts_public_voices(self):
        agent = DeepDiveAgent()
        agent.sections = {"structural": {"data": {"pain_points": [
            {"source": "HN", "text": f"complaint number {i} about the workflow being broken", "url": ""}
            for i in range(4)]}}}
        data = asyncio.run(agent.build(_ev()))
        target = next(i for i in data["reality_check"]["items"] if "Support" in i["area"])
        assert "4" in target["what"]


class TestMarketingV2:
    def test_higher_scoring_snippet_wins_and_url_kept(self):
        ev = _ev()
        ev.search = [
            {"title": "weak hit", "snippet": "they have a free tier", "url": "https://weak"},
            {"title": "strong hit", "snippet": "the free tier and free plan beat every freemium rival", "url": "https://strong"},
        ]
        data = asyncio.run(DeepDiveAgent().build(ev))
        m = next(m for m in data["marketing"]["mechanics"] if "product is the ad" in m["mechanic"].lower())
        assert "freemium rival" in m["how_they_used_it"]
        assert m["evidence_url"] == "https://strong"

    def test_current_push_from_newest_milestones(self):
        agent = DeepDiveAgent()
        agent.sections = {"features": {"data": {"features": [
            {"feature": "Notion Mail launched for gmail", "detail": "", "date": "2025-01"},
            {"feature": "Notion 1.0 released in August 2016", "detail": "", "date": "2016-08"},
            {"feature": "databases", "detail": "", "class": "day1"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        push = data["marketing"]["current_push"]
        assert push and "Mail" in push[0]

    def test_hook_from_pricing_tiers(self):
        agent = DeepDiveAgent()
        agent.sections = {"pricing": {"data": {"tiers": [{"name": "Free"}, {"name": "Plus"}]}}}
        data = asyncio.run(agent.build(_ev()))
        assert "Free" in data["marketing"]["the_hook"]





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


class TestOfficialSite:
    def test_official_site_picked_from_wiki_extlinks(self):
        from app.scrapers.wikipedia import _official_site
        links = [
            "https://twitter.com/notion",
            "https://www.notion.so/",
            "https://notion.com/pricing",
            "https://en.wikipedia.org/wiki/Notion",
        ]
        assert _official_site(links, "Notion") == "notion.com" or _official_site(links, "Notion") == "notion.so"

    def test_official_site_requires_subject_token(self):
        from app.scrapers.wikipedia import _official_site
        links = ["https://example-corp.com", "https://webflow.com"]
        assert _official_site(links, "Notion") == ""

    def test_official_site_handles_protocol_relative(self):
        from app.scrapers.wikipedia import _official_site
        assert _official_site(["//stripe.com"], "Stripe") == "stripe.com"


class TestJunkQuotes:
    def test_news_noise_never_becomes_a_quote(self):
        agent = DeepDiveAgent()
        agent.sections = {"friction": {"data": {"representative_voices": [
            {"source": "Churn posts", "text": "Trump will rally in Iowa and Kansas after initially canceling weekend trips before midterms ABC7 Los Angeles", "url": "https://x1"},
            {"source": "Churn posts", "text": "Vince Shorts RV Town Hall becomes a year of broken promises, postponements, cancellations, and delays", "url": "https://x2"},
        ]}}}
        ev = _ev(subject="Notion")
        data = asyncio.run(agent.build(ev))
        assert data["what_they_do"]["the_problem_in_user_words"] == []


SITEMAP = """<?xml version="1.0"?>
<urlset>
<url><loc>https://notion.com/help/databases</loc></url>
<url><loc>https://notion.com/help/notion-ai</loc></url>
<url><loc>https://notion.com/privacy</loc></url>
<url><loc>https://notion.com/careers</loc></url>
<url><loc>https://notion.com/help/templates</loc></url>
</urlset>"""

DB_PAGE = """<html><head><meta name="description" content="Databases let you store anything,
view it as a table, board or calendar, and roll up related pages across your workspace.">
</head><body class="page"><h1>Databases</h1><p>The heart of the product.</p>
<h2>Sign up</h2></body></html>"""

AI_PAGE = """<html><head><meta name="description" content="Notion AI answers questions,
writes drafts and autofills databases across your whole workspace, instantly.">
</head><body class="page"><h1>Notion AI</h1><p>Your assistant inside the tool.</p></body></html>"""


class TestSitemapHarvest:
    def _with_fetcher(self):
        import app.agents.deepdive as AD

        class FakeFetcher:
            offline = False

            async def try_text(self, url, **kw):
                if url.endswith("/sitemap.xml"):
                    return SITEMAP
                if url == "https://notion.com/help/databases":
                    return DB_PAGE
                if url == "https://notion.com/help/notion-ai":
                    return AI_PAGE
                if url == "https://notion.com/help/templates":
                    return AI_PAGE  # reuse
                return None

        orig = AD.Fetcher
        AD.Fetcher = lambda ev: FakeFetcher()  # type: ignore[misc]
        try:
            ev = _ev()
            ev.wiki_domain_hint = "notion.com"
            data = asyncio.run(DeepDiveAgent().build(ev))
        finally:
            AD.Fetcher = orig
        return data

    def test_feature_pages_become_inventory_with_real_descriptions(self):
        data = self._with_fetcher()
        names = {f["feature"].lower(): f for f in data["feature_inventory"]}
        assert "notion ai" in names
        assert "databases" in names
        # the text under the heading is the real description, meta is the fallback
        assert "assistant inside the tool" in names["notion ai"]["what_it_does"]
        assert "roll up related pages" in names["databases"]["what_it_does"]

    def test_junk_paths_never_fetched(self):
        data = self._with_fetcher()
        names = {f["feature"].lower() for f in data["feature_inventory"]}
        assert "privacy" not in " ".join(names) and "careers" not in " ".join(names)

    def test_all_get_on_site_kind_and_trigger(self):
        data = self._with_fetcher()
        for f in data["feature_inventory"]:
            if f["kind"] == "on-site":
                assert "current selling surface" in f["the_trigger"]


class TestFoundingStory:
    def test_founded_by_sentence_wins_with_names(self):
        ev = _ev()
        ev.wiki = {"title": "Notion", "summary": "Notion is a productivity app.",
                   "history": "The company began in 2013. Notion was founded by Ivan Zhao and Simon Last in 2013 in San Francisco.",
                   "extract": ""}
        agent = DeepDiveAgent()
        data = asyncio.run(agent.build(ev))
        assert "Ivan Zhao" in data["what_they_do"]["the_trigger"]

    def test_summary_fallback_when_no_history(self):
        ev = _ev()
        ev.wiki = {"title": "X", "summary": "X Corp was created in 2019 to fix payroll.",
                   "history": "", "extract": ""}
        agent = DeepDiveAgent()
        data = asyncio.run(agent.build(ev))
        assert "payroll" in data["what_they_do"]["the_trigger"]


class TestProblemCluster:
    def test_dominant_cluster_anchored_into_problem(self):
        agent = DeepDiveAgent()
        agent.sections = {"friction": {"data": {"complaint_clusters": [
            {"cluster": "Pricing & value", "share": "31%"},
        ]}}}
        data = asyncio.run(agent.build(_ev()))
        assert "Pricing & value" in data["what_they_do"]["the_problem"]
        assert "31%" in data["what_they_do"]["the_problem"]

    def test_idea_mode_stays_framer_without_cluster(self):
        agent = DeepDiveAgent()
        agent.sections = {"friction": {"data": {"complaint_clusters": [
            {"cluster": "Pricing & value", "share": "31%"},
        ]}}}
        ev = _ev(mode="idea")
        data = asyncio.run(agent.build(ev))
        assert "friction the current tools" in data["what_they_do"]["the_problem"]


class TestHeadingDescriptions:
    def _build(self, pages):
        import app.agents.deepdive as AD

        class FakeFetcher:
            offline = False

            async def try_text(self, url, **kw):
                if url.endswith("/sitemap.xml"):
                    return '<urlset><url><loc>https://notion.com/help/databases</loc></url></urlset>'
                return pages.get(url)

        orig = AD.Fetcher
        AD.Fetcher = lambda ev: FakeFetcher()  # type: ignore[misc]
        try:
            ev = _ev()
            ev.wiki_domain_hint = "notion.com"
            data = asyncio.run(DeepDiveAgent().build(ev))
        finally:
            AD.Fetcher = orig
        return data

    def test_text_under_heading_becomes_the_description(self):
        page = ("<html><body><h1>Databases</h1><p>Store anything as a table, board or calendar "
                "and relate pages to each other.</p><h2>Sign up</h2></body></html>")
        data = self._build({"https://notion.com/help/databases": page})
        db = next((f for f in data["feature_inventory"] if f["feature"].lower() == "databases"), None)
        assert db and "table, board or calendar" in db["what_it_does"]

    def test_sitewide_tagline_never_repeats_on_every_card(self):
        tagline = "Build custom agents and automate busywork, the AI workspace for teams."
        homepage = f'<html><head><meta name="description" content="{tagline}"></head><body><h1>Notion</h1><p>One workspace.</p></body></html>'
        page_a = f'<html><head><meta name="description" content="{tagline}"></head><body><h1>Web Clipper</h1></body></html>'
        page_b = f'<html><head><meta name="description" content="{tagline}"></head><body><h1>Notion Mail</h1></body></html>'

        import app.agents.deepdive as AD

        class FakeFetcher:
            offline = False

            async def try_text(self, url, **kw):
                if url.endswith("/sitemap.xml"):
                    return ("<urlset><url><loc>https://notion.com/help/clipper</loc></url>"
                            "<url><loc>https://notion.com/help/mail</loc></url></urlset>")
                return {"https://notion.com": homepage,
                        "https://notion.com/help/clipper": page_a,
                        "https://notion.com/help/mail": page_b}.get(url)

        orig = AD.Fetcher
        AD.Fetcher = lambda ev: FakeFetcher()  # type: ignore[misc]
        try:
            ev = _ev()
            ev.wiki_domain_hint = "notion.com"
            data = asyncio.run(DeepDiveAgent().build(ev))
        finally:
            AD.Fetcher = orig
        cards = [f for f in data["feature_inventory"] if f["feature"] in ("Web Clipper", "Notion Mail")]
        assert len(cards) == 2
        # the shared site-wide tagline is blanked - each card falls back to its own name
        for c in cards:
            assert c["what_it_does"] != tagline
