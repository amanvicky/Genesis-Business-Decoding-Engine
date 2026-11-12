"""Tab 14 — Product DNA: the philosophy and psychology behind every feature.

Company mode: every decoded feature is matched against a pattern KB and broken
down into why it was built (philosophy), which named psychological principles
make it work, the business mechanism it serves, how the pattern actually played
out (evidence-mined outcomes + a documented example), and how the founder can
steal or avoid it. Idea mode: the levers that matter for their sector.
"""
from __future__ import annotations

import re

from ..data import dna as KB
from ..models import Evidence
from .base import Agent

# sector -> which patterns historically decide winners there
SECTOR_LENS: dict[str, list[str]] = {
    "payroll": ["Freemium / free tier", "Enterprise controls (SSO, audit, roles)", "Integrations & ecosystem",
                "Usage-based & per-seat pricing", "Onboarding checklists & progress bars", "Social proof surfaces"],
    "fintech": ["Freemium / free tier", "Enterprise controls (SSO, audit, roles)", "Integrations & ecosystem",
                "Social proof surfaces", "Usage-based & per-seat pricing"],
    "saas": ["Freemium / free tier", "Onboarding checklists & progress bars", "Integrations & ecosystem",
             "Referrals & invites", "AI copilots & auto-magic", "Usage-based & per-seat pricing"],
    "devtools": ["Open source & community", "Freemium / free tier", "Templates & starter content",
                 "Integrations & ecosystem", "Usage-based & per-seat pricing"],
    "commerce": ["Social proof surfaces", "Urgency & scarcity mechanics", "Referrals & invites",
                 "Personalization & recommendations", "Templates & starter content"],
    "health": ["Onboarding checklists & progress bars", "Enterprise controls (SSO, audit, roles)",
               "Social proof surfaces", "Personalization & recommendations"],
    "edu": ["Onboarding checklists & progress bars", "Streaks & habit mechanics", "Social proof surfaces",
            "Templates & starter content"],
    "logistics": ["Integrations & ecosystem", "Usage-based & per-seat pricing", "Social proof surfaces"],
    "generic": ["Onboarding checklists & progress bars", "Freemium / free tier", "Social proof surfaces",
                "Templates & starter content"],
}

# outcome signals: how a pattern actually played out, mined from evidence
OUTCOME_RES = [
    ("scale", re.compile(r"\b\d[\d.,]*\s*(?:million|billion|M|k|thousand)\+?\s*(?:registered )?(?:users|customers|subscribers|members|teams|sign-?ups|downloads|employees|people|companies)\b", re.I)),
    ("money", re.compile(r"\b(?:valued at|raised|acquired for|revenue (?:of|reached|surpassed)|worth|billion|million dollars)\b", re.I)),
    ("credibility", re.compile(r"\b(?:soc ?2|iso\s?27001|hipaa compliant|award|acquired|acquisition|partnership with|trusted by|featured in|named (?:a|one)|winner|top \d)\b", re.I)),
    ("growth", re.compile(r"\b(?:grew|grown|doubled|tripled|surged|jumped|expanded to|adopted by|switched to|went viral|became the default)\b", re.I)),
]


def _outcomes(ev: Evidence) -> list[dict]:
    """Outcome sentences from the evidence, with their source snippet.

    Keeps the whole source snippet (`src`) alongside each sentence: the pattern
    keyword and the outcome often live in the SAME ARTICLE but different
    sentences, and snippet-level attribution is what connects them."""
    from ..text import clean as _clean
    out: list[dict] = []
    seen: set[str] = set()
    sources: list[tuple[str, str]] = (
        [(f"{r.get('title', '')} {r.get('snippet', '')}", r.get("url", "")) for r in ev.search]
        + [(f"{r.get('title', '')} {r.get('selftext', '')}", r.get("url", "")) for r in ev.reddit]
        + [(r.get("snippet", ""), r.get("url", "")) for r in ev.reviews]
        + [(f"{r.get('name', '')} {r.get('body', '')}", r.get("url", "")) for r in ev.releases]
    )
    for text, url in sources:
        text = _clean(text)
        if not text:
            continue
        src = text[:400].lower()
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if len(sent) < 25 or sent.lower()[:60] in seen:
                continue
            kind = next((k for k, rx in OUTCOME_RES if rx.search(sent)), None)
            if kind:
                seen.add(sent.lower()[:60])
                out.append({"kind": kind, "text": sent[:220], "url": url, "src": src})
    return out


def _patterns_for(text: str) -> list[dict]:
    low = text.lower()
    return [p for p in KB.PATTERNS if any(kw in low for kw in p["kw"])]


def _entry(p: dict) -> dict:
    return {
        "name": p["name"],
        "philosophy": p["philosophy"],
        "psychology": [{"principle": n, "explained": x} for n, x in p["psychology"]],
        "business": p["business"],
        "refine": p["refine"],
    }


def _product_name(ev: Evidence) -> str:
    return ev.subject or "the product"


def json_dump(obj) -> str:
    import json
    return json.dumps(obj, default=str)


class DnaAgent(Agent):
    id = "dna"
    title = "Product DNA — Philosophy & Psychology"
    icon = "☯"
    tab = 9

    async def build(self, ev: Evidence) -> dict:
        is_idea = ev.req.mode.value == "idea"
        sections = getattr(self, "sections", {}) or {}
        feats = ((sections.get("features") or {}).get("data") or {}).get("features") or []

        outcomes = _outcomes(ev)

        founded = ev.wiki.get("founded_year") if ev.wiki else None

        def _timing(date_str: str, pattern_name: str) -> dict:
            """WHY THEN: the stage logic for adding this pattern at that moment."""
            year = int(date_str[:4]) if date_str and re.match(r"^(19|20)\d\d", str(date_str)) else None
            age = (year - founded) if (year and founded) else None
            stage_key = None
            if age is not None:
                stage_key = "search" if age <= 2 else "growth" if age <= 5 else "scale"
            stage = {"search": "search (year 0-2)", "growth": "growth (year 3-5)", "scale": "scale (year 6+)"}.get(stage_key)
            note = (KB.TIMING_NOTES.get(pattern_name, {}) or {})
            why_then = (note.get("early") if stage_key == "search" else
                        note.get("late") if stage_key in ("growth", "scale") else None)
            when = date_str or "undated"
            when += f" (company year {age})" if age is not None else ""
            return {"when": when, "year": year, "company_age": age, "stage": stage,
                    "why_then": why_then or "timing context unknown - the date carried no company-age anchor",
                    "major_reason": (
                        f"Added {when}: {why_then}. The purpose: {note and (KB.PATTERNS and [p2 for p2 in KB.PATTERNS if p2['name'] == pattern_name][0]['philosophy'])}"
                        if why_then else f"Added {when}."
                    )}

        # per-feature breakdown (company mode has real feature history to mine)
        feature_breakdowns: list[dict] = []
        for f in feats[:60]:
            text = f"{f.get('feature', '')} {f.get('detail', '')}"
            hits = _patterns_for(text)
            if not hits:
                continue
            fwords = {w for w in re.findall(r"[a-z]{5,}", text.lower())}
            entries = []
            for p in hits[:2]:
                entry = _entry(p)
                # outcomes attributed to this pattern when the source snippet
                # mentions its keywords; prefer ones that also touch the
                # feature's own words, fall back to pattern-level outcomes
                pat_outs = [o for o in outcomes if any(kw in o["src"] for kw in p["kw"])]
                near = [o for o in pat_outs if fwords & set(o["src"].split())] or pat_outs
                entry["played_out"] = [{"kind": o["kind"], "text": o["text"], "url": o["url"]} for o in near[:2]]
                entry["worked"] = p["worked"]
                entries.append(entry)
            timing = _timing(f.get("date", ""), hits[0]["name"])
            feature_breakdowns.append({
                "feature": f.get("feature", "")[:140],
                "class": f.get("class", ""),
                "source": f.get("source", ""),
                "timing": timing,
                "patterns": entries,
            })
            if len(feature_breakdowns) >= 10:
                break

        # product-wide: which patterns show up across the whole evidence corpus
        pool = ev.snippet_pool(8000).lower()
        corpus_hits: list[tuple[dict, int]] = []
        for p in KB.PATTERNS:
            c = sum(1 for kw in p["kw"] if kw in pool)
            if c:
                corpus_hits.append((p, c))
        corpus_hits.sort(key=lambda x: -x[1])
        top = corpus_hits[:3]

        subject_words = {w.lower() for w in _product_name(ev).split() if len(w) > 2}
        credibility = [
            {"kind": o["kind"], "text": o["text"], "url": o["url"]}
            for o in outcomes
            if o["kind"] in ("credibility", "money", "scale")
            and (subject_words & set(o["text"].lower().split()))
        ][:5]

        product_philosophy = {
            "headline": (
                f"What {_product_name(ev)} optimizes for, read from its own trail: "
                + "; ".join(p["name"].lower() for p, _ in top) + "."
            ) if top else "Not enough evidence to read a product philosophy — run online for a fuller picture.",
            "top_patterns": [{"name": p["name"], "mentions": c, "philosophy": p["philosophy"]} for p, c in top],
            "credibility": credibility,
        }

        # idea mode: the levers that decide winners in this sector
        idea_lens = None
        if is_idea:
            lens_names = SECTOR_LENS.get(ev.sector, SECTOR_LENS["generic"])
            by_name = {p["name"]: p for p in KB.PATTERNS}
            recommended = [_entry(by_name[n]) for n in lens_names if n in by_name]
            for r in recommended:
                r["worked"] = next(p["worked"] for p in KB.PATTERNS if p["name"] == r["name"])
            idea_lens = {
                "sector": ev.sector,
                "recommended": recommended,
                "note": ("These are the levers your sector's winners pull. Pick TWO and design them properly "
                         "before launch — a product that tries all of them at once does none well."),
            }

        # glossaries: only the terms/principles actually used above, so the
        # definitions at the bottom always match what the user just read
        used_text = json_dump(top) + json_dump(feature_breakdowns) + json_dump(idea_lens)
        glossary_business = {t: d for t, d in KB.BUSINESS_GLOSSARY.items()
                             if any(re.search(rf"\b{re.escape(a)}\b", used_text, re.I)
                                    for a in t.replace("(", "").split(" / "))}
        used_principles = {ps["principle"] for fb in feature_breakdowns for pat in fb["patterns"]
                           for ps in pat["psychology"]}
        if idea_lens:
            used_principles |= {ps["principle"] for r in idea_lens["recommended"] for ps in r["psychology"]}
        glossary_psych = {n: KB.PSYCH_GLOSSARY[n] for n in sorted(used_principles) if n in KB.PSYCH_GLOSSARY}

        sequencing = [
            {"when": fb["timing"]["when"], "feature": fb["feature"]}
            for fb in sorted(feature_breakdowns, key=lambda x: x["timing"]["year"] or 9999)
            if fb["timing"]["year"]
        ][:12]

        return {
            "product_philosophy": product_philosophy,
            "sequencing": sequencing,
            "features": feature_breakdowns,
            "idea_lens": idea_lens,
            "glossary_business": glossary_business,
            "glossary_psych": glossary_psych,
            "note": ("Plain-language definitions for every term used are at the bottom of this tab. "
                     "Nothing here is hidden behind jargon."),
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        if data.get("idea_lens"):
            n = len(data["idea_lens"]["recommended"])
            return (f"{n} psychological levers recommended for a {ev.sector} idea, each with the "
                    f"philosophy, the named principles, how it played out in the wild, and how to apply it. Pick two.")
        n = len(data.get("features", []))
        top = (data.get("product_philosophy") or {}).get("top_patterns") or []
        lead = top[0]["name"].lower() if top else "no dominant pattern"
        return (f"{n} feature(s) broken down into philosophy + psychology + business mechanics + how it "
                f"played out (dominant pattern: {lead}). Every term defined at the bottom.")

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. From the decoded product patterns, name the ONE psychological "
            "principle this company's product most exploits, in one line, and the single refinement a "
            "founder copying this category should make differently."
        )
