"""Verdict Protocol: turns a finished dossier into a GO / NO-GO call.

Gates come from the report itself (structural score, market math, red-team
fatals), founder-market-fit comes from the founder's own answers. No LLM in
here on purpose, a verdict you can argue with is worthless.

    any gate FAIL         -> NO-GO
    any gate CAUTION      -> CONDITIONAL
    all pass + FMF >= 5/6 -> GO
    all pass + FMF < 5    -> CONDITIONAL
    FMF unanswered        -> PENDING
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_MAX_FMF_ANSWERS = 12


def build_memo(report: dict, fmf_answers: list[bool] | None = None) -> dict:
    subject = str(report.get("subject") or "Unknown")
    sections: dict[str, Any] = report.get("sections") or {}

    def data(sid: str) -> dict:
        return ((sections.get(sid) or {}).get("data") or {})

    structural = data("structural")
    marketsize = data("marketsize")
    adversary = data("adversary")
    compliance = data("compliance")
    distribution = data("distribution")
    fin = (data("financial").get("computed") or {})

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

    # --- Gate 2: Market math --------------------------------------------------
    tone = marketsize.get("verdict_tone")
    mv = str(marketsize.get("verdict") or "")
    if not mv:
        g2_status, g2_fix = "pending", "Market sizing absent — re-run the decode."
    elif tone == "red":
        g2_status, g2_fix = "fail", mv[:220]
    elif tone == "amber":
        g2_status, g2_fix = "caution", mv[:220]
    else:
        g2_status, g2_fix = "pass", mv[:220]
    gates.append({
        "name": "Market math",
        "status": g2_status,
        "basis": mv[:220] or "no sizing in this report",
        "fix": g2_fix,
    })

    # --- Gate 3: Death patterns (red-team fatals) ------------------------------
    fatal = adversary.get("fatal_count")
    if fatal is None:
        g3_status, g3_fix = "pending", "Red-team panel absent — re-run the decode."
    elif fatal >= 6:
        g3_status, g3_fix = "fail", f"{fatal} fatal challenges. The panel found plan-killers — answer or cut each one (Tab 14)."
    elif fatal >= 3:
        g3_status, g3_fix = "caution", f"{fatal} fatal challenges — each needs a written answer before build (Tab 14)."
    else:
        g3_status, g3_fix = "pass", f"Only {fatal} fatal challenge(s) — manageable with written answers."
    gates.append({
        "name": "Death patterns",
        "status": g3_status,
        "basis": f"{fatal} fatal red-team challenges" if fatal is not None else "no adversarial panel",
        "fix": g3_fix,
    })

    # --- Founder-market-fit (the human half) -----------------------------------
    fmf_block = marketsize.get("founder_market_fit") or {}
    questions = fmf_block.get("questions") or []
    answers = list(fmf_answers or [])
    fmf_total = len(questions) or len(answers)
    fmf_score: int | None = None
    fmf_rows: list[dict] = []
    if answers:
        for i, q in enumerate(questions):
            want_yes = not q.get("invert", False)
            ans = answers[i] if i < len(answers) else None
            good = (ans is True and want_yes) or (ans is False and not want_yes)
            fmf_rows.append({"q": q.get("q", f"Q{i + 1}"), "weight": q.get("weight", "medium"),
                             "answer": ans, "good": good if ans is not None else None})
        answered = [r for r in fmf_rows if r["answer"] is not None]
        fmf_score = sum(1 for r in answered if r["good"])
        if len(answered) < len(questions):
            fmf_score = None  # partial answers don't produce a score
    else:
        fmf_rows = [{"q": q.get("q", ""), "weight": q.get("weight", "medium"), "answer": None, "good": None}
                    for q in questions]

    # --- Decision ---------------------------------------------------------------
    statuses = [g["status"] for g in gates]
    if any(s == "fail" for s in statuses):
        decision = "NO-GO"
        failed = [g for g in gates if g["status"] == "fail"]
        rationale = "Gate failure: " + "; ".join(f"{g['name']} — {g['basis']}" for g in failed)
    elif any(s == "caution" for s in statuses):
        decision = "CONDITIONAL"
        cautioned = [g for g in gates if g["status"] == "caution"]
        rationale = "Caution on: " + "; ".join(g["name"] for g in cautioned) + ". Clear these, then re-verify."
    elif fmf_score is None:
        decision = "PENDING"
        rationale = "All gates pass, but the founder-market-fit checklist is unanswered. The gates measure the idea; the checklist measures YOU."
    elif fmf_score >= max(1, round(fmf_total * 5 / 6)):
        decision = "GO"
        rationale = (f"All gates pass and founder-market-fit is {fmf_score}/{fmf_total}. "
                     "Condition: the first kill-gate (Tab 5, G0) still applies — GO means start, not skip.")
    else:
        decision = "CONDITIONAL"
        rationale = (f"Gates pass but founder-market-fit is {fmf_score}/{fmf_total}. Either find a co-founder who "
                     "closes the gaps, or pick the wedge that matches what you already have.")

    # --- Conditions & next actions ------------------------------------------------
    conditions = [g["fix"] for g in gates if g["status"] in ("caution", "fail") and g["fix"]]
    if decision == "CONDITIONAL" and fmf_score is not None and fmf_score < max(1, round(fmf_total * 5 / 6)):
        conditions.append("Founder-market-fit gap: close it with a co-founder or a narrower wedge before spending build weeks.")
    next_actions: list[str] = []
    if decision in ("GO", "CONDITIONAL"):
        first_ten = distribution.get("first_ten") or []
        if first_ten:
            next_actions.append(f"This week: {first_ten[0].get('action', '')[:180]}")
        critical = compliance.get("critical_count")
        if critical:
            next_actions.append(f"Start the compliance clock — {critical} launch-blocking obligations (Tab 3, ordered list).")
        if fin.get("breakeven_customers"):
            next_actions.append(f"Know your number: {fin['breakeven_customers']:,} customers at ARPA {fin.get('arpa_assumption')} to breakeven.")
    else:
        next_actions.append("Do not write product code. Fix the failed gates, then re-decode.")
        if decision == "NO-GO":
            next_actions.append("NO-GO is a result, not a failure: a killed idea in an afternoon is cheaper than a dead company in two years.")

    return {
        "subject": subject,
        "decision": decision,
        "rationale": rationale,
        "gates": gates,
        "founder_market_fit": {"score": fmf_score, "total": fmf_total, "rows": fmf_rows},
        "conditions": conditions,
        "next_actions": next_actions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "protocol_version": 1,
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
    fmf = memo.get("founder_market_fit") or {}
    if fmf.get("rows"):
        lines += ["", f"## Founder-Market Fit ({fmf.get('score')}/{fmf.get('total')})", ""]
        for r in fmf["rows"]:
            mark = "—" if r.get("answer") is None else ("✔" if r.get("good") else "✘")
            lines.append(f"- {mark} ({r.get('weight')}) {r.get('q')}")
    if memo.get("conditions"):
        lines += ["", "## Conditions", ""]
        lines += [f"- {c}" for c in memo["conditions"]]
    if memo.get("next_actions"):
        lines += ["", "## Next Actions", ""]
        lines += [f"- {a}" for a in memo["next_actions"]]
    lines += ["", f"*Verdict Protocol v{memo.get('protocol_version', 1)} · generated {memo.get('generated_at', '')[:19]} · planning-grade, not advice.*"]
    return "\n".join(lines)
