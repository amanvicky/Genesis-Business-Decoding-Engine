"""Full pipeline, offline: section coverage, ordering, cross-section wiring,
and per-agent failure containment."""
from __future__ import annotations

import asyncio

import pytest

from app import pipeline as pipeline_mod
from app.agents.structural import StructuralAgent
from app.export import TAB_ORDER
from app.models import AnalyzeRequest
from app.pipeline import run_pipeline


async def _collect(req: AnalyzeRequest) -> list[dict]:
    events: list[dict] = []

    async def emit(event: dict) -> None:
        events.append(event)

    await run_pipeline(req, emit)
    return events


def _run(mode: str = "idea", query: str = "AI meeting notes for sales teams") -> list[dict]:
    req = AnalyzeRequest(mode=mode, query=query)
    return asyncio.run(_collect(req))


@pytest.fixture(scope="module")
def events():
    return _run()


class TestOfflineDecode:

    def test_all_fourteen_sections(self, events):
        secs = [e["section"]["id"] for e in events if e["type"] == "section"]
        assert len(secs) == 16
        assert set(secs) == set(TAB_ORDER)

    def test_no_error_events(self, events):
        errs = [e for e in events if e.get("type") == "error"]
        assert errs == []
        for e in events:
            if e["type"] == "section":
                assert "error" not in (e["section"].get("data") or {}), e["section"]["id"]

    def test_every_section_reports_status_done(self, events):
        done_ids = {e["agent"] for e in events if e.get("type") == "status" and e.get("state") == "done"}
        assert {"recon", *TAB_ORDER} <= done_ids

    def test_done_report_sections_complete(self, events):
        done = [e for e in events if e["type"] == "done"][0]
        assert set(done["report"]["sections"]) == set(TAB_ORDER)

    def test_company_mode_too(self):
        events = _run("company", "Stripe")
        assert len([e for e in events if e["type"] == "section"]) == 16

    def test_pricing_sandbox_receives_burn(self, events):
        """_post_process must wire financial burn into the pricing sandbox."""
        done = [e for e in events if e["type"] == "done"][0]["report"]
        fin = done["sections"]["financial"]["data"]
        burn = ((fin.get("computed") or {}).get("burn_month"))
        sandbox = done["sections"]["pricing"]["data"].get("sandbox") or {}
        if burn is not None:
            assert sandbox.get("opex_month") == burn

    def test_subject_whitespace_stripped(self):
        events = _run("idea", "   padded subject name   ")
        done = [e for e in events if e["type"] == "done"][0]
        assert done["report"]["subject"] == "padded subject name"


class TestFailureContainment:
    def test_one_agent_crash_does_not_kill_pipeline(self, monkeypatch):
        async def boom(self, ev):
            raise RuntimeError("agent exploded")
        monkeypatch.setattr(StructuralAgent, "build", boom)
        events = _run()
        secs = {e["section"]["id"]: e["section"] for e in events if e["type"] == "section"}
        assert len(secs) == 16                      # still a full report
        assert "RuntimeError" in secs["structural"]["data"]["error"]
        assert secs["structural"]["data"]["partial"] is True
        assert [e for e in events if e.get("type") == "error"] == []

    def test_pipeline_still_yields_done_after_crash(self, monkeypatch):
        async def boom(self, ev):
            raise ValueError("nope")
        monkeypatch.setattr(StructuralAgent, "build", boom)
        events = _run()
        assert any(e["type"] == "done" for e in events)
