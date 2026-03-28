import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.calculations import resolve_move_action
from auto_ptu.rules.hooks import move_specials


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(name, move, *, items=None):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=10,
        moves=[move],
        movement={"overland": 4},
        items=list(items or []),
    )


def _build_battle(move, *, attacker_items=None):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, items=attacker_items),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move),
        controller_id="b",
        position=(1, 0),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
    )
    battle.rng = SequenceRNG([20, 20, 20, 20])
    return battle, "a-1", "b-1"


def _build_battle_with_grid(move, *, attacker_items=None):
    battle, attacker_id, defender_id = _build_battle(move, attacker_items=attacker_items)
    battle.grid = GridState(width=8, height=8)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll, *, attacker_items=None):
    battle, attacker_id, defender_id = _build_battle(move, attacker_items=attacker_items)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    battle.rng = SequenceRNG([roll, 20, 20, 20])
    result = resolve_move_action(battle.rng, attacker, defender, move)
    result = dict(result)
    move_specials.handle_move_specials(
        battle=battle,
        attacker_id=attacker_id,
        attacker=attacker,
        defender_id=defender_id,
        defender=defender,
        move=move,
        result=result,
        damage_dealt=0,
        phase="pre_damage",
    )
    move_specials.handle_move_specials(
        battle=battle,
        attacker_id=attacker_id,
        attacker=attacker,
        defender_id=defender_id,
        defender=defender,
        move=move,
        result=result,
        damage_dealt=0,
        phase="post_damage",
    )
    return battle, result


class AuditBatch17MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_mh_adept_no_crash(self):
        move = MoveSpec(name="MH Adept", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)

    def test_mh_expert_no_crash(self):
        move = MoveSpec(name="MH Expert", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)

    def test_moonblast_lowers_spatk_15(self):
        move = MoveSpec(
            name="Moonblast",
            type="Fairy",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Moonblast lowers the target's Special Attack by -1 CS on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spatk"), -1)

    def test_multi_attack_type_from_item(self):
        move = MoveSpec(name="Multi-Attack", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move, attacker_items=[{"name": "Flame Plate"}])
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        last_event = battle.log[-1] if battle.log else {}
        context = last_event.get("context", {}) if isinstance(last_event, dict) else {}
        roll_options = context.get("roll_options", []) if isinstance(context, dict) else []
        self.assertIn("type:fire", roll_options)

    def test_multi_attack_ss_type_from_item(self):
        move = MoveSpec(name="Multi-Attack [SS]", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move, attacker_items=[{"name": "Flame Plate"}])
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        last_event = battle.log[-1] if battle.log else {}
        context = last_event.get("context", {}) if isinstance(last_event, dict) else {}
        roll_options = context.get("roll_options", []) if isinstance(context, dict) else []
        self.assertIn("type:fire", roll_options)

    def test_name_no_crash(self):
        move = MoveSpec(name="Name", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)

    def test_nasty_plot_spatk_plus2(self):
        move = MoveSpec(
            name="Nasty Plot",
            type="Dark",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Special Attack by +2 CS.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("spatk"), 2)

    def test_needle_arm_flinch_15(self):
        move = MoveSpec(
            name="Needle Arm",
            type="Grass",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            effects_text="Needle Arm Flinches the target on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))

    def test_night_slash_crit_18(self):
        move = MoveSpec(name="Night Slash", type="Dark", category="Physical", db=7, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_oh_adept_no_crash(self):
        move = MoveSpec(name="OH Adept", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)
