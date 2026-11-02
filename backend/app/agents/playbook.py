"""Tab 12 — The Systematic Execution Playbook."""
from __future__ import annotations

from ..data import compliance as KB
from ..models import Evidence
from .base import Agent

GATEWAY_FRICTION = {
    "india": [
        {"step": "Razorpay/Cashfree account", "friction": "PAN + business proof + website/app review (they check your product exists and policies pages are live). Pre-revenue personal accounts get rejected for business KYC.", "fix": "Have: registered entity, live landing page, Privacy/Terms/Refund pages, and a working demo BEFORE applying.", "time": "2–7 days"},
        {"step": "Settlement & GST setup", "friction": "Settlements need a current account in the entity's name; personal accounts cause TDR settlement failures.", "fix": "Open current account with the incorporation certificate + GSTIN; reconcile TCS/TDS monthly.", "time": "1–2 weeks"},
        {"step": "If touching others' funds (PA model)", "friction": "RBI PA authorisation: ₹15cr net worth, escrow with eligible bank, system audit.", "fix": "Don't. Stay a sub-merchant; settle only your own revenue until scale demands more.", "time": "n/a — avoid"},
    ],
    "us": [
        {"step": "Stripe account", "friction": "EIN + entity docs + beneficial-ownership (FinCEN BOI) details. Personal SSN-only accounts work but entangle personal taxes.", "fix": "File EIN (free, same day) before applying; note the Corporate Transparency Act BOI filing.", "time": "1–3 days"},
        {"step": "Sales tax on SaaS", "friction": "Economic nexus ($100k typical) creates filings per state — the surprise audit generator.", "fix": "Track thresholds from day 1 (free tier of tax tools exists); register when crossed, not at audit.", "time": "Ongoing"},
        {"step": "If touching others' funds (money movement)", "friction": "State MTLs (49 + DC) or sponsor-bank partnership.", "fix": "Partner (BaaS) first; own licenses only when unit economics justify a 7-figure compliance program.", "time": "6–18 months BD"},
    ],
}

KYC_DOCS = {
    "india": ["Company PAN", "Certificate of Incorporation", "MOA/AOA", "GST registration", "Director KYC (DIN, PAN, Aadhaar-linked)", "Bank current account + cancelled cheque", "Board resolution for account signatory"],
    "us": ["EIN letter (CP 575)", "Articles of Incorporation/Organization", "Operating agreement / bylaws", "Beneficial ownership info (FinCEN BOI)", "Bank account letter", "W-9"],
    "global": ["Entity registration docs in home jurisdiction", "Tax ID equivalents", "Bank account in entity name", "Proof of address"],
}

SCALING_HURDLES = [
    {"hurdle": "Support load grows with users, not revenue", "strategy": "Instrument ticket-to-user ratio from day 1; self-serve docs before hiring; every ticket answered twice becomes a doc page."},
    {"hurdle": "Compliance scope expands with geography", "strategy": "Sequence expansions (see Jurisdiction decoder expansion order); one state/jurisdiction fully operational before adding the next."},
    {"hurdle": "Ops hiring precedes margin", "strategy": "Automate only the top-3 repeated ops tasks; measure time-per-task before automating anything else."},
    {"hurdle": "Churn surfaces at month 3+ (post-onboarding)", "strategy": "Cohort retention by acquisition month is the real P&L; fix onboarding when week-4 cohort dips below 40% (B2B)."},
    {"hurdle": "Pricing debt: early custom deals poison list pricing", "strategy": "All early discounts: manual, expiring, and documented; enterprise contracts stay on a separate SKU path."},
]


class PlaybookAgent(Agent):
    id = "playbook"
    title = "The Systematic Execution Playbook"
    icon = "🗺"
    tab = 12

    async def build(self, ev: Evidence) -> dict:
        geo = ev.req.geography.value if ev.req.geography.value in ("india", "us") else "us"
        landmines = KB.landmines_for(ev.sector, geo)
        critical = sorted([l for l in landmines if l["severity"] == "critical"], key=lambda x: {"Register licenses first": 0}.get(x["item"], 0))
        legal_steps = [{"action": f"File/obtain: {l['item']}", "cost": l["cost"], "window": l["time"]} for l in critical[:6]]

        phases = [
            {
                "phase": "Phase 0 — Validate (pre-code)",
                "steps": [
                    "20 problem interviews; log current spend + hours wasted per interviewee.",
                    "Sell the outcome manually to 3 customers (concierge MVP). Receipts or it didn't happen.",
                    "Write the one-page contribution-margin equation. Every future feature must not worsen it.",
                ],
                "hurdle": "Founder skips validation because building feels like progress.",
            },
            {
                "phase": "Phase 1 — Legal & compliance floor",
                "steps": legal_steps,
                "hurdle": "Licenses are parallelizable — start the slowest (entity + gateway KYC) in week 1, not after the product is 'ready'.",
            },
            {
                "phase": "Phase 2 — MVP build",
                "steps": [
                    "Auth + the ONE core action + manual back-office. Nothing else.",
                    "Wire the compliance-approved gateway with webhook idempotency (scaffold provided in Tab 10).",
                    "Instrument the single activation metric; review cohort weekly.",
                ],
                "hurdle": "Scope creep disguised as 'competitiveness'. You are replicating a wedge, not the incumbent's 15-year feature surface.",
            },
            {
                "phase": "Phase 3 — Payments & KYC friction",
                "steps": GATEWAY_FRICTION[geo],
                "hurdle": "Gateway account reviews reject pre-revenue sites without policy pages; prepare them before applying.",
            },
            {
                "phase": "Phase 4 — Distribution ignition",
                "steps": [
                    "Pick 2 zero-cost loops (Tab 9); give each a weekly scoreboard.",
                    "Ship the flagship content asset (teardown/calculator/comparison) in week 2, not month 6.",
                    "Ask every paying user for one referral at the moment of first value.",
                ],
                "hurdle": "Building for 6 weeks before any distribution act. Distribution starts before the product does.",
            },
            {
                "phase": "Phase 5 — Scaling mechanics",
                "steps": SCALING_HURDLES,
                "hurdle": "Scaling amplifies whatever unit economics you had — including broken ones.",
            },
        ]
        return {
            "phases": phases,
            "kyc_docs": KYC_DOCS[geo],
            "kill_criteria": [
                "G0: <5 strong-pain interviews → stop.",
                "G2: no channel produces signups twice → new channel, not new features.",
                "G5: week-4 cohort retention <25% → the wedge is wrong; return to interviews.",
            ],
            "note": "Sequenced by gates and dependencies, not calendar optimism. No dates are promised because no honest ones can be.",
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        return f"6 phases, {sum(len(p['steps']) for p in data['phases'])} sequenced steps, {len(data['kyc_docs'])} KYC documents pre-listed ({ev.req.geography.value})."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. Identify the step in this playbook that is most commonly delayed and what the delay actually costs."
