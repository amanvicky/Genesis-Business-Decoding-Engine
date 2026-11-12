"""Verdict Protocol v2: turns a finished brief into a GO / NO-GO call.

v2 is the pure-research cut: every gate reads only evidence about the subject
— the signal score mined from public voices, and the red-team's fatal count.
The old market-math gate and the founder-market-fit quiz died with the
planning tabs (a quiz is not research, and a verdict you can argue into
another outcome is worthless).

    any gate FAIL         -> NO-GO
    any gate PENDING      -> PENDING (unmeasured — no honest call exists)
    any gate CAUTION      -> CONDITIONAL
    all pass              -> GO (the first kill-gate in the playbook era is
                             gone with the playbook; GO means the evidence
                             supports starting, nothing more)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_memo(report: dict, fmf_answers: list[bool] | None = None) -> dict:
    subject = str(report.get("subject") or "Unknown")
    sections: dict[str, Any] = report.get("sections") or {}

    def data(sid: str) -> dict:
        return ((sections.get(sid) or {}).get("data") or {})

    structural = data("structural")
    adversary = data("adversary")

    gates: list[dict] = []

    # --- Gate 1: Problem (structural signal) ---------------------------------
    sv = str(structural.get("verdict") or "")
    score = structural.get("verdict_score")
    if "UNKNOWN" in sv or score is None:
        g1_status, g1_fix = "pending", "Re-run the decode online — signal is unmeasured, not weak."
    elif score >= 30:
        g1_status, g1_fix = "pass", ""
    elif score >= 15:
        g1_status, g1_fix = "caution", "Signal is thin: 20 problem interviews before code (Tab 1 pain tables are the script)."
    else:
        g1_status, g1_fix = "fail", "Measured weak signal with evidence gathered — the pain is not voiced publicly. Interview or change the wedge."
    gates.append({
        "name": "Problem signal",
        "status": g1_status,
        "basis": sv[:220] or "no structural verdict in this report",
        "fix": g1_fix,
    })

    # --- Gate 2: Death patterns (red-team fatals) ------------------------------
    fatal = adversary.get("fatal_count")
    if fatal is None:
        g2_status, g2_fix = "pending", "Red-team panel absent — re-run the decode."
    elif fatal >= 6:
        g2_status, g2_fix = "fail", f"{fatal} fatal challenges. The panel found plan-killers — answer or cut each one (Tab 13)."
    elif fatal >= 3:
        g2_status, g2_fix = "caution", f"{fatal} fatal challenges — each needs a written answer before build (Tab 13)."
    else:
        g2_status, g2_fix = "pass", f"Only {fatal} fatal challenge(s) — manageable with written answers."
    gates.append({
        "name": "Death patterns",
        "status": g2_status,
        "basis": f"{fatal} fatal red-team challenges" if fatal is not None else "no adversarial panel",
        "fix": g2_fix,
    })

    # --- Decision ---------------------------------------------------------------
    statuses = [g["status"] for g in gates]
    if any(s == "fail" for s in statuses):
        decision = "NO-GO"
        failed = [g for g in gates if g["status"] == "fail"]
        rationale = "Gate failure: " + "; ".join(f"{g['name']} — {g['basis']}" for g in failed)
    elif any(s == "pending" for s in statuses):
        decision = "PENDING"
        pending = [g for g in gates if g["status"] == "pending"]
        rationale = "Unmeasured: " + "; ".join(g["name"] for g in pending) + ". A call needs evidence, not optimism — re-run the decode online."
    elif any(s == "caution" for s in statuses):
        decision = "CONDITIONAL"
        cautioned = [g for g in gates if g["status"] == "caution"]
        rationale = "Caution on: " + "; ".join(g["name"] for g in cautioned) + ". Clear these, then re-verify."
    else:
        decision = "GO"
        rationale = ("Both research gates pass — the pain is voiced publicly and the red team found no plan-killers. "
                     "GO means the evidence supports starting; the surviving tabs hold everything you still have to answer.")

    # --- Conditions & next actions ------------------------------------------------
    conditions = [g["fix"] for g in gates if g["status"] in ("caution", "fail") and g["fix"]]
    comp = data("compliance")
    critical = comp.get("critical_count")
    next_actions: list[str] = []
    if decision in ("GO", "CONDITIONAL"):
        if critical:
            next_actions.append(f"Start the compliance clock — {critical} launch-blocking obligations (Tab 3, ordered list).")
        features = data("features")
        build_now = (features.get("binary_roadmap") or {}).get("build_now") or []
        if build_now:
            next_actions.append(f"First build: {str(build_now[0].get('feature', ''))[:150]}")
    else:
        next_actions.append("Do not write product code. Fix the failed gates, then re-decode.")
        if decision == "NO-GO":
            next_actions.append("NO-GO is a result, not a failure: a killed idea in an afternoon is cheaper than a dead company in two years.")

    return {
        "subject": subject,
        "decision": decision,
        "rationale": rationale,
        "gates": gates,
        "founder_market_fit": {"score": None, "total": 0, "rows": []},
        "conditions": conditions,
        "next_actions": next_actions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol_version": 2,
    }


def memo_to_markdown(memo: dict) -> str:
    cur_mark = {"pass": "✅", "caution": "⚠️", "fail": "❌", "pending": "⏳"}
    lines = [
        f"# GENESIS VERDICT — {memo.get('subject', 'Unknown')}",
        "",
        f"## Decision: **{memo.get('decision', 'PENDING')}**",
        "",
        memo.get("rationale", ""),
        "",
        "## Gates",
        "",
    ]
    for g in memo.get("gates", []):
        lines.append(f"- {cur_mark.get(g.get('status'), '•')} **{g.get('name')}** — {g.get('basis')}")
        if g.get("fix"):
            lines.append(f"  - fix: {g['fix']}")
    if memo.get("conditions"):
        lines += ["", "## Conditions", ""]
        lines += [f"- {c}" for c in memo["conditions"]]
    if memo.get("next_actions"):
        lines += ["", "## Next Actions", ""]
        lines += [f"- {a}" for a in memo["next_actions"]]
    lines += ["", f"*Verdict Protocol v{memo.get('protocol_version', 2)} · research-only gates · generated {memo.get('generated_at', '')[:19]} · planning-grade, not advice.*"]
    return "\n".join(lines)
