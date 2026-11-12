"""Pipeline orchestrator: recon → 13 analysis agents → assembled Report.

Every agent is research — a dossier tab about the decoded subject. The
planning agents (burn calculator, market sizing, founder school, starter
code, playbook, distribution coach) were removed in the pure-research cut;
the brief ends in facts and a verdict, not in coaching.

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
    FeaturesAgent,
    FrictionAgent,
    DnaAgent,
    MarketsAgent,
    RegistryAgent,
    DeepDiveAgent,
    PremortemAgent,
    PricingAgent,
    StructuralAgent,
    TimelineAgent,
)
from .agents.base import Agent, Emit
from .agents.recon import ReconAgent
from .models import AnalyzeRequest, Evidence, Mode, Report
from .scrapers import site as site_mod
from .scrapers.client import Fetcher
from .text import detect_sector

AGENTS: list[type[Agent]] = [
    StructuralAgent,
    FeaturesAgent,
    ComplianceAgent,
    PremortemAgent,
    TimelineAgent,
    PricingAgent,
    FrictionAgent,
    DarkWebAgent,
    DnaAgent,  # reads the feature list from the features tab
    MarketsAgent,  # stock performance; reads EDGAR evidence for tickers
    DeepDiveAgent,  # reads features/dna/timeline/premortem/compliance — after all of them
    RegistryAgent,  # the legal/registry layer; reads the site profile + EDGAR identity
    AdversaryAgent,  # must run last — it cross-examines the assembled report
]


async def run_pipeline(req: AnalyzeRequest, emit: Emit) -> Report:
    subject = req.query.strip()
    ev = Evidence(req=req, subject=subject)

    # URL mode: the company's own site is read FIRST — it names the brand, and
    # its words become part of the shared evidence corpus every agent mines.
    if req.mode is Mode.url:
        target = site_mod.normalize_target(subject)
        url, domain = target if target else ("https://" + subject, subject)
        await emit({"type": "log", "level": "agent", "agent": "recon", "msg": f"url mode — reading {domain} directly (primary source)…"})
        f0 = Fetcher(ev)
        try:
            profile = await site_mod.read_site(f0, url, domain)
        except Exception as exc:
            profile = {"url": url, "domain": domain, "error": f"{type(exc).__name__}: {exc}"[:200]}
        if profile.get("error") and not f0.offline:
            # the live site is down (or refusing us) — the Wayback Machine may
            # still hold the company's own pages; complete details beat dead air
            await emit({"type": "log", "level": "info", "agent": "recon", "msg": "live site unreachable — checking the Wayback Machine's latest archived copy…"})
            wb = await site_mod.read_site_from_wayback(f0, url, domain)
            if wb:
                profile = wb
                await emit({"type": "log", "level": "success", "agent": "recon", "msg": f"archived copy read: {domain} — snapshot {str((profile.get('snapshot') or {}).get('timestamp', ''))[:8]}"})
        if profile.get("error"):
            await emit({"type": "log", "level": "warn", "agent": "recon", "msg": f"site read failed ({profile['error'][:80]}) — researching the domain name instead"})
            subject = domain
        else:
            if "pages" not in profile:
                profile["pages"] = await site_mod.read_pages(f0, profile.get("links") or {})
            profile["brand"] = profile.get("brand") or site_mod.brand_of(profile) or domain.split(".")[0].title()
            subject = profile["brand"]
            ev.add_source(url, kind="site", title=profile.get("title") or domain)
            from urllib.parse import urlparse as _up
            for p in profile["pages"]:
                ev.search.append({
                    "title": f"{domain}{_up(p['url']).path or '/'} (own site)",
                    "url": p["url"],
                    "snippet": p["text"][:400],
                })
            await emit({"type": "log", "level": "success", "agent": "recon", "msg": (
                f"primary source read: {subject}"
                + (" (from the Wayback Machine — the live site is unreachable)" if profile.get("via_wayback") else "")
                + (f" — “{profile.get('title') or ''}”" if profile.get("title") else "")
                + f" · {len(profile.get('pages') or [])} own pages, {len(profile.get('tech') or [])} technologies, {len(profile.get('socials') or {})} socials"
            )})
        # the registry layer must know a failed fetch happened — a site that
        # timed out is not the same as "no URL given", and the coverage notes
        # say so instead of misleading
        ev.site = profile
        ev.subject = subject
        ev.wiki_domain_hint = domain  # type: ignore[attr-defined]

    ev.sector = detect_sector(subject + " " + (req.context or "") + " " + (ev.site or {}).get("text", "")[:1500])

    await emit({"type": "log", "level": "agent", "agent": "genesis", "msg": f"GENESIS pipeline engaged — decoding '{subject}'"})
    llm_model = await llm.resolve_model()
    await emit({"type": "log", "level": "info", "agent": "genesis", "msg": f"LLM enrichment: {f'available ({llm_model})' if llm_model else 'offline — deterministic analysis engine only'}"})

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
