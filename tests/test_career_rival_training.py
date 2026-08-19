from auto_ptu.career.battle import _rival_stat_training
from auto_ptu.career.models import BattleSpec


def spec(*, league: str = "junior", season: int = 1, seed: int = 42) -> BattleSpec:
    return BattleSpec(
        id="training-test",
        seed=seed,
        region="kanto",
        league=league,
        season=season,
        home_club="Saffron Comets",
        away_club="Cerulean Current",
        home_species="Bulbasaur",
        away_species="Squirtle",
        level=10,
    )


def test_rivals_train_from_the_first_season_deterministically() -> None:
    battle = spec()
    first = _rival_stat_training(battle, 0)
    second = _rival_stat_training(battle, 0)

    assert first == second
    assert sum(first.values()) == 2
    assert all(0 < value <= 12 for value in first.values())


def test_rival_training_accumulates_with_career_and_league_progression() -> None:
    junior = _rival_stat_training(spec(league="junior", season=1), 0)
    elite = _rival_stat_training(spec(league="elite", season=8), 0)
    teammate = _rival_stat_training(spec(league="elite", season=8), 1)

    assert sum(elite.values()) > sum(junior.values())
    assert sum(elite.values()) <= 30
    assert elite != teammate
    assert len(elite) <= 3
