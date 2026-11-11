"""Reality Watch: due logic, the re-decode diff, and the three alert tiers.

The re-decode itself is monkeypatched here (a real pipeline run hits the
network) — what's under test is the watch engine around it: which briefs are
due, when drift produces a memo + chip alert, when a clean check stays silent.
"""
from __future__ import annotations

import asyncio
import json
import time

import pytest

from app import fields, vault, watch
from app.models import AnalyzeRequest, Report, Section


@pytest.fixture
def env(tmp_path, monkeypatch):
    briefs = tmp_path / "briefs"
    monkeypatch.setattr(vault, "BRIEFS", briefs)
    monkeypatch.setattr(watch, "STATUS_FILE", tmp_path / "runtime" / "watch_status.json")
    monkeypatch.setattr(watch, "WATCH_LOG", tmp_path / "logs" / "watch.log")
    watch.STATUS.update({"running": False, "done": 0, "total": 0, "current": ""})
    return {"briefs": briefs, "tmp": tmp_path}


def _report(subject: str = "Acme", mode: str = "url", legal_name: str = "Acme Systems Private Limited",
            score: int = 34, breakeven: int = 230) -> Report:
    req = AnalyzeRequest(mode=mode, query="https://acme.io" if mode == "url" else subject, geography="global")
    return Report(
        request=req, subject=subject, sector="saas",
        sections={
            "structural": Section(id="structural", title="T", data={"verdict_score": score}),
            "financial": Section(id="financial", title="T", data={"computed": {"breakeven_customers": breakeven}}),
            "publicrecord": Section(id="publicrecord", title="T", data={
                "site": {"tech": ["shopify"], "emails": ["hello@acme.io"]},
                "legal_identity": {"legal_name": legal_name},
            }),
        },
    )


def _store_report(**kw) -> dict:
    return vault.save(_report(**kw).model_dump())


@pytest.fixture
def due_entry(env):
    entry = _store_report()
    vault.mark(entry["id"], watched=True, days=1)
    return entry


class TestDue:
    def test_watched_and_never_checked_is_due(self, due_entry):
        assert watch.due(vault.get(due_entry["id"])) is True

    def test_unwatched_is_never_due(self, env):
        entry = _store_report()
        assert watch.due(vault.get(entry["id"])) is False

    def test_inside_interval_not_due(self, due_entry):
        vault.update_after_check(due_entry["id"], fields.extract_fields(_report().model_dump()))
        assert watch.due(vault.get(due_entry["id"])) is False

    def test_past_interval_due_again(self, due_entry):
        vault.update_after_check(due_entry["id"], fields.extract_fields(_report().model_dump()))
        five_days_later = time.time() + 5 * 86400  # the check happened, then 5 days passed
        assert watch.due(vault.get(due_entry["id"]), now=five_days_later) is True

    def test_ideas_are_never_due_even_forced(self, env):
        entry = _store_report(mode="idea")
        vault.mark(entry["id"], watched=True, days=1)
        assert watch.due(vault.get(entry["id"]), force=True) is False

    def test_force_overrides_the_interval(self, due_entry):
        vault.update_after_check(due_entry["id"], fields.extract_fields(_report().model_dump()))
        assert watch.due(vault.get(due_entry["id"]), force=True) is True


class TestCheckDue:
    def test_drift_writes_memo_chip_and_updates_memo(self, env, due_entry, monkeypatch):
        changed = _report(legal_name="Acme Systems LLC", score=41)  # +7 → past threshold
        async def fake_pipeline(req, emit):
            return changed
        monkeypatch.setattr(watch, "run_pipeline", fake_pipeline)
        events: list[dict] = []
        summary = asyncio.run(watch.check_due(events.append))
        assert summary["drifts"] == 1 and summary["total"] == 1
        # tier 2: markdown memo next to the briefs
        memos = list(env["briefs"].glob("drift_acme_*.md"))
        assert len(memos) == 1
        text = memos[0].read_text(encoding="utf-8")
        assert "Legal name" in text and "Acme Systems LLC" in text
        # tier 3: chip data persisted, unseen
        status = json.loads(watch.STATUS_FILE.read_text(encoding="utf-8"))
        assert status["drifts"][0]["seen"] is False
        assert status["drifts"][0]["subject"] == "Acme"
        assert len(status["drifts"][0]["rows"]) == 2  # legal_name + signal_score
        # tier 1: the silent log — one line for the check
        assert "2 drift field(s)" in watch.WATCH_LOG.read_text(encoding="utf-8")
        # the stored memo now holds the NEW fields — next check diffs against them
        stored = vault.get(due_entry["id"])
        assert stored["fields"]["legal_name"] == "Acme Systems LLC"
        assert stored["last_checked"] is not None
        assert any("drifted" in e.get("msg", "") for e in events)

    def test_clean_check_stays_silent(self, env, due_entry, monkeypatch):
        async def fake_pipeline(req, emit):
            return _report()
        monkeypatch.setattr(watch, "run_pipeline", fake_pipeline)
        asyncio.run(watch.check_due())
        assert not list(env["briefs"].glob("drift_*.md"))
        status = json.loads(watch.STATUS_FILE.read_text(encoding="utf-8"))
        assert status["drifts"] == []
        assert "no drift" in watch.WATCH_LOG.read_text(encoding="utf-8")

    def test_nothing_due_is_a_no_op(self, env):
        summary = asyncio.run(watch.check_due())
        assert summary == {"total": 0, "drifts": 0, "at": summary["at"]}

    def test_failed_redecode_leaves_the_memo_untouched(self, env, due_entry, monkeypatch):
        async def boom(req, emit):
            raise RuntimeError("engine ban")
        monkeypatch.setattr(watch, "run_pipeline", boom)
        events: list[dict] = []
        asyncio.run(watch.check_due(events.append))
        stored = vault.get(due_entry["id"])
        assert stored["last_checked"] is None       # will retry next time
        assert not list(env["briefs"].glob("drift_*.md"))
        assert any("failed" in e.get("msg", "") for e in events)

    def test_checks_run_sequentially(self, env, monkeypatch):
        _store_report(subject="One", mode="company")
        _store_report(subject="Two", mode="company")
        for e in vault.list_all():
            vault.mark(e["id"], watched=True, days=1)
        active = {"n": 0, "max": 0}

        async def fake_pipeline(req, emit):
            active["n"] += 1
            active["max"] = max(active["max"], active["n"])
            await asyncio.sleep(0.01)
            active["n"] -= 1
            return _report(subject=req.query, mode="company")

        monkeypatch.setattr(watch, "run_pipeline", fake_pipeline)
        asyncio.run(watch.check_due())
        assert active["max"] == 1  # one decode at a time, always

    def test_drifts_capped_in_the_status_file(self, env, due_entry, monkeypatch):
        watch.STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        watch.STATUS_FILE.write_text(json.dumps({"drifts": [{"id": f"old-{i}", "seen": False} for i in range(55)]}), encoding="utf-8")
        async def fake_pipeline(req, emit):
            return _report(legal_name="Changed LLC")
        monkeypatch.setattr(watch, "run_pipeline", fake_pipeline)
        asyncio.run(watch.check_due())
        status = json.loads(watch.STATUS_FILE.read_text(encoding="utf-8"))
        assert len(status["drifts"]) == 50
        assert status["drifts"][0]["subject"] == "Acme"  # newest first


class TestAck:
    def test_ack_marks_every_drift_seen(self, env, due_entry, monkeypatch):
        async def fake_pipeline(req, emit):
            return _report(legal_name="Changed LLC")
        monkeypatch.setattr(watch, "run_pipeline", fake_pipeline)
        asyncio.run(watch.check_due())
        watch.ack()
        status = watch.load_status()
        assert all(d["seen"] for d in status["drifts"])
        watch.ack()  # ack with no file / already clean never raises
