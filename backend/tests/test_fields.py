"""The KB field extractor: what gets stored, what counts as drift.

The extractor's job is to be BORING — only deterministic fields, never search
order or LLM text, so two decodes of the same subject on the same day produce
the same dict and watch.py's alerts mean something.
"""
from __future__ import annotations

from app.fields import DRIFT_FIELDS, diff_fields, extract_fields


def _report(**over) -> dict:
    """A minimal finished report in the exact shape the pipeline emits."""
    sections = {
        "structural": {"id": "structural", "title": "T", "data": {"verdict_score": 34, "verdict": "measured"}},
        "adversary": {"id": "adversary", "title": "T", "data": {"fatal_count": 2, "serious_count": 4}},
        "compliance": {"id": "compliance", "title": "T", "data": {"critical_count": 3}},
        "marketsize": {"id": "marketsize", "title": "T", "data": {"verdict_tone": "green"}},
        "financial": {"id": "financial", "title": "T", "data": {"computed": {"breakeven_customers": 230, "burn_month": 12000}}},
        "publicrecord": {"id": "publicrecord", "title": "T", "data": {
            "site": {"tech": ["Shopify", "Google Tag Manager"], "emails": ["Hello@Acme.io"], "socials": {"x": "https://x.com/acme", "in": "https://linkedin.com/company/acme"}},
            "legal_identity": {"legal_name": "Acme Systems Private Limited", "registration_no": "U72900TG2014PTC094321",
                                "registered_office": "12  Marina   Blvd, Singapore", "incorporation": "incorporated 2014"},
            "domain_record": {"registrar": "GoDaddy", "registered": "2013-11-02"},
            "edgar": {"cik": 8670, "name": "ADP"},
        }},
    }
    return {"subject": "Acme", "sector": "saas", "request": {"mode": "url", "query": "https://acme.io"}, "sections": {**sections, **over}}


def _fields(**over) -> dict:
    base = extract_fields(_report())
    base.update(over)
    return base


class TestExtract:
    def test_identity_fields_come_from_the_legal_layer(self):
        f = extract_fields(_report())
        assert f["legal_name"] == "Acme Systems Private Limited"
        assert f["registration_no"] == "U72900TG2014PTC094321"
        assert f["domain_registrar"] == "GoDaddy"
        assert f["edgar_cik"] == 8670
        assert f["mode"] == "url"

    def test_sets_are_normalized_and_sorted(self):
        f = extract_fields(_report())
        # emails lowercase, tech lowercase+sorted, socials joined key:value —
        # comparison must never depend on scrape order or letter case
        assert f["emails"] == ["hello@acme.io"]
        assert f["tech"] == ["google tag manager", "shopify"]
        assert f["socials"] == ["in:https://linkedin.com/company/acme", "x:https://x.com/acme"]

    def test_registered_office_is_whitespace_collapsed(self):
        f = extract_fields(_report())
        assert f["registered_office"] == "12 marina blvd, singapore"

    def test_missing_sections_yield_none_not_crash(self):
        f = extract_fields({"subject": "Ghost", "sections": {}})
        assert f["legal_name"] is None
        assert f["signal_score"] is None
        assert f["breakeven_customers"] is None
        assert f["tech"] == []

    def test_junk_breakeven_does_not_raise(self):
        f = extract_fields(_report(financial={"id": "financial", "title": "T", "data": {"computed": {"breakeven_customers": "n/a"}}}))
        assert f["breakeven_customers"] is None


class TestDiff:
    def test_two_identical_decodes_never_drift(self):
        # THE memo-stability contract: same report twice → zero alerts
        a, b = extract_fields(_report()), extract_fields(_report())
        assert diff_fields(a, b) == []

    def test_exact_field_change_alerts(self):
        old = _fields(legal_name="Acme Systems Private Limited")
        new = _fields(legal_name="Acme Systems LLC")
        rows = diff_fields(old, new)
        assert [r["field"] for r in rows] == ["legal_name"]
        assert rows[0]["action"] == "changed"
        assert rows[0]["tab"].startswith("Tab 18")

    def test_appearing_or_vanishing_values_stay_silent(self):
        # value appearing (better scraping) or vanishing (fetch hiccup) is not
        # news — only a real value→different-value transition alerts
        assert diff_fields(_fields(legal_name=None), _fields(legal_name="Acme LLC")) == []
        assert diff_fields(_fields(legal_name="Acme Inc"), _fields(legal_name=None)) == []

    def test_set_fields_alert_both_directions(self):
        old = _fields()
        new = _fields(tech=["google tag manager", "shopify", "vercel"])  # superset: one addition
        rows = diff_fields(old, new)
        assert [(r["action"], r["new"]) for r in rows] == [("added", "vercel")]
        rows = diff_fields(new, old)
        assert [(r["action"], r["old"]) for r in rows] == [("removed", "vercel")]

    def test_score_threshold_5(self):
        assert diff_fields(_fields(signal_score=34), _fields(signal_score=37)) == []   # noise band
        rows = diff_fields(_fields(signal_score=34), _fields(signal_score=29))
        assert [r["field"] for r in rows] == ["signal_score"]

    def test_breakeven_ratio_threshold_20pct(self):
        assert diff_fields(_fields(breakeven_customers=230), _fields(breakeven_customers=260)) == []  # +13%
        rows = diff_fields(_fields(breakeven_customers=230), _fields(breakeven_customers=300))       # +30%
        assert [r["field"] for r in rows] == ["breakeven_customers"]
        # zero/None old values never divide by zero
        assert diff_fields(_fields(breakeven_customers=None), _fields(breakeven_customers=300)) == []

    def test_drift_field_set_is_bounded_and_labeled(self):
        # the one-pager's promise: ~8-12 bounded signals, each with a label + tab
        assert 8 <= len(DRIFT_FIELDS) <= 14
        for spec in DRIFT_FIELDS.values():
            assert spec["label"] and spec["tab"].startswith("Tab ")
