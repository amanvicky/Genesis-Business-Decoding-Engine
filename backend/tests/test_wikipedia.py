"""Founding-year extraction and the wiki_search fallback row shape."""
import asyncio

from app.scrapers.wikipedia import _founding_year, _wikidata_inception, wiki_search


class TestFoundingYear:
    def test_year_nearest_to_the_keyword_wins_not_last(self):
        # the live bug: "Founded in 1996" and "by 2005" share a sentence —
        # the old rule took the LAST year and reported 2005
        text = "Acme was founded in 1996, and by 2005 it had 1,000 staff."
        assert _founding_year(text) == 1996

    def test_summary_without_a_year_does_not_steal_a_random_one(self):
        # live Zoho shape: founding sentence has no year; the only year in the
        # extract is an "as of 2025" user figure — None beats a wrong guess
        extract = (
            "Zoho Corporation is a technology company founded by Sridhar Vembu. "
            "It's based in Austin, Texas and Chennai, India. According to Forbes, "
            "as of 2025, its software is used by over 120 million users."
        )
        assert _founding_year(extract) is None

    def test_history_section_rescues_the_year(self):
        extract = "Zoho Corporation is a technology company founded by Sridhar Vembu."
        history = "The company was founded in 1996 by Sridhar Vembu and Tony Thomas."
        assert _founding_year(extract, history) == 1996

    def test_founded_by_then_year_pattern(self):
        assert _founding_year("It was founded by Henry Taub in 1949 in Paterson, New Jersey.") == 1949

    def test_started_sentence_takes_its_near_year(self):
        assert _founding_year("In 1949, Henry Taub started Automatic Payrolls System with his brother William.") == 1949

    def test_explicit_pattern_across_the_sentence_boundary(self):
        text = "The company was established. Its founding came in 1984."
        assert _founding_year(text) == 1984

    def test_empty_inputs(self):
        assert _founding_year("") is None
        assert _founding_year(None) is None  # type: ignore[arg-type]


class TestWikiSearch:
    def test_parses_hits_into_search_rows(self):
        class FakeFetcher:
            async def try_json(self, url):
                return {"query": {"search": [
                    {"title": "Zoho Corporation", "snippet": "<span>technology</span> company"},
                    {"title": "", "snippet": "no title, skipped"},
                ]}}

        rows = asyncio.run(wiki_search(FakeFetcher(), "Zoho"))
        assert len(rows) == 1
        assert rows[0]["title"] == "Zoho Corporation"
        assert rows[0]["url"] == "https://en.wikipedia.org/wiki/Zoho_Corporation"
        assert "technology" in rows[0]["snippet"] and "<span>" not in rows[0]["snippet"]

    def test_no_hits_returns_empty(self):
        class FakeFetcher:
            async def try_json(self, url):
                return None

        assert asyncio.run(wiki_search(FakeFetcher(), "nothing")) == []


class TestWikidataInception:
    def test_reads_p571_year(self):
        class FakeFetcher:
            async def try_json(self, url):
                return {"entities": {"Q12345": {"claims": {"P571": [
                    {"mainsnak": {"datavalue": {"value": {"time": "+1996-07-15T00:00:00Z", "precision": 11}}}},
                ]}}}}

        assert asyncio.run(_wikidata_inception(FakeFetcher(), "Zoho Corporation")) == 1996

    def test_missing_claim_returns_none(self):
        class FakeFetcher:
            async def try_json(self, url):
                return {"entities": {"Q12345": {"claims": {}}}}

        assert asyncio.run(_wikidata_inception(FakeFetcher(), "X")) is None

    def test_broken_payload_returns_none(self):
        class FakeFetcher:
            async def try_json(self, url):
                return None

        assert asyncio.run(_wikidata_inception(FakeFetcher(), "X")) is None
