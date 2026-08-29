from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.roster import capture_species, initialize_roster


def test_initialize_roster_repairs_duplicate_active_ids() -> None:
    run = CareerEngine().new_run(
        player_id="roster-recovery",
        name="Roster Recovery",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=9913,
    )
    first_replacement = capture_species(run, "Pidgey", source="recovery-test", spend_ball=False)
    second_replacement = capture_species(run, "Spearow", source="recovery-test", spend_ball=False)
    assert first_replacement is not None
    assert second_replacement is not None

    partner_id = run.pokemon[0].id
    run.active_roster = [partner_id, partner_id, partner_id]

    changed = initialize_roster(run, stable_seed=run.seed)

    assert changed is True
    assert run.active_roster == [partner_id, first_replacement.id, second_replacement.id]
    assert len(run.active_roster) == len(set(run.active_roster))
