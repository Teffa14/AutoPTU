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
