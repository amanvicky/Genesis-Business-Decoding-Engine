"""Idea Battle: the rule-based winner, the sequential decode contract, and
the honest-tie rule. Offline mode makes llm.prose return None, so the prose
fallback path is exercised for real here."""
from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from app import battle, vault
from app.battle import _key, _tier, pick_winner, run_battle
from app.models import AnalyzeRequest, BattleRequest, Report, Section


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(vault, "BRIEFS", tmp_path / "briefs")
    return tmp_path / "briefs"


def _row(i: int, subject: str, *, gates: dict, score=None, fatals=None, breakeven=None, criticals=None, decision="PENDING") -> dict:
    return battle._row(i, subject, {"signal_score": score, "fatal_count": fatals,
                                    "breakeven_customers": breakeven, "compliance_criticals": criticals},
                       gates, decision)


def _report(subject: str, score: int) -> Report:
    req = AnalyzeRequest(mode="idea", query=subject)
    return Report(request=req, subject=subject,
                  sections={"structural": Section(id="structural", title="T", data={"verdict_score": score})})


class TestWinnerRules:
    def test_fully_measured_beats_a_failed_gate(self):
        rows = [_row(0, "A", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=20),
                _row(1, "B", gates={"pass": 0, "caution": 0, "fail": 1, "pending": 0}, score=45)]
        assert pick_winner(rows) == 0

    def test_higher_score_wins_within_a_tier(self):
        rows = [_row(0, "A", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=30),
                _row(1, "B", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=44)]
        assert pick_winner(rows) == 1

    def test_fatals_break_a_score_tie(self):
        rows = [_row(0, "A", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=5),
                _row(1, "B", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=2)]
        assert pick_winner(rows) == 1

    def test_breakeven_breaks_a_fatal_tie(self):
        rows = [_row(0, "A", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=2, breakeven=400),
                _row(1, "B", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=2, breakeven=120)]
        assert pick_winner(rows) == 1

    def test_caution_tier_between_pass_and_fail(self):
        assert _tier(_row(0, "A", gates={"pass": 2, "caution": 1, "fail": 0, "pending": 0})) == 2
        assert _tier(_row(0, "A", gates={"pass": 0, "caution": 0, "fail": 1, "pending": 0})) == 3
        assert _tier(_row(0, "A", gates={"pass": 2, "caution": 0, "fail": 0, "pending": 1})) == 4

    def test_full_tie_is_pending_never_a_coin_flip(self):
        rows = [_row(0, "A", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=2, breakeven=100, criticals=1),
                _row(1, "B", gates={"pass": 3, "caution": 0, "fail": 0, "pending": 0}, score=40, fatals=2, breakeven=100, criticals=1)]
        assert pick_winner(rows) is None
        assert _key(rows[0]) == _key(rows[1])

    def test_unmeasured_loses_to_measured(self):
        rows = [_row(0, "A", gates={"pass": 0, "caution": 0, "fail": 0, "pending": 3}),   # decode failed
                _row(1, "B", gates={"pass": 0, "caution": 1, "fail": 0, "pending": 0}, score=10)]
        assert pick_winner(rows) == 1

    def test_empty_rows_no_winner(self):
        assert pick_winner([]) is None


class TestBattleRequest:
    def test_two_to_three_ideas_only(self):
        assert BattleRequest(ideas=["a payroll idea", "a rival idea"]).ideas == ["a payroll idea", "a rival idea"]
        with pytest.raises(ValidationError):
            BattleRequest(ideas=["only one idea here"])
        with pytest.raises(ValidationError):
            BattleRequest(ideas=["a", "b", "c", "d"])

    def test_duplicates_and_stubs_rejected(self):
        with pytest.raises(ValidationError):
            BattleRequest(ideas=["Payroll for SMBs", "  payroll for SMBs "])
        with pytest.raises(ValidationError):
            BattleRequest(ideas=["ok idea here", "x"])

    def test_ideas_are_stripped(self):
        assert BattleRequest(ideas=["  idea one  ", "idea two"]).ideas == ["idea one", "idea two"]


class TestRunBattle:
    def _fake_pipeline(self, scores: dict[str, int | Exception]):
        async def fake(req: AnalyzeRequest, emit):
            await emit({"type": "log", "level": "agent", "agent": "recon", "msg": f"decoding {req.query}"})
            out = scores[req.query]
            if isinstance(out, Exception):
                raise out
            return _report(req.query, out)
        return fake

    def test_event_sequence_and_fallback_prose(self, env, monkeypatch):
        monkeypatch.setattr(battle, "run_pipeline", self._fake_pipeline({"A payroll idea": 40, "B rival idea": 22}))
        events: list[dict] = []
        result = asyncio.run(run_battle(BattleRequest(ideas=["A payroll idea", "B rival idea"]), events.append))
        kinds = [e["type"] for e in events]
        # sections swallowed, battle frame wrapped around pipeline logs
        assert kinds[0] == "battle_start"
        assert "idea_start" in kinds and "idea_done" in kinds
        assert kinds[-1] == "battle_done"
        assert "log" in kinds  # pipeline logs pass through
        # offline → rule-written prose, honestly labeled
        assert result["prose"].startswith("Rule-based call:")
        assert result["llm_wrote_prose"] is False
        assert result["winner"] == 0  # score 40 beats 22 in the same tier
        assert result["rows"][0]["score"] == 40
        assert result["rows"][1]["subject"] == "B rival idea"

    def test_each_battled_idea_is_vaulted(self, env, monkeypatch):
        monkeypatch.setattr(battle, "run_pipeline", self._fake_pipeline({"idea one x": 30, "idea two y": 31}))
        asyncio.run(run_battle(BattleRequest(ideas=["idea one x", "idea two y"]), lambda e: None))
        entries = vault.list_all()
        assert {e["subject"] for e in entries} == {"idea one x", "idea two y"}
        assert all(e["battle"] for e in entries)
        assert all(e["mode"] == "idea" for e in entries)

    def test_failed_idea_scores_as_unmeasured_and_battle_continues(self, env, monkeypatch):
        monkeypatch.setattr(battle, "run_pipeline", self._fake_pipeline({"good idea here": 35, "doomed idea": RuntimeError("engine ban")}))
        events: list[dict] = []
        result = asyncio.run(run_battle(BattleRequest(ideas=["good idea here", "doomed idea"]), events.append))
        assert result["winner"] == 0
        doomed = result["rows"][1]
        assert doomed["gates"]["pending"] == 3
        assert doomed["decision"] == "PENDING"
        assert any("decode failed" in e.get("msg", "") for e in events if e["type"] == "log")

    def test_tie_prose_names_the_honest_outcome(self, env, monkeypatch):
        monkeypatch.setattr(battle, "run_pipeline", self._fake_pipeline({"same idea a": 40, "same idea b": 40}))
        result = asyncio.run(run_battle(BattleRequest(ideas=["same idea a", "same idea b"]), lambda e: None))
        assert result["winner"] is None
        assert result["prose"].startswith("No honest winner")
