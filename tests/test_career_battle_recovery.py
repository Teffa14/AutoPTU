from pathlib import Path

import pytest

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript, CareerRun
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def successful_battle(spec: BattleSpec) -> BattleTranscript:
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team="career-home",
        winner_label=spec.home_club,
        rounds=2,
        events=[{"type": "test", "seed": spec.seed}],
        initial_state={"combatants": []},
        final_state={"battle_over": True, "winner_team": "career-home", "combatants": []},
        sha256=f"recovery-{spec.seed}",
    )


class FailOnceBattleRunner:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, spec: BattleSpec) -> BattleTranscript:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("simulated battle engine load failure")
        return successful_battle(spec)


def test_failed_featured_generation_keeps_retriable_battle_state(tmp_path: Path) -> None:
    runner = FailOnceBattleRunner()
    service = CareerService(store=CareerStore(tmp_path / "career"), engine=CareerEngine(runner))
    created = service.create_run(
        "recovery-user",
        {
            "name": "Recovery Trainer",
            "region": "kanto",
            "starter": "Rattata",
            "classes": ["Ace Trainer"],
            "seed": 822,
        },
    )
    run = CareerRun.from_dict(created)

    response = service.decide(
        "recovery-user",
        run.id,
        {"expected_revision": run.revision, "option_id": run.season.decision.options[0].id},
        "recovery-decision-1",
    )

    prepared = CareerRun.from_dict(response["run"])
    assert prepared.season.status == "battle"
    assert prepared.season.decisions_completed == prepared.season.decisions_required == 1
    assert "featured_battle" not in response

    featured_id = next(spec.id for spec in prepared.season.battles if spec.featured)
    with pytest.raises(KeyError):
        service.store.load_battle(featured_id)

    recovered = service.battle("recovery-user", run.id, featured_id)

    assert recovered["battle_id"] == featured_id
    assert runner.calls == 2
    assert service.store.load_battle(featured_id)["battle_id"] == featured_id
    still_prepared = CareerRun.from_dict(service.get_run("recovery-user", run.id))
    assert still_prepared.season.status == "battle"
    assert still_prepared.season.decisions_completed == still_prepared.season.decisions_required == 1
