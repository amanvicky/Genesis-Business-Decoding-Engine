"""Tab 12 — Public Record: the legal/registry layer of the company.

When the founder gives a URL, the company's own legal pages are parsed for the
registration identifiers the law makes them print (CIN/GSTIN in India, company
numbers in the UK, VAT ids in the EU, incorporation statements everywhere).
Those are cross-checked against the keyless public layers: RDAP for the domain
registration, SEC EDGAR registration fields for US-listed entities, and
Wikidata's structured legal facts when an encyclopedia entry exists. Where a
national registry has no open API (India's MCA), the tab says so plainly and
points at it — it never invents a filing.
"""
from __future__ import annotations

import asyncio

from ..models import Evidence
from ..scrapers import registry, search, wikipedia
from ..scrapers.client import Fetcher
from ..text import domain_of
from .base import Agent


class RegistryAgent(Agent):
    id = "publicrecord"
    title = "Public Record — Registration & Corporate Footprint"
    icon = "§"
    tab = 12

    async def build(self, ev: Evidence) -> dict:
        mode = ev.req.mode.value
        geo = ev.req.geography.value
        site = ev.site or {}
        domain = site.get("domain") or domain_of(ev.req.query if mode == "url" else "") or ev.wiki_domain_hint or ""

        # 1. legal identifiers from the company's own properties
        texts: list[tuple[str, str]] = []
        if site.get("text"):
            texts.append((site.get("url") or domain, site["text"]))
        for p in site.get("pages") or []:
            if p.get("text"):
                texts.append((p["url"], p["text"]))
        registrations = registry.legal_identities(texts)

        # 2. the keyless public layers, all soft-failing
        f = Fetcher(ev)
        wd_title = (ev.wiki or {}).get("title") or ""
        rdap_task = registry.rdap_domain(f, domain) if domain else _none()
        wd_task = wikipedia.wikidata_company(f, wd_title) if wd_title else _none()
        rdap, wd = await asyncio.gather(rdap_task, wd_task, return_exceptions=True)
        if isinstance(rdap, Exception):
            rdap = {}
        if isinstance(wd, Exception):
            wd = {}

        edgar_reg: dict = {}
        edgar_meta = ev.identity.get("edgar") or {}
        if edgar_meta:
            edgar_reg = dict(ev.identity.get("edgar_registration") or {})
            edgar_reg.setdefault("name", edgar_meta.get("name"))
            edgar_reg.setdefault("ticker", edgar_meta.get("ticker"))
            edgar_reg.setdefault("cik", edgar_meta.get("cik"))

        # 3. search-cascade fallback when the own-site layer found nothing
        mentions: list[dict] = []
        brand = site.get("brand") or ev.subject
        if not registrations and domain and not f.offline:
            for batch in await asyncio.gather(
                *[search.ddg_search(f, q, 6) for q in registry.mention_queries(brand, domain, geo)[:2]],
                return_exceptions=True,
            ):
                if isinstance(batch, Exception):
                    continue
                for r in batch[:4]:
                    mentions.append({"title": r.get("title", ""), "snippet": r.get("snippet", ""), "url": r.get("url", "")})

        # the most identity-defining row set, kept with its sources — when the
        # profile came from the Wayback Machine, source links point at the
        # archived page (the live site is unreachable, that's the point)
        source_url = site.get("url") or domain
        if site.get("via_wayback") and (site.get("snapshot") or {}).get("url"):
            source_url = site["snapshot"]["url"]
        legal_identity: dict = {}
        if site.get("jsonld_legal_name"):
            legal_identity["legal_name"] = site["jsonld_legal_name"]
            legal_identity["legal_name_source"] = source_url
        if site.get("address"):
            legal_identity["address_jsonld"] = site["address"]
            legal_identity["address_source"] = source_url
        if site.get("founding_date"):
            legal_identity["founding_date_selfdeclared"] = site["founding_date"]
        for row in registrations:
            kind = row["kind"]
            if "office" in kind and "registered_office" not in legal_identity:
                legal_identity["registered_office"] = row["value"]
                legal_identity["registered_office_source"] = row["source"]
            elif "incorporation" in kind and "incorporation" not in legal_identity:
                legal_identity["incorporation"] = row["value"]
                legal_identity["incorporation_source"] = row["source"]
            elif ("cin" in kind or "company no" in kind) and "registration_no" not in legal_identity:
                legal_identity["registration_no"] = row["value"]
                legal_identity["registration_kind"] = kind
                legal_identity["registration_source"] = row["source"]
            elif "vat" in kind and "tax_id" not in legal_identity:
                legal_identity["tax_id"] = row["value"]
                legal_identity["tax_id_kind"] = kind
                legal_identity["tax_id_source"] = row["source"]

        # 4. honest coverage: what was checked, what keyless can't reach
        coverage: list[str] = []
        if site:
            if site.get("error"):
                coverage.append(f"own site fetch failed ({site['error']}) — the legal-page layer is degraded")
            elif site.get("via_wayback"):
                coverage.append(f"live site unreachable — own site read from a Wayback Machine snapshot "
                                f"({(site.get('snapshot') or {}).get('timestamp', '')[:8]})")
            else:
                n_pages = len(site.get("pages") or [])
                coverage.append(f"own site parsed: {domain} ({'+' if n_pages else 'no extra '}{'legal/about/contact pages' if n_pages else ''})")
        else:
            coverage.append("own site not read (no URL given) — legal-page identifiers need the company's URL")
        coverage.append("domain record via rdap.org (keyless)" + ("" if rdap else " — no RDAP coverage for this TLD"))
        coverage.append("SEC EDGAR registration fields" + ("" if edgar_reg else " — no US filing match (private or non-US entity)"))
        coverage.append("Wikidata structured legal facts" + ("" if wd else " — none available"))
        coverage.append("national corporate registries (India MCA, Companies House API…): no open keyless API — "
                        "identifiers above come from the company's own legally-required disclosures; verify there")

        return {
            "mode": mode,
            "domain": domain,
            "site": {
                "url": site.get("url"),
                "title": site.get("title"),
                "description": site.get("description"),
                "tech": site.get("tech") or [],
                "socials": site.get("socials") or {},
                "emails": site.get("emails") or [],
                "phones": site.get("phones") or [],
            } if site else None,
            "legal_identity": legal_identity,
            "registrations": registrations,
            "domain_record": rdap or None,
            "edgar": edgar_reg or None,
            "wikidata": wd or None,
            "registry_mentions": mentions,
            "coverage": coverage,
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        li = data.get("legal_identity") or {}
        bits: list[str] = []
        if li.get("legal_name"):
            bits.append(f"legal name {li['legal_name']}")
        if li.get("registration_no"):
            bits.append(f"{li['registration_kind']} {li['registration_no']}")
        dr = data.get("domain_record") or {}
        if dr.get("registered"):
            bits.append(f"domain registered {dr['registered']}")
        if dr.get("registrar"):
            bits.append(f"via {dr['registrar']}")
        n = len(data.get("registrations") or [])
        if bits:
            return " · ".join(bits) + (f" — {n} public identifiers cross-checked" if n else "")
        if data.get("edgar"):
            e = data["edgar"]
            return f"US filer {e.get('name')} (CIK {e.get('cik')}) — incorporated {e.get('state_of_incorporation') or 'in the US'}, {e.get('sic_description') or 'see EDGAR'}"
        return "no public registration identifiers surfaced — run with the company's URL so the legal pages can be read"


async def _none() -> dict:
    return {}
