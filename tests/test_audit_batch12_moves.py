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


def _pokemon_spec(name, move, *, spd=10):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=spd,
        moves=[move],
        movement={"overland": 4},
    )


def _build_battle(move, *, attacker_spd=10, defender_spd=10):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, spd=attacker_spd),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, spd=defender_spd),
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


def _build_battle_with_grid(move, *, attacker_spd=10, defender_spd=10):
    battle, attacker_id, defender_id = _build_battle(move, attacker_spd=attacker_spd, defender_spd=defender_spd)
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
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0)), battle


def _effective_db_from_move(move, *, attacker_spd=10, defender_spd=10):
    battle, attacker_id, defender_id = _build_battle_with_grid(move, attacker_spd=attacker_spd, defender_spd=defender_spd)
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=battle.pokemon[defender_id].position,
    )
    for event in reversed(battle.log):
        if "effective_db" in event:
            return int(event.get("effective_db") or 0), battle
    return 0, battle


class AuditBatch12MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_gear_grind_double_strike_range(self):
        move = MoveSpec(name="Gear Grind", type="Steel", category="Physical", db=8, ac=2, range_kind="Melee", range_text="Melee, 1 Target, Double Strike")
        self.assertEqual(strike_count(move), 2)

    def test_giga_drain_drains(self):
        move = MoveSpec(name="Giga Drain", type="Grass", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        self.assertGreater(attacker.hp, before)

    def test_grass_whistle_sleeps(self):
        move = MoveSpec(
            name="Grass Whistle",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="The target falls Asleep.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertTrue(battle.pokemon["b-1"].has_status("Sleep"))

    def test_grav_apple_lowers_def(self):
        move = MoveSpec(
            name="Grav Apple",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="The target's Defense is lowered by 1 CS.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("def"), -1)

    def test_growth_raises_attack_and_spatk(self):
        move = MoveSpec(
            name="Growth",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Attack and Special Attack by +1 CS each.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 1)
        self.assertEqual(attacker.combat_stages.get("spatk"), 1)

    def test_growth_sunny_doubles(self):
        move = MoveSpec(
            name="Growth",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Attack and Special Attack by +1 CS each. If it is Sunny, double the amount of Combat Stages gained.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.weather = "Sunny"
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 2)
        self.assertEqual(attacker.combat_stages.get("spatk"), 2)

    def test_gunk_shot_poison_15(self):
        move = MoveSpec(
            name="Gunk Shot",
            type="Poison",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Gunk Shot Poisons the target on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Poisoned"))

    def test_gyro_ball_bonus_db(self):
        move = MoveSpec(name="Gyro Ball", type="Steel", category="Physical", db=4, ac=2, range_kind="Ranged", range_value=6)
        base_db, _ = _effective_db_from_move(move, attacker_spd=10, defender_spd=10)
        boosted_db, _ = _effective_db_from_move(move, attacker_spd=5, defender_spd=12)
        self.assertGreater(boosted_db, base_db)

    def test_harden_raises_def(self):
        move = MoveSpec(
            name="Harden",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Defense by +1 CS.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("def"), 1)

    def test_head_charge_push_and_recoil(self):
        move = MoveSpec(
            name="Head Charge",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Push, Recoil 1/3",
            effects_text="The target is Pushed back 2 meters.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        before_pos = defender.position
        before_hp = attacker.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertNotEqual(defender.position, before_pos)
        self.assertLess(attacker.hp, before_hp)

    def test_head_smash_push_and_recoil(self):
        move = MoveSpec(
            name="Head Smash",
            type="Rock",
            category="Physical",
            db=15,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Dash, Push, Recoil 1/3",
            effects_text="The target is pushed 2 meters.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        before_pos = defender.position
        before_hp = attacker.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertNotEqual(defender.position, before_pos)
        self.assertLess(attacker.hp, before_hp)
