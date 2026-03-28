import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    BattleState,
    GridState,
    InitiativeEntry,
    PokemonState,
    TrainerState,
    TurnPhase,
    UseMoveAction,
)
from auto_ptu.rules import calculations
from auto_ptu.rules.hooks import move_specials


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
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch45AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_teravolt_suppresses_defender(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Zek", ability="Teravolt", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("neutralized"))

    def test_teravolt_errata_suppresses_defender(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Zek", abilities=["Teravolt [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("neutralized"))

    def test_thermosensitive_boosts_attack_in_sun(self):
        spec = _pokemon_spec("Thermo", ability="Thermosensitive")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sunny"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("atk"), 2)
        self.assertEqual(mon.combat_stages.get("spatk"), 2)

    def test_thrust_adds_push_to_melee_hit(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Pusher", ability="Thrust", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[defender_id].position
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertNotEqual(battle.pokemon[defender_id].position, origin)

    def test_thunder_boost_increases_damage_for_adjacent_ally(self):
        move = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Water"])
        battle_boost, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally = PokemonState(
            spec=_pokemon_spec("Ally", ability="Thunder Boost", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle_boost.pokemon["a-2"] = ally
        battle_boost.rng = SequenceRNG([19] + [3] * 20)
        before = battle_boost.pokemon[defender_id].hp
        battle_boost.resolve_move_targets(attacker_id, move, defender_id, battle_boost.pokemon[defender_id].position)
        damage_boost = before - battle_boost.pokemon[defender_id].hp

        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_boost, damage_base)

    def test_tingle_drains_tick_and_penalizes_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tingle", ability="Tingle", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("damage_penalty"))

    def test_tingly_tongue_paralyzes_with_lick(self):
        lick = MoveSpec(
            name="Lick",
            type="Ghost",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Licker", ability="Tingly Tongue", moves=[lick], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[lick])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, lick, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Paralyzed"))

    def test_tinted_lens_increases_resisted_damage(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Lens", ability="Tinted Lens", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Water"])
        battle_lens, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_lens.rng = SequenceRNG([19] + [3] * 20)
        before = battle_lens.pokemon[defender_id].hp
        battle_lens.resolve_move_targets(attacker_id, move, defender_id, battle_lens.pokemon[defender_id].position)
        damage_lens = before - battle_lens.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Lens", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_lens, damage_base)

    def test_tochukaso_resists_bug_damage(self):
        move = MoveSpec(
            name="Bug Bite",
            type="Bug",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Bugger", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Shell", ability="Tochukaso", moves=[move], types=["Grass"])
        battle_resist, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_resist.rng = SequenceRNG([19] + [3] * 20)
        before = battle_resist.pokemon[defender_id].hp
        battle_resist.resolve_move_targets(attacker_id, move, defender_id, battle_resist.pokemon[defender_id].position)
        damage_resist = before - battle_resist.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Shell", moves=[move], types=["Grass"])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_resist, damage_base)

    def test_tolerance_further_resists_types(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Resist", ability="Tolerance", moves=[move], types=["Water"])
        battle_tol, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_tol.rng = SequenceRNG([19] + [3] * 20)
        before = battle_tol.pokemon[defender_id].hp
        battle_tol.resolve_move_targets(attacker_id, move, defender_id, battle_tol.pokemon[defender_id].position)
        damage_tol = before - battle_tol.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Resist", moves=[move], types=["Water"])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_tol, damage_base)

    def test_tonguelash_paralyzes_and_flinches(self):
        lick = MoveSpec(
            name="Lick",
            type="Ghost",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Licker", ability="Tonguelash", moves=[lick], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[lick])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, lick, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Paralyzed"))
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinched"))

    def test_toxic_boost_raises_attack_when_poisoned(self):
        spec = _pokemon_spec("Toxic", ability="Toxic Boost")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Poisoned"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("atk"), 2)

    def test_toxic_boost_errata_raises_atk_and_spatk(self):
        toxic_boost = MoveSpec(
            name="Toxic Boost [Errata]",
            type="Poison",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Toxic", abilities=["Toxic Boost [Errata]"], moves=[toxic_boost])
        defender_spec = _pokemon_spec("Target", moves=[toxic_boost])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[attacker_id].statuses.append({"name": "Poisoned"})
        battle.resolve_move_targets(attacker_id, toxic_boost, attacker_id, battle.pokemon[attacker_id].position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk"), 3)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("spatk"), 3)

    def test_toxic_nourishment_cures_poison_and_grants_temp_hp(self):
        toxic_nourishment = MoveSpec(
            name="Toxic Nourishment",
            type="Poison",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Nourish", ability="Toxic Nourishment", moves=[toxic_nourishment])
        defender_spec = _pokemon_spec("Target", moves=[toxic_nourishment])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].statuses.append({"name": "Poisoned"})
        battle.resolve_move_targets(attacker_id, toxic_nourishment, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[defender_id].has_status("Poisoned"))
        self.assertGreater(battle.pokemon[attacker_id].temp_hp, 0)

    def test_trace_copies_target_ability(self):
        trace = MoveSpec(
            name="Trace",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tracer", ability="Trace", moves=[trace])
        defender_spec = _pokemon_spec("Target", abilities=["Overgrow"], moves=[trace])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, trace, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("entrained_ability"))

    def test_transporter_empowers_teleport(self):
        teleport = MoveSpec(
            name="Teleport",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Porter", ability="Transporter", moves=[teleport])
        defender_spec = _pokemon_spec("Target", moves=[teleport])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, teleport, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Transporter"
                and event.get("effect") == "teleport_boost"
                for event in battle.log
            )
        )

    def test_transporter_errata_requires_ready_then_teleport(self):
        transporter = MoveSpec(
            name="Transporter [Errata]",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        teleport = MoveSpec(
            name="Teleport",
            type="Psychic",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Porter", abilities=["Transporter [Errata]"], moves=[transporter, teleport])
        defender_spec = _pokemon_spec("Target", moves=[teleport])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, transporter, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, teleport, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Transporter [Errata]"
                and event.get("effect") == "teleport_boost"
                for event in battle.log
            )
        )

    def test_triage_grants_priority_to_healing(self):
        heal = MoveSpec(
            name="Recover",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
            keywords=["Healing"],
        )
        attacker_spec = _pokemon_spec("Healer", ability="Triage", moves=[heal])
        defender_spec = _pokemon_spec("Target", moves=[heal])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=heal.name)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], heal)
        self.assertGreaterEqual(effective.priority, 1)

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
        attacker_spec = _pokemon_spec("Tri", ability="Trinity", moves=[tri], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[tri])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([17] + [3] * 20)
        battle.resolve_move_targets(attacker_id, tri, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Frozen"))

    def test_truant_can_skip_standard_action(self):
        spec = _pokemon_spec("Lazy", ability="Truant")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.rng = SequenceRNG([1])
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertFalse(mon.has_action_available(battle.ActionType.STANDARD) if hasattr(battle, 'ActionType') else mon.has_action_available)
        self.assertTrue(mon.get_temporary_effects("save_bonus"))

    def test_turboblaze_suppresses_defender(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Resh", ability="Turboblaze", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("neutralized"))

    def test_turboblaze_errata_suppresses_defender(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Resh", abilities=["Turboblaze [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("neutralized"))

    def test_twisted_power_adds_damage(self):
        move = MoveSpec(
            name="Psybeam",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Twist", ability="Twisted Power", moves=[move], atk=16, spatk=12)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_twist, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_twist.rng = SequenceRNG([19] + [3] * 20)
        before = battle_twist.pokemon[defender_id].hp
        battle_twist.resolve_move_targets(attacker_id, move, defender_id, battle_twist.pokemon[defender_id].position)
        damage_twist = before - battle_twist.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Twist", moves=[move], atk=16, spatk=12)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_twist, damage_base)

    def test_type_aura_boosts_matching_type_damage(self):
        move = MoveSpec(
            name="Thunder Shock",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Target", moves=[move], types=["Water"])
        battle_aura, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally = PokemonState(
            spec=_pokemon_spec("Aura", ability="Type Aura", moves=[move], types=["Electric"]),
            controller_id="a",
            position=(2, 4),
            active=True,
        )
        battle_aura.pokemon["a-2"] = ally
        battle_aura.rng = SequenceRNG([19] + [3] * 20)
        before = battle_aura.pokemon[defender_id].hp
        battle_aura.resolve_move_targets(attacker_id, move, defender_id, battle_aura.pokemon[defender_id].position)
        damage_aura = before - battle_aura.pokemon[defender_id].hp

        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_aura, damage_base)

    def test_type_strategist_grants_damage_reduction(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Strat", ability="Type Strategist", moves=[move], types=["Normal"], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("damage_reduction"))

    def test_ugly_flinches_on_high_roll(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Ugly", ability="Ugly", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinched"))

    def test_unaware_ignores_positive_defense_stages(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Aware", ability="Unaware", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_unaware, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_unaware.pokemon[defender_id].combat_stages["def"] = 2
        battle_unaware.rng = SequenceRNG([19] + [3] * 20)
        before = battle_unaware.pokemon[defender_id].hp
        battle_unaware.resolve_move_targets(attacker_id, move, defender_id, battle_unaware.pokemon[defender_id].position)
        damage_unaware = before - battle_unaware.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Aware", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.pokemon[defender_base_id].combat_stages["def"] = 2
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_unaware, damage_base)

    def test_unbreakable_adds_damage_at_low_hp(self):
        move = MoveSpec(
            name="Iron Head",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Tank", ability="Unbreakable", moves=[move], atk=14, hp_stat=9)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_unbreak, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_unbreak.pokemon[attacker_id].hp = 1
        battle_unbreak.rng = SequenceRNG([19] + [3] * 20)
        before = battle_unbreak.pokemon[defender_id].hp
        battle_unbreak.resolve_move_targets(attacker_id, move, defender_id, battle_unbreak.pokemon[defender_id].position)
        damage_unbreak = before - battle_unbreak.pokemon[defender_id].hp

        base_spec = _pokemon_spec("Tank", moves=[move], atk=14, hp_stat=9)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_spec, defender_spec)
        battle_base.pokemon[attacker_base_id].hp = 1
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_unbreak, damage_base)

    def test_vanguard_adds_damage_before_target_acts(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Lead", ability="Vanguard", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_vanguard, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_vanguard.initiative_order = [
            InitiativeEntry(
                actor_id=attacker_id,
                trainer_id="a",
                speed=10,
                trainer_modifier=0,
                roll=10,
                total=20,
            ),
            InitiativeEntry(
                actor_id=defender_id,
                trainer_id="b",
                speed=8,
                trainer_modifier=0,
                roll=5,
                total=13,
            ),
        ]
        battle_vanguard.rng = SequenceRNG([19] + [3] * 20)
        before = battle_vanguard.pokemon[defender_id].hp
        battle_vanguard.resolve_move_targets(attacker_id, move, defender_id, battle_vanguard.pokemon[defender_id].position)
        damage_vanguard = before - battle_vanguard.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Lead", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.initiative_order = list(battle_vanguard.initiative_order)
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_vanguard, damage_base)

    def test_venom_last_chance_boosts_poison_damage(self):
        move = MoveSpec(
            name="Poison Jab",
            type="Poison",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Venom", ability="Venom", moves=[move], atk=14, hp_stat=9)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle_venom, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_venom.pokemon[attacker_id].hp = 1
        battle_venom.rng = SequenceRNG([19] + [3] * 20)
        before = battle_venom.pokemon[defender_id].hp
        battle_venom.resolve_move_targets(attacker_id, move, defender_id, battle_venom.pokemon[defender_id].position)
        damage_venom = before - battle_venom.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Venom", moves=[move], atk=14, hp_stat=9)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.pokemon[attacker_base_id].hp = 1
        battle_base.rng = SequenceRNG([19] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_venom, damage_base)

    def test_vicious_grants_extra_action_on_hone_claws(self):
        hone_claws = MoveSpec(
            name="Hone Claws",
            type="Dark",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Vicious", ability="Vicious", moves=[hone_claws])
        defender_spec = _pokemon_spec("Target", moves=[hone_claws])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, hone_claws, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[attacker_id].get_temporary_effects("extra_action"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Vicious"
                and event.get("effect") == "extra_action"
                for event in battle.log
            )
        )

    def test_victory_star_boosts_ally_accuracy(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Ally", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon["a-2"] = PokemonState(
            spec=_pokemon_spec("Star", ability="Victory Star", moves=[move]),
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Victory Star"
                and event.get("effect") == "accuracy_bonus"
                for event in battle.log
            )
        )

    def test_vigor_heals_after_endure(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=16)
        defender_spec = _pokemon_spec("Vigor", ability="Vigor", moves=[move], hp_stat=9)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Endure"})
        defender.hp = 1
        battle.rng = SequenceRNG([19] + [3] * 20)
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertGreater(defender.hp, 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Vigor"
                and event.get("effect") == "heal"
                for event in battle.log
            )
        )

    def test_vital_spirit_blocks_sleep(self):
        move = MoveSpec(
            name="Hypnosis",
            type="Psychic",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Caster", moves=[move])
        defender_spec = _pokemon_spec("Spirit", ability="Vital Spirit", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=battle.pokemon[defender_id],
            status="Asleep",
            effect="test",
            description="Test",
            remaining=1,
        )
        self.assertFalse(battle.pokemon[defender_id].has_status("Asleep"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Vital Spirit"
                and event.get("effect") == "status_block"
                for event in events
            )
        )

    def test_unburden_errata_grants_speed_stage(self):
        spec = _pokemon_spec("Runner", abilities=["Unburden [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spd"), 2)

    def test_unnerve_errata_blocks_buffs(self):
        unnerve = MoveSpec(
            name="Unnerve [Errata]",
            type="Dark",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Nerve", abilities=["Unnerve [Errata]"], moves=[unnerve])
        defender_spec = _pokemon_spec("Target", moves=[unnerve])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, unnerve, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("unnerved"))
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("digestion_blocked"))
