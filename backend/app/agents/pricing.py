"""Tab 6 — Logical Pricing & Unit Economics Architecture."""
from __future__ import annotations

import re

from ..models import Evidence
from ..text import _amt, sentences
from .base import Agent

PSYCH_DRIVERS = [
    ("Anchoring", "The highest tier exists to make the middle tier look reasonable. If tier-3 ≥ 3× tier-2, it's an anchor."),
    ("Decoy pricing", "A tier priced to be obviously dominated ('same price, fewer features') pushes buyers to the target tier."),
    ("Feature gating", "Enterprise-tier words (SSO, audit logs, admin roles) are margin via org-size, not feature cost."),
    ("Contact-sales gating", "'Contact us' = six-figure ACV flag: they price on negotiated value, not list."),
    ("Free tier as acquisition", "Freemium only works with near-zero marginal cost per free user — check your hosting math."),
    ("Per-seat escalation", "Per-seat pricing makes the buyer's growth your revenue growth; flat pricing caps it. Note which the target uses."),
]


class PricingAgent(Agent):
    id = "pricing"
    title = "Pricing — Tiers, History & Packaging Psychology"
    icon = "📐"
    tab = 6

    async def build(self, ev: Evidence) -> dict:
        tiers = ev.current_pricing or self._tiers_from_corpus(ev)
        history = ev.pricing_history

        # Packaging psychology detection
        psych = []
        # sort by amount: the tier list is keyword-ordered, not price-ordered —
        # comparing positions compared names, not prices
        prices = sorted(((_t["name"], _amt(_t["price"])) for _t in tiers), key=lambda x: x[1])
        if len(prices) >= 3 and prices[-1][1] and prices[1][1] and prices[-1][1] >= 3 * prices[1][1]:
            psych.append({"driver": "Anchoring", "evidence": f"{prices[-1][0]} at {prices[-1][1]:,.0f} vs {prices[1][0]} at {prices[1][1]:,.0f}"})
        if any("contact" in str(t.get("context", "")).lower() or str(t.get("price", "")).lower() == "$0" for t in tiers):
            psych.append({"driver": "Gating observed", "evidence": "contact-sales or quote-based tier present"})
        names = [t["name"].lower() for t in tiers]
        if "free" in names:
            psych.append({"driver": "Freemium acquisition", "evidence": "free tier present — marginal cost per free user is the constraint"})

        return {
            "tiers": tiers,
            "history": history[:10],
            "psychology": psych + [{"driver": d, "evidence": w} for d, w in PSYCH_DRIVERS if not any(p["driver"] == d for p in psych)][:4],
        }

    def _tiers_from_corpus(self, ev: Evidence) -> list[dict]:
        from ..text import extract_tiers

        text = ev.snippet_pool(8000)
        return extract_tiers(text)



    def summarize(self, ev: Evidence, data: dict) -> str:
        n = len(data.get("tiers") or [])
        if n:
            names = [str(t.get("name", "?")) for t in (data.get("tiers") or [])[:3]]
            return f"{n} tier(s) decoded from live evidence: {', '.join(names)}"
        if data.get("history"):
            return f"no current tiers visible — {len(data['history'])} wayback snapshot(s) show past pricing"
        return "no public pricing decoded — quote-based sales or pricing hidden behind demo gates"
