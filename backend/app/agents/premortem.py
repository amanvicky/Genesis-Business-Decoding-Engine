"""Tab 4 — Pre-Mortem & Failure Post-Mortems."""
from __future__ import annotations

from ..data import failures as KB
from ..models import Evidence
from .base import Agent

QUESTIONS = [
    "If this dies, what does the autopsy say killed it: acquisition cost, retention, compliance, or platform dependence?",
    "Which number, if wrong by 30%, makes the model unworkable — and do you measure it today?",
    "What is your counterpart (platform, sponsor bank, gateway, regulator) allowed to change unilaterally that breaks you?",
    "Where exactly does your cash conversion cycle break: before revenue (credit), at revenue (collections), or after (refunds/chargebacks)?",
    "Which competitor died doing the same thing, and did they die from the model or from execution?",
    "What is the smallest experiment whose failure would stop you from building the next 3 months of features?",
]


class PremortemAgent(Agent):
    id = "premortem"
    title = "Pre-Mortem & Failure Post-Mortems"
    icon = "☠️"
    tab = 4

    async def build(self, ev: Evidence) -> dict:
        analogs = KB.matching_failures(ev.subject, ev.sector)
        if not analogs:
            analogs = KB.matching_failures(ev.sector, "generic")

        # Field reports: search for shutdowns/post-mortems in this exact domain
        from ..scrapers.client import Fetcher
        from ..scrapers.search import ddg_search

        f = Fetcher(ev)
        field_reports: list[dict] = []
        for q in [f'"{ev.subject}" shut down post-mortem why failed', f"{ev.sector} startup shut down 2024 2025 post-mortem"]:
            results = await ddg_search(f, q, 6)
            for r in results:
                if any(k in r["url"] for k in ["news.ycombinator.com", "reddit.com", "medium.com", "postmortem", "blog"]):
                    field_reports.append({"title": r["title"], "url": r["url"], "snippet": r["snippet"][:200]})

        # Derive common failure modes from the matched analogs
        modes: dict[str, int] = {}
        for a in analogs:
            text = (a["root_cause"] + " " + a["operational_flaw"]).lower()
            for mode, kws in {
                "Unit economics never closed": ["unit econom", "negative contribution", "margin", "cac", "ltv"],
                "Regulatory/licensing wall": ["regulat", "licen", "cfpb", "rbi", "compliance"],
                "Platform dependence": ["platform", "rented", "partner", "sponsor", "api"],
                "Demand was temporary": ["pandemic", "temporary", "cyclical", "shock", "rates"],
                "Pricing below cost": ["pric", "$0", "free", "unlimited", "below cost"],
                "Fixed costs before demand": ["fixed cost", "capex", "factory", "lease", "headcount"],
            }.items():
                if any(k in text for k in kws):
                    modes[mode] = modes.get(mode, 0) + 1
        ranked = sorted(modes.items(), key=lambda x: -x[1])

        return {
            "analogs": analogs,
            "field_reports": field_reports[:8],
            "common_failure_modes": [
                {"mode": m, "analogs_affected": c, "counter": self._counter(m)} for m, c in ranked
            ],
            "premortem_questions": QUESTIONS,
        }

    def _counter(self, mode: str) -> str:
        return {
            "Unit economics never closed": "Write the contribution-margin-per-user equation on one page. Update it weekly. If it needs 'scale' to turn positive, name the exact mechanism and deadline.",
            "Regulatory/licensing wall": "Map the license timeline before writing code; partner-licence routes (BaaS/PA) first, own-license second.",
            "Platform dependence": "Price the vendor's ability to raise rates or de-platform you; keep an exit abstraction layer from day one.",
            "Demand was temporary": "Identify the exogenous driver of your demand; stress-test at minus 50%.",
            "Pricing below cost": "Charge from customer #1. If you can't, the free cohort must produce measured proof, not vibes.",
            "Fixed costs before demand": "Rent variability: contractors before employees, usage-based infra before reserved capacity.",
        }.get(mode, "Instrument the failure mode; make it a number you review weekly.")

    def summarize(self, ev: Evidence, data: dict) -> str:
        names = ", ".join(a["name"] for a in data["analogs"][:3]) or "no direct analogs in the database"
        top = data["common_failure_modes"][0]["mode"] if data["common_failure_modes"] else "insufficient data"
        return f"{len(data['analogs'])} collapsed operators matched ({names}). Dominant death pattern in this domain: {top}."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. Write the founder's pre-mortem: it is 18 months from now and the company just died. "
            "State the 3 most probable causes of death given this domain's failure history, most-likely first."
        )
