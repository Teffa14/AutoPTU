from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from auto_ptu.career.battle import simulate_battle
from auto_ptu.career.models import BattleSpec


def _spec(battle_id: str, seed: int, *, region: str = "kanto", home: str = "Rattata", away: str = "Caterpie") -> BattleSpec:
    return BattleSpec(
        id=battle_id,
        seed=seed,
        region=region,
        league="junior",
        season=1,
        home_club="Home",
        away_club="Away",
        home_species=home,
        away_species=away,
        level=5,
    )


def test_same_battle_twice_has_identical_transcript_hash() -> None:
    spec = _spec("deterministic", 123)
    first = simulate_battle(spec)
    second = simulate_battle(spec)
    assert first.sha256 == second.sha256
    assert first.events == second.events
    assert first.final_state == second.final_state
    assert all(entry["stats"] for entry in first.initial_state["combatants"])
    assert all(entry["moves"] for entry in first.initial_state["combatants"])
    assert all(entry["nature"] for entry in first.initial_state["combatants"])
    assert all(entry["abilities"] for entry in first.initial_state["combatants"])
    assert all(entry["types"] for entry in first.initial_state["combatants"])
    assert all(entry["size"] and entry["footprint_side"] >= 1 for entry in first.initial_state["combatants"])
    rattata = next(entry for entry in first.initial_state["combatants"] if entry["team"] == "career-home")
    assert {move["name"] for move in rattata["moves"]}.isdisjoint({"Thunder", "Ice Beam", "Surf"})


def test_run_identity_does_not_change_mechanical_transcript_hash() -> None:
    first = simulate_battle(_spec("first-run-s1-m1", 123))
    second = simulate_battle(_spec("second-run-s1-m1", 123))
    assert first.sha256 == second.sha256


def test_concurrent_battles_do_not_share_engine_state() -> None:
    specs = [_spec("battle-a", 301), _spec("battle-b", 902, home="Weedle", away="Spearow")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(simulate_battle, specs))
    assert {entry.battle_id for entry in results} == {"battle-a", "battle-b"}
    assert results[0].sha256 != results[1].sha256
    assert all(entry.events for entry in results)


def test_paldea_pbs_species_can_enter_real_ptu_battle() -> None:
    transcript = simulate_battle(_spec("paldea", 321, region="paldea", home="Lechonk", away="Pawmi"))
    assert transcript.rounds > 0
    assert transcript.winner_team in {"career-home", "career-away"}
    assert transcript.sha256


def test_career_preparation_bonus_uses_real_ptu_levels() -> None:
    baseline = simulate_battle(_spec("baseline", 777))
    prepared_spec = _spec("prepared", 777)
    prepared_spec.home_level_bonus = 2
    prepared_spec.away_level_bonus = -1
    prepared = simulate_battle(prepared_spec)
    baseline_levels = {entry["team"]: entry["level"] for entry in baseline.initial_state["combatants"]}
    prepared_levels = {entry["team"]: entry["level"] for entry in prepared.initial_state["combatants"]}
    assert prepared_levels["career-home"] == baseline_levels["career-home"] + 2
    assert prepared_levels["career-away"] == baseline_levels["career-away"] - 1
    assert prepared.sha256 != baseline.sha256


def test_complete_team_battle_uses_tactical_engine_ai_on_both_sides() -> None:
    spec = _spec("team-ai", 7)
    spec.home_team_species = ["Rattata", "Caterpie"]
    spec.home_pokemon_ids = ["partner", "capture-1"]
    spec.home_team_levels = [8, 8]
    spec.away_team_species = ["Spearow", "Weedle"]
    spec.away_team_levels = [8, 8]
    transcript = simulate_battle(spec)

    assert len(transcript.initial_state["combatants"]) == 4
    assert transcript.spec.home_ai_level == transcript.spec.away_ai_level == "tactical"
    engine_actions = [event for event in transcript.events if event.get("type") in {"move", "shift", "switch"}]
    assert any(str(event.get("actor", "")).startswith("career-home-") for event in engine_actions)
    assert any(str(event.get("actor", "")).startswith("career-away-") for event in engine_actions)
    assert any(event.get("type") == "switch" for event in transcript.events)
    assert not any(event.get("type") == "match_adjudicated" for event in transcript.events)
    team_hp = {
        team: sum(max(0, int(entry["hp"])) for entry in transcript.final_state["combatants"] if entry["team"] == team)
        for team in ("career-home", "career-away")
    }
    assert team_hp[transcript.winner_team] > 0
    assert team_hp["career-away" if transcript.winner_team == "career-home" else "career-home"] == 0
    damaging = next(event for event in transcript.events if event.get("type") == "move" and event.get("damage", 0) > 0)
    assert {"attack_value", "defense_value", "type_multiplier", "effective_db"}.issubset(damaging)
    expected_types = {
        "Rattata": {"Normal"}, "Caterpie": {"Bug"},
        "Spearow": {"Normal", "Flying"}, "Weedle": {"Bug", "Poison"},
    }
    assert all(set(entry["types"]) == expected_types[entry["species"]] for entry in transcript.initial_state["combatants"])
    repeated = simulate_battle(spec)
    assert repeated.sha256 == transcript.sha256
    assert repeated.events == transcript.events
