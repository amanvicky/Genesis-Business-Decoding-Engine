"""Multi-layer source triangulation.

Anchors every scraped result to a triangulated subject identity:
  layer 1 — Wikipedia canonical name + acronym expansion
  layer 2 — official domain consensus across search results
  layer 3 — SEC EDGAR filing match (US-listed subjects)
  layer 4 — news RSS corroboration

Results that collide with a different entity sharing the acronym ("adPEAS" vs
ADP, the payroll company) are down-weighted or sunk, and the search list is
re-ordered by relevance so downstream agents read corroborated evidence first.
"""
from __future__ import annotations

import re
from collections import Counter

from ..models import Evidence
from ..text import domain_of

AGGREGATOR_DOMAINS = {
    "en.wikipedia.org", "wikipedia.org", "linkedin.com", "crunchbase.com", "bloomberg.com",
    "youtube.com", "facebook.com", "x.com", "twitter.com", "reddit.com", "news.google.com",
    "bing.com", "duckduckgo.com", "github.com", "reuters.com", "forbes.com", "cnbc.com",
    "economictimes.com", "moneycontrol.com", "g2.com", "capterra.com", "trustpilot.com",
    "glassdoor.com", "indeed.com", "zapier.com", "similarweb.com", "sec.gov",
}

STOP_TOKENS = {"inc", "corp", "llc", "ltd", "limited", "the", "company", "plc", "group", "co"}


def is_acronym(subject: str) -> bool:
    return subject.isupper() and 2 <= len(subject) <= 6


def _expansion_from_wiki(wiki: dict, subject: str) -> list[str]:
    """Extract the acronym's expansion from the wiki summary, e.g.
    'Automatic Data Processing, Inc. (ADP) is…' → ['automatic','data','processing']."""
    text = (wiki or {}).get("summary") or ""
    if not text:
        return []
    m = re.search(rf"([A-Z][A-Za-z&.,' -]{{2,70}}?)\s*\(\s*{re.escape(subject)}\s*\)", text)
    phrase = m.group(1).strip(" .,") if m else (wiki or {}).get("title", "")
    phrase = re.sub(r"^(?:The|A|An)\s+", "", phrase, flags=re.I)
    return [t for t in (w.lower() for w in re.findall(r"[A-Za-z]{3,}", phrase)) if t not in STOP_TOKENS][:6]


async def triangulate(ev: Evidence, emit) -> None:
    subject = ev.subject
    low_subject = subject.lower()
    subj_tokens = {t for t in re.findall(r"[a-z0-9]{2,}", low_subject) if t not in STOP_TOKENS}

    # Layer 2: official-domain consensus (company mode only)
    domain_counts: Counter[str] = Counter()
    for r in ev.search:
        d = domain_of(r["url"])
        if d and d not in AGGREGATOR_DOMAINS:
            domain_counts[d] += 1
    official_domain = ""
    for d, _c in domain_counts.most_common(15):
        head = d.split(".")[0]
        if subj_tokens & set(re.findall(r"[a-z0-9]{2,}", d)):
            official_domain = d
            break

    # Layer 1: acronym expansion
    acronym = is_acronym(subject)
    expansion = _expansion_from_wiki(ev.wiki, subject) if ev.wiki else []

    # Score + re-order the search corpus
    scored: list[tuple[int, dict]] = []
    for r in ev.search:
        blob = (r.get("title", "") + " " + r.get("snippet", "")).lower()
        d = domain_of(r["url"])
        score = 0
        if official_domain and d == official_domain:
            score += 3
        if low_subject in blob:
            score += 2
        if acronym and expansion:
            hits = sum(1 for t in expansion if t in blob)
            score += 2 if hits >= 2 else (1 if hits == 1 else -3)  # collision penalty
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    ev.search[:] = [r for _s, r in scored]

    corroborated = sum(1 for s, _ in scored if s >= 3)
    layers = 1 + bool(ev.wiki) + bool(ev.identity.get("edgar")) + bool(ev.financials)

    ev.identity.update(
        {
            "official_domain": official_domain,
            "acronym": acronym,
            "expansion": expansion,
            "confidence_layers": layers,
            "corroborated_results": corroborated,
            "total_results": len(scored),
        }
    )

    if emit is not None:
        detail = f"identity='{(ev.wiki or {}).get('title', subject)}'"
        if official_domain:
            detail += f", domain={official_domain}"
        if acronym and expansion:
            detail += f", expansion='{' '.join(expansion)}'"
        detail += f" — {layers}/4 layers, {corroborated}/{len(scored)} results corroborated"
        await emit({"type": "log", "level": "agent", "agent": "recon", "msg": f"triangulation: {detail}"})
        if acronym and expansion and corroborated < 3:
            await emit({"type": "log", "level": "warn", "agent": "recon", "msg": "acronym collision risk: few results match the expansion — verify subject before acting on this decode"})
