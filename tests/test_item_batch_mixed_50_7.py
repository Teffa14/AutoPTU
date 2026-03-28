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
    "Sleeping Bag",
    "Sleeping Bag (Double)",
    "Smart Fashion",
    "Smart Poffin",
    "Soldier Pill",
    "Soothe Bell",
    "Spray Case",
    "Stairs Orb",
    "Stat Suppressants",
    "Storage Case",
    "Study Manual [5-15 Playtest]",
    "Sturdy Rope",
    "Sun Stone",
    "Super Bait",
    "Super Repel",
    "Tent",
    "Tera Orb",
    "The Joy of Cooking [5-15 Playtest]",
]


WEAPON_ITEMS = [
    "Silver Spike",
    "Spadroon",
    "Spear",
    "Stick",
    "Submachine Gun",
    "Sword",
    "Taser",
    "Taser Club",
]


Z_CRYSTALS = [
    ("Snorlium-Z", None),
    ("Solganium-Z", None),
    ("Steelium-Z", "Steel"),
    ("Tapunium-Z", None),
]


MEGA_STONES = [
    ("Slowbronite", "Slowbro", "Mega Slowbro"),
    ("Steelixite", "Steelix", "Mega Steelix"),
    ("Swampertite", "Swampert", "Mega Swampert"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch7(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch7(item_name: str) -> None:
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
def test_z_crystals_ready_batch7(item_name: str, expected_type: str | None) -> None:
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
def test_mega_stones_apply_forms_batch7(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_sizebust_orb_damage_by_weight_class() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Sizebust Orb"}]
    defender_spec = _pokemon_spec("Eevee")
    defender_spec.weight = 5
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={
            "ash-1": PokemonState(spec=attacker_spec, controller_id=ash.identifier),
            "gary-1": PokemonState(spec=defender_spec, controller_id=gary.identifier),
        },
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "sizebust_orb")
    print(f"Sizebust Orb event: {event}")
    assert event.get("damage") == 80


def test_skyloft_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Skyloft Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Skyloft Clay events: {events}")
    assert any(evt.get("weather") == "windy" for evt in events)


def test_smooth_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Smooth Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Smooth Rock event: {event}")
    assert event.get("weather") == "dusty"
    assert event.get("bonus") == 3


def test_snatch_orb_uses_snatch() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Snatch Orb"}]
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
    event = next(evt for evt in battle.log if evt.get("effect") == "snatch_orb")
    print(f"Snatch Orb event: {event}")
    assert event.get("move") == "Snatch"


def test_soggy_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Soggy Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Soggy Clay events: {events}")
    assert any(evt.get("weather") == "rainy" for evt in events)


def test_soothing_seed_clears_stages() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Soothing Seed"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    user.combat_stages["atk"] = 2
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "soothing_seed")
    print(f"Soothing Seed event: {event}")
    assert user.combat_stages["atk"] == 0


def test_spritz_spray_bonuses() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Spritz Spray"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "spritz_spray")
    print(f"Spritz Spray event: {event}")
    assert event.get("initiative_bonus") == 5
    assert event.get("evasion_bonus") == 1


def test_steelium_z_ready() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Steelium-Z"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "item")
    print(f"Steelium-Z event: {event}")
    assert event.get("z_type") == "Steel"


def test_sunny_clay_weather_immunity() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Sunny Clay"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    print(f"Sunny Clay events: {events}")
    assert any(evt.get("weather") == "sunny" for evt in events)


def test_sunny_orb_sets_weather() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Sunny Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "weather")
    print(f"Sunny Orb weather event: {event}")
    assert battle.weather == "Sunny"


def test_surround_orb_moves_allies() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Surround Orb"}]
    ally_spec = _pokemon_spec("Pikachu")
    target_spec = _pokemon_spec("Eevee")
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    ally = PokemonState(spec=ally_spec, controller_id=ash.identifier)
    target = PokemonState(spec=target_spec, controller_id=gary.identifier)
    attacker.position = (0, 0)
    ally.position = (4, 4)
    target.position = (2, 2)
    grid = GridState(width=5, height=5)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "ash-2": ally, "gary-1": target},
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "surround_orb")
    print(f"Surround Orb event: {event}")
    assert ally.position != (4, 4)


def test_sweet_apple_stat_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Applin", types=["Grass", "Dragon"])
    user_spec.items = [{"name": "Sweet Apple"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Sweet Apple event: {event}")
    assert event.get("stat") == "spd"
    assert event.get("multiplier") == 1.3


def test_switcher_orb_swaps_positions() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Switcher Orb"}]
    defender_spec = _pokemon_spec("Eevee")
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=defender_spec, controller_id=gary.identifier)
    attacker.position = (0, 0)
    defender.position = (2, 2)
    grid = GridState(width=5, height=5)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
        grid=grid,
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "switcher_orb")
    print(f"Switcher Orb event: {event}")
    assert attacker.position == (2, 2)
    assert defender.position == (0, 0)


def test_syrupy_apple_stat_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Applin", types=["Grass", "Dragon"])
    user_spec.items = [{"name": "Syrupy Apple"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Syrupy Apple event: {event}")
    assert event.get("stat") == "spdef"
    assert event.get("multiplier") == 1.3


def test_tart_apple_stat_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Applin", types=["Grass", "Dragon"])
    user_spec.items = [{"name": "Tart Apple"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Tart Apple event: {event}")
    assert event.get("stat") == "def"
    assert event.get("multiplier") == 1.3


def test_teal_mask_spd_scalar() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Ogerpon", types=["Grass"])
    user_spec.items = [{"name": "Teal Mask"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "stat_scalar")
    print(f"Teal Mask event: {event}")
    assert event.get("stat") == "spd"
    assert event.get("multiplier") == 1.2


def test_tenebrous_rock_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Tenebrous Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Tenebrous Rock event: {event}")
    assert event.get("weather") == "shady"
    assert event.get("bonus") == 3


def test_terrain_extender_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Terrain Extender"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.item_system.apply_held_item_start("ash-1")
    events = []
    battle._apply_terrain(
        events,
        attacker_id="ash-1",
        move=MoveSpec(name="Grassy Terrain", type="Grass", category="Status"),
        name="Grassy Terrain",
        remaining=5,
        description="Test terrain.",
    )
    print(f"Terrain Extender events: {events}")
    assert battle.terrain.get("remaining") == 7


def test_terrain_extender_event_logged() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Terrain Extender"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.item_system.apply_held_item_start("ash-1")
    events = []
    battle._apply_terrain(
        events,
        attacker_id="ash-1",
        move=MoveSpec(name="Grassy Terrain", type="Grass", category="Status"),
        name="Grassy Terrain",
        remaining=5,
        description="Test terrain.",
    )
    event = next(evt for evt in events if evt.get("effect") == "terrain_duration_bonus")
    print(f"Terrain Extender item event: {event}")
    assert event.get("bonus") == 2
