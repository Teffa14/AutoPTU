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
    "Magmarizer",
    "Main + Off Hand",
    "Main Hand",
    "Max Repel",
    "Medicine Case",
    "Mega Stone",
    "Memory",
    "Microphone",
    "Moon Stone",
    "Mulch",
    "Nightvision Goggles",
    "Off-Hand",
    "Old Rod",
    "Orange Shard",
    "Oval Stone",
    "Oxygenation Vial",
    "Personal Forcefield",
]


WEAPON_ITEMS = [
    "Mace",
    "Machine Pistol",
    "Marksman Rifle",
    "Medium Machinegun",
    "Magikarp (Weapon)",
    "Pickaxe",
]


Z_CRYSTALS = [
    ("Lycanium-Z", None),
    ("Marshadium-Z", None),
    ("Mewnium-Z", None),
    ("Mimikium-Z", None),
    ("Normalium-Z", "Normal"),
    ("Pikanium-Z", None),
    ("Pikashunium-Z", None),
]


MEGA_STONES = [
    ("Manectite", "Manectric", "Mega Manectric"),
    ("Mawilite", "Mawile", "Mega Mawile"),
    ("Medichamite", "Medicham", "Mega Medicham"),
    ("Metagrossite", "Metagross", "Mega Metagross"),
    ("Mewtwonite X", "Mewtwo", "Mega Mewtwo X"),
    ("Mewtwonite Y", "Mewtwo", "Mega Mewtwo Y"),
    ("Pidgeotite", "Pidgeot", "Mega Pidgeot"),
]


@pytest.mark.parametrize("item_name", NON_COMBAT_ITEMS)
def test_non_combat_placeholders_batch4(item_name: str) -> None:
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
def test_weapon_items_can_be_equipped_batch4(item_name: str) -> None:
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
def test_z_crystals_ready_batch4(item_name: str, expected_type: str | None) -> None:
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
def test_mega_stones_apply_forms_batch4(stone_name: str, species_name: str, mega_form: str) -> None:
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


def test_misty_rock_weather_duration_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Misty Rock"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "weather_duration_bonus")
    print(f"Misty Rock held event: {event}")
    assert event.get("weather") == "Foggy"
    assert event.get("bonus") == 3


def test_macro_galaxy_pioneer_armor_stats() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Macro-Galaxy Pioneer Armor"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.item_system.apply_held_item_start("ash-1")
    effects = user.get_temporary_effects("stat_modifier")
    print(f"Pioneer Armor stat modifiers: {effects}")
    assert any(entry.get("stat") == "def" and entry.get("amount") == 5 for entry in effects)
    assert any(entry.get("stat") == "spdef" and entry.get("amount") == 5 for entry in effects)


def test_lysandre_fire_rescue_armour_burn_immunity() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    defender_spec = _pokemon_spec("Eevee")
    defender_spec.items = [{"name": "Lysandre Labs Fire Rescue Armour"}]
    defender = PokemonState(spec=defender_spec, controller_id=ash.identifier)
    attacker = PokemonState(spec=_pokemon_spec("Vulpix"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": defender, "gary-1": attacker},
    )
    battle.item_system.apply_held_item_start("ash-1")
    events: list[dict] = []
    battle._apply_status(
        events,
        attacker_id="gary-1",
        target_id="ash-1",
        move=MoveSpec(name="Will-O-Wisp", type="Fire", category="Status"),
        target=defender,
        status="Burned",
        effect="item_status",
        description="Burn attempt.",
    )
    event = next(evt for evt in events if evt.get("effect") == "status_immunity_block")
    print(f"Fire Rescue Armour immunity event: {event}")
    assert defender.has_status("Burned") is False


def test_lysandre_fire_rescue_armour_fire_reduction() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.moves = [MoveSpec(name="Ember", type="Fire", category="Special", db=5, ac=2, freq="EOT")]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender_spec = _pokemon_spec("Eevee")
    defender_spec.items = [{"name": "Lysandre Labs Fire Rescue Armour"}]
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
    event = next(evt for evt in events if evt.get("effect") == "fire_rescue_reduction")
    print(f"Fire Rescue Armour mitigation event: {event}")
    assert result["damage"] == 10


def test_metal_coat_resistance_bonus() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Steelix", types=["Steel"])
    user_spec.items = [{"name": "Metal Coat"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    events = battle.item_system.apply_held_item_start("ash-1")
    event = next(evt for evt in events if evt.get("effect") == "resistance_bonus")
    print(f"Metal Coat held event: {event}")
    assert event.get("amount") == 20


def test_masterpiece_teacup_bonuses() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Poltchageist")
    user_spec.items = [{"name": "Masterpiece Teacup"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.item_system.apply_held_item_start("ash-1")
    drain = user.get_temporary_effects("drain_multiplier")
    stat_mods = user.get_temporary_effects("stat_modifier")
    print(f"Masterpiece Teacup drain: {drain}")
    print(f"Masterpiece Teacup stat mods: {stat_mods}")
    assert any(entry.get("multiplier") == 1.3 for entry in drain)
    assert any(entry.get("stat") == "spatk" and entry.get("amount") == 10 for entry in stat_mods)


def test_medicinal_leek_heals() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Medicinal Leek"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    user.hp = 5
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "heal")
    print(f"Medicinal Leek event: {event}")
    assert event.get("amount") == 5


def test_metronome_consecutive_power_bonus() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Metronome"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
    battle.resolve_next_action()
    battle.queue_action(UseMoveAction(actor_id="ash-1", move_name="Tackle", target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "metronome_power")
    print(f"Metronome bonus event: {event}")
    assert event.get("multiplier") == 1.2


def test_mirror_herb_copies_stage_gain() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    holder_spec = _pokemon_spec("Eevee")
    holder_spec.items = [{"name": "Mirror Herb"}]
    holder = PokemonState(spec=holder_spec, controller_id=ash.identifier)
    target = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": holder, "gary-1": target},
    )
    events: list[dict] = []
    battle._apply_combat_stage(
        events,
        attacker_id="gary-1",
        target_id="gary-1",
        move=MoveSpec(name="Howl", type="Normal", category="Status"),
        target=target,
        stat="atk",
        delta=1,
        description="Howl raises Attack.",
    )
    event = next(evt for evt in events if evt.get("effect") == "mirror_herb_copy")
    print(f"Mirror Herb copy event: {event}")
    assert holder.combat_stages.get("atk", 0) == 1
    assert all(item.get("name") != "Mirror Herb" for item in holder.spec.items)


def test_normal_plate_multi_attack_mapping() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Normal Plate"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    mapped = battle._item_type_from_item({"name": "Normal Plate"})
    print(f"Normal Plate item type: {mapped}")
    assert mapped == "Normal"


def test_pester_ball_requires_choice() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Pester Ball"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "pester_ball_choice_required")
    print(f"Pester Ball choice event: {event}")
    assert event.get("item") == "Pester Ball"


def test_pester_ball_burn_inflicts_status() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Pester Ball (Burn)"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("type") == "status" and evt.get("status") == "Burned")
    print(f"Pester Ball (Burn) status event: {event}")
    assert defender.has_status("Burned")


def test_mug_orb_uses_thief() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "Mug Orb"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    before_hp = defender.hp
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "mug_orb_thief")
    print(f"Mug Orb event: {event}")
    assert defender.hp < before_hp


def test_one_shot_orb_uses_guillotine() -> None:
    ash = TrainerState(identifier="ash", name="Ash")
    gary = TrainerState(identifier="gary", name="Gary")
    attacker_spec = _pokemon_spec("Eevee")
    attacker_spec.items = [{"name": "One-Shot Orb"}]
    attacker = PokemonState(spec=attacker_spec, controller_id=ash.identifier)
    defender = PokemonState(spec=_pokemon_spec("Pikachu"), controller_id=gary.identifier)
    battle = BattleState(
        trainers={ash.identifier: ash, gary.identifier: gary},
        pokemon={"ash-1": attacker, "gary-1": defender},
    )
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="gary-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "one_shot_orb")
    print(f"One-Shot Orb event: {event}")
    assert event.get("move") == "Guillotine"


def test_pierce_orb_sets_fling_pierce() -> None:
    trainer = TrainerState(identifier="ash", name="Ash")
    user_spec = _pokemon_spec("Eevee")
    user_spec.items = [{"name": "Pierce Orb"}]
    user = PokemonState(spec=user_spec, controller_id=trainer.identifier)
    battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": user})
    battle.queue_action(UseItemAction(actor_id="ash-1", item_index=0, target_id="ash-1"))
    battle.resolve_next_action()
    event = next(evt for evt in battle.log if evt.get("effect") == "fling_pierce")
    print(f"Pierce Orb event: {event}")
    assert user.get_temporary_effects("fling_pierce")
