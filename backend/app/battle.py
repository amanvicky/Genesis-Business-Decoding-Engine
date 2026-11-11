"""Idea Battle — 2–3 raw ideas, decoded one after another, compared on a
deterministic matrix with a rule-based winner.

Design rules this module refuses to break:
  - decodes run SEQUENTIALLY (one at a time — parallel decodes from one IP
    get every search engine ban lifted against us)
  - the winner is a RULE, never an LLM opinion. The local model writes one
    paragraph of verdict prose; when it's offline the rule-written sentence
    stands alone. A tie resolves to PENDING — no fake confidence, ever.
  - every battled idea is saved to the vault like any other decode
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from . import llm, vault
from .fields import extract_fields
from .models import AnalyzeRequest, BattleRequest, Mode
from .pipeline import run_pipeline  # module-level on purpose: tests monkeypatch this
from .verdict import build_memo

Emit = Callable[[dict], Awaitable[None]]


async def run_battle(req: BattleRequest, emit: Emit) -> dict:
    # emitters may be sync (tests, CLI) or async (the API queue) — normalize once
    async def say(event: dict) -> None:
        r = emit(event)
        if asyncio.iscoroutine(r):
            await r

    ideas = list(req.ideas)
    await say({"type": "battle_start", "ideas": ideas})

    rows: list[dict] = []
    for i, idea in enumerate(ideas):
        label = chr(ord("A") + i)
        await say({"type": "idea_start", "i": i, "subject": idea})
        areq = AnalyzeRequest(
            mode=Mode.idea,
            query=idea,
            geography=req.geography,
            context=req.context,
            team_size=req.team_size,
            runway_target_months=req.runway_target_months,
            include_darkweb=req.include_darkweb,
        )

        async def forward(event: dict) -> None:
            # the 19 sections would make the dashboard tabs flicker between
            # ideas — battle streams logs and agent progress only
            if event.get("type") == "section":
                return
            await say(event)

        try:
            report = await run_pipeline(areq, forward)
            blob = report.model_dump()
        except Exception as exc:
            await say({"type": "log", "level": "warn", "agent": "battle",
                       "msg": f"idea {label} decode failed ({type(exc).__name__}: {exc}) — scored as unmeasured"})
            rows.append(_row(i, idea, {}, {"pass": 0, "caution": 0, "fail": 0, "pending": 3}))
            continue

        memo = build_memo(blob)
        gates: dict[str, int] = {"pass": 0, "caution": 0, "fail": 0, "pending": 0}
        for g in memo.get("gates") or []:
            s = str(g.get("status") or "pending")
            gates[s] = gates.get(s, 0) + 1
        row = _row(
            i,
            idea,
            extract_fields(blob),
            gates,
            decision=str(memo.get("decision") or "PENDING"),
        )
        try:
            entry = vault.save(blob, battle=True)
            row["brief_id"] = entry["id"]
        except Exception:
            pass  # the battle still reports; the vault hiccup gets a log only
        rows.append(row)
        await say({"type": "idea_done", "i": i, "subject": idea, "brief_id": row.get("brief_id"),
                   "decision": row["decision"], "score": row["score"]})

    winner = pick_winner(rows)
    evidence = _matrix_text(rows)
    # the prose justifies the rule's call — the LLM never picks the winner
    # itself (its own read once contradicted the matrix it was commenting on)
    call = ("no winner — the matrix tied" if winner is None
            else f"idea {chr(ord('A') + winner)} ({rows[winner]['subject']})")
    llm_prose = await llm.prose(
        f"The rule-based call picked {call}. Write ONE paragraph justifying that call from the matrix. "
        "If the call is a tie, say what measurement would break it. Never pick a different option.",
        evidence,
    )
    prose = llm_prose or _fallback_prose(rows, winner)
    result = {"rows": rows, "winner": winner, "prose": prose, "llm_wrote_prose": llm_prose is not None}
    await say({"type": "battle_done", **result})
    return result


def _row(i: int, idea: str, fields: dict, gates: dict, decision: str = "PENDING") -> dict:
    return {
        "i": i,
        "label": chr(ord("A") + i),
        "subject": idea,
        "score": fields.get("signal_score"),
        "decision": decision,
        "fatals": fields.get("fatal_count"),
        "breakeven": fields.get("breakeven_customers"),
        "criticals": fields.get("compliance_criticals"),
        "gates": gates,
    }


def _tier(row: dict) -> int:
    """Gate health tier, 1 (healthy) → 4 (unmeasured). An idea with any
    pending gate can't beat a fully measured one — unmeasured is not neutral,
    it's unknown."""
    g = row.get("gates") or {}
    if g.get("pending"):
        return 4
    if g.get("fail"):
        return 3
    if g.get("caution"):
        return 2
    return 1


def _key(row: dict) -> tuple:
    """Full ranking key. Lower is better: tier, then higher signal score,
    then fewer fatals, then cheaper breakeven, then fewer compliance blockers."""
    score = row.get("score")
    fatals = row.get("fatals")
    breakeven = row.get("breakeven")
    criticals = row.get("criticals")
    return (
        _tier(row),
        -(score if isinstance(score, (int, float)) else -1),
        fatals if isinstance(fatals, (int, float)) else 999,
        breakeven if isinstance(breakeven, (int, float)) else 10**9,
        criticals if isinstance(criticals, (int, float)) else 999,
    )


def pick_winner(rows: list[dict]) -> int | None:
    """The index of the winning idea, or None when the full key ties —
    a tie on every rule is PENDING, never a coin flip."""
    if not rows:
        return None
    ranked = sorted(rows, key=_key)
    if len(ranked) >= 2 and _key(ranked[0]) == _key(ranked[1]):
        return None
    return int(ranked[0]["i"])


def _matrix_text(rows: list[dict]) -> str:
    lines = []
    for r in rows:
        g = r.get("gates") or {}
        lines.append(
            f"{r.get('label')}: \"{r.get('subject')}\" — signal score {r.get('score')}, verdict {r.get('decision')}, "
            f"{r.get('fatals')} fatal red-team challenges, breakeven {r.get('breakeven')} customers, "
            f"{r.get('criticals')} compliance blockers, gates {g.get('pass', 0)} pass / {g.get('caution', 0)} caution / {g.get('fail', 0)} fail / {g.get('pending', 0)} pending"
        )
    return "\n".join(lines)


def _fallback_prose(rows: list[dict], winner: int | None) -> str:
    if winner is None:
        return ("No honest winner: the matrix ties on every rule — same gate tier, same signal band, "
                "same fatals. Break the tie with a differentiator the decode can actually measure, or "
                "decide on founder-market-fit, the checklist no battle can answer for you.")
    w = next(r for r in rows if r["i"] == winner)
    others = [r for r in rows if r["i"] != winner]
    beat = others[0] if others else None
    why = _why(w, beat)
    return (f"Rule-based call: idea {w.get('label')} ({w.get('subject')}) — {why}. "
            f"The matrix is the evidence; this call is mechanical, not a judgment, and the red-team "
            f"fatals still need written answers before any code.")


def _why(w: dict, other: dict | None) -> str:
    bits: list[str] = []
    if other:
        if _tier(w) < _tier(other):
            bits.append("its gates are healthier")
        elif (w.get("score") or -1) > (other.get("score") or -1):
            bits.append(f"its signal score is higher ({w.get('score')} vs {other.get('score')})")
        elif (w.get("fatals") if isinstance(w.get("fatals"), (int, float)) else 999) < (other.get("fatals") if isinstance(other.get("fatals"), (int, float)) else 999):
            bits.append(f"the red team found fewer plan-killers ({w.get('fatals')} vs {other.get('fatals')})")
        elif (w.get("breakeven") if isinstance(w.get("breakeven"), (int, float)) else 10**9) < (other.get("breakeven") if isinstance(other.get("breakeven"), (int, float)) else 10**9):
            bits.append(f"it breaks even with fewer customers ({w.get('breakeven')} vs {other.get('breakeven')})")
        else:
            bits.append("it carries fewer compliance blockers")
    if not bits:
        bits.append(f"signal score {w.get('score')}, {w.get('fatals')} fatal challenges, verdict {w.get('decision')}")
    return "; ".join(bits)
