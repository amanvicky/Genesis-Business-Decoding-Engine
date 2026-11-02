"""Pipeline orchestrator: recon → 12 analysis agents → assembled Report.

Streams NDJSON events:
  {"type":"log","level","agent","msg"}
  {"type":"status","step","agent","state","title","ms"?}
  {"type":"section","section":{...}}          (arrives tab by tab, live)
  {"type":"done","report":{...}}
  {"type":"error","msg"}
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import llm
from .agents import (
    AdversaryAgent,
    ComplianceAgent,
    DarkWebAgent,
    DistributionAgent,
    FeaturesAgent,
    FinancialAgent,
    FrictionAgent,
    PlaybookAgent,
    PremortemAgent,
    PricingAgent,
    StructuralAgent,
    TechArchAgent,
    TimelineAgent,
)
from .agents.base import Agent, Emit
from .agents.recon import ReconAgent
from .models import AnalyzeRequest, Evidence, Report
from .text import detect_sector

AGENTS: list[type[Agent]] = [
    StructuralAgent,
    FeaturesAgent,
    ComplianceAgent,
    PremortemAgent,
    TimelineAgent,
    PricingAgent,
    FrictionAgent,
    FinancialAgent,
    DistributionAgent,
    TechArchAgent,
    DarkWebAgent,
    PlaybookAgent,
    AdversaryAgent,  # must run last — it cross-examines the assembled report
]


def _post_process(sections: dict) -> None:
    """Cross-section enrichment that needs two agents' outputs at once."""
    fin = (sections.get("financial") or {}).get("data") or {}
    burn = ((fin.get("computed") or {}).get("burn_month"))
    pricing = sections.get("pricing")
    if pricing and burn:
        data = dict(pricing.get("data") or {})
        data["sandbox"] = {**((data.get("sandbox") or {})), "opex_month": burn}
        sections["pricing"] = {**pricing, "data": data}


async def run_pipeline(req: AnalyzeRequest, emit: Emit) -> Report:
    subject = req.query.strip()
    ev = Evidence(req=req, subject=subject)
    ev.sector = detect_sector(subject + " " + (req.context or ""))

    await emit({"type": "log", "level": "agent", "agent": "genesis", "msg": f"GENESIS pipeline engaged — decoding '{subject}'"})
    await emit({"type": "log", "level": "info", "agent": "genesis", "msg": f"LLM enrichment: {'available (Ollama)' if await llm.available() else 'offline — deterministic analysis engine only'}"})

    recon = ReconAgent()
    await emit({"type": "status", "step": 0, "agent": recon.id, "state": "running", "title": recon.title})
    try:
        ev = await recon.run_recon(ev, emit)
        await emit({"type": "status", "step": 0, "agent": recon.id, "state": "done", "title": recon.title})
    except Exception as exc:
        await emit({"type": "log", "level": "warn", "agent": recon.id, "msg": f"recon degraded ({type(exc).__name__}: {exc}) — continuing with knowledge bases"})

    # Re-detect sector with the full evidence corpus (query alone is often ambiguous)
    refined = detect_sector(subject + " " + (req.context or "") + " " + ev.snippet_pool(4000))
    if refined != "generic":
        ev.sector = refined
        await emit({"type": "log", "level": "info", "agent": "genesis", "msg": f"sector refined via evidence corpus → {refined}"})

    sections = {}
    for agent_cls in AGENTS:
        agent = agent_cls()
        probe: list[dict] = []

        async def capture(event: dict, _p: list[dict] = probe) -> None:
            _p.append(event)
            await emit(event)

        await agent.run(ev, capture, sections=sections)
        for event in probe:
            if event.get("type") == "section":
                sec = event["section"]
                sections[sec["id"]] = sec

    _post_process(sections)

    report = Report(
        request=req,
        subject=subject,
        sector=ev.sector,
        generated_at=datetime.now(timezone.utc).isoformat(),
        sections=sections,
        sources=ev.sources,
    )
    await emit({"type": "log", "level": "success", "agent": "genesis", "msg": f"decode complete — {len(sections)}/{len(AGENTS)} sections, {len(ev.sources)} sources cited"})
    await emit({"type": "done", "report": report.model_dump()})
    return report
