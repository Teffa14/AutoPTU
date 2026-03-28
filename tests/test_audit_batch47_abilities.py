
import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    BattleState,
    GridState,
    PokemonState,
    ShiftAction,
    TrainerState,
    TurnPhase,
    UseMoveAction,
)
from auto_ptu.rules import calculations
from auto_ptu.rules.abilities.ability_moves import build_ability_moves


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b

    def choice(self, seq):
        return seq[0]


def _pokemon_spec(
    name,
    *,
    ability=None,
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    level=20,
    items=None,
    movement=None,
    gender="",
):
    ability_list = abilities if abilities is not None else ([ability] if ability else [])
    return PokemonSpec(
        species=name,
        level=level,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=[{"name": entry} for entry in ability_list],
        items=items or [],
        movement=movement or {"overland": 4},
        weight=5,
        gender=gender,
    )


def _build_battle(attacker_spec, defender_spec):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 200)
    return battle, "a-1", "b-1"


class AuditBatch47AbilityTests(unittest.TestCase):
    def test_weird_power_adds_higher_stat(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Weird", abilities=["Weird Power"], moves=[move], atk=16, spatk=10)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        damage_weird = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], atk=16, spatk=10)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_weird, damage_base)

    def test_accelerate_adds_priority_and_damage(self):
        accelerate = MoveSpec(
            name="Accelerate",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Accel", abilities=["Accelerate"], moves=[accelerate, tackle], spd=14)
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, accelerate, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Accelerate"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_anchored_grants_anchor_token(self):
        spec = _pokemon_spec("Anchor", abilities=["Anchored"])
        mon = PokemonState(spec=spec, controller_id="a", position=(1, 1), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        self.assertTrue(battle.has_anchor_token("a-1"))

    def test_battery_charges_ally_special(self):
        battery = MoveSpec(
            name="Battery",
            type="Electric",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
        )
        psybeam = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Battery", abilities=["Battery"], moves=[battery], spd=12)
        ally_spec = _pokemon_spec("Ally", moves=[psybeam], spd=12)
        defender_spec = _pokemon_spec("Foe", moves=[psybeam])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 3), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(2, 6), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "a-2": ally, "b-1": defender},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([19] + [3] * 50)
        battle.resolve_move_targets("a-1", battery, "a-2", ally.position)
        battle.resolve_move_targets("a-2", psybeam, "b-1", defender.position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Battery"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_berserk_triggers_below_half(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Berserk", abilities=["Berserk"], moves=[move], hp_stat=12)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].hp = 20
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("spatk"), 1)

    def test_beast_boost_raises_highest_stat_on_ko(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Beast", abilities=["Beast Boost"], moves=[move], spd=18)
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].hp = 1
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spd"), 1)

    def test_dancer_copies_dance_move(self):
        dance = MoveSpec(
            name="Swords Dance",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Lead", moves=[dance])
        dancer_spec = _pokemon_spec("Dancer", abilities=["Dancer"], moves=[dance])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        dancer = PokemonState(spec=dancer_spec, controller_id="a", position=(2, 4), active=True)
        battle = BattleState(
            trainers={"a": trainer_a},
            pokemon={"a-1": attacker, "a-2": dancer},
            grid=GridState(width=10, height=10),
        )
        battle.resolve_move_targets("a-1", dance, "a-1", attacker.position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Dancer"
                and event.get("effect") == "copy"
                for event in battle.log
            )
        )

    def test_disguise_blocks_first_hit(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Mask", abilities=["Disguise"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        before = battle.pokemon[defender_id].hp
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].hp, before)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("def"), 1)

    def test_dazzling_suppresses_priority(self):
        dazzling = MoveSpec(
            name="Dazzling",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Dazzle", abilities=["Dazzling"], moves=[dazzling])
        defender_spec = _pokemon_spec("Target", moves=[dazzling])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, dazzling, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("priority_blocked"))
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("initiative_penalty"))
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("no_interrupts"))

    def test_chemical_romance_infatuates_male(self):
        move = MoveSpec(
            name="Poison Gas",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Burst",
            range_text="Burst 1",
        )
        attacker_spec = _pokemon_spec("Chem", abilities=["Chemical Romance"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], gender="Male")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Infatuated"))

    def test_comatose_sets_sleep_and_heals(self):
        comatose = MoveSpec(
            name="Comatose",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Doze", abilities=["Comatose"], moves=[comatose], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[comatose])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].hp = 10
        battle.resolve_move_targets(attacker_id, comatose, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].has_status("Sleep"))
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("comatose_active"))
        self.assertGreater(battle.pokemon[attacker_id].hp, 10)

    def test_corrosion_allows_toxic_on_steel(self):
        toxic = MoveSpec(
            name="Toxic",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Corrode", abilities=["Corrosion"], moves=[toxic])
        defender_spec = _pokemon_spec("Steel", moves=[toxic], types=["Steel"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, toxic, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Badly Poisoned"))

        base_spec = _pokemon_spec("Base", moves=[toxic])
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        battle_base.resolve_move_targets(attacker_base_id, toxic, defender_base_id, battle_base.pokemon[defender_base_id].position)
        self.assertFalse(battle_base.pokemon[defender_base_id].has_status("Badly Poisoned"))

    def test_electric_surge_sets_terrain(self):
        surge = MoveSpec(
            name="Electric Surge",
            type="Electric",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Surge", abilities=["Electric Surge"], moves=[surge])
        defender_spec = _pokemon_spec("Target", moves=[surge])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, surge, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual((battle.terrain or {}).get("name"), "Electric Terrain")

    def test_emergency_exit_switches_out(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=16)
        defender_spec = _pokemon_spec("Exit", abilities=["Emergency Exit"], moves=[move], hp_stat=10)
        backup_spec = _pokemon_spec("Backup", moves=[move], hp_stat=10)
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(2, 3), active=True)
        backup = PokemonState(spec=backup_spec, controller_id="b", position=(2, 4), active=False)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": defender, "b-2": backup},
            grid=GridState(width=10, height=10),
        )
        battle.pokemon["b-1"].hp = 20
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets("a-1", move, "b-1", defender.position)
        self.assertFalse(battle.pokemon["b-1"].active)
        self.assertTrue(battle.pokemon["b-2"].active)

    def test_fluffy_reduces_melee_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Fluff", abilities=["Fluffy"], moves=[move])
        battle_fluff, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_fluff.rng = SequenceRNG([19] + [3] * 20)
        before = battle_fluff.pokemon[defender_id].hp
        battle_fluff.resolve_move_targets(attacker_id, move, defender_id, battle_fluff.pokemon[defender_id].position)
        damage_fluff = before - battle_fluff.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_fluff, damage_base)

    def test_full_metal_body_blocks_stage_drop(self):
        move = MoveSpec(name="Growl", type="Normal", category="Status", db=0, ac=None)
        attacker_spec = _pokemon_spec("Foe", moves=[move])
        defender_spec = _pokemon_spec("Metal", abilities=["Full Metal Body"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle._apply_combat_stage(
            [],
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            stat="def",
            delta=-1,
            description="Test",
            effect="test",
        )
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("def"), 0)

    def test_galvanize_converts_normal_to_electric(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Galv", abilities=["Galvanize"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Ground", moves=[move], types=["Ground"])
        battle_galv, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_galv.rng = SequenceRNG([19] + [3] * 20)
        before = battle_galv.pokemon[defender_id].hp
        battle_galv.resolve_move_targets(attacker_id, move, defender_id, battle_galv.pokemon[defender_id].position)
        damage_galv = before - battle_galv.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_galv, damage_base)

    def test_glisten_blocks_fairy_and_boosts_defense(self):
        move = MoveSpec(
            name="Dazzling Gleam",
            type="Fairy",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Glisten", abilities=["Glisten"], moves=[move], defense=14, spdef=10)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        before_hp = battle.pokemon[defender_id].hp
        before_def = battle.pokemon[defender_id].combat_stages.get("def")
        before_spdef = battle.pokemon[defender_id].combat_stages.get("spdef")
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        after_def = battle.pokemon[defender_id].combat_stages.get("def")
        after_spdef = battle.pokemon[defender_id].combat_stages.get("spdef")
        self.assertEqual(battle.pokemon[defender_id].hp, before_hp)
        self.assertTrue(after_def > before_def or after_spdef > before_spdef)

    def test_grassy_surge_sets_terrain(self):
        surge = MoveSpec(
            name="Grassy Surge",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Surge", abilities=["Grassy Surge"], moves=[surge])
        defender_spec = _pokemon_spec("Target", moves=[surge])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, surge, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual((battle.terrain or {}).get("name"), "Grassy Terrain")

    def test_handyman_selects_item_index(self):
        spec = _pokemon_spec(
            "Handy",
            abilities=["Handyman"],
            items=[{"name": "Potion"}, {"name": "Super Potion", "equipped": True}],
        )
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.add_temporary_effect("handyman_choice", item_index=1)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        idx = battle._delivery_bird_item_index(mon, mon.spec.items)
        self.assertEqual(idx, 1)

    def test_horde_break_cures_status_on_schooling_return(self):
        spec = _pokemon_spec("School", abilities=["Schooling", "Horde Break"], hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.add_temporary_effect("schooling_active")
        mon.statuses.append({"name": "Burned", "remaining": 3})
        mon.hp = 1
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertFalse(mon.statuses)

    def test_innards_out_retaliates(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Innards", abilities=["Innards Out"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before_attacker = battle.pokemon[attacker_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[attacker_id].hp, before_attacker)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Innards Out"
                and event.get("effect") == "retaliate"
                for event in battle.log
            )
        )

    def test_liquid_voice_converts_sonic_status_to_damage(self):
        sonic = MoveSpec(
            name="Sonic Cry",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
            keywords=["Sonic"],
        )
        attacker_spec = _pokemon_spec("Voice", abilities=["Liquid Voice"], moves=[sonic], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[sonic])
        battle_voice, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_voice.rng = SequenceRNG([19] + [3] * 20)
        before = battle_voice.pokemon[defender_id].hp
        battle_voice.resolve_move_targets(attacker_id, sonic, defender_id, battle_voice.pokemon[defender_id].position)
        damage_voice = before - battle_voice.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[sonic], spatk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, sonic, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_voice, damage_base)

    def test_long_reach_extends_range(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Reach", abilities=["Long Reach"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=move.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], move)
        self.assertEqual(effective.range_kind, "Ranged")
        self.assertEqual(effective.range_value, 8)

    def test_merciless_forces_crit_on_poisoned(self):
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker = PokemonState(
            spec=_pokemon_spec("Mercy", abilities=["Merciless"], moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        defender = PokemonState(
            spec=_pokemon_spec("Target", moves=[move]),
            controller_id="b",
            position=(0, 1),
            active=True,
        )
        defender.statuses.append({"name": "Poisoned", "remaining": 2})
        rng = SequenceRNG([19])
        result = calculations.attack_hits(rng, attacker, defender, move)
        self.assertTrue(result.get("crit"))

    def test_misty_surge_sets_terrain(self):
        surge = MoveSpec(
            name="Misty Surge",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Surge", abilities=["Misty Surge"], moves=[surge])
        defender_spec = _pokemon_spec("Target", moves=[surge])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, surge, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual((battle.terrain or {}).get("name"), "Misty Terrain")

    def test_mud_shield_grants_temp_hp(self):
        mud = MoveSpec(
            name="Mud Shield",
            type="Ground",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Mud", abilities=["Mud Shield"], moves=[mud], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[mud])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, mud, attacker_id, battle.pokemon[attacker_id].position)
        self.assertGreater(battle.pokemon[attacker_id].temp_hp, 0)

    def test_neuroforce_adds_damage_on_super_effective(self):
        move = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Neuro", abilities=["Neuroforce"], moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Water", moves=[move], types=["Water"])
        battle_neuro, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_neuro.rng = SequenceRNG([19] + [3] * 20)
        before = battle_neuro.pokemon[defender_id].hp
        battle_neuro.resolve_move_targets(attacker_id, move, defender_id, battle_neuro.pokemon[defender_id].position)
        damage_neuro = before - battle_neuro.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], spatk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_neuro, damage_base)

    def test_power_construct_grants_temp_hp_below_half(self):
        power = MoveSpec(
            name="Power Construct",
            type="Dragon",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Zygarde", abilities=["Power Construct"], moves=[power], hp_stat=10)
        defender_spec = _pokemon_spec("Target", moves=[power])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        max_hp = battle.pokemon[attacker_id].max_hp()
        battle.pokemon[attacker_id].hp = max(1, max_hp // 4)
        battle.resolve_move_targets(attacker_id, power, attacker_id, battle.pokemon[attacker_id].position)
        self.assertGreaterEqual(battle.pokemon[attacker_id].temp_hp, max(1, max_hp // 2))
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("power_construct_active"))

    def test_power_of_alchemy_copies_ability(self):
        power = MoveSpec(
            name="Power of Alchemy",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Mixer", abilities=["Power of Alchemy"], moves=[power])
        defender_spec = _pokemon_spec("Target", abilities=["Rough Skin"], moves=[power])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, power, defender_id, battle.pokemon[defender_id].position)
        granted = [
            entry
            for entry in battle.pokemon[attacker_id].get_temporary_effects("ability_granted")
            if entry.get("source") == "Power of Alchemy" and entry.get("ability") == "Rough Skin"
        ]
        self.assertTrue(granted)


if __name__ == "__main__":
    unittest.main()
