"""Tab 13 — Adversarial Red-Team Simulator.

A virtual cross-examination panel (enterprise buyer, skeptical VC, regulatory
auditor) that reads the *assembled* report sections and attacks them: every
challenge cites the evidence that triggered it and states what answer survives.
This is why the agent runs last in the pipeline.
"""
from __future__ import annotations

from ..models import Evidence
from .base import Agent

PERSONA_META = [
    ("enterprise_buyer", "Enterprise Buyer (procurement)", "buys at $50k+/yr and has a security review gate"),
    ("skeptic_vc", "Skeptical VC (investment committee)", "funds scale and has seen this deck die before"),
    ("regulator", "Regulatory Auditor (exam team)", "checks licenses, KYC, and data handling first"),
]


class AdversaryAgent(Agent):
    id = "adversary"
    title = "Adversarial Red-Team Simulator"
    icon = "⚔"
    tab = 13

    async def build(self, ev: Evidence) -> dict:
        sections = getattr(self, "sections", {}) or {}

        def data(tab: str) -> dict:
            return (sections.get(tab) or {}).get("data") or {}

        pricing = data("pricing")
        compliance = data("compliance")
        structural = data("structural")
        premortem = data("premortem")
        features = data("features")
        financial = data("financial")
        darkweb = data("darkweb")
        ue = pricing.get("unit_economics") or {}

        buyer: list[dict] = []
        vc: list[dict] = []
        auditor: list[dict] = []

        # ---------------- enterprise buyer ----------------
        buyer.append({
            "severity": "fatal",
            "question": "Our procurement gate requires a security review: SOC 2 Type II (or equivalent), SSO, and a signed DPA. Which of the three can you show today?",
            "why_fatal": "No security packet = no enterprise deal regardless of product quality; this is the #1 silent killer of B2B pipelines.",
            "triggered_by": "no SOC2/SSO evidence in the feature decode",
            "passing_answer": "SOC 2 Type II report (or a dated roadmap commitment your security team accepts), SAML SSO in a live demo, DPA + sub-processor list on the website.",
        })
        tier_names = [str(t.get("name", "")).lower() for t in (pricing.get("tiers") or [])]
        if not any("enterprise" in n or "business" in n or "team" in n for n in tier_names):
            buyer.append({
                "severity": "serious",
                "question": "Your pricing has no org-sized tier. How do I buy 200 seats without you re-negotiating every year?",
                "why_fatal": "Procurement needs a predictable SKU path; ad-hoc enterprise pricing fails vendor onboarding.",
                "triggered_by": f"decoded tiers: {', '.join(n for n in tier_names) or 'none'}",
                "passing_answer": "A published team/business tier with seat or record bands and an enterprise 'contact us' lane.",
            })
        if darkweb.get("findings") and any(f.get("risk") in ("high", "medium") for f in darkweb["findings"]):
            buyer.append({
                "severity": "serious",
                "question": "Your name surfaces in OSINT/paste findings. Why should my security team approve a vendor with public exposure?",
                "why_fatal": "Third-party risk teams reject vendors with unexplained breach surface.",
                "triggered_by": "Dark-Web Shield findings flagged high/medium",
                "passing_answer": "A one-page incident history: what surfaced, remediation, current monitoring.",
            })
        buyer.append({
            "severity": "probe",
            "question": "What is your contractual uptime, and what do we get when you miss it?",
            "why_fatal": "No SLA = no production workloads; buyers plan around vendor downtime.",
            "triggered_by": "no SLA/uptime commitments decoded",
            "passing_answer": "A stated uptime target with service credits, even at 99.5% for MVP.",
        })

        # ---------------- skeptical VC ----------------
        ratio = ue.get("ltv_cac_ratio")
        if ratio is not None and ratio < 3:
            vc.append({
                "severity": "fatal",
                "question": f"Your own model shows LTV:CAC of {ratio}×. You are buying revenue at a loss — why does scale fix a broken unit?",
                "why_fatal": "Scale multiplies whatever unit economics exist, positive or negative.",
                "triggered_by": f"LTV {ue.get('currency','')}{ue.get('ltv')} vs organic-CAC proxy {ue.get('currency','')}{ue.get('cac_organic_proxy')}",
                "passing_answer": "A channel plan with measured CAC ≤ 1/3 of LTV, or a price/margin change that gets there.",
            })
        vc.append({
            "severity": "fatal",
            "question": "Show me week-4 cohort retention for the core action — not signup retention. What is the number?",
            "why_fatal": "LTV without retention curves is a spreadsheet fiction; every dead company in the pre-mortem had confident LTV slides.",
            "triggered_by": f"pre-mortem dominant death pattern: {premortem.get('common_failure_modes', [{}])[0].get('mode', 'unit economics')}",
            "passing_answer": "A cohort chart by acquisition month with ≥40% (B2B) week-4 core-action retention.",
        })
        moats = structural.get("moats") or []
        if not moats:
            vc.append({
                "severity": "fatal",
                "question": "Which of your moats survives your incumbent shipping your wedge as a checkbox?",
                "why_fatal": "No detected moat + replicable wedge = you built their free feature roadmap.",
                "triggered_by": "no moat-type evidence in the structural corpus",
                "passing_answer": "A named moat (data, network, switching cost, regulatory) with the mechanism it compounds through.",
            })
        top_analog = (premortem.get("analogs") or [{}])[0]
        if top_analog.get("name"):
            vc.append({
                "severity": "serious",
                "question": f"{top_analog.get('name')} died here: {top_analog.get('operational_flaw', '')[:120]} What is structurally different about you?",
                "why_fatal": "The same operational flaw with better execution is still the same flaw.",
                "triggered_by": "matched failure analog in this domain",
                "passing_answer": "A structural difference in revenue model, cost structure, or distribution — not 'we execute better'.",
            })
        computed = financial.get("computed") or {}
        if computed.get("breakeven_customers"):
            vc.append({
                "severity": "serious",
                "question": f"Breakeven is ~{computed['breakeven_customers']} customers on a {financial.get('team_size','?')}-person team. Show the first 10 named prospects.",
                "why_fatal": "Breakeven math without a pipeline is a runway countdown, not a plan.",
                "triggered_by": f"burn {financial.get('currency','')}{computed.get('burn_month')}/mo, ARPA assumption {computed.get('arpa_assumption')}",
                "passing_answer": "Ten named prospects with a current pain event each (job post, deadline, complaint).",
            })

        # ---------------- regulatory auditor ----------------
        critical = [l for l in (compliance.get("landmines") or []) if l.get("severity") == "critical"]
        for l in critical[:3]:
            auditor.append({
                "severity": "fatal" if l is critical[0] else "serious",
                "question": f"You flagged '{l.get('item')}' as launch-blocking. Show the application receipt — not the plan.",
                "why_fatal": "Regulators examine the artifact, and operating before the license is personal-liability territory.",
                "triggered_by": f"compliance landmine: {l.get('item')} ({l.get('time')})",
                "passing_answer": f"Filed application / registration number for {l.get('item')}, or a partner structure that legally avoids it.",
            })
        if ev.sector == "fintech":
            auditor.append({
                "severity": "fatal",
                "question": "Walk me through KYC end-to-end: which regulated entity holds the customer relationship, and who bears AML liability?",
                "why_fatal": "In both the US (BSA) and India (PMLA) the liability lands on a licensed entity — if it's not you, your sponsor contract decides who gets terminated.",
                "triggered_by": "fintech sector detected; BaaS/PA structures decoded",
                "passing_answer": "A named regulated counterparty (sponsor bank / licensed PA), a signed program agreement, and your place in the KYC chain.",
            })
        if ev.sector == "payroll":
            auditor.append({
                "severity": "serious",
                "question": "You file taxes on the client's behalf — who signs Form 8655 (US) / holds the PT & SUI registrations (IN), and what happens when a client walks mid-quarter?",
                "why_fatal": "Reporting-agent status transfers filing liability; mid-quarter exits strand statutory filings.",
                "triggered_by": "payroll sector: per-state/per-state-code registration engine",
                "passing_answer": "Reporting-agent authorizations per client, plus an offboarding runbook that files final returns.",
            })
        auditor.append({
            "severity": "serious",
            "question": "Show me your consent artifacts and deletion pipeline: what data do you hold, on what lawful basis, and how does a deletion request execute end-to-end?",
            "why_fatal": "US state privacy laws and India's DPDP Act both make 'we'll add it later' a finable position.",
            "triggered_by": "DPDP/CCPA-family landmines decoded",
            "passing_answer": "A data map + consent record store + a tested deletion path under 30 days.",
        })
        auditor.append({
            "severity": "probe",
            "question": "If your payment webhook processes the same charge twice, who eats the reversal — and can you prove it didn't?",
            "why_fatal": "Idempotency failures are the most common money-integrity finding in gateway audits.",
            "triggered_by": "webhook idempotency scaffold in the architecture section",
            "passing_answer": "Persist-then-ack webhook with a unique event log you can show an examiner.",
        })

        personas = []
        for pid, role, stance in PERSONA_META:
            kills = {"enterprise_buyer": buyer, "skeptic_vc": vc, "regulator": auditor}[pid]
            fatal = sum(1 for k in kills if k["severity"] == "fatal")
            personas.append({
                "persona": pid,
                "role": role,
                "stance": stance,
                "verdict": (
                    f"{fatal} fatal gap(s) found — answer them before building further."
                    if fatal
                    else "No fatal gaps on this axis; challenges are preparation, not blockers."
                ),
                "kills": kills,
            })

        fatal_count = sum(1 for k in buyer + vc + auditor if k["severity"] == "fatal")
        serious_count = len(buyer) + len(vc) + len(auditor) - fatal_count
        return {
            "fatal_count": fatal_count,
            "serious_count": serious_count,
            "personas": personas,
            "overall_verdict": (
                f"Playbook has {fatal_count} fatal gap(s) that would end the company in cross-examination."
                if fatal_count
                else "Playbook survives first-pass cross-examination — the challenges that remain are execution probes."
            ),
            "protocol": [
                "Answer every challenge in writing, 25 words max — vague answers lose.",
                "Any 'fatal' left unanswered after 48 hours = that assumption is not real; cut it.",
                "Re-run this simulator after each major pivot; the panel only gets sharper.",
                "Passing answers require artifacts (reports, receipts, filings) — 'it's on the roadmap' scores zero.",
            ],
            "identity": ev.identity,
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        return f"{data['fatal_count']} fatal, {data['serious_count']} serious challenges across 3 adversarial personas. {data['overall_verdict']}"

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. You are the most hostile member of the panel. Add ONE challenge the deterministic "
            "panel missed — the question a founder cannot answer without evidence."
        )
