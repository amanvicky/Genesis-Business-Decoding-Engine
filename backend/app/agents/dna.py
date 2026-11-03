"""Tab 14 — Product DNA: the philosophy and psychology behind every feature.

Company mode: every decoded feature is matched against a pattern KB and broken
down into why it was built (philosophy), which named psychological principles
make it work, the business mechanism it serves, and how the founder can steal
or avoid it. Idea mode: the levers that matter for their sector, so they can
refine before they build. Every term is defined in plain words at the bottom.
"""
from __future__ import annotations

import re
from collections import Counter

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


class DnaAgent(Agent):
    id = "dna"
    title = "Product DNA — Philosophy & Psychology"
    icon = "☯"
    tab = 14

    async def build(self, ev: Evidence) -> dict:
        is_idea = ev.req.mode.value == "idea"
        sections = getattr(self, "sections", {}) or {}
        feats = ((sections.get("features") or {}).get("data") or {}).get("features") or []

        # per-feature breakdown (company mode has real feature history to mine)
        feature_breakdowns: list[dict] = []
        for f in feats[:60]:
            text = f"{f.get('feature', '')} {f.get('detail', '')}"
            hits = _patterns_for(text)
            if not hits:
                continue
            feature_breakdowns.append({
                "feature": f.get("feature", "")[:140],
                "class": f.get("class", ""),
                "source": f.get("source", ""),
                "patterns": [_entry(p) for p in hits[:2]],
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
        product_philosophy = {
            "headline": (
                f"What {_product_name(ev)} optimizes for, read from its own trail: "
                + "; ".join(p["name"].lower() for p, _ in top) + "."
            ) if top else "Not enough evidence to read a product philosophy — run online for a fuller picture.",
            "top_patterns": [{"name": p["name"], "mentions": c, "philosophy": p["philosophy"]} for p, c in top],
        }

        # idea mode: the levers that decide winners in this sector
        idea_lens = None
        if is_idea:
            lens_names = SECTOR_LENS.get(ev.sector, SECTOR_LENS["generic"])
            by_name = {p["name"]: p for p in KB.PATTERNS}
            recommended = [_entry(by_name[n]) for n in lens_names if n in by_name]
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

        return {
            "product_philosophy": product_philosophy,
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
                    f"philosophy, the named principles, and how to apply it. Pick two.")
        n = len(data.get("features", []))
        top = (data.get("product_philosophy") or {}).get("top_patterns") or []
        lead = top[0]["name"].lower() if top else "no dominant pattern"
        return (f"{n} feature(s) broken down into philosophy + psychology + business mechanics "
                f"(dominant pattern: {lead}). Every term defined at the bottom.")

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. From the decoded product patterns, name the ONE psychological "
            "principle this company's product most exploits, in one line, and the single refinement a "
            "founder copying this category should make differently."
        )


def _product_name(ev: Evidence) -> str:
    return ev.subject or "the product"


def json_dump(obj) -> str:
    import json
    return json.dumps(obj, default=str)
