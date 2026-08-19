from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript, CareerRun
from auto_ptu.career.roster import TRAINING_KIT_WEAR, grant_stat_training, progress_after_season, set_active_roster
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def new_run(tmp_path: Path) -> CareerRun:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine())
    return CareerRun.from_dict(service.create_run("longevity-user", {
        "name": "Longevity Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": 9912,
    }))


def test_normal_training_does_not_consume_pokemon_career_health(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    pokemon = run.pokemon[0]

    trained = grant_stat_training(run, pokemon.id, "hp", 2, source="season_training:conditioning")

    assert trained is not None
    assert pokemon.career_health == 100
    assert pokemon.training_wear == 0
    assert pokemon.status != "retired"


def test_training_kits_consume_longevity_and_eventually_retire_pokemon(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    pokemon = run.pokemon[0]
    stats = ["hp", "atk", "def", "spatk", "spdef", "spd"]
    uses = 0

    while pokemon.status != "retired":
        stat = stats[uses % len(stats)]
        trained = grant_stat_training(run, pokemon.id, stat, 2, source="item:training_kit")
        assert trained is not None
        uses += 1
        assert uses < 20

    assert pokemon.career_health == 0
    assert pokemon.training_wear == uses * TRAINING_KIT_WEAR
    assert pokemon.retired_reason == "training_wear"
    assert pokemon.retired_season == run.season_number
    assert pokemon.id not in run.active_roster
    assert any(entry.get("type") == "pokemon.retired" and entry.get("pokemon_id") == pokemon.id for entry in run.timeline)


def test_season_workload_creates_natural_competitive_lifespan(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    pokemon = run.pokemon[0]
    spec = BattleSpec(
        id="longevity-match",
        seed=1,
        region=run.build.region,
        league=run.league,
        season=1,
        home_club="Career Club",
        away_club="Rival Club",
        home_species=pokemon.species,
        away_species="Pidgey",
        level=pokemon.level,
        home_pokemon_id=pokemon.id,
        home_team_species=[pokemon.species],
        home_pokemon_ids=[pokemon.id],
    )
    transcript = BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team="career-home",
        winner_label="Career Club",
        rounds=1,
        events=[],
        initial_state={},
        final_state={},
        sha256="0" * 64,
    )

    retired_at = 0
    for season in range(1, 45):
        run.season_number = season
        spec.season = season
        progress_after_season(run, [spec], [transcript])
        if pokemon.status == "retired":
            retired_at = season
            break

    assert 20 <= retired_at <= 35
    assert pokemon.career_health == 0
    assert pokemon.training_wear == 0
    assert pokemon.retired_reason == "career_wear"
    assert any(entry.get("type") == "pokemon.longevity_updated" for entry in run.timeline)


def test_training_kit_is_multiple_seasons_of_normal_wear(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    pokemon = run.pokemon[0]
    before = pokemon.career_health

    trained = grant_stat_training(run, pokemon.id, "atk", 2, source="item:training_kit")

    assert trained is not None
    assert before - pokemon.career_health == TRAINING_KIT_WEAR
    assert TRAINING_KIT_WEAR >= 3 * 3


def test_retired_pokemon_cannot_be_reselected_and_longevity_round_trips(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    pokemon = run.pokemon[0]
    pokemon.career_health = 0
    pokemon.status = "retired"
    run.active_roster = [entry.id for entry in run.pokemon if entry.id != pokemon.id][:6]

    restored = CareerRun.from_dict(run.to_dict())
    retired = next(entry for entry in restored.pokemon if entry.id == pokemon.id)

    assert retired.career_health == 0
    assert retired.status == "retired"
    try:
        set_active_roster(restored, [pokemon.id])
    except ValueError as exc:
        assert "retired or unavailable" in str(exc) or "exactly" in str(exc)
    else:
        raise AssertionError("Retired Pokémon must not be selectable.")