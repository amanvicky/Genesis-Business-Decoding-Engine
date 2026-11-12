"""Tab 11 — Deep/Dark Web & Vulnerability Shield.

Lawful, passive OSINT only: Ahmia (legal onion index), public paste-board
search results surfaced by search engines, and the free HIBP breach corpus.
Tor is used for anonymity when a local SOCKS5 proxy (127.0.0.1:9050) is up.
Illegal sourcing queries are refused. No interaction, no purchases, no markets.
"""
from __future__ import annotations

from ..models import Evidence
from ..scrapers import tor as tor_mod
from ..scrapers.client import Fetcher
from .base import Agent

GUIDANCE = [
    "Treat every dark-web mention as an unverified claim until corroborated by two independent sources.",
    "If your own domain/data appears in a paste or dump: rotate exposed credentials, check exfiltration paths, and document for disclosure obligations (US: state breach laws; India: DPDP Act).",
    "Competitor operational flaws (complaints from insiders, infra rants) are signal for YOUR sales copy — never for interference.",
    "Never contact, purchase, or negotiate on hidden services. Reading public indexes is the entire scope of this module.",
]


class DarkWebAgent(Agent):
    id = "darkweb"
    title = "Deep/Dark Web & Vulnerability Shield"
    icon = "🛡"
    tab = 8

    async def build(self, ev: Evidence) -> dict:
        f = Fetcher(ev)
        if not ev.req.include_darkweb:
            return {"skipped": True, "reason": "Disabled in request settings.", "tor": {"available": False}, "findings": []}

        status = await tor_mod.probe(f)

        if not tor_mod.check_query_legal(ev.subject):
            return {"skipped": True, "reason": "Query refused: appears to seek illegal content. This module reads public OSINT only.", "tor": status, "findings": []}

        findings: list[dict] = []
        # Ahmia: legal onion search index
        ahmia = await tor_mod.ahmia_search(f, f'"{ev.subject}" leak OR dump OR complaint OR vulnerability', status, 8)
        for a in ahmia:
            findings.append({"source": "ahmia (onion index)", "title": a["title"][:120], "url": a["url"], "snippet": a["snippet"][:200], "risk": self._risk(a["title"] + a["snippet"])})

        # Surface-web paste/board chatter that search engines already index
        from ..scrapers.search import ddg_search

        for q in [f'"{ev.subject}" site:pastebin.com OR site:ghostbin.com OR site:justpaste.it', f'"{ev.subject}" breach OR leaked OR dump forum']:
            for r in await ddg_search(f, q, 6):
                findings.append({"source": "surface-indexed pastes/boards", "title": r["title"][:120], "url": r["url"], "snippet": r["snippet"][:200], "risk": self._risk(r["title"] + r["snippet"])})

        breaches = await tor_mod.breach_intel(f, ev.subject)

        return {
            "tor": status,
            "findings": findings[:12],
            "breaches": breaches,
            "guidance": GUIDANCE,
            "ethics_notice": (
                "Lawful-use module: passive reading of publicly indexed OSINT (Ahmia index, search-indexed paste sites, "
                "free HIBP breach corpus). No marketplaces, no credentials, no purchases, no interaction, no evasion. "
                "Offensive use against systems you don't own is illegal — this tool will never provide it."
            ),
        }

    def _risk(self, text: str) -> str:
        low = text.lower()
        if any(k in low for k in ["leak", "dump", "breach", "credentials", "database"]):
            return "high"
        if any(k in low for k in ["complaint", "scam", "fraud", "outage"]):
            return "medium"
        return "info"

    def summarize(self, ev: Evidence, data: dict) -> str:
        if data.get("skipped"):
            return data.get("reason", "skipped")
        t = data.get("tor", {})
        mode = "Tor-routed" if t.get("available") else "clearnet-degraded (no local Tor)"
        return f"{mode}: {len(data.get('findings', []))} raw findings, {len(data.get('breaches', []))} breach-corpus matches. Passive lawful OSINT only."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. From these OSINT findings, state whether there is a credible exposed-data or reputation risk and the one defensive action to take."
