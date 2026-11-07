"""The registry probe: statutory identifier extraction (CIN/GSTIN/UK/VAT),
RDAP domain records, EDGAR registration fields, Wikidata legal facts."""
from __future__ import annotations

import asyncio

from app.scrapers import registry
from app.scrapers.filings import registration_from_submissions
from app.scrapers.wikipedia import wikidata_company


class TestLegalIdentities:

    def test_indian_cin_found_with_source(self):
        text = ("Acme Systems Private Limited. CIN: U72900TG2014PTC094321. Registered office at Hyderabad.")
        rows = registry.legal_identities([("https://acme.io/terms", text)])
        cin = [r for r in rows if r["kind"].startswith("cin")]
        assert cin and cin[0]["value"] == "U72900TG2014PTC094321"
        assert cin[0]["source"] == "https://acme.io/terms"
        assert "CIN" in cin[0]["context"]

    def test_gstin_found(self):
        text = "GSTIN 36AAECS1234F1Z5 is shown on every invoice."
        rows = registry.legal_identities([("https://acme.io", text)])
        assert any(r["kind"].startswith("gstin") and r["value"] == "36AAECS1234F1Z5" for r in rows)

    def test_uk_number_only_near_companies_house(self):
        near = "Registered in England and Wales, company number 09876543."
        far = "Our order reference is 12345678 and the invoice total is 44000000."
        rows = registry.legal_identities([("https://uk.example/terms", near)])
        assert any(r["kind"].startswith("company no") for r in rows)
        assert registry.legal_identities([("https://uk.example/terms", far)]) == []

    def test_vat_only_near_vat_keyword(self):
        near = "VAT number: DE 123456789"
        far = "Room 44 123456789"
        assert any(r["kind"] == "vat/tax id" for r in registry.legal_identities([("s", near)]))
        assert registry.legal_identities([("s", far)]) == []

    def test_registered_office_and_incorporation(self):
        text = ("Registered office: 12 Marina Blvd, Singapore 018982. The company is "
                "incorporated in Singapore under the Companies Act 1967.")
        rows = registry.legal_identities([("https://acme.io/terms", text)])
        kinds = {r["kind"] for r in rows}
        assert "registered office" in kinds
        assert "incorporation statement" in kinds
        office = next(r for r in rows if r["kind"] == "registered office")
        assert "Marina Blvd" in office["value"]

    def test_dedupe_across_pages(self):
        text = "CIN U72900TG2014PTC094321"
        rows = registry.legal_identities([("https://a.io", text), ("https://b.io", text)])
        assert len([r for r in rows if r["kind"].startswith("cin")]) == 1


RDAP = {
    "events": [
        {"eventAction": "registration", "eventDate": "2011-06-09T00:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2027-06-09T00:00:00Z"},
    ],
    "entities": [{"roles": ["registrar"], "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "GoDaddy.com, LLC"]]]}],
    "status": ["client transfer prohibited"],
    "nameservers": [{"ldhName": "NS1.EXAMPLE.COM"}, {"ldhName": "NS2.EXAMPLE.COM"}],
}


class _RdapFetcher:
    async def try_json(self, url, *, kind="api", headers=None):
        return RDAP if "rdap.org" in url else None


class _NoneFetcher:
    async def try_json(self, url, *, kind="api", headers=None):
        return None


class TestRdap:

    def test_registration_record_parsed(self):
        out = asyncio.run(registry.rdap_domain(_RdapFetcher(), "example.com"))
        assert out["registrar"] == "GoDaddy.com, LLC"
        assert out["registered"] == "2011-06-09"
        assert out["expires"] == "2027-06-09"
        assert out["nameservers"] == ["ns1.example.com", "ns2.example.com"]

    def test_no_coverage_is_empty_not_an_error(self):
        assert asyncio.run(registry.rdap_domain(_NoneFetcher(), "example.in")) == {}


class TestEdgarRegistration:

    def test_registration_fields_extracted(self):
        reg = registration_from_submissions({
            "entityType": "operating",
            "stateOfIncorporation": "DE",
            "sic": 7372,
            "sicDescription": "Services-Prepackaged Software",
            "exchanges": ["NYSE"],
            "fiscalYearEnd": "1231",
            "formerNames": [{"name": "Old Name Inc", "from": "2010"}],
            "addresses": {"business": {"street1": "1 Main St", "city": "Wilmington", "stateOrCountry": "DE", "zip": "19801"}},
        })
        assert reg["entity_type"] == "operating"
        assert reg["state_of_incorporation"] == "DE"
        assert reg["sic_description"] == "Services-Prepackaged Software"
        assert reg["former_names"] == ["Old Name Inc"]
        assert "1 Main St" in reg["addresses"][0]

    def test_empty_payload_stays_clean(self):
        assert registration_from_submissions({}) == {}
        assert registration_from_submissions(None) == {}


class TestWikidataCompany:

    def test_labels_resolved_for_entity_claims(self):
        class F:
            async def try_json(self, url, *, kind="api", headers=None):
                if "props=labels" in url:
                    return {"entities": {"Q183": {"labels": {"en": {"value": "Germany"}}}}}
                return {"entities": {"Q42": {"claims": {
                    "P1454": [{"mainsnak": {"datavalue": {"type": "wikibase-entityid", "value": {"id": "Q183"}}}}],
                    "P571": [{"mainsnak": {"datavalue": {"type": "time", "value": {"time": "+1996-00-00T00:00:00Z"}}}}],
                }}}}
        out = asyncio.run(wikidata_company(F(), "Zoho Corporation"))
        assert out["inception"] == "1996"
        assert out["legal_form"] == "Germany"

    def test_no_title_is_empty(self):
        assert asyncio.run(wikidata_company(_NoneFetcher(), "")) == {}


class TestMentionQueries:

    def test_us_geo_gets_us_queries(self):
        qs = registry.mention_queries("Acme", "acme.com", "us")
        assert any("EDGAR" in q for q in qs)

    def test_default_gets_registry_queries(self):
        qs = registry.mention_queries("Acme", "acme.in", "india")
        assert any("MCA" in q for q in qs)
