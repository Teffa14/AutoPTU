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
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2)],
    )


NON_COMBAT_ITEMS = [
    "Camera Kit",
    "Chemistry Set",
    "Collection Jar",
    "Consumable",
    "Cooking Set",
    "Cuirass",
    "Cute Fashion",
    "Cute Poffin",
    "Dawn Stone",
    "Deep Sea Scale",
    "Deep Sea Tooth",
    "Deepseascale",
    "Deepseatooth",
    "Devil Case",
    "DevonCorp Exo-Rig",
    "DevonCorp Impact Glove",
    "DIY Engineering [5-15 Playtest]",
    "Doctor's Bag",
    "Dowsing for Dummies [5-15 Playtest]",
    "Dowsing Rod",
    "Dragon Scale",
    "Dubious Disc",
    "Dubious Disk",
    "Dusk Stone",
    "Egg Warmer",
    "Electirizer",
    "Escape Orb",
    "EVA Suit",
    "Everstone",
    "Feet",
    "Fire Stone",
]

Z_CRYSTALS = [
    "Buginium-Z",
    "Darkinium-Z",
    "Decidium-Z",
    "Dragonium-Z",
    "Eevium-Z",
    "Electrium-Z",
    "Fairium-Z",
    "Fightinium-Z",
]

CAPTURE_BALL_ITEMS = [
    "Dark Ball",
    "Dive Ball",
    "Dusk Ball",
    "Earth Ball",
    "Fabulous Ball",
    "Fast Ball",
    "Feather Ball",
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders(item_name: str) -> None:
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


@pytest.mark.parametrize("item_name", Z_CRYSTALS)
def test_z_crystals_ready(item_name: str) -> None:
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
    assert user.get_temporary_effects("z_crystal_ready")


@pytest.mark.parametrize(
    ("item_name", "base_modifier", "multiplier"),
    [
        ("Dark Ball", 0, 1.0),
        ("Dive Ball", 0, 1.0),
        ("Dusk Ball", 0, 1.0),
        ("Earth Ball", 0, 1.0),
        ("Fabulous Ball", -5, 1.0),
        ("Fast Ball", 0, 1.0),
        ("Feather Ball", 0, 1.0),
    ],
)
def test_capture_ball_default_modifiers(item_name: str, base_modifier: int, multiplier: float) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": item_name}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=trainer.identifier)
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={"ash-1": user, "gary-1": target},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"{item_name} capture event: {event}")
    assert event.get("effect") == "capture_attempt"
    assert event.get("base_modifier") == base_modifier
    assert event.get("multiplier") == multiplier

def test_damp_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Damp Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Damp Rock held event: {event}")
    assert event.get("weather") == "Rain"
    assert event.get("bonus") == 3


def test_drought_orb_sets_scorched_terrain() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Drought Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "terrain")
    print(f"Drought Orb terrain event: {event}")
    assert battle.terrain is not None
    assert battle.terrain.get("name") == "Scorched Terrain"
    assert battle.terrain.get("remaining") == 5


def test_encourage_seed_applies_amped() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Encourage Seed"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    status_names = {entry.get("name") for entry in user.statuses if isinstance(entry, dict)}
    event = next(evt for evt in battle.log if evt.get("type") == "status")
    print(f"Encourage Seed status event: {event}")
    assert "Amped" in status_names


def test_evasion_orb_grants_evasion() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Evasion Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"Evasion Orb item event: {event}")
    bonuses = user.get_temporary_effects("evasion_bonus")
    assert any(entry.get("amount") == 1 for entry in bonuses if isinstance(entry, dict))
    assert event.get("effect") == "evasion_bonus"


def test_eject_pack_use_ready() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Eject Pack"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"Eject Pack item event: {event}")
    assert event.get("effect") == "eject_pack_ready"
    assert user.get_temporary_effects("eject_pack_ready")


def test_eject_button_triggers_on_hit() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    foe = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    defender_spec = _pokemon_spec("Pikachu")
    defender_spec.items = [{"name": "Eject Button"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=trainer.identifier)
    defender = PokemonState(spec=defender_spec, controller_id=foe.identifier)
    battle = BattleState(
        trainers={trainer.identifier: trainer, foe.identifier: foe},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "eject_button_ready")
    print(f"Eject Button trigger event: {event}")
    assert defender.get_temporary_effects("eject_button_ready")
    assert not defender.spec.items


def test_dart_can_be_equipped() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Dart"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
    battle.resolve_next_action()
    event = next(
        evt
        for evt in battle.log
        if evt.get("type") == "item" and evt.get("effect") == "equip_weapon"
    )
    print(f"Dart equip event: {event}")
    assert event.get("item") == "Dart"


def test_doublade_weapon_can_be_equipped() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Doublade (Weapon)"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(EquipWeaponAction(actor_id="ash-1", item_index=0))
    battle.resolve_next_action()
    event = next(
        evt
        for evt in battle.log
        if evt.get("type") == "item" and evt.get("effect") == "equip_weapon"
    )
    print(f"Doublade (Weapon) equip event: {event}")
    assert event.get("item") == "Doublade (Weapon)"


def test_diancite_mega_evolves_diancie() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Diancie")
    user_spec.items = [{"name": "Diancite"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "mega_evolution")
    print(f"Diancite mega evolution event: {event}")
    assert user.get_temporary_effects("mega_form")
    assert event.get("mega_form") == "Mega Diancie"
