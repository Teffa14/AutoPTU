from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.items import buy_product
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


def test_save_loader_recovers_missing_money_from_corrupt_legacy_earnings() -> None:
    run = CareerEngine().new_run(
        player_id="save-money-recovery",
        name="Luz",
        region="paldea",
        starter="Sprigatito",
        classes=["Ace Trainer"],
        seed=1221,
    )

    for corrupt_value in (None, "not-a-number", float("nan"), float("inf"), -500):
        payload = run.to_dict()
        payload.pop("money", None)
        payload["career_earnings"] = corrupt_value

        restored = CareerRun.from_dict(payload)

        assert restored.money == 0

    payload = run.to_dict()
    payload.pop("money", None)
    payload["career_earnings"] = "350"

    restored = CareerRun.from_dict(payload)

    assert restored.money == 350


def test_save_loader_sanitizes_explicit_money_before_market_use() -> None:
    run = CareerEngine().new_run(
        player_id="save-explicit-money-recovery",
        name="Nora",
        region="kanto",
        starter="Pikachu",
        classes=["Ace Trainer"],
        seed=1441,
    )

    for corrupt_value in (None, "not-a-number", float("nan"), float("inf"), -500):
        payload = run.to_dict()
        payload["money"] = corrupt_value

        restored = CareerRun.from_dict(payload)

        assert restored.money == 0
        assert isinstance(restored.money, int)

    payload = run.to_dict()
    payload["money"] = "350"

    restored = CareerRun.from_dict(payload)
    purchase = buy_product(restored, "pokeball")

    assert restored.money == 320
    assert purchase["money"] == 320
