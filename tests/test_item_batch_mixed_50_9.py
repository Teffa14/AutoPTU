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


def _pokemon_spec(name: str = "Eevee", *, types: list[str] | None = None) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=12,
        moves=[MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2, freq="EOT")],
    )


NON_COMBAT_ITEMS = [
    "Waterproof Flashlight",
    "Waterproof Lighter",
    "Whipped Dream",
    "White Apricorn",
    "White Light",
    "Yellow Apricorn",
    "Yellow Shard",
    "Zap Case",
    "Batch Pending Item 1",
    "Batch Pending Item 2",
]


WEAPON_ITEMS = [
    "Whip",
    "Xernean Longbow",
    "Zweihander",
]


Z_CRYSTALS = [
    ("Z-Crystal", "Fire"),
    ("Z-Power-Crystal", "Fire"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch9(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch9(item_name: str) -> None:
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


def test_weather_lock_orb_clears_weather() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Weather Lock Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.weather = "Rainy"
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "weather")
    print(f"Weather Lock Orb event: {event}")
    assert battle.weather == "Clear"


def test_wellspring_mask_spdef_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Ogerpon", types=["Grass"])
    user_spec.items = [{"name": "Wellspring Mask"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Wellspring Mask event: {event}")
    assert event.get("stat") == "spdef"
    assert event.get("multiplier") == 1.2


def test_wishing_star_ready() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Wishing Star"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "zenith_core_ready")
    print(f"Wishing Star event: {event}")
    assert event.get("item") == "Wishing Star"


def test_zenith_core_ready() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Zenith Core"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "zenith_core_ready")
    print(f"Zenith Core event: {event}")
    assert event.get("item") == "Zenith Core"


@pytest.mark.parametrize("item_name,expected_type", Z_CRYSTALS)
def test_generic_z_crystals_ready(item_name: str, expected_type: str) -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": item_name, "type": expected_type}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "z_crystal_ready")
    print(f"{item_name} z-crystal event: {event}")
    assert event.get("z_type") == expected_type
