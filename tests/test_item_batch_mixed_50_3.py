from __future__ import annotations

import pytest

from auto_ptu.rules import (
    BattleState,
    TrainerState,
    PokemonState,
    UseItemAction,
    UseMoveAction,
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
    "Hearty Meal",
    "How Berries?? [5-15 Playtest]",
    "How To Avoid Being Spooked [5-15 Playtest]",
    "Ice Stone",
    "Item",
    "Key Stone",
    "Leaf Stone",
    "Lighter",
    "Linking Cord",
    "Lock Case",
    "Locus Lozenge",
]

WEAPON_ITEMS = [
    "Heavy Crossbow",
    "Heavy Machinegun",
    "Heavy Shield",
    "Highland Thistle (Sword)",
    "Honedge (Weapon)",
    "Iron Spike",
    "Lance",
    "Lever-Action Rifle",
    "Lever-Action Shotgun",
    "Light Crossbow",
    "Light Machinegun",
    "Light Shield",
    "Long Spear",
    "Longbow",
]

Z_CRYSTALS = [
    ("Icium-Z", "Ice"),
    ("Incinium-Z", None),
    ("Kommonium-Z", None),
    ("Lunalium-Z", None),
]

MEGA_STONES = [
    ("Heracronite", "Heracross", "Mega Heracross"),
    ("Houndoominite", "Houndoom", "Mega Houndoom"),
    ("Houndoomite", "Houndoom", "Mega Houndoom"),
    ("Kangaskhanite", "Kangaskhan", "Mega Kangaskhan"),
    ("Latiosite", "Latios", "Mega Latios"),
    ("Lopunnite", "Lopunny", "Mega Lopunny"),
    ("Lucarioinite", "Lucario", "Mega Lucario"),
    ("Lucarionite", "Lucario", "Mega Lucario"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch3(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch3(item_name: str) -> None:
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
def test_z_crystals_ready_batch3(item_name: str, expected_type: str | None) -> None:
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


@pytest.mark.parametrize("stone_name,species_name,mega_form", MEGA_STONES)
def test_mega_stones_apply_forms_batch3(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_heat_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Heat Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Heat Rock held event: {event}")
    assert event.get("weather") == "Sunny"
    assert event.get("bonus") == 3


def test_icy_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Icy Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Icy Rock held event: {event}")
    assert event.get("weather") == "Snowy"
    assert event.get("bonus") == 3


def test_light_clay_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Light Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "effect_duration_bonus")
    print(f"Light Clay held event: {event}")
    assert event.get("amount") == 2


def test_heavy_clothing_armor_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Heavy Clothing"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    speed_event = next(evt for evt in events if evt.get("effect") == "armor_speed_scalar")
    resist_event = next(evt for evt in events if evt.get("effect") == "resistance_bonus")
    print(f"Heavy Clothing events: {events}")
    assert speed_event.get("multiplier") == 0.9
    assert resist_event.get("amount") == 5


def test_husarine_plate_armor_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Husarine Plate"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    speed_event = next(evt for evt in events if evt.get("effect") == "armor_speed_scalar")
    resist_event = next(evt for evt in events if evt.get("effect") == "resistance_bonus")
    print(f"Husarine Plate events: {events}")
    assert speed_event.get("multiplier") == 0.8
    assert resist_event.get("amount") == 15


def test_legend_plate_damage_scalar() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.moves = [MoveSpec(name="Smash", type="Normal", category="Physical", db=10, ac=2, freq="EOT")]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender_spec = _pokemon_spec("Arceus")
    defender_spec.items = [{"name": "Legend Plate"}]
    defender = PokemonState(spec=defender_spec, controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    events: list[dict] = []
    result = {"damage": 20, "type_multiplier": 1.0}
    battle.item_system.apply_defender_item_mitigation(
        "gary-1",
        defender,
        "ash-1",
        attacker_spec.moves[0],
        result,
        events,
    )
    event = next(evt for evt in events if evt.get("effect") == "legend_plate_damage_scalar")
    print(f"Legend Plate mitigation event: {event}")
    assert event.get("item") == "Legend Plate"


def test_jetpack_grants_flight_movement() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.movement["sky"] = 0
    user_spec.items = [{"name": "Jetpack"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "movement_override")
    print(f"Jetpack held event: {event}")
    assert user.can_fly()
    assert user.movement_speed("sky") == 15


def test_jade_orb_mega_evolves_rayquaza() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Rayquaza")
    user_spec.items = [{"name": "Jade Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "mega_evolution")
    print(f"Jade Orb mega evolution event: {event}")
    assert event.get("mega_form") == "Mega Rayquaza"


def test_huge_apple_restores_pp() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Huge Apple"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.frequency_usage = {"ash-1": {"Tackle": 2}}
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "pp_restore_all")
    print(f"Huge Apple event: {event}")
    assert "ash-1" not in battle.frequency_usage


def test_hunger_seed_reduces_pp() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Hunger Seed"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "pp_loss")
    print(f"Hunger Seed event: {event}")
    assert battle.frequency_usage["gary-1"]["Tackle"] == 3


def test_herbal_restorative_save_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Herbal Restorative"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "save_bonus")
    print(f"Herbal Restorative event: {event}")
    assert any(entry.get("amount") == 2 for entry in user.get_temporary_effects("save_bonus"))


def test_lob_orb_attack_hits_target() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Lob Orb"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    before_hp = defender.hp
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "lob_orb_attack")
    print(f"Lob Orb event: {event}")
    assert defender.hp < before_hp


def test_longtoss_orb_fling_range_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Longtoss Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "fling_range_scalar")
    print(f"Longtoss Orb event: {event}")
    assert any(entry.get("multiplier") == 2 for entry in user.get_temporary_effects("fling_range_scalar"))
