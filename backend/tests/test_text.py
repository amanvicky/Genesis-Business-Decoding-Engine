"""Text utility heuristics — pure functions, exhaustive edge cases."""
from __future__ import annotations

import pytest

from app.text import (
    classify_feature,
    clean,
    detect_sector,
    domain_of,
    extract_tiers,
    find_years,
    keyphrases,
    money_values,
    sentences,
    tokens,
)


class TestClean:
    def test_strips_tags_and_unescapes_entities_before_tag_removal(self):
        assert clean("<p>Tom &amp; Jerry&nbsp;ltd</p>") == "Tom & Jerry ltd"

    @pytest.mark.parametrize("bad", [None, "", "   "])
    def test_falsy_input(self, bad):
        assert clean(bad) == ""

    def test_collapses_whitespace(self):
        assert clean("a\n\n  b\tc") == "a b c"


class TestSentences:
    def test_splits_and_drops_short_fragments(self):
        out = sentences("Short. This sentence is definitely long enough to keep. Done!")
        assert out == ["This sentence is definitely long enough to keep."]

    def test_empty_and_none(self):
        assert sentences("") == []
        assert sentences(None) == []

    def test_no_terminator_still_kept_if_long(self):
        assert sentences("one single very long sentence without terminal punctuation here") == [
            "one single very long sentence without terminal punctuation here"
        ]


class TestTokens:
    def test_lowercases_and_requires_three_chars(self):
        assert tokens("The Big API-Server 2024 don't") == ["the", "big", "api-server", "don't"]

    def test_empty(self):
        assert tokens("") == []
        assert tokens(None) == []


class TestKeyphrases:
    def test_repeated_phrase_rises_to_top(self):
        text = ("payroll automation platform saves hours. "
                "payroll automation platform is the future. hr tools love it.")
        top = keyphrases(text, top=3)
        assert top and top[0][0] == "payroll automation"
        assert top[0][1] == 2

    def test_single_occurrence_excluded(self):
        assert keyphrases("one off payroll automation mention only once here", top=5) == []

    def test_stopword_edges_filtered(self):
        # n-grams whose first or last word is a stopword are dropped
        assert all(p.split()[0] not in ("the", "a", "of") and p.split()[-1] not in ("the", "a", "of")
                   for p, _ in keyphrases("the payroll of doom. the payroll of doom.", top=5))

    def test_empty(self):
        assert keyphrases("") == []


class TestDetectSector:
    @pytest.mark.parametrize(("text", "sector"), [
        ("payroll compliance wages and benefits", "payroll"),
        ("payments upi neobank wallet", "fintech"),
        ("marketplace ecommerce checkout cart", "commerce"),
        ("telemedicine clinic patient diagnostics", "health"),
        ("edtech course student exam tutor", "edu"),
        ("devtools sdk observability database ci/cd", "devtools"),
        ("saas crm analytics workflow subscription", "saas"),
        ("logistics fleet warehouse supply chain delivery", "logistics"),
    ])
    def test_known_sectors(self, text, sector):
        assert detect_sector(text) == sector

    def test_generic_fallback(self):
        assert detect_sector("") == "generic"
        assert detect_sector("nothing matches here xyzzy") == "generic"


class TestYearsAndMoney:
    def test_find_years_sorted(self):
        out = find_years("The company famously began operations in 1998 quietly. By 2015 annual revenue had grown substantially worldwide.")
        assert [y for y, _ in out] == [1998, 2015]

    def test_find_years_none(self):
        assert find_years("no digits of that kind here") == []

    def test_money_basic_and_per_mo(self):
        out = money_values("Pro costs $99 per month")
        assert len(out) == 1
        assert out[0]["raw"] == "$99"
        assert out[0]["per_mo"] is True

    def test_money_indian_rupee_and_thousands(self):
        out = money_values("priced at ₹1,299.50 one time")
        assert out[0]["currency"] == "₹"
        assert out[0]["amount"] == "1,299.50"
        assert out[0]["per_mo"] is False

    def test_money_dedupe_same_raw(self):
        assert len(money_values("$10 and again $10 but different $5")) == 2

    def test_money_empty(self):
        assert money_values("") == []
        assert money_values(None) == []


class TestTiersAndFeatures:
    def test_extract_tiers_order_and_price(self):
        text = "Starter costs $29. Pro plan is $99 per month. Enterprise $499 flat."
        tiers = extract_tiers(text)
        names = [t["name"] for t in tiers]
        assert names == ["Starter", "Pro", "Enterprise"]
        assert [t["price"] for t in tiers] == ["$29", "$99", "$499"]

    def test_extract_tiers_keeps_higher_price_for_same_tier(self):
        text = "Pro $50 basic. Pro $99 full."
        tiers = extract_tiers(text)
        assert len(tiers) == 1
        assert tiers[0]["price"] == "$99"

    @pytest.mark.parametrize(("name", "body", "age", "expected"), [
        ("SSO & SAML", "", None, "enterprise"),
        ("Audit log + HIPAA", "", None, "enterprise"),
        ("Mobile app", "", 3.0, "growth"),
        ("Integrations API", "", None, "day1"),  # growth kw but no age → day1
        ("Dashboard", "", 0.5, "day1"),
    ])
    def test_classify_feature(self, name, body, age, expected):
        assert classify_feature(name, body, age) == expected


class TestDomain:
    @pytest.mark.parametrize(("url", "expected"), [
        ("https://www.example.com/a?b=c", "example.com"),
        ("http://sub.domain.org", "sub.domain.org"),
        ("not a url", ""),
        ("", ""),
    ])
    def test_domain_of(self, url, expected):
        assert domain_of(url) == expected
