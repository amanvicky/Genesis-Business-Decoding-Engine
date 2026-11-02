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
    title = "Logical Pricing & Unit Economics"
    icon = "📐"
    tab = 6

    async def build(self, ev: Evidence) -> dict:
        tiers = ev.current_pricing or self._tiers_from_corpus(ev)
        history = ev.pricing_history

        # Unit economics (explicit formulas — this is reverse-engineering, not vibes)
        is_fintech = ev.sector in ("fintech", "payroll")
        gross_margin = 0.62 if is_fintech else 0.82  # compliance/ops cost drag vs pure SaaS
        arpa = self._arpa(tiers) or (999 if ev.req.geography.value == "india" else 29)
        avg_lifetime_months = 24  # B2B SaaS proxy; sensitivity shown client-side
        ltv = arpa * gross_margin * (avg_lifetime_months / 12)
        cac_organic = 180 if ev.req.geography.value != "india" else 2400  # in local units, content/organic proxy
        currency = "₹" if ev.req.geography.value == "india" else "$"
        if arpa and ltv:
            ratio = ltv / cac_organic
            payback = (cac_organic / (arpa * gross_margin)) * 12 if arpa * gross_margin else None
        else:
            ratio, payback = None, None

        # Packaging psychology detection
        psych = []
        prices = [(_t["name"], _amt(_t["price"])) for _t in tiers]
        if len(prices) >= 3 and prices[-1][1] and prices[1][1] and prices[-1][1] >= 3 * prices[1][1]:
            psych.append({"driver": "Anchoring", "evidence": f"{prices[-1][0]} at {prices[-1][1]} vs {prices[1][0]} at {prices[1][1]}"})
        if any("contact" in str(t.get("context", "")).lower() or t["price"].lower() == "$0" for t in tiers):
            psych.append({"driver": "Gating observed", "evidence": "contact-sales or quote-based tier present"})
        names = [t["name"].lower() for t in tiers]
        if "free" in names:
            psych.append({"driver": "Freemium acquisition", "evidence": "free tier present — marginal cost per free user is the constraint"})

        rec = self._recommend(ev, arpa)

        return {
            "tiers": tiers,
            "history": history[:10],
            "unit_economics": {
                "arpa": arpa,
                "currency": currency,
                "assumed_gross_margin": gross_margin,
                "margin_basis": "compliance+ops drag (fintech/payroll)" if is_fintech else "standard SaaS hosting+support",
                "avg_lifetime_months": avg_lifetime_months,
                "ltv": round(ltv, 2) if ltv else None,
                "cac_organic_proxy": cac_organic,
                "ltv_cac_ratio": round(ratio, 2) if ratio else None,
                "cac_payback_months": round(payback, 1) if payback else None,
                "formulas": [
                    "LTV = ARPA × gross_margin × (lifetime_months / 12)",
                    "LTV:CAC target ≥ 3 (organic proxy CAC substituted where paid CAC unknown)",
                    "Payback (months) = CAC / (ARPA × gross_margin)",
                ],
            },
            "psychology": psych + [{"driver": d, "evidence": w} for d, w in PSYCH_DRIVERS if not any(p["driver"] == d for p in psych)][:4],
            "recommendation": rec,
        }

    def _tiers_from_corpus(self, ev: Evidence) -> list[dict]:
        from ..text import extract_tiers

        text = ev.snippet_pool(8000)
        return extract_tiers(text)

    def _arpa(self, tiers: list[dict]) -> float | None:
        vals = [(_t["name"].lower(), _amt(_t["price"])) for _t in tiers if _amt(_t["price"]) > 0]
        if not vals:
            return None
        paid = [v for name, v in vals if "free" not in name]
        pool = paid or vals
        mid = sorted(v for _, v in pool)
        return mid[len(mid) // 2]  # median tier price ≈ blended ARPA proxy

    def _recommend(self, ev: Evidence, arpa: float | None) -> list[str]:
        geo = ev.req.geography.value
        cur = "₹" if geo == "india" else "$"
        base = arpa or (999 if geo == "india" else 29)
        return [
            f"3 tiers, no free tier: {cur}{round(base*0.3)}, {cur}{round(base)} (anchor features here), {cur}{round(base*4)} — ratio 1 : 3.3 : 13.",
            "Gate on org size (seats/records), never on 'premium support' — support is a cost center, org size is a value proxy.",
            f"Annual prepay at 10× monthly ({cur}{round(base*10)}) — funds CAC and kills churn between invoices.",
            "Charge from customer #1: discounts are manual and expire; a free tier is a permanent COGS line.",
            f"Compliance-required: {'Razorpay (no PA licence needed as sub-merchant; TDR ~2%)' if geo == 'india' else 'Stripe (tokenized, SAQ-A; ~2.9%+30¢)'} — price with {('2%+GST on MRR' if geo == 'india' else '3%') + ' gateway drag included in margin model.'}",
        ]

    def summarize(self, ev: Evidence, data: dict) -> str:
        ue = data["unit_economics"]
        tiers = len(data["tiers"])
        if ue.get("arpa"):
            return f"{tiers} tier(s) decoded. ARPA proxy {ue['currency']}{ue['arpa']}, assumed GM {int(ue['assumed_gross_margin']*100)}%, LTV:CAC(organic) {ue.get('ltv_cac_ratio', '—')}."
        return "No public pricing tier decoded — recommendation set built from geography-adjusted defaults."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. State the pricing leverage move this target leaves on the table and who gets hurt by it."
