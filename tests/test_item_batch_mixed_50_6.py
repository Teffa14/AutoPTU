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


class _FixedRng:
    def __init__(self, value: int) -> None:
        self._value = value

    def randint(self, _low: int, _high: int) -> int:
        return self._value


NON_COMBAT_ITEMS = [
    "Pure Seed",
    "Radar Orb",
    "Rambo Roids",
    "Rare Quality Orb",
    "Reaper Cloth",
    "Red Apricorn",
    "Red Shard",
    "Repel",
    "Running Shoes",
    "Sachet",
    "Saddle",
    "Scanner Orb",
    "Scroll of Masteries",
    "Sealed Air Supply",
    "See-Trap Orb",
    "Shiny Stone",
    "Shock Syringe",
]


WEAPON_ITEMS = [
    "Revolver",
    "Rocket Launcher",
    "RPG",
    "Saber",
    "Semi-Auto Rifle",
    "Semi-Auto Shotgun",
    "Sheathed Knife",
    "Short Spear",
    "Shield [9-15 Playtest]",
    "SilphCo Defender Sidearm",
    "SilphCo Laslock Rifle",
]


Z_CRYSTALS = [
    ("Rockium-Z", "Rock"),
]


MEGA_STONES = [
    ("Sablenite", "Sableye", "Mega Sableye"),
    ("Salamencite", "Salamence", "Mega Salamence"),
    ("Sceptilite", "Sceptile", "Mega Sceptile"),
    ("Scizorite", "Scizor", "Mega Scizor"),
    ("Sharpedonite", "Sharpedo", "Mega Sharpedo"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch6(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch6(item_name: str) -> None:
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
def test_z_crystals_ready_batch6(item_name: str, expected_type: str | None) -> None:
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
def test_mega_stones_apply_forms_batch6(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_pure_incense_resistance_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Pure Incense"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "resistance_bonus")
    print(f"Pure Incense resistance event: {event}")
    assert event.get("amount") == 10


def test_pure_incense_omniboost_on_sonic() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Chingling")
    attacker_spec.items = [{"name": "Pure Incense"}]
    defender_spec = _pokemon_spec("Eevee")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    battle.rng = _FixedRng(5)
    attacker = battle.pokemon["ash-1"]
    defender = battle.pokemon["ash-2"]
    move = MoveSpec(
        name="Echoed Voice",
        type="Normal",
        category="Special",
        db=4,
        ac=2,
        freq="EOT",
        keywords=["sonic"],
    )
    events = battle.item_system.apply_attacker_item_post_damage(
        "ash-1",
        attacker,
        "ash-2",
        defender,
        move,
        damage_dealt=10,
        result={},
    )
    print(f"Pure Incense omniboost events: {events}")
    assert attacker.combat_stages.get("atk") == 1
    assert any(evt.get("effect") == "omniboost" for evt in events)


def test_quick_orb_overland_bonus() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    brock = TrainerState(identifier="brock", name="Brock")
    user_spec = _pokemon_spec("Eevee")
    ally_spec = _pokemon_spec("Pikachu")
    user_spec.items = [{"name": "Quick Orb"}]
    battle = BattleState(
        trainers={ash.identifier: ash, brock.identifier: brock},
        pokemon={
            "ash-1": PokemonState(spec=user_spec, controller_id=ash.identifier),
            "ash-2": PokemonState(spec=ally_spec, controller_id=ash.identifier),
        },
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    events = [evt for evt in battle.log if evt.get("effect") == "movement_bonus"]
    print(f"Quick Orb events: {events}")
    assert len(events) == 2


def test_rainy_orb_sets_weather() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Rainy Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "weather")
    print(f"Rainy Orb weather event: {event}")
    assert battle.weather == "Rainy"


def test_sandy_orb_sets_weather() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Sandy Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "weather")
    print(f"Sandy Orb weather event: {event}")
    assert battle.weather == "Dusty"


def test_raze_drive_item_type_mapping() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)})
    item_type = battle._item_type_from_item({"name": "Raze Drive"})
    print(f"Raze Drive item type: {item_type}")
    assert item_type == "Dragon"


def test_red_orb_primal_reversion_ready() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Groudon", types=["Ground"])
    user_spec.items = [{"name": "Red Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "primal_reversion_ready")
    print(f"Red Orb event: {event}")
    assert event.get("item") == "Red Orb"


def test_reset_urge_clears_stages() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Reset Urge"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    user.combat_stages["atk"] = 2
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "reset_urge")
    print(f"Reset Urge event: {event}")
    assert user.combat_stages["atk"] == 0


def test_reset_orb_clears_foe_stages() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    user_spec = _pokemon_spec("Eevee")
    foe_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Reset Orb"}]
    user = PokemonState(spec=user_spec, controller_id=ash.identifier)
    foe = PokemonState(spec=foe_spec, controller_id=gary.identifier)
    foe.combat_stages["def"] = -2
    battle = BattleState(trainers={ash.identifier: ash, gary.identifier: gary}, pokemon={"ash-1": user, "gary-1": foe})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "reset_orb")
    print(f"Reset Orb event: {event}")
    assert foe.combat_stages["def"] == 0


def test_reveal_glass_sets_therian_form() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Landorus", types=["Ground", "Flying"])
    user_spec.items = [{"name": "Reveal Glass"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "form_change")
    print(f"Reveal Glass event: {event}")
    assert event.get("form") == "Landorus Therian"


def test_robes_of_thaumaturgy_stat_modifiers() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Robes of Thaumaturgy"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Robes of Thaumaturgy events: {events}")
    assert any(evt.get("stat") == "spdef" and evt.get("amount") == 20 for evt in events)
    assert any(evt.get("stat") == "spatk" and evt.get("amount") == 10 for evt in events)


def test_rollcall_orb_moves_allies() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    brock = TrainerState(identifier="brock", name="Brock")
    user_spec = _pokemon_spec("Eevee")
    ally_spec = _pokemon_spec("Pikachu")
    user_spec.items = [{"name": "Rollcall Orb"}]
    user = PokemonState(spec=user_spec, controller_id=ash.identifier)
    ally = PokemonState(spec=ally_spec, controller_id=ash.identifier)
    user.position = (1, 1)
    ally.position = (3, 3)
    grid = GridState(width=5, height=5)
    battle = BattleState(
        trainers={ash.identifier: ash, brock.identifier: brock},
        pokemon={"ash-1": user, "ash-2": ally},
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "rollcall_orb")
    print(f"Rollcall Orb event: {event}")
    assert ally.position != (3, 3)


def test_sandy_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Sandy Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Sandy Clay events: {events}")
    assert any(evt.get("weather") == "dusty" for evt in events)


def test_scroll_of_darkness_damage_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Dark"])
    attacker_spec.items = [{"name": "Scroll of Darkness"}]
    defender_spec = _pokemon_spec("Eevee")
    move = MoveSpec(name="Bite", type="Dark", category="Physical", db=4, ac=2, freq="EOT")
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
    modifiers = [mod for mod in context.modifiers if mod.kind == "damage_scalar" and mod.value == 1.2]
    print(f"Scroll of Darkness modifiers: {modifiers}")
    assert modifiers


def test_scroll_of_waters_urshifu_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Urshifu", types=["Water", "Fighting"])
    attacker_spec.items = [{"name": "Scroll of Waters"}]
    defender_spec = _pokemon_spec("Eevee")
    move = MoveSpec(name="Surging Strikes", type="Water", category="Physical", db=4, ac=2, freq="EOT")
    battle = BattleState(
        trainers={trainer.identifier: trainer},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=trainer.identifier),
            "ash-2": PokemonState(spec=defender_spec, controller_id=trainer.identifier),
        },
    )
    attacker = battle.pokemon["ash-1"]
    defender = battle.pokemon["ash-2"]
    battle.item_system.apply_held_item_start("ash-1")
    context = build_attack_context(attacker, defender, move)
    battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
    modifiers = [mod for mod in context.modifiers if mod.kind == "damage_scalar" and mod.value == 1.3]
    print(f"Scroll of Waters modifiers: {modifiers}")
    assert modifiers
    stat_mods = attacker.get_temporary_effects("stat_modifier")
    assert any(entry.get("stat") == "spd" and entry.get("amount") == 10 for entry in stat_mods)


def test_shed_shell_status_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Shed Shell"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Shed Shell events: {events}")
    assert any(evt.get("status") == "Grappled" for evt in events)


def test_shock_collar_deals_damage() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Shock Collar"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    starting_hp = user.hp
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "shock_collar")
    print(f"Shock Collar event: {event}")
    assert user.hp == starting_hp - event.get("amount")
