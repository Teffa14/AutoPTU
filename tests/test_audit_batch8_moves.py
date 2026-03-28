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


def _pokemon_spec(name, move, *, spd=10, hp_stat=10):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=hp_stat,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=spd,
        moves=[move],
        movement={"overland": 4},
    )


def _build_battle(move, *, attacker_spd=10, defender_spd=10, attacker_hp_stat=10, defender_hp_stat=10):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, spd=attacker_spd, hp_stat=attacker_hp_stat),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, spd=defender_spd, hp_stat=defender_hp_stat),
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


def _build_battle_with_grid(
    move,
    *,
    attacker_spd=10,
    defender_spd=10,
    attacker_hp_stat=10,
    defender_hp_stat=10,
):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_spd=attacker_spd,
        defender_spd=defender_spd,
        attacker_hp_stat=attacker_hp_stat,
        defender_hp_stat=defender_hp_stat,
    )
    battle.grid = GridState(width=10, height=10)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll, *, attacker_spd=10, defender_spd=10):
    battle, attacker_id, defender_id = _build_battle(move, attacker_spd=attacker_spd, defender_spd=defender_spd)
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


def _damage_from_move(
    move,
    *,
    attacker_hp=None,
    defender_cs=None,
    attacker_spd=10,
    defender_spd=10,
    attacker_hp_stat=10,
    defender_hp_stat=10,
):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_spd=attacker_spd,
        defender_spd=defender_spd,
        attacker_hp_stat=attacker_hp_stat,
        defender_hp_stat=defender_hp_stat,
    )
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    if attacker_hp is not None:
        attacker.hp = attacker_hp
    if defender_cs:
        defender.combat_stages.update(defender_cs)
    before = defender.hp
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0)), battle


def _effective_db_from_move(move, *, attacker_hp=None, defender_cs=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(move)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    if attacker_hp is not None:
        attacker.hp = attacker_hp
    if defender_cs:
        defender.combat_stages.update(defender_cs)
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    for event in reversed(battle.log):
        if "effective_db" in event:
            return int(event.get("effective_db") or 0), battle
    return 0, battle


def _calc_damage(move, *, attacker_spd=10, defender_spd=10):
    battle, attacker_id, defender_id = _build_battle(move, attacker_spd=attacker_spd, defender_spd=defender_spd)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    result = resolve_move_action(battle.rng, attacker, defender, move)
    return int(result.get("damage") or 0)


class AuditBatch8MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_drill_run_crit_18(self):
        move = MoveSpec(name="Drill Run", type="Ground", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_drum_beating_lowers_speed(self):
        move = MoveSpec(
            name="Drum Beating",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=4,
            effects_text="The target's Speed is lowered by 1 CS.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spd"), -1)

    def test_dual_chop_double_strike_range(self):
        move = MoveSpec(
            name="Dual Chop",
            type="Dragon",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Doublestrike",
        )
        self.assertEqual(strike_count(move), 2)

    def test_dual_wingbeat_double_strike_range(self):
        move = MoveSpec(
            name="Dual Wingbeat",
            type="Flying",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Double Strike",
        )
        self.assertEqual(strike_count(move), 2)

    def test_dynamax_cannon_db_scales_positive_cs(self):
        move = MoveSpec(name="Dynamax Cannon", type="Dragon", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6)
        base_db, _ = _effective_db_from_move(move)
        boosted_db, _ = _effective_db_from_move(move, defender_cs={"def": 2, "spdef": 1})
        self.assertGreater(boosted_db, base_db)

    def test_echoed_voice_db_boosts_after_rounds(self):
        move = MoveSpec(name="Echoed Voice", type="Normal", category="Special", db=4, ac=2, range_kind="Ranged", range_value=3)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.round = 3
        battle.echoed_voice_rounds = [1, 2]
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 12)

    def test_eerie_impulse_lowers_spatk(self):
        move = MoveSpec(
            name="Eerie Impulse",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Lower the target's Special Attack by -2 CS.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spatk"), -2)

    def test_egg_bomb_base_damage(self):
        move = MoveSpec(name="Egg Bomb", type="Normal", category="Physical", db=8, ac=2, range_kind="Ranged", range_value=5)
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

    def test_electro_ball_uses_speed_stats(self):
        move = MoveSpec(name="Electro Ball", type="Electric", category="Special", db=6, ac=2, range_kind="Ranged", range_value=10)
        damage_low = _calc_damage(move, attacker_spd=6, defender_spd=10)
        damage_high = _calc_damage(move, attacker_spd=20, defender_spd=10)
        self.assertGreater(damage_high, damage_low)

    def test_eruption_db_reduces_when_low_hp(self):
        move = MoveSpec(name="Eruption", type="Fire", category="Special", db=12, ac=2, range_kind="Burst", range_value=1)
        base_db, battle_full = _effective_db_from_move(move)
        max_hp = battle_full.pokemon["a-1"].max_hp()
        low_db, _ = _effective_db_from_move(move, attacker_hp=max_hp // 2)
        self.assertLess(low_db, base_db)
