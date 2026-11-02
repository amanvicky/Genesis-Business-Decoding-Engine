"""Tab 9 — Unfair Distribution & Organic Acquisition Channels."""
from __future__ import annotations

from ..data import channels as KB
from ..models import Evidence
from .base import Agent


class DistributionAgent(Agent):
    id = "distribution"
    title = "Unfair Distribution & Organic Acquisition"
    icon = "📡"
    tab = 9

    async def build(self, ev: Evidence) -> dict:
        channels = KB.channels_for(ev.sector, ev.req.geography.value)
        # Rank by evidence: which channels does the corpus already show working here
        pool = ev.snippet_pool(6000).lower()
        for ch in channels:
            hits = sum(1 for kw in [k.lower() for k in ch["name"].split()[:2]] if kw in pool)
            ch["corpus_signal"] = hits

        return {
            "channels": channels,
            "strategy": [
                "Pick TWO loops. One compounding (SEO/programmatic/OSS), one direct (HN/Reddit/cold email). Two is the maximum a 2-person team can run honestly.",
                "Each loop gets a weekly scoreboard: actions shipped, signals received, conversions. Kill a loop after 8 weeks of zero signal — not 8 weeks of zero revenue.",
                "Zero-cost ≠ zero-effort: the cost is founder hours. Budget 30% of your week to distribution from day one; product-heavy founders are the #1 cause of 'great product, no users'.",
                "Never buy ads before retention is proven — paid traffic into a leaky bucket is just faster failure with better dashboards.",
            ],
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        names = [c["name"].split("(")[0].strip() for c in data["channels"][:3]]
        return f"{len(data['channels'])} zero-cost loops ranked for {ev.sector}/{ev.req.geography.value}: {', '.join(names)}."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. From these channels, name the single loop this specific product should start with and the first action to take tomorrow."
