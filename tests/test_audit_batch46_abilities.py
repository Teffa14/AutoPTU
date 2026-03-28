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


class AuditBatch46AbilityTests(unittest.TestCase):
    def test_whirlwind_kicks_errata_burst_rapid_spin(self):
        rapid = MoveSpec(
            name="Rapid Spin",
            type="Normal",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spinner", abilities=["Whirlwind Kicks [Errata]"], moves=[rapid])
        defender_spec = _pokemon_spec("Target", moves=[rapid])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=rapid.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], rapid)
        self.assertEqual(effective.area_kind, "Burst")
        self.assertEqual(effective.area_value, 1)
        self.assertEqual(effective.range_text, "Burst 1")
        self.assertGreaterEqual(effective.priority, 1)

    def test_windveiled_errata_blocks_flying_and_charges_bonus(self):
        gust = MoveSpec(
            name="Gust",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bird", moves=[gust], spatk=14)
        defender_spec = _pokemon_spec("Veil", abilities=["Windveiled [Errata]"], moves=[gust])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, gust, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].hp, before)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("windveiled_boost"))
        action = UseMoveAction(actor_id=defender_id, move_name=gust.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[defender_id], gust, consume=True)
        self.assertEqual(effective.db, (gust.db or 0) + 1)

    def test_zen_mode_errata_activates_and_grants_moves(self):
        zen = MoveSpec(
            name="Zen Mode [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Zen", abilities=["Zen Mode [Errata]"], moves=[zen])
        defender_spec = _pokemon_spec("Target", moves=[zen])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, zen, attacker_id, battle.pokemon[attacker_id].position)
        zen_entries = battle.pokemon[attacker_id].get_temporary_effects("zen_mode")
        self.assertTrue(zen_entries)
        self.assertTrue(zen_entries[0].get("active"))
        move_names = {mv.name for mv in battle.pokemon[attacker_id].spec.moves}
        self.assertIn("Flamethrower", move_names)
        self.assertIn("Psychic", move_names)

    def test_aqua_bullet_shifts_toward_target(self):
        water = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Darter", abilities=["Aqua Bullet"], moves=[water])
        defender_spec = _pokemon_spec("Target", moves=[water])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(2, 7), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": defender},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets("a-1", water, "b-1", defender.position)
        self.assertEqual(attacker.position, (2, 6))
        self.assertTrue(attacker.get_temporary_effects("aqua_bullet_shift"))

    def test_designer_grants_ability_action(self):
        spec = _pokemon_spec("Maker", abilities=["Designer"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        ability_moves = build_ability_moves(mon)
        self.assertTrue(any(move.name == "Designer" for move in ability_moves))

    def test_combo_striker_triggers_followup(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Combo", abilities=["Combo Striker"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([10] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Combo Striker"
                and event.get("effect") == "followup"
                for event in battle.log
            )
        )

    def test_dream_smoke_puts_attacker_to_sleep(self):
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
        defender_spec = _pokemon_spec("Smoke", abilities=["Dream Smoke"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].has_status("Sleep"))

    def test_empower_readies_free_action(self):
        empower = MoveSpec(
            name="Empower",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Emp", abilities=["Empower"], moves=[empower])
        defender_spec = _pokemon_spec("Target", moves=[empower])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, empower, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("action_override"))

    def test_flower_power_swaps_grass_category(self):
        leaf = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Flower", abilities=["Flower Power"], moves=[leaf], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[leaf])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].add_temporary_effect("flower_power_choice", category="special")
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, leaf, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Flower Power"
                and event.get("effect") == "category_swap"
                for event in battle.log
            )
        )

    def test_full_guard_sets_ready(self):
        guard = MoveSpec(
            name="Full Guard",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Guard", abilities=["Full Guard"], moves=[guard])
        defender_spec = _pokemon_spec("Target", moves=[guard])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, guard, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("full_guard_ready"))

    def test_giver_forces_present_roll(self):
        present = MoveSpec(
            name="Present",
            type="Normal",
            category="Physical",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Giver", abilities=["Giver"], moves=[present], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[present], hp_stat=10)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19, 1] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, present, defender_id, battle.pokemon[defender_id].position)
        damage = before - battle.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Base", moves=[present], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.rng = SequenceRNG([19, 1] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, present, defender_base_id, battle_base.pokemon[defender_base_id].position)
        healed_base = battle_base.pokemon[defender_base_id].hp - before_base

        self.assertGreater(damage, 0)
        self.assertGreater(healed_base, 0)

    def test_heliovolt_adds_evasion_and_sunny_resonance(self):
        heliovolt = MoveSpec(
            name="Heliovolt",
            type="Electric",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Helio", abilities=["Heliovolt"], moves=[heliovolt])
        defender_spec = _pokemon_spec("Target", moves=[heliovolt])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, heliovolt, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("heliovolt_active"))
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("evasion_bonus"))

    def test_juicy_energy_uses_level_heal(self):
        spec = _pokemon_spec("Juice", abilities=["Juicy Energy"], level=20, hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.hp = 10
        mon.food_buffs = [{"effect": "restores 30 hit points"}]
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle._apply_food_buff_start("a-1", force=True)
        healed = mon.hp - 10

        base_spec = _pokemon_spec("Base", level=20, hp_stat=10)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        base.hp = 10
        base.food_buffs = [{"effect": "restores 30 hit points"}]
        battle_base = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": base},
            grid=GridState(width=6, height=6),
        )
        battle_base._apply_food_buff_start("a-1", force=True)
        healed_base = base.hp - 10

        self.assertEqual(healed, 20)
        self.assertEqual(healed_base, 30)

    def test_lancer_grants_crit_after_charge(self):
        spec = _pokemon_spec("Lancer", abilities=["Lancer"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.add_temporary_effect("lancer_shift", round=0, distance=3)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.round = 0
        mon._handle_ability_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertTrue(mon.get_temporary_effects("crit_range_bonus"))

    def test_leaf_rush_adds_priority_and_damage_bonus(self):
        rush = MoveSpec(
            name="Leaf Rush",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        leaf = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rush", abilities=["Leaf Rush"], moves=[rush, leaf], spd=14)
        defender_spec = _pokemon_spec("Target", moves=[leaf])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, rush, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, leaf, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Leaf Rush"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_leafy_cloak_grants_abilities(self):
        cloak = MoveSpec(
            name="Leafy Cloak",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Cloak", abilities=["Leafy Cloak"], moves=[cloak])
        defender_spec = _pokemon_spec("Target", moves=[cloak])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, cloak, attacker_id, battle.pokemon[attacker_id].position)
        granted = battle.pokemon[attacker_id].get_temporary_effects("ability_granted")
        self.assertTrue(any(entry.get("ability") == "Chlorophyll" for entry in granted))
        self.assertTrue(any(entry.get("ability") == "Leaf Guard" for entry in granted))

    def test_line_charge_blocks_diagonal_shift(self):
        spec = _pokemon_spec("Line", abilities=["Line Charge"])
        mon = PokemonState(spec=spec, controller_id="a", position=(1, 1), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        action = ShiftAction(actor_id="a-1", destination=(2, 2))
        with self.assertRaises(ValueError):
            action.validate(battle)

    def test_maestrom_pulse_adds_priority_and_damage_bonus(self):
        pulse = MoveSpec(
            name="Maestrom Pulse",
            type="Water",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        surf = MoveSpec(
            name="Surf",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pulse", abilities=["Maestrom Pulse"], moves=[pulse, surf], spd=14)
        defender_spec = _pokemon_spec("Target", moves=[surf])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, pulse, attacker_id, battle.pokemon[attacker_id].position)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, surf, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Maelstrom Pulse"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_nimble_strikes_adds_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Nimble", abilities=["Nimble Strikes"], moves=[move], spd=14, atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        damage_bonus = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Base", moves=[move], spd=14, atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_bonus, damage_base)

    def test_ragelope_enrages_on_high_roll(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rage", abilities=["Ragelope"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([18] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].has_status("Enraged"))
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spd"), 1)

    def test_sacred_bell_resists_dark(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Bell", abilities=["Sacred Bell"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        damage_resist = before - battle.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Bell", moves=[move])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_resist, damage_base)

    def test_seasonal_grants_ability(self):
        spec = _pokemon_spec("Deer", abilities=["Seasonal"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        seasonal = mon.get_temporary_effects("seasonal")
        granted = [entry for entry in mon.get_temporary_effects("ability_granted") if entry.get("source") == "Seasonal"]
        self.assertTrue(seasonal)
        self.assertTrue(granted)

    def test_snuggle_grants_temp_hp_to_both(self):
        snuggle = MoveSpec(
            name="Snuggle",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Snug", abilities=["Snuggle"], moves=[snuggle])
        defender_spec = _pokemon_spec("Target", moves=[snuggle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, snuggle, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(battle.pokemon[attacker_id].temp_hp, 0)
        self.assertGreater(battle.pokemon[defender_id].temp_hp, 0)

    def test_sol_veil_grants_evasion_and_dr_in_sun(self):
        spec = _pokemon_spec("Veil", abilities=["Sol Veil"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sunny"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        evasion = [
            entry
            for entry in mon.get_temporary_effects("evasion_bonus")
            if entry.get("source") == "Sol Veil"
        ]
        dr = [
            entry
            for entry in mon.get_temporary_effects("damage_reduction")
            if entry.get("source") == "Sol Veil"
        ]
        self.assertTrue(evasion)
        self.assertEqual(evasion[0].get("amount"), 2)
        self.assertTrue(dr)

    def test_sorcery_adds_special_attack_bonus(self):
        spec = _pokemon_spec("Mage", abilities=["Sorcery"], level=30)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        bonus = [
            entry
            for entry in mon.get_temporary_effects("stat_modifier")
            if entry.get("stat") == "spatk" and entry.get("source") == "Sorcery"
        ]
        self.assertTrue(bonus)

    def test_spike_shot_extends_melee_range(self):
        strike = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_value=1,
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Spike", abilities=["Spike Shot"], moves=[strike])
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=strike.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], strike)
        self.assertEqual(effective.range_kind, "Ranged")
        self.assertEqual(effective.range_value, 8)

    def test_tingle_drains_tick_and_applies_penalty(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tingle", abilities=["Tingle"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        after = battle.pokemon[defender_id].hp
        self.assertLess(after, before)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("damage_penalty"))

    def test_tonguelash_paralyzes_and_flinches(self):
        lick = MoveSpec(
            name="Lick",
            type="Ghost",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tongue", abilities=["Tonguelash"], moves=[lick], atk=12)
        defender_spec = _pokemon_spec("Target", moves=[lick])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, lick, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Paralyzed"))
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinched"))

    def test_trinity_tri_attack_applies_frozen_first(self):
        tri = MoveSpec(
            name="Tri Attack",
            type="Normal",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tri", abilities=["Trinity"], moves=[tri], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[tri])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([17] + [3] * 20)
        battle.resolve_move_targets(attacker_id, tri, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Frozen"))

    def test_type_aura_adds_damage_bonus(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14, types=["Water"])
        aura_spec = _pokemon_spec("Aura", abilities=["Type Aura"], moves=[move], types=["Water"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        aura = PokemonState(spec=aura_spec, controller_id="a", position=(2, 4), active=True)
        defender = PokemonState(spec=defender_spec, controller_id="b", position=(2, 6), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "a-2": aura, "b-1": defender},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets("a-1", move, "b-1", defender.position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Type Aura"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )


if __name__ == "__main__":
    unittest.main()
