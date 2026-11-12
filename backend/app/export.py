"""Report exporters: Markdown rendering, report ZIP, and schema-versioned JSON (stdlib only)."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from . import __version__

TAB_ORDER = [
    "structural", "features", "compliance", "premortem", "timeline", "pricing",
    "friction", "darkweb", "dna", "markets", "deepdive", "publicrecord", "adversary",
]

TITLES = {
    "structural": "Structural Feasibility & Core Mechanics",
    "features": "Granular Feature Breakdown & MVP Sequencing",
    "compliance": "Jurisdictional & Regulatory Complexity Decoder",
    "premortem": "Pre-Mortem & Failure Post-Mortems",
    "timeline": "Genesis & Historical Timeline",
    "pricing": "Pricing — Tiers, History & Packaging Psychology",
    "friction": "Market Friction & Consumer Psychology",
    "darkweb": "Deep/Dark Web & Vulnerability Shield",
    "dna": "Product DNA — Philosophy & Psychology",
    "markets": "Stock Performance — Rise & Fall",
    "deepdive": "Company Deep-Dive — What, Why, Reality & Marketing",
    "publicrecord": "Public Record — Registration & Corporate Footprint",
    "adversary": "Adversarial Red-Team Simulator",
}


def _fmt_cell(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= 220 else s[:217] + "…"


def render_table(rows: list[dict], max_cols: int = 6) -> str:
    if not rows:
        return ""
    cols: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in cols and len(cols) < max_cols:
                cols.append(k)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(_fmt_cell(r.get(c)) for c in cols) + " |")
    return "\n".join(lines)


def render_value(v: Any, indent: int = 0) -> str:
    pad = "  " * indent
    out: list[str] = []
    if isinstance(v, dict):
        for k, val in v.items():
            if val in (None, "", [], {}):
                continue
            if isinstance(val, (dict, list)):
                out.append(f"{pad}- **{k}**:")
                out.append(render_value(val, indent + 1))
            else:
                out.append(f"{pad}- **{k}**: {_fmt_cell(val)}")
    elif isinstance(v, list):
        if all(isinstance(i, dict) for i in v) and v:
            out.append(render_table(v))
        else:
            for i in v:
                out.append(f"{pad}- {_fmt_cell(i)}")
    else:
        out.append(f"{pad}{_fmt_cell(v)}")
    return "\n".join(x for x in out if x)


def report_to_markdown(report: dict) -> str:
    req = report.get("request", {})
    lines = [
        f"# Genesis Decoding Report — {report.get('subject', 'Unknown')}",
        "",
        f"*Mode:* {req.get('mode', '?')} · *Geography:* {req.get('geography', '?')} · *Sector:* {report.get('sector', 'generic')} · *Generated:* {report.get('generated_at', '')[:19]}",
        "",
        "---",
        "",
    ]
    sections = report.get("sections", {})
    for i, sid in enumerate(TAB_ORDER, 1):
        sec = sections.get(sid)
        if not sec:
            continue
        lines.append(f"## {i}. {sec.get('title', TITLES.get(sid, sid))}")
        lines.append("")
        if sec.get("summary"):
            lines.append(f"> {sec['summary']}")
            lines.append("")
        lines.append(render_value(sec.get("data", {})))
        lines.append("")
    sources = report.get("sources", [])
    if sources:
        lines.append("## Appendix — Evidence Sources")
        lines.append("")
        for s in sources:
            lines.append(f"- [{s.get('kind', 'web')}] {s.get('url', '')}")
    lines.append("")
    lines.append("*Planning-grade intelligence from public sources. Not legal, financial, or tax advice.*")
    return "\n".join(lines)


def report_to_json(report: dict) -> bytes:
    """Schema-versioned structured export for programmatic imports."""
    payload = {
        "schema": "genesis.report/v1",
        "generator": f"Genesis {__version__}",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "report": report,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def report_to_zip(report: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("GENESIS_REPORT.md", report_to_markdown(report))
        zf.writestr("GENESIS_REPORT.json", report_to_json(report).decode("utf-8"))
        zf.writestr(
            "manifest.json",
            json.dumps(
                {"subject": report.get("subject"), "generated_at": report.get("generated_at"), "sections": list((report.get("sections") or {}).keys())},
                indent=2,
            ),
        )
    return buf.getvalue()
