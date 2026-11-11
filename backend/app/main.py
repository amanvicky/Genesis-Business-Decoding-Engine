"""Genesis FastAPI application.

Endpoints:
  GET  /api/health            — liveness + Tor/Ollama capability probes
  POST /api/analyze/stream    — NDJSON event stream (logs → sections → report)
  POST /api/battle/stream     — 2–3 ideas decoded sequentially, then the matrix
  GET  /api/briefs            — the vault (every decode, newest first)
  POST /api/briefs/watch      — mark a stored brief watched (re-decode interval)
  GET  /api/watch/status      — drift chip data + live checker progress
  GET  /api/watch/check       — lazy trigger: re-decode what's due, in background
  POST /api/watch/ack         — mark drift alerts seen
  POST /api/export/markdown   — full report → .md download
  POST /api/export/zip        — full report + scaffold → .zip download
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import __version__, advise, battle, export, llm, vault, verdict, watch
from .config import get_settings
from .models import AnalyzeRequest, BattleRequest
from .pipeline import run_pipeline
from .scrapers import tor as tor_mod

app = FastAPI(title="Genesis — Business Decoding & Replication Engine", version=__version__)
# Only the local dashboard may call this API from a browser — "*" let any
# website the founder visits read the decoded report via CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Subject text flows into the Content-Disposition header — anything outside this
# set (quotes, semicolons, CR/LF, unicode) is either header injection or breakage.
_FILESAFE = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_filename(report: dict) -> str:
    subject = str(report.get("subject") or "genesis")
    return _FILESAFE.sub("_", subject).strip("_")[:40] or "genesis"


async def _report_body(request: Request) -> dict:
    raw = await request.body()
    if len(raw) > 5_000_000:
        raise HTTPException(status_code=413, detail="report payload too large")
    try:
        body = json.loads(raw or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON body: {exc}") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")
    return body


@app.get("/api/health")
async def health() -> dict:
    settings = get_settings()
    tor = {"available": False, "reason": "disabled"}
    if settings.tor_enabled and not settings.genesis_offline:
        try:
            tor = await tor_mod.tor_status(settings.tor_proxy)
        except Exception:
            tor = {"available": False, "reason": "probe failed"}
    llm_model = await llm.resolve_model()
    return {
        "status": "ok",
        "version": __version__,
        "offline_mode": settings.genesis_offline,
        "tor": tor,
        "llm": {"available": llm_model is not None, "model": llm_model},
    }


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    async def generate():
        import asyncio

        queue: asyncio.Queue = asyncio.Queue(maxsize=256)

        async def push(event: dict) -> None:
            await queue.put(event)

        async def runner() -> None:
            try:
                report = await run_pipeline(req, push)
                # every decode lands in the vault — battle, watch and the
                # dashboard's watch-button all stand on this one save.
                # A vault hiccup must never turn a finished decode into an error.
                try:
                    entry = vault.save(report.model_dump())
                    await push({"type": "saved", "brief_id": entry["id"], "subject": entry["subject"]})
                except Exception as exc:
                    await push({"type": "log", "level": "warn", "agent": "genesis",
                                "msg": f"vault save failed ({type(exc).__name__}) — the brief still rendered above, it just isn't stored"})
            except Exception as exc:
                await push({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
            finally:
                await queue.put(None)

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
        finally:
            task.cancel()

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/battle/stream")
async def battle_stream(req: BattleRequest):
    """Idea Battle: decode 2–3 ideas one after another, then the matrix +
    rule-based winner. Events: battle_start → idea_start → (pipeline logs)
    → idea_done ×N → battle_done."""

    async def generate():
        import asyncio

        queue: asyncio.Queue = asyncio.Queue(maxsize=256)

        async def push(event: dict) -> None:
            await queue.put(event)

        async def runner() -> None:
            try:
                await battle.run_battle(req, push)
            except Exception as exc:
                await push({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
            finally:
                await queue.put(None)

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
        finally:
            task.cancel()

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/briefs")
async def briefs_list() -> dict:
    return {"briefs": [_brief_meta(e) for e in vault.list_all()]}


def _brief_meta(e: dict) -> dict:
    """The list view: metadata only — full fields live in the stored entry."""
    return {
        "id": e.get("id"),
        "subject": e.get("subject"),
        "mode": e.get("mode"),
        "created_at": e.get("created_at"),
        "watched": bool(e.get("watched")),
        "watch_days": e.get("watch_days"),
        "last_checked": e.get("last_checked"),
        "checks": e.get("checks"),
        "battle": bool(e.get("battle")),
    }


@app.post("/api/briefs/watch")
async def briefs_watch(request: Request):
    body = await _report_body(request)
    brief_id = str(body.get("brief_id") or "")
    days = body.get("days", vault.DEFAULT_WATCH_DAYS)
    if not isinstance(days, int) or not (1 <= days <= 90):
        raise HTTPException(status_code=422, detail="days must be an integer between 1 and 90")
    entry = vault.get(brief_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="no such brief in the vault")
    if entry.get("mode") not in ("company", "url"):
        raise HTTPException(status_code=422, detail="only company/url decodes can be watched — an idea has no stable identity to re-check")
    updated = vault.mark(brief_id, watched=True, days=days)
    return {"ok": True, "brief": _brief_meta(updated or {})}


@app.get("/api/watch/status")
async def watch_status() -> dict:
    s = watch.load_status()
    watched = sum(1 for e in vault.list_all() if e.get("watched"))
    return {**s, "watched_count": watched}


@app.get("/api/watch/check")
async def watch_check() -> dict:
    """The lazy trigger the dashboard calls on open: re-decode whatever is due,
    in the background. Never blocks and never double-runs."""
    started = watch.launch_background()
    return {"started": started, "running": bool(watch.STATUS.get("running"))}


@app.post("/api/watch/ack")
async def watch_ack() -> dict:
    watch.ack()
    return {"ok": True}


@app.post("/api/advise/stream")
async def advise_stream(request: Request):
    """Real-time founder advisor: NDJSON reasoning trail → grounded answer.

    Body: {"question": "...", "report": {<full report>}} — stateless by design;
    the brief the founder already decoded IS the context.
    """
    body = await _report_body(request)
    question = str(body.get("question") or "")
    if not question.strip():
        raise HTTPException(status_code=422, detail="question is required")
    if len(question) > advise.MAX_QUESTION:
        raise HTTPException(status_code=422, detail=f"question too long (max {advise.MAX_QUESTION} chars)")
    report = body.get("report")
    if not isinstance(report, dict):
        raise HTTPException(status_code=422, detail="report (the decoded brief) is required")

    async def generate():
        import asyncio

        queue: asyncio.Queue = asyncio.Queue(maxsize=64)

        async def push(event: dict) -> None:
            await queue.put(event)

        async def runner() -> None:
            try:
                trail = _reasoning_trail(question, report)
                for msg in trail:
                    await push({"type": "log", "msg": msg})
                answer = advise.advise(question, report)
                await push({"type": "answer", **answer})
            except Exception as exc:
                await push({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
            finally:
                await queue.put(None)

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield json.dumps(event, ensure_ascii=False, default=str) + "\n"
        finally:
            task.cancel()

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _reasoning_trail(question: str, report: dict) -> list[str]:
    """Short honest trail of what the advisor is reading — real-time feel
    without theater: each line names the tab actually consulted."""
    intent = advise.detect_intent(question)
    trail = [f"question routed → {intent}"]
    tab_map = {
        "capital": ["Tab 8 — burn calculator", "Tab 13 — capital strategy"],
        "market": ["Tab 13 — TAM/SAM/SOM"],
        "competitors": ["Tab 2 — alternatives scan"],
        "mvp": ["Tab 2 — build sequence"],
        "compliance": ["Tab 3 — statutory checklist"],
        "pricing": ["Tab 6 — unit economics"],
        "burn": ["Tab 8 — financial reality"],
        "customers": ["Tab 9 — distribution loops"],
        "risk": ["Tab 4 — failure post-mortems"],
        "redteam": ["Tab 19 — adversarial panel"],
        "dna": ["Tab 14 — product DNA"],
        "markets": ["Tab 16 — stock performance"],
        "deepdive": ["Tab 17 — company deep-dive"],
        "next": ["your brief's verdicts"],
        "hello": [],
    }
    for t in tab_map.get(intent, []):
        trail.append(f"reading {t}…")
    return trail


@app.post("/api/verdict")
async def verdict_endpoint(request: Request):
    """The Verdict Protocol: report + optional founder-market-fit answers →
    a deterministic GO / NO-GO / CONDITIONAL / PENDING memo. No LLM here on
    purpose — a verdict that can be argued into another outcome is worthless."""
    body = await _report_body(request)
    report = body.get("report")
    if not isinstance(report, dict):
        raise HTTPException(status_code=422, detail="report (the decoded brief) is required")
    answers = body.get("fmf_answers")
    if answers is not None:
        if (not isinstance(answers, list) or len(answers) > verdict._MAX_FMF_ANSWERS
                or not all(isinstance(a, bool) for a in answers)):
            raise HTTPException(status_code=422,
                                detail=f"fmf_answers must be a list of booleans (max {verdict._MAX_FMF_ANSWERS})")
    return verdict.build_memo(report, answers)


@app.post("/api/export/markdown")
async def export_markdown(request: Request):
    report = await _report_body(request)
    md = export.report_to_markdown(report)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return StreamingResponse(
        iter([md.encode("utf-8")]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="GENESIS_{_safe_filename(report)}_{stamp}.md"'},
    )


@app.post("/api/export/json")
async def export_json(request: Request):
    report = await _report_body(request)
    blob = export.report_to_json(report)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return StreamingResponse(
        iter([blob]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="GENESIS_{_safe_filename(report)}_{stamp}.json"'},
    )


@app.post("/api/export/zip")
async def export_zip(request: Request):
    report = await _report_body(request)
    blob = export.report_to_zip(report)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="GENESIS_{_safe_filename(report)}_{stamp}.zip"'},
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


# single-port hosting (cloud demo): when GENESIS_STATIC_DIR points at the
# static frontend export, FastAPI serves the dashboard itself — one origin for
# /api and the page, no proxy, no CORS. Declared last so /api routes win.
import os as _os  # noqa: E402

from fastapi.staticfiles import StaticFiles  # noqa: E402

_static_dir = _os.environ.get("GENESIS_STATIC_DIR")
if _static_dir and _os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="dashboard")
