from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from auto_ptu.api import career_api
from auto_ptu.career.decisions import build_season_decision
from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript


def fake_battle(spec: BattleSpec) -> BattleTranscript:
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team="career-home",
        winner_label=spec.home_club,
        rounds=1,
        events=[],
        initial_state={},
        final_state={"winner_team": "career-home"},
        sha256=f"decision-resilience-{spec.seed}",
    )


def test_decision_generation_survives_missing_persisted_trainer_class() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="legacy-empty-class",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        locale="en",
        seed=2041,
    )
    run.build.classes = []

    decision = build_season_decision(run)

    assert len(decision.options) == 3
    assert "experience as a Trainer" in decision.body


class _FakeCareerService:
    def __init__(self, *, club_completed: bool) -> None:
        self.club_completed = club_completed
        self.decide_calls = 0

    def preseason(self, player_id: str, run_id: str) -> dict:
        assert player_id == "trainer-1"
        assert run_id == "run-1"
        return {"club_completed": self.club_completed}

    def decide(self, player_id: str, run_id: str, payload: dict, idempotency_key: str) -> dict:
        self.decide_calls += 1
        return {
            "player_id": player_id,
            "run_id": run_id,
            "payload": payload,
            "idempotency_key": idempotency_key,
        }


def test_decision_api_blocks_schedule_progress_until_club_is_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _FakeCareerService(club_completed=False)
    monkeypatch.setattr(career_api, "SERVICE", service)
    monkeypatch.setattr(career_api, "_user", lambda authorization, development_user: SimpleNamespace(user_id="trainer-1"))

    with pytest.raises(HTTPException) as exc_info:
        career_api.career_decision(
            "run-1",
            {"option_id": "train"},
            authorization="",
            x_career_user="trainer-1",
            idempotency_key="decision-1",
        )

    assert exc_info.value.status_code == 400
    assert "Choose a club" in str(exc_info.value.detail)
    assert service.decide_calls == 0


def test_decision_api_allows_progress_after_club_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _FakeCareerService(club_completed=True)
    monkeypatch.setattr(career_api, "SERVICE", service)
    monkeypatch.setattr(career_api, "_user", lambda authorization, development_user: SimpleNamespace(user_id="trainer-1"))

    result = career_api.career_decision(
        "run-1",
        {"option_id": "train"},
        authorization="",
        x_career_user="trainer-1",
        idempotency_key="decision-1",
    )

    assert service.decide_calls == 1
    assert result["idempotency_key"] == "decision-1"
    assert result["payload"] == {"option_id": "train"}
