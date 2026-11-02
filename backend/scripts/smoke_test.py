"""Offline smoke test: run the full 12-section pipeline with no network.

Usage (from backend/):  python scripts/smoke_test.py [subject]
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("GENESIS_OFFLINE", "1")

from app.models import AnalyzeRequest  # noqa: E402
from app.pipeline import run_pipeline  # noqa: E402


async def main() -> None:
    args = sys.argv[1:]
    mode = "idea"
    if args and args[0] in ("company", "idea"):
        mode = args.pop(0)
    subject = " ".join(args) or "AI meeting notes for sales teams"
    req = AnalyzeRequest(mode=mode, query=subject, geography="global", team_size=3, runway_target_months=12)

    sections = 0
    total = 13
    async for event in _stream(req):
        etype = event.get("type")
        if etype == "log":
            print(f"[{event.get('level', 'info'):>7}] {event.get('agent', '?'):>10}: {event.get('msg', '')}")
        elif etype == "section":
            sections += 1
            sec = event["section"]
            print(f"   + section {sections:>2}/{total}  {sec['id']}: {sec['summary'][:100]}")
        elif etype == "error":
            print(f"[  ERROR] {event.get('msg')}")
            sys.exit(1)
    print(f"\nOK: pipeline produced {sections}/{total} sections offline.")


async def _stream(req: AnalyzeRequest):
    import asyncio
    import json

    from app.pipeline import run_pipeline

    queue: asyncio.Queue = asyncio.Queue()

    async def push(event: dict) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            await run_pipeline(req, push)
        except Exception as exc:
            await queue.put({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
        finally:
            await queue.put(None)

    task = asyncio.create_task(runner())
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield json.loads(json.dumps(event, default=str))
    finally:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
