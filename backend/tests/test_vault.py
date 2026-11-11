"""The briefs vault: persist every decode as JSON + markdown twin, cap 3 per
subject, and stay harmless when files are corrupt or the folder is missing."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app import vault


@pytest.fixture
def briefs(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "BRIEFS", tmp_path / "briefs")
    return tmp_path / "briefs"


class _Clock:
    """Each save gets its own second — two saves of the same subject must be
    two entries, not one overwritten file."""
    def __init__(self):
        self.n = 0

    def now(self, tz=None):
        self.n += 1
        return datetime(2026, 11, 12, 10, 0, self.n % 60, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    c = _Clock()
    monkeypatch.setattr(vault, "datetime", c)
    return c


def _report(subject="Razorpay", mode="url", query="https://razorpay.com", **sec_over):
    return {
        "subject": subject,
        "sector": "fintech",
        "request": {"mode": mode, "query": query, "geography": "india", "team_size": 3,
                     "runway_target_months": 12, "include_darkweb": True},
        "sections": {"publicrecord": {"id": "publicrecord", "title": "T", "data": {
            "legal_identity": {"legal_name": "Razorpay Software Services Pvt Ltd"}}}},
    }


class TestSave:
    def test_json_and_markdown_twin_written(self, briefs, clock):
        entry = vault.save(_report())
        j, m = briefs / f"{entry['id']}.json", briefs / f"{entry['id']}.md"
        assert j.exists() and m.exists()
        stored = json.loads(j.read_text(encoding="utf-8"))
        assert stored["subject"] == "Razorpay"
        assert stored["fields"]["legal_name"] == "Razorpay Software Services Pvt Ltd"
        assert stored["domain"] == "razorpay.com"
        assert stored["watched"] is False
        assert "# Brief — Razorpay" in m.read_text(encoding="utf-8")

    def test_cap_three_per_subject_oldest_evicted(self, briefs, clock):
        ids = [vault.save(_report())["id"] for _ in range(4)]
        assert len(list(briefs.glob("razorpay-*.json"))) == 3
        assert ids[0] not in [p.stem for p in briefs.glob("*.json")]          # oldest gone
        assert not (briefs / f"{ids[0]}.md").exists()                          # twin evicted too
        assert ids[3] in [p.stem for p in briefs.glob("*.json")]               # newest kept

    def test_subjects_do_not_evict_each_other(self, briefs, clock):
        vault.save(_report(subject="Zoho", query="zoho.com"))
        vault.save(_report(subject="ADP", mode="company", query="ADP"))
        assert len(vault.list_all()) == 2

    def test_prefix_collision_never_evicts_a_longer_subject(self, briefs, clock):
        # "Razorpay Labs" files start with "razorpay-" too — a filename glob
        # would let Razorpay saves evict them; grouping reads each subject
        for _ in range(3):
            vault.save(_report(subject="Razorpay Labs", query="razorpaylabs.com"))
        vault.save(_report())  # plain Razorpay save
        subjects = {e["subject"] for e in vault.list_all()}
        assert subjects == {"Razorpay Labs", "Razorpay"}
        assert len([e for e in vault.list_all() if e["subject"] == "Razorpay Labs"]) == 3

    def test_unsafe_subject_slugs_stay_filesafe(self, briefs, clock):
        entry = vault.save(_report(subject="../../etc/passwd & co"))
        assert "/" not in entry["id"] and ".." not in entry["id"]
        assert entry["id"].startswith("etc-passwd-co")


class TestListAndGet:
    def test_list_newest_first_and_corrupt_files_skipped(self, briefs, clock):
        vault.save(_report(subject="A"))
        vault.save(_report(subject="B"))
        (briefs / "junk.json").write_text("{not json", encoding="utf-8")
        names = [e["subject"] for e in vault.list_all()]
        assert names == ["B", "A"]  # junk skipped, newest first

    def test_list_on_missing_folder_is_empty(self, briefs):
        assert vault.list_all() == []

    def test_get_rejects_path_traversal(self, briefs, clock):
        assert vault.get("../secret") is None
        assert vault.get("with/slash") is None


class TestMarkAndUpdate:
    def test_mark_watched_clamps_days(self, briefs, clock):
        entry = vault.save(_report())
        updated = vault.mark(entry["id"], watched=True, days=9999)
        assert updated["watched"] is True
        assert updated["watch_days"] == 90  # clamped, not trusted
        assert vault.mark("no-such-id", watched=True) is None

    def test_update_after_check_stamps_the_memo(self, briefs, clock):
        entry = vault.save(_report())
        vault.update_after_check(entry["id"], {"legal_name": "New Name Ltd", "tech": []})
        stored = vault.get(entry["id"])
        assert stored["fields"] == {"legal_name": "New Name Ltd", "tech": []}
        assert stored["checks"] == 1
        assert stored["last_checked"] is not None
