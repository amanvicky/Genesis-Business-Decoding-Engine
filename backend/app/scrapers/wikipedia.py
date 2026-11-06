"""Wikipedia: company genesis data — summary, history section, founding year."""
from __future__ import annotations

import re
from urllib.parse import quote, urlparse

from .client import Fetcher
from ..text import clean, sentences

API = "https://en.wikipedia.org/w/api.php"


async def company_brief(fetcher: Fetcher, subject: str) -> dict:
    search = await fetcher.try_json(
        f"{API}?action=query&list=search&srsearch={quote(subject)}&srlimit=5&format=json&origin=*"
    )
    hits = ((search or {}).get("query", {}) or {}).get("search", [])
    if not hits:
        return {}

    # Only a page actually titled with the subject is evidence ABOUT it. Pages
    # that merely mention it (founders, partners, comparison lists) poison every
    # downstream section — e.g. "Razorpay" resolving to founder Kunal Shah's
    # biography. No direct article → no wiki data; other sources carry the decode.
    token = (subject.lower().split() or [""])[0]
    hits = [h for h in hits if token in h["title"].lower()]
    if not hits:
        return {}

    # Skip disambiguation pages ("X may refer to:") — for short acronyms they
    # otherwise outrank the actual company page and poison every downstream section.
    def is_disambig(hit: dict) -> bool:
        blob = (hit.get("title", "") + " " + hit.get("snippet", "")).lower()
        return "may refer to" in blob or "disambiguation" in hit.get("title", "").lower()

    ranked = sorted(hits, key=lambda h: (is_disambig(h), 0 if token in h["title"].lower() else 1))
    picked = None
    extract = ""
    for candidate in ranked[:3]:
        if is_disambig(candidate) and not all(is_disambig(h) for h in ranked[:3]):
            continue
        picked = candidate["title"]
        extract_resp = await fetcher.try_json(
            f"{API}?action=query&prop=extracts&explaintext=1&titles={quote(picked)}&format=json&origin=*"
        )
        pages = ((extract_resp or {}).get("query", {}) or {}).get("pages", {})
        for _, page in pages.items():
            extract = page.get("extract", "")
            break
        if "may refer to:" not in extract[:300].lower():
            break
        picked, extract = None, ""
    if not picked:
        return {}

    summary = await fetcher.try_text(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(picked.replace(' ', '_'))}",
        kind="wiki",
    )
    import json

    try:
        summary_json = json.loads(summary) if summary else {}
    except Exception:
        summary_json = {}
    extract = _strip_headers(extract)

    history = _slice_section(extract, ("History", "Founding", "Early history", "Background"))
    founded = _founding_year(extract or summary_json.get("extract", ""), history)
    if founded is None:
        # The infobox is stripped from plaintext extracts — Zoho's article says
        # "founded by Sridhar Vembu" and never prints the year. Wikidata carries
        # it structured (P571 inception) on the same keyless API.
        founded = await _wikidata_inception(fetcher, picked)

    website = ""
    ext = await fetcher.try_json(
        f"{API}?action=query&prop=extlinks&titles={quote(picked)}&ellimit=30&format=json&formatversion=2&origin=*"
    )
    links: list[str] = []
    try:
        pages = ((ext or {}).get("query", {}) or {}).get("pages", [])
        if pages and isinstance(pages, list):
            links = [e.get("url", "") for e in (pages[0].get("extlinks") or []) if isinstance(e, dict)]
    except Exception:
        links = []
    site = _official_site(links, subject)
    if site:
        website = f"https://{site}"

    return {
        "title": picked,
        "summary": clean(summary_json.get("extract", "") or (sentences(extract)[0] if extract else "")),
        "extract": extract[:12000],
        "history": history[:6000],
        "founded_year": founded,
        "website": website,
        "url": f"https://en.wikipedia.org/wiki/{quote(picked.replace(' ', '_'))}",
    }


def _official_site(links: list[str], subject: str) -> str:
    """The company's own domain from the article's external links: must contain
    a subject token and not be a reference/social/archive domain."""
    tokens = [t for t in re.findall(r"[a-z0-9]{4,}", subject.lower())]
    bad = ("wikipedia.org", "wikimedia", "archive.org", "twitter.com", "x.com",
           "facebook.com", "youtube.com", "linkedin.com", "instagram.com", "reddit.com",
           "medium.com", "github.com", "apple.com", "play.google.com", "crunchbase.com",
           "bloomberg.com", "forbes.com", "techcrunch.com", "theverge.com", "producthunt.com")
    best = ""
    for link in links or []:
        link = (link or "").strip()
        if link.startswith("//"):
            link = "https:" + link
        if not link.startswith("http"):
            link = "https://" + link
        try:
            net = urlparse(link).netloc.lower().removeprefix("www.")
        except Exception:
            continue
        if not net or any(b in net for b in bad):
            continue
        if not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", net):
            continue
        if tokens and not any(t in net for t in tokens):
            continue
        if not best or len(net) < len(best):
            best = net
    return best


def _strip_headers(text: str) -> str:
    """Drop '== Section ==' header lines from plaintext extracts."""
    # linear membership checks — the old "=+...=+" regex backtracked on
    # "="-run lines crafted into article content
    return "\n".join(
        line for line in (text or "").split("\n")
        if not (st := line.strip()).startswith("=") or not st.endswith("=") or len(st) < 2
    )


def _slice_section(text: str, headings: tuple[str, ...]) -> str:
    if not text:
        return ""
    lines = text.split("\n")
    out: list[str] = []
    capturing = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("=="):
            name = stripped.strip("= ").lower()
            capturing = any(h.lower() == name or name.startswith(h.lower()) for h in headings)
            continue
        if capturing and stripped:
            out.append(stripped)
    return "\n".join(out)


_FOUNDED_WORD = re.compile(r"\b(?:founded|founding|incorporated|established)\b", re.I)
_STARTED_WORD = re.compile(r"\b(?:started|launched|began)\b", re.I)
_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")


def _nearest_year(s: str, m: re.Match) -> int | None:
    """The year closest to the keyword match, within a 60-char reach."""
    best, dist = None, 61
    for ym in _YEAR.finditer(s):
        d = min(abs(ym.start() - m.end()), abs(m.start() - ym.end()))
        if d < dist:
            best, dist = int(ym.group(1)), d
    return best


def _founding_year(text: str, history: str = "") -> int | None:
    """The founding year, from years that actually sit next to founding words.

    Priority: a year within reach of a founded/incorporated/established
    mention ("Founded in 1996, ... by 2005 it had 1,000 staff" → 1996, not the
    last year in the sentence), then an explicit "founded in YYYY" pattern,
    then started/launched/began mentions — summary first, then the History
    section. A bare year elsewhere ("as of 2025, 120M users") is NOT a
    founding year; returning None is more honest than guessing.
    """
    def scan(blob: str, word_re: re.Pattern) -> int | None:
        for s in sentences(blob or ""):
            for m in word_re.finditer(s):
                y = _nearest_year(s, m)
                if y is not None:
                    return y
        return None

    for blob in (text, history):
        y = scan(blob, _FOUNDED_WORD)
        if y is not None:
            return y
    for blob in (text, history):
        m = re.search(
            r"(?:founded|incorporated|established)[^.]{0,80}?in\s+((?:19|20)\d{2})",
            (blob or "")[:20000],
            re.I,
        )
        if m:
            return int(m.group(1))
    for blob in (text, history):
        y = scan(blob, _STARTED_WORD)
        if y is not None:
            return y
    return None


async def _wikidata_inception(fetcher: Fetcher, title: str) -> int | None:
    """The structured inception year (Wikidata P571) of the article's subject."""
    data = await fetcher.try_json(
        "https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki"
        f"&titles={quote(title)}&props=claims&format=json&origin=*"
    )
    entities = (data or {}).get("entities", {}) or {}
    ent = next(iter(entities.values()), {}) if isinstance(entities, dict) else {}
    for snak in (ent.get("claims", {}) or {}).get("P571", []) or []:
        value = (((snak.get("mainsnak") or {}).get("datavalue")) or {}).get("value") or {}
        m = re.search(r"([12]\d{3})", str(value.get("time", "")))
        if m:
            return int(m.group(1))
    return None


async def wiki_search(fetcher: Fetcher, query: str, limit: int = 8) -> list[dict]:
    """MediaWiki fulltext search — the bot-tolerant last rung of the surface-web
    cascade. When every web engine rate-limits a datacenter IP at once, the
    subject's encyclopedia footprint still reaches the pipeline. Rows are
    shaped like search results so every downstream consumer works unchanged."""
    data = await fetcher.try_json(
        f"{API}?action=query&list=search&srsearch={quote(query)}&srlimit={limit}&format=json&origin=*"
    )
    out: list[dict] = []
    for hit in ((data or {}).get("query", {}) or {}).get("search", []) or []:
        title = clean(hit.get("title", ""))
        if not title:
            continue
        snippet = re.sub(r"<[^>]+>", " ", hit.get("snippet", "") or "")
        out.append({
            "title": title,
            "url": f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
            "snippet": clean(snippet)[:300],
        })
    return out
