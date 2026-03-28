import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.calculations import resolve_move_action
from auto_ptu.rules.hooks import move_specials
from auto_ptu.rules.move_traits import strike_count


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(name, move):
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
    )


def _build_battle(move):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move),
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


def _build_battle_with_grid(move):
    battle, attacker_id, defender_id = _build_battle(move)
    battle.grid = GridState(width=6, height=6)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll):
    battle, attacker_id, defender_id = _build_battle(move)
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


class AuditBatch6MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_disarming_voice_cannot_miss(self):
        move = MoveSpec(
            name="Disarming Voice",
            type="Fairy",
            category="Special",
            db=4,
            ac=2,
            range_kind="Burst",
            range_value=3,
            effects_text="Disarming Voice cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_discharge_paralyze_15(self):
        move = MoveSpec(name="Discharge", type="Electric", category="Special", db=8, ac=2, range_kind="Burst", range_value=2)
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Paralyzed"))

    def test_dizzy_punch_confuse_17(self):
        move = MoveSpec(
            name="Dizzy Punch",
            type="Normal",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            effects_text="Dizzy Punch Confuses the target on 17+.",
        )
        battle, result = _resolve_with_roll(move, 17)
        self.assertTrue(battle.pokemon["b-1"].has_status("Confused"))

    def test_double_hit_double_strike_range(self):
        move = MoveSpec(
            name="Double Hit",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Double Strike",
        )
        self.assertEqual(strike_count(move), 2)

    def test_double_slap_five_strike_range(self):
        move = MoveSpec(
            name="Double Slap",
            type="Normal",
            category="Physical",
            db=3,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Five Strike",
        )
        self.assertEqual(strike_count(move), 5)

    def test_double_swipe_double_strike_range(self):
        move = MoveSpec(
            name="Double Swipe",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="WR, 2 Targets; or WR, 1 Target, Double Strike",
        )
        self.assertEqual(strike_count(move), 2)

    def test_double_team_grants_charges(self):
        move = MoveSpec(name="Double Team", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        attacker = battle.pokemon["a-1"]
        effects = attacker.get_temporary_effects("double_team")
        self.assertTrue(effects)
        self.assertEqual(effects[0].get("charges"), 3)

    def test_draco_meteor_spatk_drop(self):
        move = MoveSpec(name="Draco Meteor", type="Dragon", category="Special", db=13, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 20)
        attacker = battle.pokemon["a-1"]
        self.assertEqual(attacker.combat_stages.get("spatk"), -2)

    def test_dragon_darts_double_strike_range(self):
        move = MoveSpec(
            name="Dragon Darts",
            type="Dragon",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="6, 1 Target, Double Strike; or 6, 2 Targets",
        )
        self.assertEqual(strike_count(move), 2)

    def test_dragon_hammer_base_damage(self):
        move = MoveSpec(name="Dragon Hammer", type="Dragon", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertLess(defender.hp, before)
