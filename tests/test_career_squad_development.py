from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript, CareerRun
from auto_ptu.career.roster import capture_species, progress_after_season
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def new_run(tmp_path: Path) -> CareerRun:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine())
    return CareerRun.from_dict(service.create_run("development-user", {
        "name": "Development Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": 7070,
    }))


def test_late_capture_enters_close_to_current_squad_level(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    run.league = "regular"
    run.season_number = 8
    partner = run.pokemon[0]
    partner.level = 45

    captured = capture_species(run, "Pidgey", source="late-season-scouting", spend_ball=False)

    assert captured is not None
    assert captured.level >= partner.level - 3


def test_reserve_training_prevents_multi_season_level_lock_in(tmp_path: Path) -> None:
    run = new_run(tmp_path)
    run.league = "regular"
    run.season_number = 8
    for species in ("Pidgey", "Spearow", "Ekans", "Sandshrew", "Zubat", "Oddish"):
        assert capture_species(run, species, source="squad-depth", spend_ball=False) is not None

    available = [pokemon for pokemon in run.pokemon if pokemon.status != "retired"]
    run.active_roster = [pokemon.id for pokemon in available[:6]]
    reserve = available[6]
    for pokemon in available:
        pokemon.level = 30

    for season in range(8, 12):
        run.season_number = season
        active = [pokemon for pokemon in run.pokemon if pokemon.id in run.active_roster]
        spec = BattleSpec(
            id=f"development-s{season}",
            seed=season,
            region=run.build.region,
            league=run.league,
            season=season,
            home_club="Career Club",
            away_club="Rival Club",
            home_species=active[0].species,
            away_species="Pidgey",
            level=active[0].level,
            home_pokemon_id=active[0].id,
            home_team_species=[pokemon.species for pokemon in active],
            home_pokemon_ids=[pokemon.id for pokemon in active],
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
        progress_after_season(run, [spec], [transcript])

    active_average = round(sum(pokemon.level for pokemon in run.pokemon if pokemon.id in run.active_roster) / len(run.active_roster))
    assert reserve.level >= active_average - 3
