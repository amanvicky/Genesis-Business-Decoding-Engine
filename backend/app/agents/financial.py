"""Tab 8 — Financial Reality & Burn Calculator (zero sugarcoating)."""
from __future__ import annotations

from ..models import Evidence
from .base import Agent

# Loaded annual cost per engineer (salary × 1.25–1.35 employer burden).
COST_MODELS = {
    "us": {"currency": "$", "engineer_loaded": 155000, "founder_draw": 90000, "infra_base_month": 250, "tools_per_seat_month": 40, "legal_base_year": 4000, "office_none": 0},
    "india": {"currency": "₹", "engineer_loaded": 1500000, "founder_draw": 900000, "infra_base_month": 18000, "tools_per_seat_month": 3000, "legal_base_year": 60000},
    "global": {"currency": "$", "engineer_loaded": 120000, "founder_draw": 70000, "infra_base_month": 200, "tools_per_seat_month": 40, "legal_base_year": 4000},
}

SECTOR_COST_OVERRIDES = {
    "fintech": {
        "us": {"legal_base_year": 60000, "warning": "US fintech: MTL route is a $100k–$1M multi-year program; BaaS/sponsor-bank route trades it for rev-share + program fees + a partner who can terminate you. Model both."},
        "india": {"legal_base_year": 400000, "warning": "India fintech: RBI PA authorisation demands ₹15cr net worth (₹25cr at scale) + escrow + audits. As a sub-merchant on Razorpay/Cashfree you skip the licence but carry 1.5–2.3% TDR and settlement-cycle float risk."},
    },
    "payroll": {
        "us": {"legal_base_year": 25000, "warning": "Payroll product = per-state tax engines. Every new state is 2–6 weeks of registrations + edge-case maintenance forever. First 5 states ≈ 1 engineer-quarter."},
        "india": {"legal_base_year": 200000, "warning": "India payroll = EPF/ESI/PT/LWF per state + inspection exposure. EPF arrears carry damages up to 25% + interest — build the filing calendar before the first client."},
    },
    "health": {"us": {"legal_base_year": 30000, "warning": "HIPAA program (BAAs, logging, breach process) is $10k–$50k before your first patient row exists."}},
}


class FinancialAgent(Agent):
    id = "financial"
    title = "Financial Reality & Burn Calculator"
    icon = "🔥"
    tab = 8

    async def build(self, ev: Evidence) -> dict:
        geo = ev.req.geography.value if ev.req.geography.value in COST_MODELS else "global"
        m = dict(COST_MODELS[geo])
        sector = ev.sector
        warnings: list[str] = []
        if sector in SECTOR_COST_OVERRIDES:
            ov = SECTOR_COST_OVERRIDES[sector].get(geo) or SECTOR_COST_OVERRIDES[sector].get("us")
            if ov:
                m.update(ov)
                warnings.append(ov["warning"])

        team = ev.req.team_size
        engineers = max(1, team - 1)
        model = {
            "currency": m["currency"],
            "team_size": team,
            "salary_engineer_loaded": m["engineer_loaded"],
            "salary_founder_draw": m["founder_draw"],
            "infra_month": m["infra_base_month"],
            "tools_month": m["tools_per_seat_month"] * team,
            "legal_year": m["legal_base_year"],
            "runway_target_months": ev.req.runway_target_months,
            "formulas": {
                "payroll_month": "founder_draw/12 + engineers × engineer_loaded/12",
                "burn_month": "payroll + infra + tools + legal/12",
                "capital_needed": "burn × runway_target",
                "breakeven_customers": "burn / (ARPA × gross_margin)",
            },
        }
        pricing_section = None  # filled by pipeline from pricing agent if present? keep independent:
        # Independent ARPA assumption by sector/geo (the pricing tab decodes real ones)
        arpa_guess = (999 if geo == "india" else 29) if sector in ("saas", "devtools", "generic") else (2499 if geo == "india" else 79)
        gm = 0.62 if sector in ("fintech", "payroll") else 0.82
        payroll = m["founder_draw"] / 12 + engineers * m["engineer_loaded"] / 12
        burn = payroll + m["infra_base_month"] + m["tools_per_seat_month"] * team + m["legal_base_year"] / 12
        model.update(
            {
                "computed": {
                    "payroll_month": round(payroll),
                    "burn_month": round(burn),
                    "capital_needed": round(burn * ev.req.runway_target_months),
                    "breakeven_customers": round(burn / (arpa_guess * gm)) if arpa_guess * gm else None,
                    "arpa_assumption": arpa_guess,
                    "gross_margin_assumption": gm,
                },
                "sensitivity": [
                    {"scenario": "Salary −25% (co-founders underpay themselves)", "burn_delta": round(-0.25 * payroll)},
                    {"scenario": "Add 1 engineer", "burn_delta": round(m["engineer_loaded"] / 12)},
                    {"scenario": "Compliance incident (audit/penalty/counsel)", "burn_delta": round(m["legal_base_year"])},
                    {"scenario": "Infra 3× (growth month)", "burn_delta": round(2 * m["infra_base_month"])},
                ],
                "warnings": warnings
                + [
                    "Zero sugarcoating: founder draw is optional, compliance is not. Cut your own salary before the statutory calendar.",
                    f"Runway rule: at {ev.req.runway_target_months} months target, start raising/selling at {max(3, ev.req.runway_target_months - 5)} months left — later than that you negotiate from weakness.",
                    "Everything here is pre-revenue math. The ONLY thing that changes it is revenue; every rupee/dollar of MRR extends runway linearly.",
                ],
            }
        )
        return model

    def summarize(self, ev: Evidence, data: dict) -> str:
        c = data["computed"]
        return (
            f"Team of {data['team_size']} @ {data['currency']}{c['burn_month']:,}/mo burn → {data['currency']}{c['capital_needed']:,} capital for the {data['runway_target_months']}-month target; "
            f"breakeven at ~{c['breakeven_customers']} customers (ARPA {data['currency']}{c['arpa_assumption']})."
        )

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. Given this burn model, name the single largest cost lever and the honest reason founders fail to pull it."
