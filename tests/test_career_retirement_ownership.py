from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerPokemon


def test_retirement_summary_counts_only_permanently_owned_pokemon() -> None:
    engine = CareerEngine()
    run = engine.new_run(
        player_id="retirement-owner",
        name="Ownership Trainer",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=9917,
    )
    owned_before = sum(1 for pokemon in run.pokemon if pokemon.ownership == "owned")
    assert owned_before == 1

    loan = CareerPokemon(
        id=f"{run.id}-loan-test",
        species="Pidgey",
        caught_species="Pidgey",
        level=run.pokemon[0].level,
        acquired_season=run.season_number,
        acquired_age=run.age,
        capture_region=run.build.region,
        ownership="loan",
        loan_club_id=run.contract.club_id if run.contract else "",
        loan_expires_season=run.season_number,
    )
    run.pokemon.append(loan)
    run.active_roster.append(loan.id)

    engine.retire(run, "voluntary")

    assert run.summary is not None
    assert len(run.pokemon) == 2
    assert run.summary.pokemon_owned == owned_before
