"""Request validation and Evidence corpus logic (incl. the sentence-dedupe change)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import AnalyzeRequest, Evidence


def _req(**over):
    base = {"query": "ADP payroll"}
    base.update(over)
    return AnalyzeRequest(**base)


class TestAnalyzeRequestValidation:
    def test_defaults(self):
        r = AnalyzeRequest(query="ab")
        assert r.mode.value == "idea"
        assert r.geography.value == "global"
        assert r.team_size == 3
        assert r.runway_target_months == 12
        assert r.include_darkweb is True
        assert r.context is None

    @pytest.mark.parametrize("bad", ["", "x", "a" * 301])
    def test_query_length_bounds(self, bad):
        with pytest.raises(ValidationError):
            _req(query=bad)

    def test_query_upper_bound_ok(self):
        assert _req(query="a" * 300).query == "a" * 300

    @pytest.mark.parametrize("bad_mode", ["enterprise", "Company", "", 123])
    def test_mode_enum_strict(self, bad_mode):
        with pytest.raises(ValidationError):
            _req(mode=bad_mode)

    @pytest.mark.parametrize("bad_geo", ["europe", "US", "INDIA", 42])
    def test_geography_enum_strict(self, bad_geo):
        with pytest.raises(ValidationError):
            _req(geography=bad_geo)

    @pytest.mark.parametrize("bad_team", [0, -1, 201])
    def test_team_size_bounds(self, bad_team):
        with pytest.raises(ValidationError):
            _req(team_size=bad_team)

    @pytest.mark.parametrize("bad_runway", [0, 61, -5])
    def test_runway_bounds(self, bad_runway):
        with pytest.raises(ValidationError):
            _req(runway_target_months=bad_runway)

    def test_context_upper_bound(self):
        with pytest.raises(ValidationError):
            _req(context="x" * 2001)
        assert _req(context="x" * 2000).context == "x" * 2000

    def test_unknown_fields_ignored(self):
        # documents current behavior: pydantic default ignores extras
        r = _req(junk_field="ignored")
        assert not hasattr(r, "junk_field")


class TestUrlMode:
    def test_bare_domain_normalized_to_https(self):
        r = _req(mode="url", query="stripe.com")
        assert r.query == "https://stripe.com"

    def test_explicit_url_preserved(self):
        r = _req(mode="url", query="https://www.zoho.com/about")
        assert r.query == "https://www.zoho.com/about"

    @pytest.mark.parametrize("bad", ["http://localhost:3000", "https://192.168.1.5/", "justonechunk"])
    def test_url_mode_rejects_non_public_targets(self, bad):
        with pytest.raises(ValidationError):
            _req(mode="url", query=bad)

    def test_url_mode_still_enforces_min_length(self):
        with pytest.raises(ValidationError):
            _req(mode="url", query="a")


class TestEvidenceSources:
    def test_add_source_dedupes_and_skips_empty(self):
        e = Evidence(req=_req(), subject="x")
        e.add_source("https://a.com", kind="web", title="A")
        e.add_source("https://a.com", kind="hn", title="dup")
        e.add_source("", kind="web")
        assert len(e.sources) == 1
        assert e.sources[0].kind == "web"

    def test_sources_land_in_report(self):
        e = Evidence(req=_req(), subject="x")
        e.add_source("https://a.com")
        assert e.sources[0].url == "https://a.com"


class TestSnippetPool:
    def test_empty_evidence(self):
        e = Evidence(req=_req(), subject="x")
        assert e.snippet_pool() == ""

    def test_dedupes_identical_sentences_across_sources(self):
        e = Evidence(req=_req(), subject="x")
        s = {"title": "Same story here", "snippet": "First sentence goes here. Second sentence follows."}
        e.search = [s]
        e.hn_comments = [{"text": "First sentence goes here. Second sentence follows."}]
        pool = e.snippet_pool().lower()
        assert pool.count("first sentence goes here") == 1

    def test_collapses_back_to_back_phrase_repeat(self):
        e = Evidence(req=_req(), subject="x")
        e.search = [{"title": "", "snippet": "PNC and ADP integrate payroll tools PNC and ADP integrate payroll tools."}]
        pool = e.snippet_pool().lower()
        assert pool.count("pnc and adp integrate payroll tools") == 1

    def test_truncates_to_limit(self):
        e = Evidence(req=_req(), subject="x")
        e.search = [{"title": "t", "snippet": "word " * 5000}]
        assert len(e.snippet_pool(limit=500)) <= 500

    def test_case_insensitive_dedupe_key(self):
        e = Evidence(req=_req(), subject="x")
        e.search = [{"title": "Header", "snippet": "The Quick Brown Fox jumps over the lazy dog today."}]
        e.reddit = [{"title": "", "selftext": "The quick brown fox jumps over the lazy dog today.", "text": ""}]
        pool = e.snippet_pool()
        assert pool.lower().count("the quick brown fox") == 1

    def test_repeat_collapse_leaves_short_repeats_alone(self):
        # the regex needs >=5 words; short stammers must survive untouched
        e = Evidence(req=_req(), subject="x")
        e.search = [{"title": "", "snippet": "very very good product"}]
        assert "very very good product" in e.snippet_pool()
