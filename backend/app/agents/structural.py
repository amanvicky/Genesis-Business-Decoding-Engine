"""Tab 1 — Structural Feasibility & Core Mechanics."""
from __future__ import annotations

import re

from ..models import Evidence
from ..text import keyphrases, sentences
from .base import Agent

PAIN_MARKERS = ["hate", "pain", "annoying", "manual", "excel", "spreadsheet", "why is", "struggle", "frustrat", "waste", "outsource", "can't", "cannot", "broken", "confus"]
DEMAND_MARKERS = ["looking for", "any tool", "recommend", "alternative to", "how do i", "best way", "need help"]
MOAT_TYPES = [
    ("Network effects", ["two-sided", "marketplace", "network effect", "flywheel", "connects buyers", "community of"]),
    ("Data compounding", ["proprietary data", "dataset", "data advantage", "benchmark data", "training data", "proprietary index"]),
    ("Switching cost", ["migration", "integrat", "workflow", "embed", "system of record", "source of truth"]),
    ("Regulatory barrier", ["license", "compliance", "rbi", "fda", "regulated", "licence"]),
    ("Brand/trust", ["trusted", "fortune 500", "audit", "certified", "brand"]),
]


class StructuralAgent(Agent):
    id = "structural"
    title = "Structural Feasibility & Core Mechanics"
    icon = "🧬"
    tab = 1

    async def build(self, ev: Evidence) -> dict:
        pool = ev.snippet_pool()
        all_sentences = sentences(pool)
        low = pool.lower()

        pains, demands = [], []
        source_texts = (
            [("reddit", r) for r in ev.reddit]
            + [("hn", r) for r in ev.hn_comments]
            + [("review", r) for r in ev.reviews]
            + [("web", r) for r in ev.search]
        )
        for kind, r in source_texts:
            text = " ".join([r.get("title", ""), r.get("selftext", ""), r.get("text", ""), r.get("snippet", "")]).lower()
            if any(m in text for m in PAIN_MARKERS) and len(text) > 60:
                pains.append({"source": kind, "text": (r.get("title") or r.get("snippet") or r.get("text", ""))[:220], "url": r.get("url", "")})
            if any(m in text for m in DEMAND_MARKERS) and len(text) > 40:
                demands.append({"source": kind, "text": (r.get("title") or r.get("snippet") or r.get("text", ""))[:220], "url": r.get("url", "")})
        pains, demands = pains[:12], demands[:10]

        # Core mechanics (company mode): sentences describing how money is made
        mechanics = []
        mech_re = re.compile(r"(revenue|charge[sd]?|fee[s]?|subscription|commission|takes? a|percent|%|per transaction|business model)", re.I)
        if ev.wiki:
            for s in sentences(ev.wiki.get("summary", "") + " " + ev.wiki.get("extract", "")[:4000]):
                if mech_re.search(s):
                    mechanics.append(s[:300])
        mechanics = mechanics[:8]

        # Moats: which structural moat types have evidence in the corpus
        moats = []
        for name, kws in MOAT_TYPES:
            hits = [s for s in all_sentences if any(k in s.lower() for k in kws)]
            if hits:
                moats.append({"type": name, "strength": "evidence found", "evidence": hits[0][:220]})

        # Timing shifts: tech/market inflection signals in the corpus
        shift_kws = ["ai ", "llm", "open source", "regulation change", "rbi", "gdpr", "remote work", "digital first", "api-first", "privacy law", "upi", "rate hike"]
        timing = []
        for kw in shift_kws:
            hits = [s for s in all_sentences if kw in s.lower()]
            if hits:
                timing.append({"shift": kw.strip(), "implication": hits[0][:220]})
        timing = timing[:6]

        demand_score = min(100, len(demands) * 8 + len(ev.hn_stories) * 2 + len(ev.reddit) * 2)
        pain_score = min(100, len(pains) * 9)
        total_evidence = sum(len(x) for x in (ev.search, ev.hn_stories, ev.hn_comments, ev.reddit, ev.reviews))

        if ev.req.mode.value == "company":
            # An established operator is never "too early" — the verdict speaks
            # about decode confidence, not idea validation coaching.
            depth = min(100, total_evidence * 3)
            verdict = (
                f"Deep public record decoded ({total_evidence} evidence items) — mechanics, moats, and friction below are historical record."
                if depth >= 55
                else f"Moderate public record ({total_evidence} evidence items) — decode is directional; complaint clusters are the highest-signal section."
                if depth >= 25
                else f"Thin public record ({total_evidence} items) — this decode leans on the built-in knowledge bases; treat as planning scaffold."
            )
            verdict_score = depth
        else:
            verdict_score = (demand_score + pain_score) // 2
            verdict = (
                "Structurally viable: real pain + real search demand signals."
                if verdict_score >= 55
                else "Conditional: signals exist but thin — validate with 20 user interviews before building."
                if verdict_score >= 30
                else "Weak public signal: either too early, too niche, or the pain is voiced offline. Interview before code."
            )

        return {
            "verdict": verdict,
            "verdict_score": verdict_score,
            "mode": ev.req.mode.value,
            "pain_points": pains,
            "demand_triggers": demands,
            "core_mechanics": mechanics,
            "moats": moats,
            "timing_shifts": timing,
            "keyphrases": [p for p, _ in keyphrases(pool, 10)],
            "evidence_volume": {
                "search_results": len(ev.search),
                "hn_stories": len(ev.hn_stories),
                "reddit_posts": len(ev.reddit),
                "review_snippets": len(ev.reviews),
            },
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        return f"{data['verdict']} (signal score {data['verdict_score']}/100 from {sum(data['evidence_volume'].values())} evidence items)."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject} ({ev.req.mode.value}). Given the scraped evidence summary, state the single "
            "most important structural mechanic (who pays whom and why they pay), the strongest moat type available, "
            "and the one market-timing shift that changes the calculus."
        )
