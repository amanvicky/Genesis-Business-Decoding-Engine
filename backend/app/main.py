"""Genesis FastAPI application.

Endpoints:
  GET  /api/health            — liveness + Tor/Ollama capability probes
  POST /api/analyze/stream    — NDJSON event stream (logs → sections → report)
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

from . import __version__, export, llm
from .config import get_settings
from .models import AnalyzeRequest
from .pipeline import run_pipeline
from .scrapers import tor as tor_mod

app = FastAPI(title="Genesis — Business Decoding & Replication Engine", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {
        "status": "ok",
        "version": __version__,
        "offline_mode": settings.genesis_offline,
        "tor": tor,
        "llm": {"available": await llm.available(), "model": settings.genesis_llm_model if await llm.available() else None},
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
                await run_pipeline(req, push)
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
