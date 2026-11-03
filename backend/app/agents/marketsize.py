"""Tab 13 — market sizing + capital strategy.

Bottom-up TAM/SAM/SOM with the formula printed next to every number, plus
raise vs bootstrap math. Every figure is an editable assumption, not a fact.
"""
from __future__ import annotations

from ..data import marketsize as KB
from ..models import Evidence
from .base import Agent


def _compact(n: float, currency: str) -> str:
    if currency == "₹":
        if abs(n) >= 1e7:
            return f"₹{n / 1e7:,.1f}Cr"
        if abs(n) >= 1e5:
            return f"₹{n / 1e5:,.1f}L"
        return f"₹{n:,.0f}"
    if abs(n) >= 1e9:
        return f"${n / 1e9:,.1f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:,.1f}M"
    if abs(n) >= 1e3:
        return f"${n / 1e3:,.0f}K"
    return f"{currency}{n:,.0f}"


FMF_CHECKLIST = [
    {"q": "Have you personally felt this problem for 6+ months (not just observed it)?", "weight": "high"},
    {"q": "Can you name 20 people who have this problem, reachable within 48 hours?", "weight": "high"},
    {"q": "Have you shipped software/processes in this exact domain before?", "weight": "medium"},
    {"q": "Does this wedge need relationships you do NOT have (enterprise, government, banks)?", "weight": "high", "invert": True},
    {"q": "Could a competitor clone your MVP in one sprint once they see it?", "weight": "medium", "invert": True},
    {"q": "Are you willing to run this for 3 years at below-market salary?", "weight": "high"},
]

INVESTOR_QUESTION_MAP = [
    {"question": "How big is this market, bottom-up?", "answered_by": "Tab 13 — the TAM/SAM/SOM table with formulas"},
    {"question": "Who has this pain, and how do you know?", "answered_by": "Tab 1 — pain points with sources · Tab 7 — complaint clusters"},
    {"question": "Why hasn't this been done / why does the incumbent let you?", "answered_by": "Tab 1 — moats · Tab 2 — alternatives scan"},
    {"question": "What will you charge and why will anyone pay it?", "answered_by": "Tab 6 — decoded tiers + unit economics"},
    {"question": "How do you acquire the first 10 and the next 100, free?", "answered_by": "Tab 9 — ranked loops + first-10 plan"},
    {"question": "What kills companies like this one?", "answered_by": "Tab 4 — matched failure post-mortems"},
    {"question": "What does it cost to reach breakeven?", "answered_by": "Tab 8 — burn, capital, breakeven customers"},
    {"question": "What compliance wall stands between you and launch?", "answered_by": "Tab 3 — costed statutory checklist"},
]


class MarketSizeAgent(Agent):
    id = "marketsize"
    title = "Market Sizing & Capital Strategy"
    icon = "◎"
    tab = 13

    async def build(self, ev: Evidence) -> dict:
        geo = ev.req.geography.value
        sector_bases = KB.MARKET_BASES.get(ev.sector) or KB.MARKET_BASES["generic"]
        base = sector_bases.get(geo) or sector_bases.get("global") or list(KB.MARKET_BASES["generic"].values())[0]
        tam_base = (KB.MARKET_BASES.get(ev.sector) or KB.MARKET_BASES["generic"]).get("global", base)

        # live ARPA/burn from the tabs that computed them (sections built earlier)
        sections = getattr(self, "sections", {}) or {}
        ue = ((sections.get("pricing") or {}).get("data") or {}).get("unit_economics") or {}
        arpa = ue.get("arpa") or (999 if geo == "india" else 29)
        currency = ue.get("currency") or ("₹" if geo == "india" else "$")
        computed = ((sections.get("financial") or {}).get("data") or {}).get("computed") or {}
        burn = computed.get("burn_month")
        breakeven = computed.get("breakeven_customers")

        units = base["buying_units"]
        annual = arpa * 12
        tam = tam_base["buying_units"] * annual
        sam = units * annual
        som_customers = {y: round(units * pct) for y, pct in KB.ADOPTION_CURVE.items()}
        som_values = {y: round(units * pct * annual) for y, pct in KB.ADOPTION_CURVE.items()}

        # does the math close? year-3 obtainable customers vs what the team needs
        verdict, verdict_tone = "UNKNOWN — breakeven missing; fill the burn calculator (Tab 8).", "amber"
        if breakeven:
            y3 = som_customers[3]
            if y3 < breakeven:
                verdict = (f"MATH DOESN'T CLOSE: year-3 obtainable customers ({y3:,}) < breakeven ({breakeven:,}) "
                           f"at this team size. Shrink the team, raise the price, or widen the wedge — the order "
                           f"of those three levers is exactly your strategy.")
                verdict_tone = "red"
            elif y3 >= breakeven * 5:
                verdict = (f"MATH CLOSES COMFORTABLY: year-3 obtainable ({y3:,}) is {y3 // max(breakeven, 1)}× breakeven. "
                           f"Your risk is execution and distribution, not demand arithmetic.")
                verdict_tone = "green"
            else:
                verdict = (f"MATH CLOSES, THINLY: year-3 obtainable ({y3:,}) vs breakeven ({breakeven:,}) leaves no "
                           f"slack for churn or slow quarters. Prove retention early or trim the plan.")
                verdict_tone = "amber"

        norms = KB.FUNDING_NORMS.get(geo) or KB.FUNDING_NORMS["global"]
        raise_18 = round(burn * 18 * 1.25) if burn else None
        dilution_pct = round(100 * raise_18 / norms["pre_seed_cap_usd"]) if raise_18 else None

        capital = {
            "recommended_raise": raise_18,
            "raise_formula": "burn × 18 months × 1.25 buffer — 18mo buys two iterations past the first milestone",
            "raise_when": "NOT now. Raise after timeline gate G1 (problem custody + first paid pilots) — pre-gate money buys nothing but dilution.",
            "dilution_at_geo_cap_pct": dilution_pct,
            "dilution_formula": "raise ÷ geo-typical pre-seed cap (SAFE conversion, approximate)",
            "geo_norms": norms,
            "bootstrap_note": (
                f"Bootstrap benchmark: 3-yr SOM of {_compact(som_values[3], currency)} vs {_compact(breakeven * arpa * 12, currency)} "
                "breakeven revenue — if you can live on the gap, keep the equity; raise for speed, not survival."
                if breakeven else "Fill Tab 8 to unlock the bootstrap benchmark."
            ),
        }

        money_signals = [
            {"raw": m["raw"], "context": m["context"]}
            for m in self._money_in_evidence(ev)
        ][:4]

        return {
            "market_base": {**base, "sector": ev.sector, "geography": geo},
            "assumptions": {
                "arpa": arpa,
                "currency": currency,
                "arpa_source": "decoded tiers (Tab 6)" if ue.get("arpa") else "geography default — edit in the Tab 6 sandbox",
            },
            "tam": {"value": round(tam), "display": _compact(tam, currency), "basis": tam_base["basis"]},
            "sam": {"value": round(sam), "display": _compact(sam, currency), "basis": base["basis"]},
            "som_by_year": [
                {"year": f"Year {y}", "customers": som_customers[y], "value": som_values[y],
                 "display": _compact(som_values[y], currency), "adoption": f"{KB.ADOPTION_CURVE[y] * 100:.1f}%"}
                for y in sorted(KB.ADOPTION_CURVE)
            ],
            "formulas": [
                "TAM = sector buying units (global) × ARPA × 12",
                "SAM = sector buying units (your geography wedge) × ARPA × 12",
                "SOM(y) = SAM units × adoption(y) × ARPA × 12 — adoption is earned: 0.5% → 1.5% → 3.0%",
            ],
            "verdict": verdict,
            "verdict_tone": verdict_tone,
            "capital_strategy": capital,
            "founder_market_fit": {
                "instruction": "Score honestly: each 'no' on a high-weight question is a co-founder search or a wedge change, not a note-to-self.",
                "questions": FMF_CHECKLIST,
            },
            "investor_question_map": INVESTOR_QUESTION_MAP,
            "evidence_money_signals": money_signals,
            "note": "All figures are planning-grade starting assumptions — replace the ARPA and base with your own research and every number recomputes.",
        }

    @staticmethod
    def _money_in_evidence(ev: Evidence) -> list[dict]:
        from ..text import money_values
        return money_values(ev.snippet_pool(4000))

    def summarize(self, ev: Evidence, data: dict) -> str:
        cur = data["assumptions"]["currency"]
        cap = data["capital_strategy"]
        dil = cap.get("dilution_at_geo_cap_pct")
        return (f"SAM {data['sam']['display']} · 3-yr SOM {data['som_by_year'][-1]['display']} "
                f"(bottom-up, formulas shown). "
                + (f"Raise ~{cap['recommended_raise'] and _compact(cap['recommended_raise'], cur)} for 18 months "
                   f"≈ {dil}% dilution at the geo-typical cap — after gate G1." if cap.get("recommended_raise") else ""))

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject} ({ev.sector}/{ev.req.geography.value}). Given the sizing table, name the ONE "
            "assumption most likely to be wrong and by how much it would move the numbers — then say whether the "
            "founder should raise or bootstrap and why in one line."
        )
