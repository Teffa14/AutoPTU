from pathlib import Path

import pytest

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript, CareerRun
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def fake_battle(spec: BattleSpec) -> BattleTranscript:
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team="career-home",
        winner_label=spec.home_club,
        rounds=3,
        events=[{"type": "test", "seed": spec.seed}],
        initial_state={"combatants": []},
        final_state={"battle_over": True, "winner_team": "career-home", "combatants": []},
        sha256=f"test-{spec.seed}",
    )


def service_for(tmp_path: Path) -> CareerService:
    return CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))


def test_decision_returns_after_featured_battle_then_finalizes_calendar(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    created = service.create_run(
        "pipeline-user",
        {
            "name": "Ari",
            "region": "kanto",
            "starter": "Rattata",
            "classes": ["Ace Trainer"],
            "seed": 818,
        },
    )
    run = CareerRun.from_dict(created)
    option_id = run.season.decision.options[0].id

    response = service.decide(
        "pipeline-user",
        run.id,
        {"expected_revision": run.revision, "option_id": option_id},
        "pipeline-decision-1",
    )

    prepared = CareerRun.from_dict(response["run"])
    assert response["season_resolved"] is False
    assert prepared.season_number == 1
    assert prepared.season.status == "battle"
    assert len(response["battle_ids"]) == 6

    featured_id = next(spec.id for spec in prepared.season.battles if spec.featured)
    assert response["featured_battle"]["battle_id"] == featured_id
    assert service.store.load_battle(featured_id)["battle_id"] == featured_id

    missing_id = next(battle_id for battle_id in response["battle_ids"] if battle_id != featured_id)
    with pytest.raises(KeyError):
        service.store.load_battle(missing_id)

    finalized = service.finalize_season("pipeline-user", run.id, featured_id)
    assert finalized["season_number"] == 2
    assert finalized["season"]["status"] == "decision"
    totals = finalized["totals"]
    assert totals["wins"] + totals["losses"] + totals["draws"] == 6
    assert all(service.store.load_battle(battle_id)["battle_id"] == battle_id for battle_id in response["battle_ids"])


def test_finalize_season_is_safe_to_retry_after_completion(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    created = service.create_run(
        "retry-user",
        {
            "name": "Rei",
            "region": "johto",
            "starter": "Sentret",
            "classes": ["Mentor"],
            "seed": 819,
        },
    )
    run = CareerRun.from_dict(created)
    response = service.decide(
        "retry-user",
        run.id,
        {"expected_revision": run.revision, "option_id": run.season.decision.options[0].id},
        "pipeline-decision-retry",
    )
    featured_id = response["featured_battle"]["battle_id"]

    first = service.finalize_season("retry-user", run.id, featured_id)
    second = service.finalize_season("retry-user", run.id, featured_id)

    assert second["revision"] == first["revision"]
    assert second["season_number"] == first["season_number"] == 2
    assert second["totals"] == first["totals"]


def test_resolve_prepared_season_rejects_duplicate_battle_transcripts() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="duplicate-transcript-user",
        name="Mara",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=820,
    )
    option_id = run.season.decision.options[0].id
    run, specs = engine.prepare_season(run, option_id=option_id)
    transcripts = [fake_battle(spec) for spec in specs]
    transcripts.append(fake_battle(specs[-1]))

    with pytest.raises(ValueError, match="duplicate"):
        engine.resolve_prepared_season(run, transcripts)


def test_resolve_prepared_season_rejects_duplicate_prepared_battle_ids() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="duplicate-calendar-user",
        name="Nia",
        region="johto",
        starter="Sentret",
        classes=["Mentor"],
        seed=821,
    )
    option_id = run.season.decision.options[0].id
    run, specs = engine.prepare_season(run, option_id=option_id)
    transcripts = [fake_battle(spec) for spec in specs]
    run.season.battles.append(specs[-1])
    run.season.battle_ids.append(specs[-1].id)

    with pytest.raises(ValueError, match="duplicate"):
        engine.resolve_prepared_season(run, transcripts)
