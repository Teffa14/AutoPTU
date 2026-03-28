from __future__ import annotations

import pytest

from auto_ptu.rules import (
    BattleState,
    TrainerState,
    PokemonState,
    UseItemAction,
    EquipWeaponAction,
    GridState,
)
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules.calculations import build_attack_context


def _pokemon_spec(name: str = "Eevee", *, types: list[str] | None = None, moves: list[MoveSpec] | None = None) -> PokemonSpec:
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
        moves=moves
        or [MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2, freq="EOT")],
    )


NON_COMBAT_ITEMS = [
    "Thunder Stone",
    "Tinfoil Gospel: Your Primer on Thwarting the Conspiracies of the New World Order [5-15 Playtest]",
    "TM - <Attack Name>",
    "Tough Fashion",
    "Tough Poffin",
    "Traditional Medicine Reference [5-15 Playtest]",
    "Travel Guide [5-15 Playtest]",
    "Type Study Manual [5-15 Playtest]",
    "Up-Grade",
    "Utility Rope",
    "Violet Shard",
    "Water Filter",
    "Water Stone",
    "Warp Rigging",
]


WEAPON_ITEMS = [
    "Tomahawk",
    "Toucannon (Weapon)",
    "Trumbeak (Weapon)",
    "Vikavolt (Weapon)",
    "Wand of Barking",
    "Wand of Buzzing",
    "Wand of Dazzling",
    "Wand of Embers",
    "Wand of Minds",
    "Wand of Mirrors",
    "Wand of Quartz",
    "Wand of Sands",
    "Wand of Snowballs",
    "Wand of Sprouts",
    "Wand of Toxins",
    "Wand of Umbra",
    "Wand of Wet",
    "Wand of Zap",
    "War Club",
]


Z_CRYSTALS = [
    ("Ultranecrozmium-Z", None),
    ("Waterium-Z", "Water"),
]


MEGA_STONES = [
    ("Tyranitarite", "Tyranitar", "Mega Tyranitar"),
    ("Venusaurite", "Venusaur", "Mega Venusaur"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch8(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch8(item_name: str) -> None:
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
def test_z_crystals_ready_batch8(item_name: str, expected_type: str | None) -> None:
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
def test_mega_stones_apply_forms_batch8(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_trapper_orb_creates_traps() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Trapper Orb"}]
    defender_spec = _pokemon_spec("Eevee")
    grid = GridState(width=5, height=5, tiles={(x, y): {} for x in range(5) for y in range(5)})
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier),
        },
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "trapper_orb")
    print(f"Trapper Orb event: {event}")
    coord = event.get("tiles")[0]
    assert battle.grid.tiles[coord].get("traps")


def test_two_edge_orb_halves_hp() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Two-Edge Orb"}]
    foe_spec = _pokemon_spec("Eevee")
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=user_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=foe_spec, controller_id=gary.identifier),
        },
    )
    foe = battle.pokemon["gary-1"]
    before = foe.hp
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "two_edge_orb" and evt.get("target") == "gary-1")
    print(f"Two-Edge Orb event: {event}")
    assert foe.hp == before // 2


def test_type_booster_accuracy_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Type Booster", "type": "Fire"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "accuracy_bonus")
    print(f"Type Booster event: {event}")
    assert event.get("amount") == 2
    assert event.get("item_type") == "Fire"


def test_type_boosters_damage_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Fire"])
    attacker_spec.items = [{"name": "Type Boosters", "type": "Fire"}]
    defender_spec = _pokemon_spec("Eevee")
    move = MoveSpec(name="Ember", type="Fire", category="Special", db=4, ac=2, freq="EOT")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    attacker = battle.pokemon["ash-1"]
    defender = battle.pokemon["ash-2"]
    context = build_attack_context(attacker, defender, move)
    battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
    flat_mods = [mod for mod in context.modifiers if mod.kind == "damage_flat" and mod.value == 5]
    print(f"Type Boosters modifiers: {flat_mods}")
    assert flat_mods


def test_type_brace_reduction() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Fire"])
    defender_spec = _pokemon_spec("Eevee")
    defender_spec.items = [{"name": "Type Brace", "type": "Fire"}]
    move = MoveSpec(name="Ember", type="Fire", category="Special", db=4, ac=2, freq="EOT")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    result = {"damage": 40}
    events = []
    battle.item_system.apply_defender_item_mitigation(
        "ash-2", battle.pokemon["ash-2"], "ash-1", move, result, events
    )
    print(f"Type Brace mitigation result: {result}")
    assert result.get("damage") == 25


def test_type_gem_consumes_and_boosts() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Fire"])
    attacker_spec.items = [{"name": "Type Gem", "type": "Fire"}]
    defender_spec = _pokemon_spec("Eevee")
    move = MoveSpec(name="Ember", type="Fire", category="Special", db=4, ac=2, freq="EOT")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    attacker = battle.pokemon["ash-1"]
    defender = battle.pokemon["ash-2"]
    context = build_attack_context(attacker, defender, move)
    battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
    power_mods = [mod for mod in context.modifiers if mod.kind == "power" and mod.value == 3]
    print(f"Type Gem modifiers: {power_mods}")
    assert power_mods


def test_type_plates_apply_both_effects() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Water"])
    defender_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Type Plates", "type": "Water"}]
    defender_spec.items = [{"name": "Type Plates", "type": "Water"}]
    move = MoveSpec(name="Water Gun", type="Water", category="Special", db=4, ac=2, freq="EOT")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    attacker = battle.pokemon["ash-1"]
    defender = battle.pokemon["ash-2"]
    context = build_attack_context(attacker, defender, move)
    battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
    flat_mods = [mod for mod in context.modifiers if mod.kind == "damage_flat" and mod.value == 5]
    result = {"damage": 40}
    events = []
    battle.item_system.apply_defender_item_mitigation(
        "ash-2", defender, "ash-1", move, result, events
    )
    print(f"Type Plates modifiers: {flat_mods}")
    print(f"Type Plates mitigation result: {result}")
    assert flat_mods
    assert result.get("damage") == 25


def test_type_capacitor_sets_effect() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Type Capacitor", "type": "Fire"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "type_capacitor")
    print(f"Type Capacitor event: {event}")
    assert event.get("item_type") == "Fire"


def test_umbra_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Umbra Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Umbra Clay events: {events}")
    assert any(evt.get("weather") == "gloomy" for evt in events)


def test_unremarkable_teacup_effects() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Poltchageist", types=["Grass", "Ghost"])
    user_spec.items = [{"name": "Unremarkable Teacup"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Unremarkable Teacup events: {events}")
    assert any(evt.get("effect") == "drain_multiplier" for evt in events)
    assert any(evt.get("stat") == "hp_stat" and evt.get("amount") == 10 for evt in events)


def test_utility_umbrella_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Utility Umbrella"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_immunity")
    print(f"Utility Umbrella event: {event}")
    assert event.get("weather") == "all"


def test_warp_orb_teleports_target() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Warp Orb"}]
    defender_spec = _pokemon_spec("Eevee")
    grid = GridState(width=3, height=3, tiles={(x, y): {} for x in range(3) for y in range(3)})
    defender = PokemonState(spec=defender_spec, controller_id=gary.identifier)
    defender.position = (0, 0)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": defender,
        },
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "warp_orb")
    print(f"Warp Orb event: {event}")
    assert defender.position != (0, 0)


def test_warp_seed_teleports_target() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Warp Seed"}]
    defender_spec = _pokemon_spec("Eevee")
    grid = GridState(width=3, height=3, tiles={(x, y): {} for x in range(3) for y in range(3)})
    defender = PokemonState(spec=defender_spec, controller_id=gary.identifier)
    defender.position = (0, 0)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": defender,
        },
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "warp_seed")
    print(f"Warp Seed event: {event}")
    assert defender.position != (0, 0)
