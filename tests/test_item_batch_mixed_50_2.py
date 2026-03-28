from __future__ import annotations

import pytest

from auto_ptu.rules import (
    BattleState,
    TrainerState,
    PokemonState,
    UseItemAction,
    EquipWeaponAction,
)
from auto_ptu.data_models import MoveSpec, PokemonSpec


def _pokemon_spec(name: str = "Eevee") -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=12,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2, freq="EOT")],
    )


NON_COMBAT_ITEMS = [
    "First Aid Manual [5-15 Playtest]",
    "Fishing 101 [5-15 Playtest]",
    "Fishing Lure",
    "Flash Case",
    "Flashlight",
    "Flippers",
    "Galarica Cuff",
    "Galarica Wreath",
    "Green Apricorn",
    "Green Shard",
    "Groomer's Kit",
    "Hands",
    "Head",
    "Heart Booster",
    "Heart Scale",
]

WEAPON_ITEMS = [
    "Flintlock Carbine",
    "Flintlock Musket",
    "Flintlock Musketoon",
    "Flintlock Pistol",
    "Flintlock Rifle",
    "Grenade Rifle",
    "Halberd",
    "Hand Weapon",
    "Hatchet",
    "Geo Pebble",
    "Gold Spike",
    "Granite Rock",
    "Gravelerock",
]

Z_CRYSTALS = [
    ("Firium-Z", "Fire"),
    ("Flyinium-Z", "Flying"),
    ("Ghostium-Z", "Ghost"),
    ("Grassium-Z", "Grass"),
    ("Groundium-Z", "Ground"),
]

MEGA_STONES = [
    ("Galladite", "Gallade", "Mega Gallade"),
    ("Garchompite", "Garchomp", "Mega Garchomp"),
    ("Gardevoirite", "Gardevoir", "Mega Gardevoir"),
    ("Gengarite", "Gengar", "Mega Gengar"),
    ("Glalitite", "Glalie", "Mega Glalie"),
    ("Gyaradosite", "Gyarados", "Mega Gyarados"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch2(item_name: str) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": item_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"{item_name} placeholder event: {event}")
    assert event.get("effect") == "non_combat_placeholder"
    assert event.get("item") == item_name


@pytest.mark.parametrize("item_name", WEAPON_ITEMS)
def test_weapon_items_can_be_equipped(item_name: str) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": item_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
    battle.resolve_next_action()
    event = next(
        evt
        for evt in battle.log
        if evt.get("type") == "item" and evt.get("effect") == "equip_weapon"
    )
    print(f"{item_name} equip event: {event}")
    assert event.get("item") == item_name


@pytest.mark.parametrize("item_name,expected_type", Z_CRYSTALS)
def test_z_crystals_ready_batch2(item_name: str, expected_type: str) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": item_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"{item_name} z-crystal event: {event}")
    assert event.get("effect") == "z_crystal_ready"
    assert event.get("z_type") == expected_type


def test_force_drive_sets_item_type() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Genesect")
    user_spec.items = [{"name": "Force Drive"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    item_type = battle._item_type_from_item({"name": "Force Drive"})
    print(f"Force Drive item type: {item_type}")
    assert item_type == "Fighting"


def test_float_stone_weight_class_halved() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.weight = 4
    user_spec.items = [{"name": "Float Stone"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    base_wc = user.weight_class()
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weight_class_scalar")
    updated_wc = user.weight_class()
    print(f"Float Stone event: {event}, weight_class {base_wc} -> {updated_wc}")
    assert base_wc == 4
    assert updated_wc == 2


def test_geiger_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Geiger Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    weather_entries = [evt for evt in events if evt.get("effect") == "weather_immunity"]
    print(f"Geiger Clay weather immunity events: {weather_entries}")
    weather_names = {evt.get("weather") for evt in weather_entries}
    assert "glowy" in weather_names
    assert "intense radstorm" in weather_names


def test_glassy_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Glassy Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Glassy Rock event: {event}")
    assert event.get("weather") == "Gloomy"
    assert event.get("bonus") == 3


def test_glowing_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Glowing Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Glowing Rock event: {event}")
    assert event.get("weather") == "Glowy"
    assert event.get("bonus") == 3


def test_hearthflame_mask_attack_boost() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Ogerpon")
    user_spec.items = [{"name": "Hearthflame Mask"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Hearthflame Mask event: {event}")
    assert event.get("stat") == "atk"
    assert event.get("multiplier") == 1.2


def test_hail_orb_sets_snowy_weather() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Hail Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "weather")
    print(f"Hail Orb weather event: {event}")
    assert battle.weather == "Snowy"
    assert event.get("rounds") == 3


def test_heal_seed_cures_major_status() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Heal Seed"}]
    user_spec.statuses = [{"name": "Burned"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"Heal Seed cure event: {event}")
    assert not user.has_status("Burned")
    assert event.get("effect") == "cure_status"


def test_health_orb_cures_team_status() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    user_spec = _pokemon_spec("Eevee")
    ally_spec = _pokemon_spec("Pikachu")
    foe_spec = _pokemon_spec("Meowth")
    user_spec.items = [{"name": "Health Orb"}]
    user_spec.statuses = [{"name": "Poisoned"}]
    ally_spec.statuses = [{"name": "Paralyzed"}]
    foe_spec.statuses = [{"name": "Burned"}]
    user = PokemonState(spec=user_spec, controller_id=ash.identifier)
    ally = PokemonState(spec=ally_spec, controller_id=ash.identifier)
    foe = PokemonState(spec=foe_spec, controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": user, "ash-2": ally, "gary-1": foe},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    events = [evt for evt in battle.log if evt.get("type") == "item"]
    print(f"Health Orb cure events: {events}")
    assert not user.statuses
    assert not ally.statuses
    assert foe.has_status("Burned")


def test_golden_apple_restores_frequency_and_pp_up() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Golden Apple"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.frequency_usage = {"ash-1": {"Tackle": 2}}
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    events = [evt for evt in battle.log if evt.get("type") == "item"]
    print(f"Golden Apple events: {events}")
    assert any(evt.get("effect") == "pp_restore_all" for evt in events)
    assert any(evt.get("effect") == "pp_up" for evt in events)


def test_grip_claw_extends_bound_duration() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    foe = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Grip Claw"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=foe.identifier)
    battle = BattleState(
        trainers={trainer.identifier: trainer, foe.identifier: foe},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    events: list[dict] = []
    battle._apply_status(
        events,
        attacker_id="ash-1",
        target_id="gary-1",
        move=MoveSpec(name="Bind", type="Normal", category="Physical"),
        target=defender,
        status="Bound",
        effect="bind",
        description="Target is bound.",
        remaining=4,
    )
    bonus_event = next(evt for evt in events if evt.get("effect") == "grip_claw_bonus")
    print(f"Grip Claw bonus event: {bonus_event}")
    bound_entry = next(entry for entry in defender.statuses if entry.get("name") == "Bound")
    assert bound_entry.get("remaining") == 7


@pytest.mark.parametrize("stone_name,species_name,mega_form", MEGA_STONES)
def test_mega_stones_apply_forms(stone_name: str, species_name: str, mega_form: str) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec(species_name)
    user_spec.items = [{"name": stone_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "mega_evolution")
    print(f"{stone_name} mega evolution event: {event}")
    assert event.get("mega_form") == mega_form
