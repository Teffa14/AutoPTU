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
        phase="post_damage",
    )
    return battle, result


class AuditBatch3MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_bubble_slows_16(self):
        move = MoveSpec(name="Bubble", type="Water", category="Special", db=4, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 16)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spd"), -1)

    def test_bubblebeam_slows_18(self):
        move = MoveSpec(name="Bubblebeam", type="Water", category="Special", db=6, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 18)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spd"), -1)

    def test_bulk_up_raises_stats(self):
        move = MoveSpec(name="Bulk Up", type="Fighting", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        attacker = battle.pokemon["a-1"]
        self.assertEqual(attacker.combat_stages.get("atk"), 1)
        self.assertEqual(attacker.combat_stages.get("def"), 1)

    def test_bullseye_crit_16(self):
        move = MoveSpec(name="Bullseye", type="Normal", category="Physical", db=6, ac=2, range_kind="Ranged")
        _, result = _resolve_with_roll(move, 16)
        self.assertTrue(result.get("crit"))

    def test_captivate_spatk_drop(self):
        move = MoveSpec(name="Captivate", type="Normal", category="Status", db=0, ac=2, range_kind="Ranged")
        battle, attacker_id, defender_id = _build_battle(move)
        battle.pokemon[attacker_id].spec.gender = "Male"
        battle.pokemon[defender_id].spec.gender = "Female"
        battle.rng = SequenceRNG([20, 20, 20, 20])
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
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
            phase="post_damage",
        )
        self.assertEqual(defender.combat_stages.get("spatk"), -2)

    def test_charm_atk_drop(self):
        move = MoveSpec(name="Charm", type="Fairy", category="Status", db=0, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 20)
        defender = battle.pokemon["b-1"]
        self.assertEqual(defender.combat_stages.get("atk"), -2)

    def test_chatter_confuses_16(self):
        move = MoveSpec(name="Chatter", type="Flying", category="Special", db=4, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 16)
        self.assertTrue(battle.pokemon["b-1"].has_status("Confused"))

    def test_brutal_swing_base_damage(self):
        move = MoveSpec(name="Brutal Swing", type="Dark", category="Physical", db=6, ac=2, range_kind="Melee")
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

    def test_bullet_punch_base_damage(self):
        move = MoveSpec(name="Bullet Punch", type="Steel", category="Physical", db=6, ac=2, range_kind="Melee")
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

    def test_bullet_seed_base_damage(self):
        move = MoveSpec(name="Bullet Seed", type="Grass", category="Physical", db=4, ac=2, range_kind="Ranged")
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

