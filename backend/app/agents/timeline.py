"""Tab 5 — Genesis & Historical Timeline (company mode) / Gate-based milestones (idea mode)."""
from __future__ import annotations

import re

from ..models import Evidence
from ..text import find_years, sentences
from .base import Agent

PIVOT_WORDS = ["pivot", "shifted", "refocus", "changed its business", "moved from", "originally", "started as", "began as"]


class TimelineAgent(Agent):
    id = "timeline"
    title = "Genesis & Historical Timeline"
    icon = "🕰"
    tab = 5

    async def build(self, ev: Evidence) -> dict:
        if ev.req.mode.value == "company" and ev.wiki:
            return self._company_timeline(ev)
        return self._idea_gates(ev)

    def _company_timeline(self, ev: Evidence) -> dict:
        text = (ev.wiki or {}).get("history") or (ev.wiki or {}).get("extract", "")
        events: list[dict] = []
        seen_years: set[int] = set()
        for year, s in find_years(text):
            if year in seen_years:
                # merge into the same year's event
                for e in events:
                    if e["year"] == year:
                        e["event"] += " · " + s
                        break
                continue
            seen_years.add(year)
            events.append({"year": str(year), "event": s[:280], "pivot": any(w in s.lower() for w in PIVOT_WORDS)})

        # Add release events from GitHub as late-stage timeline entries
        for rel in ev.releases[-15:]:
            if rel.get("date"):
                events.append({"year": rel["date"][:4], "event": f"Shipped: {rel['name']}", "pivot": False, "date": rel["date"]})

        # Annual revenue milestones from SEC EDGAR (the only free structured financial archive)
        for rev in ev.financials[-8:]:
            events.append(
                {
                    "year": str(rev["fy_end"])[:4],
                    "event": f"Annual revenue ${rev['revenue_usd']:,} (10-K, FY ending {rev['fy_end']})",
                    "pivot": False,
                    "date": rev["fy_end"],
                }
            )

        events.sort(key=lambda e: (e.get("date") or e["year"]))
        pivots = [e for e in events if e["pivot"]]
        funding = [
            {"amount": m.group(0), "context": s[:200]}
            for s in sentences(text)
            for m in [re.search(r"(\$\s?[\d.]+[MB]\b|₹\s?[\d,.]+ (?:crore|cr|billion))", s)]
            if m and re.search(r"rais\w+|fund\w+|series [a-d]|investment", s, re.I)
        ][:8]
        return {
            "mode": "company",
            "founded_year": (ev.wiki or {}).get("founded_year"),
            "events": events[:40],
            "pivots": pivots,
            "funding_events": funding,
            "source": (ev.wiki or {}).get("url", ""),
        }

    def _idea_gates(self, ev: Evidence) -> dict:
        geo = ev.req.geography.value
        gates = [
            {"gate": "G0 — Problem custody", "exit_criteria": "20 problem interviews logged; at least 5 people currently pay money or waste >3h/week on the problem. Kill criteria: <5 strong-pain interviews → stop.", "artifacts": ["interview log", "current-spend tally"]},
            {"gate": "G1 — Mechanism proof", "exit_criteria": "One manual, no-code delivery of the value to 3 paying (even ₹100/$5) customers. No product build yet.", "artifacts": ["3 receipts", "delivery checklist"]},
            {"gate": "G2 — Repeatable demand", "exit_criteria": "One acquisition channel produces signups twice without founder luck (e.g., 2 posts, 2 tool pages). Kill criteria: CAC-implied > 1/3 of LTV at any channel.", "artifacts": ["channel log", "cohort sheet"]},
            {"gate": "G3 — Compliance checkpoint", "exit_criteria": f"Jurisdiction checklist started ({'Razorpay KYC docs + GST' if geo == 'india' else 'EIN + workers comp + state registrations'}); regulated-data decision made (what you will NOT store).", "artifacts": ["entity docs", "gateway account", "data map"]},
            {"gate": "G4 — Payment live", "exit_criteria": "First automated invoice/subscription charged and settled; refund path tested with a real transaction.", "artifacts": ["webhook logs", "first settlement"]},
            {"gate": "G5 — Retention evidence", "exit_criteria": "Cohort week-4 retention of the core action > 40% (B2B) or > 25% (B2C). Kill criteria: below that, the wedge is wrong — return to G0.", "artifacts": ["cohort chart"]},
        ]
        return {
            "mode": "idea",
            "gates": gates,
            "note": "No dates — gates, not gantt. You move when the exit criteria are met, not when a calendar says so.",
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        if data.get("mode") == "company":
            fy = data.get("founded_year")
            p = len(data.get("pivots", []))
            return f"{len(data['events'])} decoded milestones{' from ' + str(fy) if fy else ''} — {p} strategic pivot(s) identified, {len(data.get('funding_events', []))} funding events."
        return f"{len(data['gates'])} execution gates with kill criteria — gate-based sequencing, no fake dates."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        if data.get("mode") == "company":
            return f"Subject: {ev.subject}. From the timeline, identify the ONE pivot that changed the company's fate and what condition triggered it."
        return f"Subject (idea): {ev.subject}. Name the single riskiest assumption that gate G2 must falsify."
