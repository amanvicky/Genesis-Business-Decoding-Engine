"""Tab 3 — Jurisdictional & Regulatory Complexity Decoder."""
from __future__ import annotations

from ..data import compliance as KB
from ..models import Evidence
from .base import Agent

SECTOR_NAME = {"payroll": "Payroll/HR", "fintech": "Fintech/Payments", "commerce": "Commerce", "health": "Health", "edu": "EdTech", "devtools": "DevTools", "saas": "SaaS", "logistics": "Logistics", "generic": "Generic"}


class ComplianceAgent(Agent):
    id = "compliance"
    title = "Jurisdictional & Regulatory Complexity Decoder"
    icon = "⚖️"
    tab = 3

    async def build(self, ev: Evidence) -> dict:
        geo = ev.req.geography.value
        sector = ev.sector
        landmines = KB.landmines_for(sector, geo)
        critical = [l for l in landmines if l["severity"] == "critical"]

        data: dict = {
            "sector_detected": SECTOR_NAME.get(sector, sector),
            "jurisdictions": {
                "us": geo in ("us", "global"),
                "india": geo in ("india", "global"),
            },
            "landmines": landmines,
            "critical_count": len(critical),
            "disclaimer": "Planning-grade intelligence synthesized from public statutes and regulator guidance. Verify with a licensed professional before filing anything.",
        }

        if data["jurisdictions"]["us"]:
            data["us_state_matrix"] = [
                {"state": s, "burden": d["cost"], "severity": d["severity"], "notes": d["why"]}
                for s, d in KB.US_STATES.items()
            ]
            data["us_payroll_matrix"] = KB.US_PAYROLL_MATRIX
            data["us_expansion_order"] = [{"state": s, "why": w} for s, w in KB.US_EXPANSION_ORDER]
        if data["jurisdictions"]["india"]:
            data["india_state_notes"] = [
                {"state": "Maharashtra", "note": "PTRC (Profession Tax) + LWF half-yearly; Mumbai S&E registration is slow — start it first."},
                {"state": "Karnataka", "note": "e-Prerana PT registration; IT-sector S&E exemptions need paperwork too; K-Tech incentives if registered."},
                {"state": "Delhi NCR", "note": "Delhi S&E + no LWF; most founder-friendly registrations timeline-wise."},
                {"state": "Tamil Nadu", "note": "TN LWF + PT; stricter factory/establishment inspections."},
            ]

        # Checklist: the ordered do-now list
        data["checklist"] = [
            {"order": i + 1, "item": l["item"], "cost": l["cost"], "time": l["time"]}
            for i, l in enumerate(
                sorted(landmines, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x["severity"], 4))[:12]
            )
        ]
        return data

    def summarize(self, ev: Evidence, data: dict) -> str:
        geo = "US + India (global view)" if data["jurisdictions"]["us"] and data["jurisdictions"]["india"] else ("United States" if data["jurisdictions"]["us"] else "India")
        return f"{data['sector_detected']} sector decoded for {geo}: {len(data['landmines'])} statutory obligations, {data['critical_count']} are launch-blocking."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}, sector {data['sector_detected']}, geo {ev.req.geography.value}. "
            "Name the single compliance item founders in this sector most often discover too late, and what it costs when they do."
        )
