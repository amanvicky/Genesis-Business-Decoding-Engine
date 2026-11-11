"""The primary-source site reader: URL validation (SSRF-gated), HTML parsing,
JSON-LD legal facts, nav classification, tech fingerprints, page fetching."""
from __future__ import annotations

import asyncio

import pytest

from app.scrapers import site

HOME = """
<!doctype html><html lang="en"><head>
<title>Acme — the all-in-one widget platform</title>
<meta name="description" content="Acme builds widgets for serious teams.">
<meta property="og:site_name" content="Acme">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","legalName":"Acme Systems Private Limited",
 "foundingDate":"2014-04-01","email":"hello@acme.io",
 "address":{"@type":"PostalAddress","streetAddress":"12 Marina Blvd","addressLocality":"Singapore"},
 "sameAs":["https://linkedin.com/company/acme"]}
</script>
<script src="https://cdn.shopify.com/shopifycloud.js"></script>
<script src="https://www.googletagmanager.com/gtm.js"></script>
</head><body>
<h1>Widgets, finally serious</h1>
<nav>
  <a href="/about">About us</a>
  <a href="/pricing">Pricing</a>
  <a href="/terms">Terms of Service</a>
  <a href="/contact">Contact</a>
  <a href="https://twitter.com/acme">Twitter</a>
  <a href="https://evil-cdn.example.com/steal">external</a>
</nav>
<p>Contact us at hello@acme.io or call <a href="tel:+6512345678">+65 1234 5678</a>.</p>
<footer>© 2026 Acme Systems Private Limited. CIN U72900TG2014PTC094321. All rights reserved.</footer>
</body></html>
"""

ABOUT = "<html><head><title>About</title></head><body>" + ("Acme was incorporated in Singapore in 2014. " * 6) + "</body></html>"
TERMS = "<html><head><title>Terms</title></head><body>" + ("Legal terms apply. Registered office: 12 Marina Blvd, Singapore. " * 6) + "</body></html>"
PRICING = "<html><head><title>Pricing</title></head><body>" + ("Free, Pro $29, Business $99. " * 8) + "</body></html>"


class StubFetcher:
    def __init__(self, pages: dict[str, str], json_payloads: dict | None = None):
        self.pages = pages
        self.json_payloads = json_payloads or {}
        self.fetched: list[str] = []

    async def text(self, url: str, *, kind: str = "web", headers=None) -> str:
        if url not in self.pages:
            raise RuntimeError(f"no page for {url}")
        self.fetched.append(url)
        return self.pages[url]

    async def try_text(self, url: str, *, kind: str = "web", headers=None):
        self.fetched.append(url)
        return self.pages.get(url)

    async def try_json(self, url: str, *, kind: str = "api", headers=None):
        return self.json_payloads.get(url)


def _profile() -> dict:
    f = StubFetcher({
        "https://acme.io/": HOME,
        "https://acme.io/about": ABOUT,
        "https://acme.io/terms": TERMS,
        "https://acme.io/pricing": PRICING,
        # no /contact page: read_pages must skip it silently
    })

    async def run():
        p = await site.read_site(f, "https://acme.io/", "acme.io")
        p["pages"] = await site.read_pages(f, p.get("links") or {})
        return p

    return asyncio.run(run())


class TestNormalizeTarget:

    def test_bare_domain_gets_https(self):
        assert site.normalize_target("stripe.com") == ("https://stripe.com", "stripe.com")

    def test_www_and_paths_survive(self):
        url, domain = site.normalize_target("https://www.zoho.com/about/team")
        assert domain == "zoho.com"
        assert url.endswith("/about/team")

    @pytest.mark.parametrize("bad", [
        "http://localhost:3000",
        "https://192.168.0.1/admin",
        "https://127.0.0.1/",
        "ftp://example.com",
        "https://user:pass@example.com",
        "not a url at all",
        "",
        "https://intranet.local/",
    ])
    def test_ssrf_and_junk_blocked(self, bad):
        assert site.normalize_target(bad) is None


@pytest.fixture(scope="module")
def profile() -> dict:
    return _profile()


class TestReadSite:

    def test_meta_layer(self, profile):
        assert profile["title"].startswith("Acme —")
        assert profile["description"] == "Acme builds widgets for serious teams."
        assert profile["og_site_name"] == "Acme"
        assert profile["lang"] == "en"

    def test_jsonld_legal_facts(self, profile):
        orgs = profile["jsonld"]
        assert orgs and orgs[0]["legalName"] == "Acme Systems Private Limited"
        assert profile["jsonld_name"] == "Acme Systems Private Limited"
        assert profile["founding_date"] == "2014-04-01"
        assert "12 Marina Blvd" in profile["address"]

    def test_tech_fingerprints(self, profile):
        assert "Shopify" in profile["tech"]
        assert "Google Tag Manager" in profile["tech"]

    def test_nav_classification(self, profile):
        links = profile["links"]
        assert links["about"] == ["https://acme.io/about"]
        assert links["pricing"] == ["https://acme.io/pricing"]
        assert links["legal"] == ["https://acme.io/terms"]
        assert links["contact"] == ["https://acme.io/contact"]

    def test_socials_emails_phones(self, profile):
        assert profile["socials"]["x"] == "https://twitter.com/acme"
        assert "hello@acme.io" in profile["emails"]
        assert "+6512345678" in profile["phones"]

    def test_own_words_and_footer(self, profile):
        assert "Widgets, finally serious" in profile["text"]
        assert "CIN U72900TG2014PTC094321" in profile["footer_text"]

    def test_brand_prefers_og_then_title(self, profile):
        assert site.brand_of(profile) == "Acme"

    def test_brand_splits_headline_titles(self):
        # og:title-style full headlines must never become the subject
        p = {"title": "Razorpay - Best Payment Solution for Online Payments India", "domain": "razorpay.com"}
        assert site.brand_of(p) == "Razorpay"
        p2 = {"title": "Notion – the all-in-one workspace", "domain": "notion.so"}
        assert site.brand_of(p2) == "Notion"

    def test_brand_finds_domain_echo_at_title_end(self):
        # "tagline | Brand" pattern: the chunk that echoes the domain wins
        p = {"title": "Payroll, Tax, HR and HCM solutions | ADP", "domain": "adp.com"}
        assert site.brand_of(p) == "ADP"

    def test_dead_site_never_raises(self):
        f = StubFetcher({})
        profile = asyncio.run(site.read_site(f, "https://dead.example/", "dead.example"))
        assert "error" in profile
        assert site.brand_of(profile) == ""

    def test_secondary_pages_capped(self, profile):
        kinds = [p["kind"] for p in profile["pages"]]
        assert kinds == ["about", "legal", "pricing"]  # contact page missing → skipped
        assert all(len(p["text"]) <= site._TEXT_CAP for p in profile["pages"])


class TestUnarchive:
    def test_rewrites_recover_original_same_site_links(self):
        assert site._unarchive(
            "http://web.archive.org/web/20250407054911/https://acme.io/about", "acme.io"
        ) == "https://acme.io/about"
        assert site._unarchive(
            "https://web.archive.org/web/20240101id_/https://www.acme.io/x", "acme.io"
        ) == "https://www.acme.io/x"

    def test_foreign_and_plain_links_die(self):
        assert site._unarchive("http://web.archive.org/web/1/https://google.com/", "acme.io") is None
        assert site._unarchive("https://acme.io/plain-live-link", "acme.io") is None


ARCHIVED_HOME = """
<!doctype html><html lang="en"><head>
<title>Home &#8211; Acme</title>
<meta property="og:site_name" content="Acme">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","legalName":"Acme Systems Private Limited"}
</script>
<script src="https://web-static.archive.org/_static/js/bundle-playback.js"></script>
</head><body>
<h1>Widgets, finally serious</h1>
<nav>
  <a href="http://web.archive.org/web/20250407054911/https://acme.io/about">About us</a>
  <a href="http://web.archive.org/web/20250407054911/https://acme.io/terms">Terms</a>
  <a href="https://www.google.com/search?q=not-ours">search junk</a>
</nav>
<footer>© 2025 Acme Systems Private Limited.</footer>
</body></html>
"""

ARCHIVED_ABOUT = "<html><body>" + ("Acme was incorporated in Singapore in 2014. " * 5) + "</body></html>"

_WAYBACK_META = {
    "https://archive.org/wayback/available?url=acme.io": {
        "archived_snapshots": {"closest": {
            "url": "http://web.archive.org/web/20250407054911/https://acme.io/",
            "timestamp": "20250407054911",
            "status": "200",
        }}
    }
}


class TestWaybackFallback:

    def test_archived_site_reads_fully(self):
        f = StubFetcher({
            "http://web.archive.org/web/20250407054911/https://acme.io/": ARCHIVED_HOME,
            "https://web.archive.org/web/2/https://acme.io/about": ARCHIVED_ABOUT,
        }, _WAYBACK_META)
        profile = asyncio.run(site.read_site_from_wayback(f, "https://acme.io/", "acme.io"))
        assert profile["via_wayback"] is True
        assert profile["url"] == "https://acme.io/"           # display stays the live address
        assert profile["snapshot"]["timestamp"] == "20250407054911"
        assert profile["jsonld_legal_name"] == "Acme Systems Private Limited"  # legal facts survive the outage
        assert site.brand_of(profile) == "Acme"
        assert [p["kind"] for p in profile["pages"]] == ["about"]
        assert "incorporated in Singapore" in profile["pages"][0]["text"]
        assert "_html" not in profile                          # raw html never leaks

    def test_no_snapshot_is_none(self):
        f = StubFetcher({}, {"https://archive.org/wayback/available?url=dead.io": {}})
        assert asyncio.run(site.read_site_from_wayback(f, "https://dead.io/", "dead.io")) is None

    def test_broken_snapshot_is_none_not_a_crash(self):
        f = StubFetcher(
            {"http://web.archive.org/web/1/https://dead.io/": "junk-no-html"},
            {"https://archive.org/wayback/available?url=dead.io": {
                "archived_snapshots": {"closest": {"url": "http://web.archive.org/web/1/https://dead.io/", "timestamp": "1"}}}},
        )
        assert asyncio.run(site.read_site_from_wayback(f, "https://dead.io/", "dead.io")) is None
