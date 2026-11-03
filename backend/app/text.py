"""Text utilities: cleaning, n-gram keyphrase mining, money/year/date extraction.

Pure heuristics, zero dependencies beyond the standard library — this is what
lets Genesis produce real analysis with no paid APIs and no required LLM.
"""
from __future__ import annotations

import html
import re
from collections import Counter
from urllib.parse import urlparse

WS = re.compile(r"\s+")
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-3]\d)\b")
MONEY_RE = re.compile(r"(?P<cur>[$₹€£])\s?(?P<amt>\d{1,3}(?:[,.]\d{3})*(?:\.\d{1,2})?|\d+)\s?(?P<unit>k|m|cr|lakh|lpa)?", re.I)
PER_MO_RE = re.compile(r"(/|per\s)\s?(mo|month|mth|user|seat|employee|member)", re.I)

STOPWORDS = set(
    """a an and are as at be been but by can could for from has have how i in into is it its of on or
    our out over said same than that the their them then there these they this to was we were what
    when which who will with you your also more most new not no now one two all any get got just like
    make made may might much need only should so some still such take than them use used using very
    via want way well about after before being between did do does does down during each even ever
    first get given going great group here him his if into keep know less let ll me my off once other
    per put re see seem seen set she show since so take thing things think through too take us use
    vs while within without work would year years company companies business customers users product
    price prices pricing plan plans""".split()
)

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "payroll": ["payroll", "hr ", "human resource", "benefits", "peo", "eor", "compliance", "wages", "salary"],
    "fintech": ["fintech", "payment", "payments", "lending", "loan", "bank", "banking", "wallet", "upi", "neobank", "credit", "insurance", "insurtech", "kyc"],
    "commerce": ["e-commerce", "ecommerce", "marketplace", "retail", "d2c", "shop", "store", "cart", "checkout"],
    "health": ["health", "clinic", "medical", "telemedicine", "pharmacy", "patient", "diagnostic", "mental"],
    "edu": ["edtech", "education", "learning", "course", "school", "tutor", "exam", "student"],
    "devtools": ["developer", "devtools", "api", "ci/cd", "infrastructure", "observability", "database", "sdk", "code"],
    "saas": ["saas", "b2b", "dashboard", "analytics", "crm", "workflow", "automation", "platform", "subscription"],
    "logistics": ["logistics", "delivery", "shipping", "supply chain", "fleet", "warehouse"],
}


def clean(text: str | None) -> str:
    if not text:
        return ""
    # Unescape entities (&nbsp; &amp; …) BEFORE stripping tags, or tokens like
    # "nbsp" leak into the keyphrase/USP mining.
    return WS.sub(" ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.strip()) > 25]


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", (text or "").lower())]


def keyphrases(text: str, top: int = 12, ngrams: tuple[int, ...] = (2, 3)) -> list[tuple[str, int]]:
    """Most frequent n-gram phrases across a text corpus (distinctiveness proxy)."""
    toks = tokens(text)
    counts: Counter[str] = Counter()
    for n in ngrams:
        for i in range(len(toks) - n + 1):
            gram = toks[i : i + n]
            if gram[0] in STOPWORDS or gram[-1] in STOPWORDS:
                continue
            phrase = " ".join(gram)
            if all(w in STOPWORDS for w in gram):
                continue
            counts[phrase] += 1
    return [(p, c) for p, c in counts.most_common(top * 3) if c >= 2][:top]


def detect_sector(text: str) -> str:
    low = " " + (text or "").lower() + " "
    best, score = "generic", 0
    for sector, kws in SECTOR_KEYWORDS.items():
        s = sum(low.count(k) for k in kws)
        if s > score:
            best, score = sector, s
    return best


def find_years(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for s in sentences(text):
        for m in YEAR_RE.finditer(s):
            out.append((int(m.group(1)), s.strip()))
    return sorted(out, key=lambda x: x[0])


def money_values(text: str) -> list[dict]:
    """Extract currency amounts with a small window of context (for pricing pages)."""
    out: list[dict] = []
    seen: set[str] = set()
    for m in MONEY_RE.finditer(text or ""):
        amt = m.group("amt")
        unit = (m.group("unit") or "").lower()
        raw = m.group("cur") + amt + (unit if unit else "")
        if raw in seen:
            continue
        seen.add(raw)
        start = max(0, m.start() - 50)
        out.append(
            {
                "raw": raw,
                "currency": m.group("cur"),
                "amount": amt,
                "per_mo": bool(PER_MO_RE.search(text[m.end() : m.end() + 18])),
                "context": clean(text[start : m.end() + 50]),
            }
        )
    return out


def domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc.removeprefix("www.")
    except Exception:
        return ""


TIER_WORDS = ["free", "starter", "basic", "essential", "standard", "growth", "pro", "premium", "plus", "team", "business", "scale", "enterprise", "ultimate"]


def extract_tiers(pricing_text: str) -> list[dict]:
    """Heuristic tier detection: a tier word followed (within a window) by a price."""
    text = clean(pricing_text)
    low = text.lower()
    tiers: dict[str, dict] = {}
    for m in MONEY_RE.finditer(text):
        window = low[max(0, m.start() - 120) : m.start()]
        for w in reversed(TIER_WORDS):
            idx = window.rfind(w)
            if idx != -1 and (idx == 0 or not window[idx - 1].isalpha()):
                name = w.capitalize()
                raw = m.group("cur") + m.group("amt")
                existing = tiers.get(name)
                if existing is None or _amt(raw) > _amt(existing["price"]):
                    tiers[name] = {"name": name, "price": raw, "context": clean(text[max(0, m.start() - 60) : m.end() + 90])}
                break
    ordered = [tiers[w.capitalize()] for w in TIER_WORDS if w.capitalize() in tiers]
    return ordered[:6]


def _amt(raw: str) -> float:
    # str() coercion: scraped prices occasionally arrive as numbers, and the
    # regex cleanup below assumes a string.
    digits = re.sub(r"[^\d.]", "", str(raw).replace(",", ""))
    try:
        return float(digits)
    except ValueError:
        return 0.0


def classify_feature(name: str, body: str, years_old: float | None) -> str:
    """Bucket a feature into day1 / growth / enterprise by keywords and age."""
    text = (name + " " + (body or "")).lower()
    enterprise = any(k in text for k in ["sso", "saml", "scim", "audit log", "soc 2", "soc2", "hipaa", "gdpr", "dedicated", "enterprise", "white glove", "on-premise", "self-hosted", "admin console", "role-based", "sandbox", "sla", "custom contract", "invoice billing", "data residency"])
    growth = any(k in text for k in ["integration", "api", "mobile", "template", "automation", "report", "analytics", "billing", "team", "collaboration", "notification", "workflow", "marketplace", "white label"])
    if enterprise:
        return "enterprise"
    if years_old is not None and years_old > 2.5 and not growth:
        return "growth"
    if growth and years_old is not None and years_old > 1.5:
        return "growth"
    return "day1"
