"""HTTP contract of the battle/vault/watch endpoints (offline, TestClient):
battle stream validation, the briefs list, watch marking rules, chip status.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import vault, watch
from app.main import app

client = TestClient(app)


@pytest.fixture
def briefs(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "BRIEFS", tmp_path / "briefs")
    # the background watch task may outlive a test's monkeypatches — point its
    # writes at tmp paths so no test ever touches the real runtime/ state
    monkeypatch.setattr(watch, "STATUS_FILE", tmp_path / "runtime" / "watch_status.json")
    monkeypatch.setattr(watch, "WATCH_LOG", tmp_path / "logs" / "watch.log")
    watch.STATUS.update({"running": False, "done": 0, "total": 0, "current": ""})
    return tmp_path / "briefs"


def _store(subject="Razorpay", mode="url", query="https://razorpay.com") -> str:
    return vault.save({
        "subject": subject, "sector": "fintech",
        "request": {"mode": mode, "query": query, "geography": "india", "team_size": 3,
                     "runway_target_months": 12, "include_darkweb": True},
        "sections": {},
    })["id"]


class TestBattleValidation:
    @pytest.mark.parametrize("payload", [
        {"ideas": ["just one idea here"]},                      # too few
        {"ideas": ["a", "b"]},                                  # too short
        {"ideas": ["idea one", "idea one"]},                    # duplicates
        {"ideas": ["one", "two", "three", "four"]},             # too many
        {"ideas": ["ok idea", "other ok idea"], "team_size": 0},
        {"ideas": ["ok idea", "other ok idea"], "geography": "mars"},
    ])
    def test_422(self, payload):
        assert client.post("/api/battle/stream", json=payload).status_code == 422

    def test_malformed_body(self):
        r = client.post("/api/battle/stream", content=b"{not json",
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422


class TestBriefsApi:
    def test_list_empty_and_populated(self, briefs):
        assert client.get("/api/briefs").json() == {"briefs": []}
        brief_id = _store()
        body = client.get("/api/briefs").json()
        assert len(body["briefs"]) == 1
        meta = body["briefs"][0]
        assert meta["id"] == brief_id and meta["mode"] == "url"
        assert "fields" not in meta  # metadata only — fields live in the entry

    def test_mark_watched_happy_path(self, briefs):
        brief_id = _store()
        r = client.post("/api/briefs/watch", json={"brief_id": brief_id, "days": 3})
        assert r.status_code == 200 and r.json()["brief"]["watched"] is True
        assert vault.get(brief_id)["watch_days"] == 3

    def test_mark_watched_404_and_bad_days(self, briefs):
        assert client.post("/api/briefs/watch", json={"brief_id": "ghost"}).status_code == 404
        brief_id = _store()
        assert client.post("/api/briefs/watch", json={"brief_id": brief_id, "days": 0}).status_code == 422
        assert client.post("/api/briefs/watch", json={"brief_id": brief_id, "days": 9999}).status_code == 422

    def test_idea_decodes_cannot_be_watched(self, briefs):
        brief_id = _store(subject="An Idea", mode="idea", query="some raw idea")
        r = client.post("/api/briefs/watch", json={"brief_id": brief_id})
        assert r.status_code == 422
        assert "stable identity" in r.json()["detail"]


class TestWatchApi:
    def test_status_shape(self, briefs):
        body = client.get("/api/watch/status").json()
        assert {"running", "drifts", "watched_count", "last_run"} <= set(body)
        assert body["drifts"] == []
        assert body["watched_count"] == 0

    def test_check_endpoint_never_blocks_never_double_runs(self, briefs):
        # nothing due → the background launcher starts (or refuses politely)
        r = client.get("/api/watch/check")
        assert r.status_code == 200
        assert isinstance(r.json()["started"], bool)

    def test_ack_endpoint(self):
        assert client.post("/api/watch/ack").status_code == 200
