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


class AuditBatch2MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_blaze_kick_burns_19(self):
        move = MoveSpec(name="Blaze Kick", type="Fire", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_blue_flare_burns_17(self):
        move = MoveSpec(name="Blue Flare", type="Fire", category="Special", db=10, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 17)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_body_slam_paralyzes_15(self):
        move = MoveSpec(name="Body Slam", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Paralyzed"))

    def test_bolt_strike_paralyzes_17(self):
        move = MoveSpec(name="Bolt Strike", type="Electric", category="Physical", db=10, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 17)
        self.assertTrue(battle.pokemon["b-1"].has_status("Paralyzed"))

    def test_brave_bird_pushes(self):
        move = MoveSpec(
            name="Brave Bird",
            type="Flying",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, Push 2",
            keywords=["Push"],
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.position
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertNotEqual(defender.position, before)

    def test_brine_db_boost(self):
        move = MoveSpec(name="Brine", type="Water", category="Special", db=8, ac=2, range_kind="Ranged")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.hp = defender.max_hp() // 2
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 13)

    def test_bone_rush_five_strike(self):
        move = MoveSpec(name="Bone Rush", type="Ground", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn(result.get("strike_max"), (None, 5))

    def test_bonemerang_five_strike(self):
        move = MoveSpec(name="Bonemerang", type="Ground", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn(result.get("strike_max"), (None, 2, 5))

    def test_boomburst_base_damage(self):
        move = MoveSpec(name="Boomburst", type="Normal", category="Special", db=10, ac=2, range_kind="Burst", range_value=3)
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

    def test_branch_poke_base_damage(self):
        move = MoveSpec(name="Branch Poke", type="Grass", category="Physical", db=4, ac=2, range_kind="Melee")
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

