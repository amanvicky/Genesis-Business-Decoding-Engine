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
        # copy before ranking: channels_for returns the shared KB dicts, and
        # writing corpus_signal into them leaked one run's scores into the next
        channels = [dict(ch) for ch in KB.channels_for(ev.sector, ev.req.geography.value)]
        # Rank by evidence: which channels does the corpus already show working here
        pool = ev.snippet_pool(6000).lower()
        for ch in channels:
            hits = sum(1 for kw in [k.lower() for k in ch["name"].split()[:2]] if kw in pool)
            ch["corpus_signal"] = hits

        return {
            "channels": channels,
            "first_ten": self._first_ten(),
            "strategy": [
                "Pick TWO loops. One compounding (SEO/programmatic/OSS), one direct (HN/Reddit/cold email). Two is the maximum a 2-person team can run honestly.",
                "Each loop gets a weekly scoreboard: actions shipped, signals received, conversions. Kill a loop after 8 weeks of zero signal — not 8 weeks of zero revenue.",
                "Zero-cost ≠ zero-effort: the cost is founder hours. Budget 30% of your week to distribution from day one; product-heavy founders are the #1 cause of 'great product, no users'.",
                "Never buy ads before retention is proven — paid traffic into a leaky bucket is just faster failure with better dashboards.",
            ],
        }

    @staticmethod
    def _first_ten() -> list[dict]:
        """The first-10-customers plan — the step every founder fumbles.
        Channel-agnostic: run it inside whichever loop ranks first above."""
        return [
            {"step": 1, "window": "Day 1–3", "action": "List 30 NAMED prospects from the top-ranked loop's ecosystem — actual companies/people, not personas. If you can't name 30, the channel choice is wrong, not the list."},
            {"step": 2, "window": "Day 3–7", "action": "Contact 10/day, 3 lines each: the specific pain in their words, what you built, ask for 15 minutes. No links, no deck, no 'quick chat?' energy."},
            {"step": 3, "window": "Week 2", "action": "Run every reply as a 20-minute problem interview. Log their verbatim pain words — that transcript becomes your landing page and your pitch."},
            {"step": 4, "window": "Week 2–3", "action": "Offer the 3 hottest a PAID pilot at ~50% of intended price. Free users validate politeness, not willingness to pay."},
            {"step": 5, "window": "Week 3–4", "action": "Deliver manually (concierge MVP). The product is the excuse; the workflow knowledge you gain is the asset."},
            {"step": 6, "window": "Week 4", "action": "Ask each of the 10 for ONE referral to someone with the same pain. Warm intros convert 5–10× cold outreach — this is how 10 becomes 30."},
            {"step": 7, "window": "Day 30", "action": "Verdict: fewer than 3 paid pilots → the pain or the pitch is wrong; go back to step 1 armed with the interview transcript. 3+ paid pilots → point the compounding loop at this exact wording and scale contact volume."},
        ]

    def summarize(self, ev: Evidence, data: dict) -> str:
        names = [c["name"].split("(")[0].strip() for c in data["channels"][:3]]
        return f"{len(data['channels'])} zero-cost loops ranked for {ev.sector}/{ev.req.geography.value}: {', '.join(names)}."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. From these channels, name the single loop this specific product should start with and the first action to take tomorrow."
