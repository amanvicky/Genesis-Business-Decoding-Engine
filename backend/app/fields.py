"""The knowledge-base field extractor — the stable core of every decoded brief.

Vault, Battle and Watch all stand on this one module: it flattens a finished
report into a small dict of fields that are KNOWN to be stable across runs.
The rule is strict: a field only gets in if it comes from deterministic parsing
(the site's own legal pages, RDAP, EDGAR, the gate math) — never from search
result ordering or LLM text, which shuffle between two runs on the same day.
That is what makes drift alerts mean something.
"""
from __future__ import annotations

from typing import Any

# The bounded drift signals watch.py diffs. kind decides the comparison:
#   exact  — both values must exist and be different (a value appearing or
#            vanishing is usually better scraping or a fetch hiccup, not news)
#   set    — additions AND removals both alert (memo-stability tested)
#   score  — numeric, alerts past a threshold so normal evidence noise stays quiet
DRIFT_FIELDS: dict[str, dict[str, Any]] = {
    "legal_name":            {"label": "Legal name",            "tab": "Tab 12 · public record", "kind": "exact"},
    "registration_no":       {"label": "Registration no",       "tab": "Tab 12 · public record", "kind": "exact"},
    "registered_office":     {"label": "Registered office",     "tab": "Tab 12 · public record", "kind": "exact"},
    "domain_registrar":      {"label": "Domain registrar",      "tab": "Tab 12 · public record", "kind": "exact"},
    "tech":                  {"label": "Tech stack",            "tab": "Tab 12 · public record", "kind": "set"},
    "emails":                {"label": "Public emails",         "tab": "Tab 12 · public record", "kind": "set"},
    "socials":               {"label": "Social profiles",       "tab": "Tab 12 · public record", "kind": "set"},
    "signal_score":          {"label": "Signal score",          "tab": "Tab 1 · structural",     "kind": "score", "threshold": 5},
    "fatal_count":           {"label": "Red-team fatals",       "tab": "Tab 13 · red team",      "kind": "exact"},
    "compliance_criticals":  {"label": "Compliance blockers",   "tab": "Tab 3 · compliance",     "kind": "exact"},
}

_SCORE_THRESHOLD = 5        # |Δ| in signal points before watch calls it drift


def _norm_addr(addr: str | None) -> str | None:
    """Registered offices print differently every re-design — compare on a
    whitespace-collapsed, lowercase form so formatting churn never alerts."""
    if not addr:
        return None
    return " ".join(str(addr).lower().split())


def extract_fields(report: dict) -> dict:
    """Finished report dict → the stable field set. Never raises: a report
    missing any section simply yields None fields, and None means 'not known',
    not zero."""
    sections = report.get("sections") or {}

    def data(sid: str) -> dict:
        return ((sections.get(sid) or {}).get("data") or {})

    structural = data("structural")
    adversary = data("adversary")
    comp = data("compliance")
    pr = data("publicrecord")
    site = pr.get("site") or {}
    li = pr.get("legal_identity") or {}
    dr = pr.get("domain_record") or {}
    edgar = pr.get("edgar") or {}

    return {
        "subject": report.get("subject"),
        "sector": report.get("sector"),
        "mode": (report.get("request") or {}).get("mode"),
        # identity (kept for the vault record; not every one is diffed)
        "legal_name": li.get("legal_name") or None,
        "registration_no": li.get("registration_no") or None,
        "registered_office": _norm_addr(li.get("registered_office")),
        "incorporation": li.get("incorporation") or None,
        "domain_registrar": dr.get("registrar") or None,
        "domain_registered": dr.get("registered") or None,
        "edgar_cik": edgar.get("cik"),
        # the bounded drift signals
        "tech": sorted(str(t).lower() for t in (site.get("tech") or [])),
        "emails": sorted(str(e).lower() for e in (site.get("emails") or [])),
        "socials": sorted(f"{k}:{v}" for k, v in (site.get("socials") or {}).items()),
        "signal_score": structural.get("verdict_score"),
        "fatal_count": adversary.get("fatal_count"),
        "compliance_criticals": comp.get("critical_count"),
    }


def diff_fields(old: dict, new: dict) -> list[dict]:
    """Old stored fields vs fresh fields → drift rows (only real alerts).
    Every row carries its human label and the tab it came from, so the
    dashboard drift panel can group by tab."""
    rows: list[dict] = []
    for field, spec in DRIFT_FIELDS.items():
        o, n = old.get(field), new.get(field)
        kind = spec["kind"]
        if kind == "exact":
            if o is not None and n is not None and str(o) != str(n):
                rows.append(_row(field, spec, o, n, "changed"))
        elif kind == "set":
            os_, ns_ = set(o or []), set(n or [])
            added, removed = sorted(ns_ - os_), sorted(os_ - ns_)
            if added:
                rows.append(_row(field, spec, "", ", ".join(added), "added"))
            if removed:
                rows.append(_row(field, spec, ", ".join(removed), "", "removed"))
        elif kind == "score":
            if isinstance(o, (int, float)) and isinstance(n, (int, float)) and abs(n - o) >= spec["threshold"]:
                rows.append(_row(field, spec, o, n, "moved"))
    return rows


def _row(field: str, spec: dict, old: Any, new: Any, action: str) -> dict:
    return {
        "field": field,
        "label": spec["label"],
        "tab": spec["tab"],
        "kind": spec["kind"],
        "action": action,
        "old": "" if old == "" else str(old),
        "new": "" if new == "" else str(new),
    }
