"""HTTP contract of the FastAPI app (offline, via TestClient): health, stream
validation, NDJSON stream shape, exports incl. header-injection defense."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import __version__, export
from app.main import app

client = TestClient(app)

VALID_REPORT = {
    "request": {"mode": "idea", "geography": "global"},
    "subject": "TestCo",
    "generated_at": "2026-11-03T00:00:00+00:00",
    "sections": {"structural": {"id": "structural", "title": "T", "data": {}}},
    "sources": [],
}


class TestHealth:
    def test_ok_and_deterministic_offline(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["version"] == __version__
        assert body["offline_mode"] is True
        assert body["tor"] == {"available": False, "reason": "disabled"}
        assert body["llm"] == {"available": False, "model": None}


class TestStreamValidation:
    @pytest.mark.parametrize("payload", [
        {},                                   # query missing
        {"query": "x"},                       # below min_length
        {"query": "a" * 301},                 # above max_length
        {"query": "ab", "mode": "nonsense"},  # bad enum
        {"query": "ab", "geography": "mars"},
        {"query": "ab", "team_size": 0},
        {"query": "ab", "runway_target_months": 99},
        {"query": "ab", "context": "x" * 2001},
    ])
    def test_422(self, payload):
        assert client.post("/api/analyze/stream", json=payload).status_code == 422

    def test_malformed_json_body(self):
        r = client.post("/api/analyze/stream", content=b"{not json",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422


class TestStreamHappyPath:
    @classmethod
    def setup_class(cls):
        r = client.post("/api/analyze/stream",
                        json={"mode": "idea", "query": "AI meeting notes for sales teams",
                              "geography": "global", "team_size": 3, "runway_target_months": 12})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/x-ndjson")
        cls.lines = [json.loads(ln) for ln in r.text.splitlines() if ln.strip()]
        cls.events = cls.lines
        done = [e for e in cls.events if e.get("type") == "done"]
        cls.report = done[0]["report"] if done else None

    def test_stream_has_logs_sections_and_done(self):
        types = {e["type"] for e in self.events}
        assert {"log", "status", "section", "done"} <= types
        assert "error" not in types

    def test_fourteen_sections(self):
        sections = [e["section"] for e in self.events if e["type"] == "section"]
        assert len(sections) == 17
        ids = [s["id"] for s in sections]
        assert len(set(ids)) == 17

    def test_adversary_runs_last(self):
        ids = [e["section"]["id"] for e in self.events if e["type"] == "section"]
        assert ids[-1] == "adversary"

    def test_done_report_shape(self):
        assert self.report is not None
        assert self.report["subject"] == "AI meeting notes for sales teams"
        assert len(self.report["sections"]) == 17
        assert "request" in self.report and "sources" in self.report

    def test_every_section_has_data_and_summary(self):
        for e in self.events:
            if e["type"] != "section":
                continue
            s = e["section"]
            assert s["title"], f"section {s['id']} missing title"
            assert isinstance(s["data"], dict), f"section {s['id']} data not a dict"
            assert "error" not in s["data"], f"section {s['id']} errored: {s['data'].get('error')}"


class TestExportEndpoints:
    def test_markdown(self):
        r = client.post("/api/export/markdown", json=VALID_REPORT)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/markdown")
        assert r.headers["content-disposition"].startswith('attachment; filename="GENESIS_TestCo_')
        assert r.text.startswith("# Genesis Decoding Report — TestCo")

    def test_json(self):
        r = client.post("/api/export/json", json=VALID_REPORT)
        assert r.status_code == 200
        assert r.json()["schema"] == "genesis.report/v1"

    def test_zip(self):
        r = client.post("/api/export/zip", json=VALID_REPORT)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/zip")
        assert r.content[:2] == b"PK"

    def test_empty_body_degrades_to_empty_report(self):
        r = client.post("/api/export/markdown", content=b"",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 200
        assert "Unknown" in r.text

    def test_invalid_json_is_400(self):
        r = client.post("/api/export/markdown", content=b"{oops",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 400
        assert "invalid JSON" in r.json()["detail"]

    def test_non_object_json_is_400(self):
        r = client.post("/api/export/markdown", json=[1, 2, 3])
        assert r.status_code == 400
        assert "JSON object" in r.json()["detail"]

    def test_oversized_payload_is_413(self):
        r = client.post("/api/export/markdown",
                        content=json.dumps({"subject": "x", "pad": "y" * 5_100_000}).encode(),
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 413

    def test_content_disposition_sanitized(self):
        hostile = dict(VALID_REPORT, subject='S; filename="evil.txt"\r\nX-Inject: 1')
        r = client.post("/api/export/markdown", json=hostile)
        hdr = r.headers["content-disposition"]
        assert "\r" not in hdr and "\n" not in hdr and '"' == hdr.split("filename=")[1][0]
        assert hdr.startswith('attachment; filename="GENESIS_S')


class TestErrorHandling:
    def test_404_unknown_route(self):
        assert client.get("/api/nope").status_code == 404

    def test_unhandled_exception_returns_500_json(self, monkeypatch):
        # ServerErrorMiddleware sends the JSON 500 and then re-raises so the
        # server can log; TestClient surfaces that re-raise unless disabled.
        no_raise = TestClient(app, raise_server_exceptions=False)

        def boom(report):
            raise RuntimeError("exporter exploded")
        monkeypatch.setattr(export, "report_to_markdown", boom)
        r = no_raise.post("/api/export/markdown", json=VALID_REPORT)
        assert r.status_code == 500
        assert "RuntimeError" in r.json()["detail"]
