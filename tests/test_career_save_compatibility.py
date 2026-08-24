from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.items import buy_product, use_item
from auto_ptu.career.models import CareerRun
from auto_ptu.career.relationships import refresh_relationship_effects


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


def test_save_loader_sanitizes_competitive_totals_before_season_resolution() -> None:
    run = CareerEngine().new_run(
        player_id="save-totals-recovery",
        name="Iris",
        region="johto",
        starter="Hoothoot",
        classes=["Ace Trainer"],
        seed=1771,
    )
    payload = run.to_dict()
    payload["totals"] = {
        "wins": "12",
        "losses": None,
        "draws": float("nan"),
        "titles": -3,
        "legacy_exhibitions": 99,
    }

    restored = CareerRun.from_dict(payload)

    assert restored.totals == {"wins": 12, "losses": 0, "draws": 0, "titles": 0}
    restored.totals["wins"] += 1
    restored.totals["losses"] += 1
    restored.totals["draws"] += 1
    restored.totals["titles"] += 1
    assert restored.totals == {"wins": 13, "losses": 1, "draws": 1, "titles": 1}

    for corrupt_totals in (None, [], "broken"):
        corrupt_payload = run.to_dict()
        corrupt_payload["totals"] = corrupt_totals

        recovered = CareerRun.from_dict(corrupt_payload)

        assert recovered.totals == {"wins": 0, "losses": 0, "draws": 0, "titles": 0}


def test_save_loader_recovers_corrupt_relationship_memory_before_social_effects() -> None:
    run = CareerEngine().new_run(
        player_id="save-relationship-recovery",
        name="Sora",
        region="unova",
        starter="Oshawott",
        classes=["Ace Trainer"],
        seed=1889,
    )

    for corrupt_relationships in (None, [], "broken"):
        payload = run.to_dict()
        payload["relationships"] = corrupt_relationships

        restored = CareerRun.from_dict(payload)
        effects = refresh_relationship_effects(restored)

        assert restored.relationships == {}
        assert effects["active_contacts"] == 0
        assert effects["best_contact"] == ""

    payload = run.to_dict()
    payload["relationships"] = {
        " Mara · mentor · Unova ": "6",
        "Rex · rival · Unova": float("nan"),
        "Club Chair · owner · Unova": -4,
        "   ": 9,
    }

    restored = CareerRun.from_dict(payload)
    effects = refresh_relationship_effects(restored)

    assert restored.relationships == {
        "Mara · mentor · Unova": 6,
        "Rex · rival · Unova": 0,
        "Club Chair · owner · Unova": 0,
    }
    assert effects["mentor_training_bonus"] == 2
    assert effects["rival_scouting_bonus"] == 0
    assert effects["owner_recovery_bonus"] == 0


def test_save_loader_sanitizes_corrupt_inventory_before_bag_and_market_use() -> None:
    run = CareerEngine().new_run(
        player_id="save-inventory-recovery",
        name="Vale",
        region="hoenn",
        starter="Treecko",
        classes=["Ace Trainer"],
        seed=1993,
    )
    run.money = 500

    for corrupt_inventory in (None, [], "broken"):
        payload = run.to_dict()
        payload["inventory"] = corrupt_inventory

        restored = CareerRun.from_dict(payload)
        purchase = buy_product(restored, "super_potion")

        assert restored.inventory == {"Super Potion": 1}
        assert purchase["item"] == "Super Potion"

    payload = run.to_dict()
    payload["inventory"] = {
        " Super Potion ": "2",
        "Training Kit": float("nan"),
        "Future Token": -4,
        "   ": 8,
    }
    payload["health"] = 50

    restored = CareerRun.from_dict(payload)

    assert restored.inventory == {
        "Super Potion": 2,
        "Training Kit": 0,
        "Future Token": 0,
    }
    result = use_item(restored, "super potion")
    assert result["health"] == 12
    assert restored.health == 62
    assert restored.inventory["Super Potion"] == 1


def test_save_loader_recovers_malformed_pokemon_container_before_roster_use() -> None:
    run = CareerEngine().new_run(
        player_id="save-pokemon-container-recovery",
        name="Kai",
        region="kanto",
        starter="Bulbasaur",
        classes=["Ace Trainer"],
        seed=2039,
    )

    for corrupt_pokemon in (None, {}, "broken", [None, "bad-entry", 7]):
        payload = run.to_dict()
        payload["pokemon"] = corrupt_pokemon
        payload["roster"] = [run.build.starter]

        restored = CareerRun.from_dict(payload)

        assert len(restored.pokemon) == 1
        assert restored.pokemon[0].species == run.build.starter
        assert restored.pokemon[0].is_partner is True
        assert restored.active_roster == [restored.pokemon[0].id]

    payload = run.to_dict()
    valid_partner = dict(payload["pokemon"][0])
    payload["pokemon"] = [valid_partner, None, "bad-entry"]

    restored = CareerRun.from_dict(payload)

    assert len(restored.pokemon) == 1
    assert restored.pokemon[0].id == valid_partner["id"]
    assert restored.pokemon[0].species == valid_partner["species"]
