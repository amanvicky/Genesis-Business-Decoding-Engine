"""Wikipedia: company genesis data — summary, history section, founding year."""
from __future__ import annotations

import re
from urllib.parse import quote

from .client import Fetcher
from ..text import clean, find_years, sentences

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
    founded = _founding_year(extract or summary_json.get("extract", ""))

    return {
        "title": picked,
        "summary": clean(summary_json.get("extract", "") or (sentences(extract)[0] if extract else "")),
        "extract": extract[:12000],
        "history": history[:6000],
        "founded_year": founded,
        "url": f"https://en.wikipedia.org/wiki/{quote(picked.replace(' ', '_'))}",
    }


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


def _founding_year(text: str) -> int | None:
    if not text:
        return None
    sents = sentences(text)
    # 1) A sentence that explicitly talks about founding/incorporation — take
    #    its LAST year ("founded Stripe in Palo Alto, California, in 2010").
    for s in sents:
        if re.search(r"\b(?:founded|incorporated|established)\b", s, re.I):
            years = re.findall(r"\b(?:19|20)\d{2}\b", s)
            if years:
                return int(years[-1])
    # 2) A started/launched sentence — take its FIRST year
    #    ("In 1949, Henry Taub started Automatic Payrolls System").
    for s in sents:
        if re.search(r"\b(?:started|launched|began)\b", s, re.I):
            years = re.findall(r"\b(?:19|20)\d{2}\b", s)
            if years:
                return int(years[0])
    years = find_years(text)
    return years[0][0] if years else None
