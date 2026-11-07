"""Government / public registry probes — the "who is this company, legally" layer.

Keyless sources only, in order of authority:
  1. the company's own legal pages — CIN/GSTIN (India), company numbers (UK),
     VAT ids (EU), incorporation statements: identifiers the law makes firms
     print on their own properties
  2. RDAP (rdap.org) — the domain's own registration record
  3. SEC EDGAR — registration fields for US-listed entities (see filings.py)
  4. Wikidata — structured legal facts when a Wikipedia entry exists

National registries with no open API (India's MCA, UK Companies House without
a paid key) are never invented: the tab reports what was actually found and
says where to verify the rest.
"""
from __future__ import annotations

import re

# India: Corporate Identity Number — U/L/F + 5 digits + state code + year + class + serial (21 chars)
_CIN = re.compile(r"\b([ULF]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})\b", re.I)
# India: GSTIN — 2 digits + PAN + entity code + Z + checksum (15 chars)
_GSTIN = re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z])\b", re.I)
# UK: 8-digit or SC/OC/NI-prefixed company number — only trusted near a Companies House phrase
_UK_COMPANY = re.compile(r"\b((?:SC|OC|NI)?\d{8}|(?:SC|OC|NI)\d{6})\b")
_UK_NEAR = re.compile(r"companies house|registered in (?:england|wales|scotland|northern ireland)|registered number|company number", re.I)
# EU-style VAT id — only trusted near a VAT/GST/tax phrase
_VAT = re.compile(r"\b([A-Z]{2}\s?\d{8,12})\b")
_VAT_NEAR = re.compile(r"\bvat\b|\bgst\b|tax id|tax number", re.I)
_OFFICE = re.compile(r"registered office[:\s]*([^.\n|]{5,140})", re.I)
_INCORP = re.compile(
    r"\b((?:incorporated|registered|established)\s+(?:under the laws of\s+|under the\s+|in\s+)"
    r"[A-Z][A-Za-z .,'&()]{2,80})",
)


def legal_identities(texts: list[tuple[str, str]]) -> list[dict]:
    """(source_url, text) pairs → deduped public-identifier rows.

    Every row keeps its surrounding context and the exact page it came from —
    a registration number without its source is just a string.
    """
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, value: str, context: str, source: str) -> None:
        value = value.strip()
        if not value:
            return
        key = (kind, re.sub(r"\s+", "", value.upper()))
        if key in seen:
            return
        seen.add(key)
        rows.append({"kind": kind, "value": value, "context": re.sub(r"\s+", " ", context).strip()[:220], "source": source})

    for src, text in texts or []:
        if not text:
            continue
        for m in _CIN.finditer(text):
            add("cin (MCA India)", m.group(1).upper(), text[max(0, m.start() - 90):m.end() + 90], src)
        for m in _GSTIN.finditer(text):
            add("gstin (GST India)", m.group(1).upper(), text[max(0, m.start() - 90):m.end() + 90], src)
        for m in _UK_COMPANY.finditer(text):
            near = text[max(0, m.start() - 160):m.end() + 60]
            if _UK_NEAR.search(near):
                add("company no. (UK Companies House)", m.group(1), near, src)
        for m in _VAT.finditer(text):
            near = text[max(0, m.start() - 100):m.end() + 60]
            if _VAT_NEAR.search(near):
                add("vat/tax id", m.group(1), near, src)
        for m in _OFFICE.finditer(text):
            add("registered office", m.group(1).strip(), m.group(0), src)
        for m in _INCORP.finditer(text):
            add("incorporation statement", m.group(1).strip(), m.group(0), src)
    return rows[:20]


def _vcard_fn(entity: dict) -> str:
    v = entity.get("vcardArray")
    if isinstance(v, list) and len(v) > 1 and isinstance(v[1], list):
        for row in v[1]:
            if isinstance(row, list) and len(row) > 3 and row[0] == "fn" and row[3]:
                return str(row[3])[:120]
    return ""


async def rdap_domain(fetcher, domain: str) -> dict:
    """Domain registration record via the keyless RDAP bootstrap service.
    Empty dict for TLDs without RDAP coverage — that's reported, not hidden."""
    data = await fetcher.try_json(f"https://rdap.org/domain/{domain}", kind="registry")
    if not isinstance(data, dict):
        return {}
    out: dict = {"queried": f"https://rdap.org/domain/{domain}"}
    events: dict[str, str] = {}
    for e in data.get("events") or []:
        if isinstance(e, dict) and e.get("eventAction") and e.get("eventDate"):
            events[str(e["eventAction"])] = str(e["eventDate"])[:10]
    if events.get("registration"):
        out["registered"] = events["registration"]
    if events.get("expiration"):
        out["expires"] = events["expiration"]
    if events.get("last changed"):
        out["last_changed"] = events["last changed"]
    for ent in data.get("entities") or []:
        if isinstance(ent, dict) and "registrar" in (ent.get("roles") or []):
            name = _vcard_fn(ent)
            if name:
                out["registrar"] = name
                break
    if data.get("status"):
        out["status"] = [str(s) for s in data["status"]][:4]
    ns = [str(n.get("ldhName") or "").lower() for n in data.get("nameservers") or []
          if isinstance(n, dict) and n.get("ldhName")]
    if ns:
        out["nameservers"] = ns[:6]
    return out


def mention_queries(brand: str, domain: str, geo: str) -> list[str]:
    """Search-cascade queries for the registry layer when nothing was found
    on the company's own properties."""
    if geo == "us":
        return [f'"{brand}" Delaware incorporation registered agent', f'"{domain}" SEC EDGAR CIK company']
    return [f'"{domain}" company registration number registry', f'"{brand}" CIN MCA registered company']
