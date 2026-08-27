from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.items import complete_training
from auto_ptu.career.roster import capture_species


def test_simple_mode_trains_every_active_pokemon_before_calendar_lock() -> None:
    run = CareerEngine().new_run(
        player_id="team-training",
        name="Team Training",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        mode="simple",
        seed=4815,
    )
    assert capture_species(run, "Pidgey", source="training-depth", spend_ball=False) is not None
    assert capture_species(run, "Spearow", source="training-depth", spend_ball=False) is not None
    assert len(run.active_roster) == 3

    sessions = [complete_training(run, "conditioning", pokemon_id) for pokemon_id in run.active_roster]

    assert [session["sessions_available"] for session in sessions] == [3, 3, 3]
    assert run.season is not None
    assert run.season.training_completed is True
    assert run.season.training_completed_ids == run.active_roster
    active = [pokemon for pokemon in run.pokemon if pokemon.id in run.active_roster]
    assert all(pokemon.stat_training.get("hp") == 2 for pokemon in active)
