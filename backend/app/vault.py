"""The briefs vault — every decode persists here, capped at 3 per subject.

briefs/ holds one JSON (the machine-readable memo watch.py diffs against) and
one markdown twin (the human-readable copy) per decode. Three per subject:
a fourth decode of the same subject evicts the oldest. The folder is the
product — battle reads it, watch re-checks it, and deleting the folder resets
the whole history with zero leftovers anywhere else.

GENESIS_BRIEFS_DIR moves the folder (tests use this; users never need to).
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = Path(os.environ.get("GENESIS_BRIEFS_DIR") or (ROOT / "briefs"))

CAP_PER_SUBJECT = 3
DEFAULT_WATCH_DAYS = 7
_FILESAFE = re.compile(r"[^a-z0-9_-]+")


def slugify(subject: str) -> str:
    """Subject → one safe filename chunk. Collisions across different
    subjects don't matter: the entry carries its real subject inside, and
    prune groups by this slug only for the cap."""
    return _FILESAFE.sub("-", (subject or "unknown").lower()).strip("-")[:40] or "unknown"


def save(report: dict, *, battle: bool = False) -> dict:
    """Persist one finished decode. Returns the stored entry. Never raises to
    the caller's stream — callers wrap this; a vault hiccup must not kill a
    decode that already succeeded."""
    BRIEFS.mkdir(parents=True, exist_ok=True)
    fields = _extract(report)
    subject = str(report.get("subject") or "Unknown")
    now = datetime.now(timezone.utc)
    entry = {
        "id": f"{slugify(subject)}-{now.strftime('%Y%m%d-%H%M%S')}",
        "subject": subject,
        "sector": report.get("sector"),
        "mode": (report.get("request") or {}).get("mode") or "idea",
        "query": (report.get("request") or {}).get("query") or "",
        "domain": _domain(report),
        "request": report.get("request") or {},
        "created_at": now.isoformat(),
        "fields": fields,
        "watched": False,
        "watch_days": DEFAULT_WATCH_DAYS,
        "last_checked": None,
        "checks": 0,
        "battle": battle,
    }
    _prune(slugify(subject), keep=CAP_PER_SUBJECT - 1)
    (BRIEFS / f"{entry['id']}.json").write_text(json.dumps(entry, indent=2, default=str), encoding="utf-8")
    (BRIEFS / f"{entry['id']}.md").write_text(_markdown(entry), encoding="utf-8")
    return entry


def list_all() -> list[dict]:
    """Every stored entry, newest first. Corrupt files are skipped, not fatal —
    a half-written entry (power cut mid-write) must not hide the others."""
    if not BRIEFS.exists():
        return []
    out: list[dict] = []
    for p in sorted(BRIEFS.glob("*.json"), reverse=True):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    out.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
    return out


def get(entry_id: str) -> dict | None:
    if not entry_id or "/" in entry_id or "\\" in entry_id or ".." in entry_id:
        return None
    p = BRIEFS / f"{entry_id}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def mark(entry_id: str, watched: bool = True, days: int = DEFAULT_WATCH_DAYS) -> dict | None:
    """Flip the watch flag on a stored entry (interval 1–90 days)."""
    e = get(entry_id)
    if e is None:
        return None
    e["watched"] = bool(watched)
    e["watch_days"] = max(1, min(90, int(days)))
    _write(e)
    return e


def update_after_check(entry_id: str, new_fields: dict) -> None:
    """Watch bookkeeping after a re-decode: refresh the memo fields, stamp the
    check. The drift alert itself is watch.py's job — this only stores state."""
    e = get(entry_id)
    if e is None:
        return
    e["fields"] = new_fields
    e["last_checked"] = datetime.now(timezone.utc).isoformat()
    e["checks"] = int(e.get("checks") or 0) + 1
    _write(e)


def _write(entry: dict) -> None:
    (BRIEFS / f"{entry['id']}.json").write_text(json.dumps(entry, indent=2, default=str), encoding="utf-8")
    (BRIEFS / f"{entry['id']}.md").write_text(_markdown(entry), encoding="utf-8")


def _prune(subject_slug: str, *, keep: int) -> None:
    """Delete oldest json+md pairs of this subject beyond the cap, keeping
    `keep` slots free for the entry being written right now. Grouping reads
    each entry's own subject — a filename-prefix glob would let "Razorpay"
    evict "Razorpay Labs" entries."""
    mine: list[Path] = []
    if not BRIEFS.exists():
        return
    for p in BRIEFS.glob("*.json"):
        try:
            if slugify(json.loads(p.read_text(encoding="utf-8")).get("subject") or "") == subject_slug:
                mine.append(p)
        except Exception:
            continue  # unreadable files are never pruned by a later save
    mine.sort()
    for p in mine[:-keep] if keep else mine:
        p.unlink(missing_ok=True)
        p.with_suffix(".md").unlink(missing_ok=True)


def _extract(report: dict) -> dict:
    from . import fields as fields_mod  # late import keeps module load order simple
    return fields_mod.extract_fields(report)


def _domain(report: dict) -> str | None:
    req = report.get("request") or {}
    if req.get("mode") == "url":
        from .text import domain_of
        d = domain_of(str(req.get("query") or ""))
        return d or None
    return None


def _markdown(entry: dict) -> str:
    f = entry.get("fields") or {}
    lines = [
        f"# Brief — {entry.get('subject')}",
        "",
        f"- mode: {entry.get('mode')}" + (f" · domain: {entry['domain']}" if entry.get("domain") else ""),
        f"- decoded: {str(entry.get('created_at'))[:19].replace('T', ' ')} UTC",
        f"- watch: {'on, every ' + str(entry.get('watch_days')) + 'd' if entry.get('watched') else 'off'}"
        + (f" · checked {entry.get('checks')}×, last {str(entry.get('last_checked'))[:19]}" if entry.get("last_checked") else ""),
        "",
        "## Stable fields (what watch diffs)",
        "",
    ]
    for k, v in f.items():
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v) if v else "—"
        lines.append(f"- {k}: {v if v not in (None, '') else '—'}")
    lines += [
        "",
        "---",
        f"*stored {time.strftime('%Y-%m-%d %H:%M')} · re-check manually with `python genesis.py watch` · "
        "drift memos land next to this file*",
    ]
    return "\n".join(lines) + "\n"
