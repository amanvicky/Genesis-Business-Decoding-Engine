"""Reality Watch — lazily re-decodes watched briefs and alerts on real drift.

Three alert tiers, always in this order:
  1. silent log        — every check appends to logs/watch.log, drift or not
  2. markdown memo     — a real field change writes briefs/drift_<subject>_<ts>.md
  3. dashboard chip    — the drift lands in runtime/watch_status.json, the
                         dashboard shows it as a chip with a per-tab panel

Runs happen (a) lazily when the dashboard opens after the interval, and
(b) on demand with `python genesis.py watch`. Re-decodes are sequential — one
at a time, never parallel, the same way battles run.

`python -m app.watch` (from backend/) is the CLI form genesis.py spawns.
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import fields as fields_mod
from . import vault
from .models import AnalyzeRequest
from .pipeline import run_pipeline  # module-level on purpose: tests monkeypatch this

ROOT = Path(__file__).resolve().parents[2]
WATCH_LOG = ROOT / "logs" / "watch.log"
STATUS_FILE = ROOT / "runtime" / "watch_status.json"

# live progress of the background checker (dashboard reads this via /api/watch/status)
STATUS: dict = {"running": False, "done": 0, "total": 0, "current": ""}

_task: asyncio.Task | None = None


def due(entry: dict, *, force: bool = False, now: float | None = None) -> bool:
    """A brief is due when it's watched, decodable again (company/url — ideas
    have no stable identity to re-check), and past its interval."""
    if not entry.get("watched"):
        return False
    if entry.get("mode") not in ("company", "url"):
        return False
    if force:
        return True
    ts = entry.get("last_checked")
    if not ts:
        return True
    try:
        checked = datetime.fromisoformat(str(ts)).timestamp()
    except ValueError:
        return True
    interval = max(1, int(entry.get("watch_days") or 7)) * 86400
    return (now if now is not None else time.time()) - checked >= interval


async def check_due(emit=None, *, force: bool = False) -> dict:
    """Re-decode every due brief, sequentially. Returns the run summary that
    also lands in watch_status.json. The emitter may be sync (CLI print,
    list.append in tests) or async (the API's queue)."""
    async def say(event: dict) -> None:
        if emit is None:
            return
        r = emit(event)
        if asyncio.iscoroutine(r):
            await r

    entries = [e for e in vault.list_all() if due(e, force=force)]
    STATUS.update({"running": True, "done": 0, "total": len(entries), "current": ""})
    drifts_total = 0
    try:
        if not entries:
            await say({"type": "log", "level": "info", "agent": "watch", "msg": "watch: nothing due — every watched brief is inside its interval"})
            return _finish(0, 0)
        for e in entries:
            STATUS["current"] = str(e.get("subject"))
            await say({"type": "log", "level": "agent", "agent": "watch", "msg": f"watch: re-decoding {e.get('subject')} (check #{int(e.get('checks') or 0) + 1})…"})
            try:
                req = AnalyzeRequest(**(e.get("request") or {}))
            except Exception:
                # a stored request that no longer validates must not stop the others
                await say({"type": "log", "level": "warn", "agent": "watch", "msg": f"watch: stored request for {e.get('subject')} is invalid — skipped"})
                STATUS["done"] += 1
                continue
            try:
                report = await run_pipeline(req, say)
            except Exception as exc:
                await say({"type": "log", "level": "warn", "agent": "watch", "msg": f"watch: re-decode of {e.get('subject')} failed ({type(exc).__name__}) — memo left untouched, will retry next time"})
                STATUS["done"] += 1
                continue
            new_fields = fields_mod.extract_fields(report.model_dump())
            drift = fields_mod.diff_fields(e.get("fields") or {}, new_fields)
            vault.update_after_check(str(e.get("id")), new_fields)
            if drift:
                drifts_total += 1
                _alert(e, drift)
                await say({"type": "log", "level": "warn", "agent": "watch", "msg": f"watch: {e.get('subject')} drifted — {len(drift)} field(s) changed, memo written"})
            else:
                await say({"type": "log", "level": "success", "agent": "watch", "msg": f"watch: {e.get('subject')} unchanged"})
            _log(e, drift)
            STATUS["done"] += 1
        return _finish(len(entries), drifts_total)
    finally:
        STATUS.update({"running": False, "current": ""})


def launch_background() -> bool:
    """Dashboard-open trigger: start the checker as a fire-and-forget task.
    Returns False when a check is already running (a second dashboard open
    must never double-decode)."""
    global _task
    if STATUS.get("running") or (_task is not None and not _task.done()):
        return False
    _task = asyncio.create_task(check_due())
    return True


def load_status() -> dict:
    """What the dashboard chip needs: live progress + persisted drifts."""
    try:
        saved = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        saved = {"drifts": [], "last_run": None, "last_summary": None}
    return {**STATUS, "drifts": saved.get("drifts") or [], "last_run": saved.get("last_run"), "last_summary": saved.get("last_summary")}


def ack() -> None:
    """Mark every stored drift seen (the founder read the panel)."""
    try:
        saved = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return
    for d in saved.get("drifts") or []:
        d["seen"] = True
    _persist(saved)


def _finish(total: int, drifts: int) -> dict:
    summary = {"total": total, "drifts": drifts, "at": datetime.now(timezone.utc).isoformat()}
    try:
        saved = json.loads(STATUS_FILE.read_text(encoding="utf-8")) if STATUS_FILE.exists() else {}
    except Exception:
        saved = {}
    saved["last_run"] = summary["at"]
    saved["last_summary"] = summary
    saved.setdefault("drifts", [])
    _persist(saved)
    return summary


def _alert(entry: dict, drift: list[dict]) -> None:
    """Tier 2 + 3: drift memo next to the brief, drift row into the status file."""
    vault.BRIEFS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = vault.slugify(str(entry.get("subject")))
    memo = vault.BRIEFS / f"drift_{slug}_{ts}.md"
    lines = [
        f"# Drift — {entry.get('subject')}",
        "",
        f"*{len(drift)} watched field(s) changed · detected {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · "
        f"brief `{entry.get('id')}` · check #{int(entry.get('checks') or 0) + 1}*",
        "",
    ]
    for r in drift:
        arrow = f"`{r['old'] or '—'}` → `{r['new'] or '—'}`"
        lines.append(f"- **{r['label']}** {r['action']} ({r['tab']}): {arrow}")
    lines += ["", "The stored memo fields are already updated — the next check diffs against this new state."]
    memo.write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        saved = json.loads(STATUS_FILE.read_text(encoding="utf-8")) if STATUS_FILE.exists() else {}
    except Exception:
        saved = {}
    drifts = saved.setdefault("drifts", [])
    drifts.insert(0, {
        "id": f"{entry.get('id')}-{ts}",
        "brief_id": entry.get("id"),
        "subject": entry.get("subject"),
        "at": datetime.now(timezone.utc).isoformat(),
        "seen": False,
        "rows": drift,
    })
    del drifts[50:]  # the panel shows recent history, not an unbounded log
    _persist(saved)


def _log(entry: dict, drift: list[dict]) -> None:
    """Tier 1: the silent log — every check lands here, drift or not."""
    try:
        WATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        verdict = f"{len(drift)} drift field(s)" if drift else "no drift"
        with WATCH_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp}  {entry.get('subject')}  check #{int(entry.get('checks') or 0)}  → {verdict}\n")
    except Exception:
        pass  # the log must never break the check


def _persist(saved: dict) -> None:
    try:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text(json.dumps(saved, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------- CLI (python -m app.watch)

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(prog="genesis watch", description="re-check watched briefs now")
    p.add_argument("--force", action="store_true", help="check every watched brief, ignoring the interval")
    args = p.parse_args()

    async def _cli_emit(event: dict) -> None:
        if event.get("type") == "log":
            tag = {"warn": "[!]", "success": "[OK]", "agent": "[*]"}.get(event.get("level", ""), "[*]")
            print(f"{tag} {event.get('msg', '')}", flush=True)

    print("Reality Watch — re-decoding every watched brief that is due (sequential, one at a time)…", flush=True)
    summary = asyncio.run(check_due(_cli_emit, force=args.force))
    status = load_status()
    unseen = [d for d in status.get("drifts") or [] if not d.get("seen")]
    if unseen:
        print(f"\n[!] {len(unseen)} drift alert(s) waiting on the dashboard:", flush=True)
        for d in unseen[:10]:
            print(f"    {d.get('subject')} — {len(d.get('rows') or [])} field(s) changed at {str(d.get('at'))[:19]}", flush=True)
    elif summary.get("drifts"):
        pass
    print(f"\ndone: {summary.get('total', 0)} brief(s) checked, {summary.get('drifts', 0)} drift(s) — memos in briefs/, full history in logs/watch.log", flush=True)
