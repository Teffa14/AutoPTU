from __future__ import annotations

from auto_ptu.career.catalogs import REGIONS
from auto_ptu.career.decisions import build_season_decision
from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript
from auto_ptu.career.roster import capture_species


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
        sha256=f"capture-overflow-{spec.seed}",
    )


def test_seventh_owned_pokemon_goes_to_pc_without_replacing_active_six() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="capture-overflow",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=2031,
    )

    candidates = [species for species in REGIONS["kanto"].underdogs if species != run.build.starter]
    for species in candidates[:5]:
        assert capture_species(run, species, source="test") is not None

    assert len(run.pokemon) == 6
    assert len(run.active_roster) == 6
    active_before = list(run.active_roster)
    balls_before = run.build.pokeballs

    overflow = capture_species(run, candidates[5], source="test")

    assert overflow is not None
    assert len(run.pokemon) == 7
    assert run.active_roster == active_before
    assert overflow.id not in run.active_roster
    assert overflow.status == "pc"
    assert run.build.pokeballs == balls_before - 1
    event = run.timeline[-1]
    assert event["type"] == "pokemon.captured"
    assert overflow.species in event["species"]


def test_capture_decisions_continue_after_active_six_and_report_pc_storage() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="capture-cadence",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        locale="en",
        seed=2032,
    )

    candidates = [species for species in REGIONS["kanto"].underdogs if species != run.build.starter]
    for species in candidates[:6]:
        assert capture_species(run, species, source="test") is not None

    assert len(run.pokemon) == 7
    assert len(run.active_roster) == 6
    assert len([entry for entry in run.pokemon if entry.status == "pc"]) == 1

    # Season 4 is a forced capture cadence slot but its authored rotation would
    # otherwise resolve to research. A full active roster must not suppress it.
    run.season_number = 4
    decision = build_season_decision(run)

    assert decision.family == "capture"
    assert "6/6 active places occupied" in decision.body
    assert "1 Pokemon in PC" in decision.body
