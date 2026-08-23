from __future__ import annotations

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
        seed=2041,
    )
    run.build.classes = []

    decision = build_season_decision(run)

    assert len(decision.options) == 3
    assert "experience as a Trainer" in decision.body
