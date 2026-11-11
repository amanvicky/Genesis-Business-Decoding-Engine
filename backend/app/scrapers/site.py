"""Primary-source site reader: when the founder gives a URL, the company's own
website becomes first-class evidence.

Everything is bounded and polite: the shared honest-UA Fetcher, hard body caps,
at most four secondary pages. No JS rendering — what's in the HTML is what we
get; sites that only speak JavaScript degrade to their meta tags, and the
report says so. The point of this module is that a company's own pages are the
most authoritative source about the company: features, pricing language, and
(the legal layer) the registration identifiers most jurisdictions force them
to print.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from urllib.parse import quote, urljoin, urlparse

from ..text import domain_of
from .client import Fetcher, safe_public_http_url, soup

_TEXT_CAP = 12000
_MAX_PAGES = 4

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

_SOCIALS: dict[str, tuple[str, ...]] = {
    "linkedin": ("linkedin.com",),
    "x": ("twitter.com", "x.com"),
    "github": ("github.com",),
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
    "youtube": ("youtube.com",),
    "discord": ("discord.gg", "discord.com"),
    "telegram": ("t.me",),
    "medium": ("medium.com",),
    "reddit": ("reddit.com",),
    "whatsapp": ("wa.me", "whatsapp.com"),
    "threads": ("threads.net",),
}

# substring fingerprints over the raw HTML — deliberately broad and cheap
_TECH: dict[str, tuple[str, ...]] = {
    "Shopify": ("cdn.shopify", "shopify"),
    "WordPress": ("wp-content", "wp-includes"),
    "Next.js": ("/_next/", "__NEXT_DATA__"),
    "Nuxt": ("/_nuxt/",),
    "React": ("data-reactroot", "react-dom"),
    "Vue": ("data-v-app", "vue.runtime"),
    "Angular": ("ng-version",),
    "Svelte": ("svelte-",),
    "Webflow": ("webflow",),
    "Wix": ("wixstatic", "wix.com"),
    "Squarespace": ("squarespace",),
    "Cloudflare": ("cdn-cgi", "cloudflare"),
    "Vercel": ("vercel",),
    "Google Tag Manager": ("googletagmanager",),
    "Google Analytics": ("google-analytics", "gtag("),
    "Meta Pixel": ("connect.facebook.net", "fbq("),
    "LinkedIn Insight": ("snap.licdn.com",),
    "Segment": ("segment.io",),
    "HubSpot": ("hs-scripts", "hubspot"),
    "Intercom": ("intercom",),
    "Crisp": ("crisp.chat",),
    "Hotjar": ("hotjar",),
    "Sentry": ("sentry",),
    "Stripe": ("js.stripe.com",),
    "Razorpay": ("checkout.razorpay.com",),
    "PayPal": ("paypal.com",),
    "Zendesk": ("zendesk",),
    "Freshdesk": ("freshdesk",),
    "Ghost": ("ghost-sdk", "content-api"),
    "Discourse": ("discourse",),
    "Klaviyo": ("klaviyo",),
    "Mailchimp": ("chimpstatic", "list-manage"),
    "Calendly": ("calendly",),
    "Typeform": ("typeform",),
}

# nav-link buckets, checked in order — legal before about so
# "/company/privacy-policy" is classified by its privacy half
_KINDS: dict[str, tuple[str, ...]] = {
    "legal": ("terms", "privacy", "legal", "imprint", "refund", "tos", "cookie", "policy"),
    "pricing": ("pricing", "plans", "subscription"),
    "contact": ("contact", "get-in-touch", "reach-us"),
    "careers": ("career", "jobs", "hiring"),
    "docs": ("docs", "documentation", "developers", "help-center", "support"),
    "trust": ("security", "trust", "compliance", "status"),
    "blog": ("blog", "news", "insights", "press"),
    "about": ("about", "company", "story", "team", "mission", "who-we-are", "our-story"),
}


def normalize_target(raw: str) -> Optional[tuple[str, str]]:
    """Validate a founder-supplied URL. Returns (canonical_url, domain) or None.

    SSRF-gated like every other fetch target — a pasted "http://10.0.0.5/admin"
    or "file:///etc/passwd" must never reach the fetcher.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw.lstrip("/")
    if not safe_public_http_url(raw):
        return None
    host = urlparse(raw).hostname or ""
    if "." not in host:
        return None
    return raw, domain_of(raw)


def text_of(html: str, cap: int = _TEXT_CAP) -> str:
    doc = soup(html)
    for tag in doc(["script", "style", "noscript", "template"]):
        tag.decompose()
    return re.sub(r"\s+", " ", doc.get_text(" ")).strip()[:cap]


_LD_FIELDS = ("legalName", "name", "alternateName", "description", "foundingDate",
              "email", "telephone", "numberOfEmployees", "slogan", "url")


def _ld_values(node: dict, out: dict) -> None:
    for k in _LD_FIELDS:
        v = node.get(k)
        if isinstance(v, str) and v.strip() and k not in out:
            out[k] = v.strip()[:300]
    addr = node.get("address")
    if addr and "address" not in out:
        if isinstance(addr, dict):
            parts = [str(addr.get(p) or "") for p in
                     ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry")]
            joined = ", ".join(p for p in parts if p)
        elif isinstance(addr, str):
            joined = addr.strip()
        else:
            joined = ""
        if joined:
            out["address"] = joined[:300]
    same = node.get("sameAs")
    if isinstance(same, list) and "sameAs" not in out:
        out["sameAs"] = [str(u) for u in same if isinstance(u, str) and u.startswith("http")][:6]


def _walk_ld(node: Any, out: dict, depth: int = 0) -> None:
    if depth > 6:
        return
    if isinstance(node, dict):
        t = node.get("@type")
        types = t if isinstance(t, list) else [t] if isinstance(t, str) else []
        orgish = any(str(x).lower() in ("organization", "corporation", "localbusiness",
                                        "onlinebusiness", "website", "webpage") for x in types)
        if orgish or "legalName" in node:
            _ld_values(node, out)
        for v in node.values():
            _walk_ld(v, out, depth + 1)
    elif isinstance(node, list):
        for v in node[:20]:
            _walk_ld(v, out, depth + 1)


def jsonld_orgs(html: str) -> list[dict]:
    """schema.org JSON-LD blocks — organizations declare legalName, foundingDate,
    registered address and sameAs links right in their own markup."""
    out: list[dict] = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html, re.I | re.S):
        try:
            data = json.loads(m.group(1).strip())
        except Exception:
            continue
        blob: dict = {}
        _walk_ld(data, blob)
        if blob:
            out.append(blob)
        if len(out) >= 3:
            break
    return out


def _classify(path: str, text: str) -> str:
    for kind, words in _KINDS.items():
        low = path.lower()
        if any(w in low for w in words):
            return kind
    low = text.lower()
    for kind, words in _KINDS.items():
        if any(w in low for w in words):
            return kind
    return ""


async def read_site(fetcher: Fetcher, url: str, domain: str) -> dict:
    """Read the homepage into a bounded profile. Never raises — a dead site
    returns {"error": ...} and the pipeline falls back to name-based research."""
    profile: dict = {"url": url, "domain": domain}
    try:
        html = await fetcher.text(url, kind="site")
    except Exception as exc:
        profile["error"] = f"{type(exc).__name__}: {exc}"[:200]
        return profile

    doc = soup(html)

    def meta(*names: str) -> str:
        for n in names:
            tag = doc.find("meta", attrs={"name": n}) or doc.find("meta", attrs={"property": n})
            if tag and tag.get("content"):
                return str(tag["content"]).strip()[:300]
        return ""

    profile["title"] = (doc.title.string if doc.title and doc.title.string else "").strip()[:200]
    profile["description"] = meta("description", "og:description")
    # og:site_name only — og:title is usually the full page headline, not the brand
    profile["og_site_name"] = meta("og:site_name")
    profile["generator"] = meta("generator")
    profile["lang"] = (doc.html.get("lang") if doc.html else "") or ""
    profile["h1"] = [h.get_text(" ", strip=True)[:160] for h in doc.find_all("h1")][:3]

    orgs = jsonld_orgs(html)
    profile["jsonld"] = orgs
    # legalName only — og:site_name is a brand, and the registry layer must not
    # dress a brand up as a registered entity name
    profile["jsonld_legal_name"] = next((o.get("legalName") for o in orgs if o.get("legalName")), "")
    profile["jsonld_name"] = profile["jsonld_legal_name"] or next(
        (o.get("name") for o in orgs if o.get("name")), "")
    profile["address"] = next((o.get("address") for o in orgs if o.get("address")), "")
    profile["founding_date"] = next((o.get("foundingDate") for o in orgs if o.get("foundingDate")), "")

    # links: same-site pages classified into buckets, external ones as socials
    links: dict[str, list[str]] = {}
    seen_links: set[str] = set()
    socials: dict[str, str] = {}
    phones: list[str] = []
    for a in doc.find_all("a", href=True):
        href = str(a["href"]).strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            if href.lower().startswith("tel:") and len(phones) < 3:
                phones.append(href[4:].strip()[:30])
            continue
        u = urljoin(url, href)
        p = urlparse(u)
        if p.scheme not in ("http", "https"):
            continue
        low = u.lower()
        if len(socials) < 10:
            for name, needles in _SOCIALS.items():
                if name not in socials and any(n in low for n in needles):
                    socials[name] = u
                    break
        host = (p.hostname or "").lower()
        dhost = domain.lower()
        if not (host == dhost or host.endswith("." + dhost) or dhost.endswith("." + host)):
            continue
        if u in seen_links:
            continue
        seen_links.add(u)
        kind = _classify(p.path or "", a.get_text(" ", strip=True))
        if kind:
            links.setdefault(kind, []).append(u)
    profile["links"] = links
    profile["socials"] = socials
    profile["phones"] = phones

    text = text_of(html)
    profile["text"] = text
    # raw html is reused by the wayback fallback to recover rewritten links;
    # it never reaches the report (agents pick explicit keys only)
    profile["_html"] = html
    emails: list[str] = []
    for m in _EMAIL_RE.finditer(text):
        e = m.group(0).lower()
        if e not in emails and not e.endswith((".png", ".jpg", ".gif", ".webp")) and len(emails) < 5:
            emails.append(e)
    profile["emails"] = emails
    addr_tag = doc.find("address")
    if addr_tag:
        t = re.sub(r"\s+", " ", addr_tag.get_text(" ", strip=True)).strip()[:300]
        if t:
            profile["address"] = profile.get("address") or t

    footer = doc.find("footer")
    profile["footer_text"] = (re.sub(r"\s+", " ", footer.get_text(" ", strip=True))[:1500] if footer else "")

    low = html.lower()
    profile["tech"] = [name for name, needles in _TECH.items() if any(n in low for n in needles)]
    return profile


async def read_pages(fetcher: Fetcher, links: dict[str, list[str]]) -> list[dict]:
    """Fetch the highest-value secondary pages (about, legal, contact, pricing) —
    legal pages are where registration identifiers legally must appear."""
    out: list[dict] = []
    fetched: set[str] = set()
    for kind in ("about", "legal", "contact", "pricing"):
        if len(out) >= _MAX_PAGES:
            break
        for u in (links.get(kind) or [])[:2]:
            if len(out) >= _MAX_PAGES:
                break
            if u in fetched or not safe_public_http_url(u):
                continue
            fetched.add(u)
            html = await fetcher.try_text(u, kind="site")
            if not html or "<html" not in html.lower():
                continue
            text = text_of(html)
            if len(text) < 80:
                continue
            out.append({"url": u, "kind": kind, "text": text})
    return out


def _unarchive(href: str, domain: str) -> Optional[str]:
    """web.archive.org rewrites every link inside a captured page into
    /web/<timestamp>/<original> — recover the original target, but only when
    it belongs to the captured site (archive banner links die here)."""
    m = re.match(r"https?://web\.archive\.org/web/[^/]+/(https?://.+)", href)
    if not m:
        return None
    orig = m.group(1).rstrip("/")
    host = urlparse(orig).hostname or ""
    d = domain.lower()
    if not (host == d or host.endswith("." + d) or d.endswith("." + host)):
        return None
    return orig


_WAYBACK_AVAILABLE = "https://archive.org/wayback/available?url={domain}"


async def read_site_from_wayback(fetcher: Fetcher, url: str, domain: str) -> Optional[dict]:
    """The live site is unreachable (down or blocking us) — read its latest
    archived copy instead. archive.org's availability API is keyless, and the
    snapshot HTML parses with exactly the same rules as a live page, so the
    brand, meta layer, JSON-LD legal facts and tech fingerprints all survive
    an outage. Returns None when the archive has nothing usable."""
    info = await fetcher.try_json(_WAYBACK_AVAILABLE.format(domain=quote(domain)), kind="archive")
    snap = ((info or {}).get("archived_snapshots") or {}).get("closest") or {}
    snap_url = str(snap.get("url") or "")
    if not snap_url:
        return None
    profile = await read_site(fetcher, snap_url, domain)
    # a junk/error capture parses into a near-empty profile — that is not a
    # usable source; require a real page body before trusting the snapshot
    if profile.get("error") or len(profile.get("text") or "") < 80:
        return None
    profile["via_wayback"] = True
    profile["url"] = url  # display the live address; the snapshot is provenance
    profile["snapshot"] = {"url": snap_url, "timestamp": str(snap.get("timestamp") or "")}
    profile["pages"] = await _archived_pages(fetcher, domain, profile.get("_html", ""))
    profile.pop("_html", None)
    return profile


async def _archived_pages(fetcher: Fetcher, domain: str, archived_html: str) -> list[dict]:
    """Fetch about/legal/contact pages of an archived site via /web/2/<url>
    (which always redirects to the nearest capture of that exact URL)."""
    links: dict[str, list[str]] = {}
    seen: set[str] = set()
    for m in re.finditer(r'href="(https?://web\.archive\.org/web/[^"]+)"', archived_html, re.I):
        orig = _unarchive(m.group(1), domain)
        if not orig or orig in seen:
            continue
        seen.add(orig)
        kind = _classify(urlparse(orig).path or "", "")
        if kind:
            links.setdefault(kind, []).append(orig)
    out: list[dict] = []
    fetched: set[str] = set()
    for kind in ("about", "legal", "contact", "pricing"):
        if len(out) >= 3:
            break
        for orig in (links.get(kind) or [])[:2]:
            if len(out) >= 3:
                break
            if orig in fetched:
                continue
            fetched.add(orig)
            html = await fetcher.try_text(f"https://web.archive.org/web/2/{orig}", kind="archive")
            if not html or "<html" not in html.lower():
                continue
            text = text_of(html)
            if len(text) < 80:
                continue
            out.append({"url": orig, "kind": kind, "text": text})
    return out


def brand_of(profile: dict) -> str:
    """Best-effort brand name. Headline titles love two traps: "Brand - tagline"
    (brand first) and "tagline | Brand" (brand last). The domain itself breaks
    the tie — a chunk that echoes the domain IS the brand. A URL is never one."""
    domain = (profile.get("domain") or "").split(".")[0].lower()

    def _affine(chunk: str) -> bool:
        return len(domain) >= 3 and domain in chunk.lower() and len(chunk) <= 40

    chunks: list[str] = []
    title = profile.get("title") or ""
    if title:
        chunks = [c.strip() for c in re.split(r"\s*[|:·]\s*|\s+[–—-]\s+", title) if c.strip()]
        for c in chunks:
            if _affine(c):
                return c
    for cand in (profile.get("og_site_name"), profile.get("jsonld_name")):
        if cand and 2 <= len(str(cand).strip()) <= 60:
            return str(cand).strip()
    head = chunks[0] if chunks else ""
    if 2 <= len(head) <= 60:
        return head
    return ""
