from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun


def test_save_loader_ignores_unknown_top_level_fields() -> None:
    run = CareerEngine().new_run(
        player_id="save-forward-compat",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=731,
    )
    payload = run.to_dict()
    payload["legacy_browser_panel"] = {"tab": "club", "expanded": True}
    payload["future_extension_flag"] = True

    restored = CareerRun.from_dict(payload)

    assert restored.id == run.id
    assert restored.build.name == run.build.name
    assert restored.active_roster == run.active_roster
    assert restored.timeline == run.timeline


def test_save_loader_ignores_unknown_nested_fields() -> None:
    run = CareerEngine().new_run(
        player_id="save-nested-forward-compat",
        name="Mina",
        region="johto",
        starter="Hoothoot",
        classes=["Researcher"],
        seed=919,
    )
    payload = run.to_dict()
    payload["build"]["future_badge_display"] = {"slots": 16}
    payload["versions"]["future_rules_channel"] = "ptu-next-preview"
    payload["pokemon"][0]["future_bond_memory"] = {"mentor": "Eli", "score": 4}

    restored = CareerRun.from_dict(payload)

    assert restored.id == run.id
    assert restored.build.name == "Mina"
    assert restored.versions.career == run.versions.career
    assert restored.pokemon[0].species == run.pokemon[0].species
    assert restored.pokemon[0].is_partner is True
