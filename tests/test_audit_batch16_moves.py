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
    battle.grid = GridState(width=8, height=8)
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


def _damage_from_move(move):
    battle, attacker_id, defender_id = _build_battle_with_grid(move)
    defender = battle.pokemon[defender_id]
    before = defender.hp
    battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0)), battle


def _effective_db_from_move(move):
    battle, attacker_id, defender_id = _build_battle_with_grid(move)
    battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
    for event in reversed(battle.log):
        if "effective_db" in event:
            return int(event.get("effective_db") or 0), battle
    return 0, battle


class AuditBatch16MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_leaf_tornado_accuracy_drop_15(self):
        move = MoveSpec(
            name="Leaf Tornado",
            type="Grass",
            category="Special",
            db=7,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="On 15+, all legal targets have their Accuracy lowered by -1.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("accuracy"), -1)

    def test_light_screen_applies_status(self):
        move = MoveSpec(name="Light Screen", type="Psychic", category="Status", db=0, ac=None, range_kind="Blessing")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.has_status("Light Screen"))

    def test_low_sweep_lowers_speed(self):
        move = MoveSpec(
            name="Low Sweep",
            type="Fighting",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="Lower the target's Speed by -1 CS.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spd"), -1)

    def test_luster_purge_spdef_even(self):
        move = MoveSpec(
            name="Luster Purge",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Luster Purge lowers the target's Special Defense by -1 CS on an Even-Numbered Roll.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spdef"), -1)

    def test_magical_leaf_cannot_miss(self):
        move = MoveSpec(
            name="Magical Leaf",
            type="Grass",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Magical Leaf cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_magnet_bomb_cannot_miss(self):
        move = MoveSpec(
            name="Magnet Bomb",
            type="Steel",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Magnet Bomb cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_magnitude_db_rolls(self):
        move = MoveSpec(name="Magnitude", type="Ground", category="Physical", db=0, ac=2, range_kind="Burst", range_value=2)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.rng = SequenceRNG([6, 20, 20, 20])
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 11)

    def test_mega_drain_drains(self):
        move = MoveSpec(name="Mega Drain", type="Grass", category="Special", db=6, ac=2, range_kind="Ranged", range_value=6)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(attacker.hp, before)

    def test_metal_claw_attack_boost_18(self):
        move = MoveSpec(
            name="Metal Claw",
            type="Steel",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            effects_text="Raise the user's Attack by +1 CS on 18+.",
        )
        battle, result = _resolve_with_roll(move, 18)
        self.assertEqual(battle.pokemon["a-1"].combat_stages.get("atk"), 1)

    def test_meteor_mash_attack_boost_15(self):
        move = MoveSpec(
            name="Meteor Mash",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            effects_text="Raise the user's Attack by +1 CS on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertEqual(battle.pokemon["a-1"].combat_stages.get("atk"), 1)
