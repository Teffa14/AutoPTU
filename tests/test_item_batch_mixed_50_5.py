from __future__ import annotations

import pytest

from auto_ptu.rules import (
    BattleState,
    TrainerState,
    PokemonState,
    UseItemAction,
    UseMoveAction,
    EquipWeaponAction,
    TurnPhase,
)
from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules.calculations import build_attack_context


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
    "Pink Apricorn",
    "Poffin Mixer",
    "Poké Ball Alarm",
    "Poké Ball Technical Manual [5-15 Playtest]",
    "Poké Ball Tool Box",
    "Poké Ball Tracking Chip",
    "Pokédex",
    "Pokémon Daycare Licensing Guide [5-15 Playtest]",
    "Portable Grower",
    "Poultices",
    "Protector",
]


WEAPON_ITEMS = [
    "Pike",
    "Pikipek (Weapon)",
    "Pillow",
    "Pocket Knife",
    "Pocket Pistol",
    "Pump-Action Shotgun",
]


Z_CRYSTALS = [
    ("Poisonium-Z", "Poison"),
    ("Primarium-Z", None),
    ("Psychium-Z", "Psychic"),
]


MEGA_STONES = [
    ("Pinsirite", "Pinsir", "Mega Pinsir"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch5(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch5(item_name: str) -> None:
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
def test_z_crystals_ready_batch5(item_name: str, expected_type: str | None) -> None:
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
def test_mega_stones_apply_forms_batch5(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_pink_pearl_spoink_spatk_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Spoink", types=["Psychic"])
    user_spec.items = [{"name": "Pink Pearl"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.item_system.apply_held_item_start("ash-1")
    effects = user.get_temporary_effects("stat_modifier")
    print(f"Pink Pearl stat modifiers: {effects}")
    assert any(entry.get("stat") == "spatk" and entry.get("amount") == 1 for entry in effects)


def test_pink_pearl_psychic_damage_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    attacker_spec = _pokemon_spec("Eevee", types=["Psychic"])
    attacker_spec.items = [{"name": "Pink Pearl"}]
    defender_spec = _pokemon_spec("Eevee")
    move = MoveSpec(name="Confusion", type="Psychic", category="Special", db=4, ac=2, freq="EOT")
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
    events = battle.item_system.apply_attacker_item_modifiers("ash-1", attacker, move, context)
    flat_mods = [mod for mod in context.modifiers if mod.kind == "damage_flat" and mod.value == 5]
    print(f"Pink Pearl damage events: {events}")
    print(f"Pink Pearl damage modifiers: {flat_mods}")
    assert flat_mods


def test_porous_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Porous Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Porous Rock held event: {event}")
    assert event.get("weather") == "Windy"
    assert event.get("bonus") == 3


def test_pounce_orb_uses_pounce() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Pounce Orb"}]
    defender_spec = _pokemon_spec("Eevee")
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier),
        },
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "pounce_orb")
    print(f"Pounce Orb event: {event}")
    assert event.get("move") == "Pounce"


def test_prick_drive_item_type_mapping() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": PokemonState(spec=user_spec, controller_id=trainer.identifier)})
    item_type = battle._item_type_from_item({"name": "Prick Drive"})
    print(f"Prick Drive item type: {item_type}")
    assert item_type == "Poison"


def test_prison_bottle_form_change() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Hoopa", types=["Psychic", "Ghost"])
    user_spec.items = [{"name": "Prison Bottle"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "form_change")
    print(f"Prison Bottle event: {event}")
    assert event.get("form") == "Hoopa Unbound"
    assert "Dark" in user.spec.types


def test_protective_pads_blocks_contact_effects() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Protective Pads"}]
    defender_spec = _pokemon_spec("Eevee")
    defender_spec.abilities = ["Static"]
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier),
        },
    )
    battle.item_system.apply_held_item_start("ash-1")
    battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "contact_ability_block")
    print(f"Protective Pads event: {event}")
    assert battle.pokemon["ash-1"].has_status("Paralyzed") is False


def test_puissance_pellet_ignores_injury_and_expires() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Puissance Pellet"}]
    defender_spec = _pokemon_spec("Eevee")
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier),
        },
    )
    attacker = battle.pokemon["ash-1"]
    attacker.injuries = 5
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    apply_event = next(evt for evt in battle.log if evt.get("effect") == "puissance_pellet")
    battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
    battle.resolve_next_action()
    ignore_event = next(evt for evt in battle.log if evt.get("effect") == "puissance_pellet_ignore")
    injury_events = [evt for evt in battle.log if evt.get("type") == "injury_damage"]
    print(f"Puissance Pellet ignore event: {ignore_event}")
    print(f"Puissance Pellet injury events: {injury_events}")
    assert not injury_events
    battle.round = int(apply_event.get("expires_round", 6)) + 1
    attacker.handle_phase_effects(battle, TurnPhase.START, "ash-1")
    expire_event = next(evt for evt in battle.log if evt.get("effect") == "puissance_pellet_expire")
    print(f"Puissance Pellet expire event: {expire_event}")
    assert attacker.injuries == 6

