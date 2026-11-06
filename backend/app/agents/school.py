"""Tab 15 — Founder School: the knowledge transfer.

The curriculum someone who has been through zero -> scale would teach a
first-time builder: mental models, money mechanics with the founder's own
numbers substituted in, user psychology, distribution, operations, and the
fundraising game. Deterministic and offline - the personalization comes from
the decoded report, not from a model.
"""
from __future__ import annotations

from ..data import dna as dna_kb
from ..data import school as KB
from ..models import Evidence
from .base import Agent


def _num(v, currency="$") -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    if currency == "₹":
        if abs(n) >= 1e7:
            return f"₹{n / 1e7:,.1f}Cr"
        if abs(n) >= 1e5:
            return f"₹{n / 1e5:,.1f}L"
        return f"₹{n:,.0f}"
    if abs(n) >= 1e6:
        return f"${n / 1e6:,.1f}M"
    return f"{currency}{n:,.0f}"


class SchoolAgent(Agent):
    id = "school"
    title = "Founder School — The Knowledge Transfer"
    icon = "✦"
    tab = 15

    async def build(self, ev: Evidence) -> dict:
        sections = getattr(self, "sections", {}) or {}
        computed = ((sections.get("financial") or {}).get("data") or {}).get("computed") or {}
        ms = (sections.get("marketsize") or {}).get("data") or {}
        ue = (ms.get("assumptions") or {})
        currency = ue.get("currency") or ("₹" if ev.req.geography.value == "india" else "$")
        arpa = ue.get("arpa") or computed.get("arpa_assumption")
        burn = computed.get("burn_month")
        breakeven = computed.get("breakeven_customers")
        capital = computed.get("capital_needed")
        gm = computed.get("gross_margin_assumption") or (0.62 if ev.sector in ("fintech", "payroll") else 0.82)

        # personalize the money lessons with the founder's own decoded numbers
        personal: dict[str, str] = {}
        if arpa and burn:
            monthly_profit = arpa * gm
            payback_months = round(arpa / monthly_profit) if monthly_profit else None
            personal["the_one_equation"] = (
                f"With YOUR brief's numbers: one customer pays {_num(arpa, currency)}/month at "
                f"{int(gm * 100)}% gross margin = {_num(monthly_profit, currency)} profit/month. Your burn is "
                f"{_num(burn, currency)}/month, so you need about {breakeven} such customers to cover the whole burn. "
                "That's the whole game - now every feature decision is 'does this get me to that number faster?'"
            )
            personal["cac_ltv"] = (
                f"Your 12-month CAC ceiling: if a customer pays {_num(arpa, currency)}/month, spend at most "
                f"{_num(arpa * 12 * gm, currency)} to acquire one and you break even in year one - everything "
                f"they stay beyond that is profit. Your brief's current LTV:CAC proxy is "
                f"{(ms.get('unit_economics') or {}).get('ltv_cac_ratio', '—')}."
            )
        if capital:
            personal["oxygen"] = (
                f"YOUR oxygen: {_num(capital, currency)} buys {ev.req.runway_target_months} months at your current "
                f"burn of {_num(burn, currency)}/month. Every month you delay launch extends the date you run out. "
                "Decide accordingly."
            )
        if burn and breakeven:
            personal["runway_discipline"] = (
                f"Your sensitivity: cut burn by 25% and breakeven drops from {breakeven} customers to "
                f"about {round(breakeven * 0.75):,}. That's why salary discipline is a strategy, not a sacrifice."
            )

        sector_note = (
            f"Watching a {ev.sector} company in this brief? Notice which tab patterns repeat across its "
            f"features - that's the sector's playbook showing itself."
        )

        phases_out = []
        for phase in KB.PHASES:
            lessons = []
            for lid in phase["lesson_ids"]:
                l = KB.LESSONS.get(lid)
                if not l:
                    continue
                lessons.append({
                    "id": lid,
                    "title": l["title"],
                    "lesson": l["lesson"],
                    "truth": l["truth"],
                    "action": l["action"],
                    "terms": l["terms"],
                    "with_your_numbers": personal.get(lid),
                })
            phases_out.append({
                "phase": phase["phase"],
                "name": phase["name"],
                "why": phase["why"],
                "lessons": lessons,
            })

        return {
            "phases": phases_out,
            "vocabulary": {
                "business": dna_kb.BUSINESS_GLOSSARY,
                "psychology": dna_kb.PSYCH_GLOSSARY,
            },
            "sector_note": sector_note,
            "note": ("Read phases 1-3 before you write another line of code. Phases 4-6 are for the week "
                     "you decide to commit. Every lesson's 'do this now' is small on purpose - the whole "
                     "curriculum is doable alongside a job."),
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        n = sum(len(p["lessons"]) for p in data["phases"])
        return (f"{n}-lesson knowledge transfer in {len(data['phases'])} phases: what a startup is, the money "
                f"mechanics with your own numbers, user psychology, distribution, operations, and the "
                f"fundraising game. Built for someone starting from zero.")
