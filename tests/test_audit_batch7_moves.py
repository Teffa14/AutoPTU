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
    battle.grid = GridState(width=10, height=10)
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


def _damage_from_move(move, *, attacker_hp=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(move)
    attacker = battle.pokemon[attacker_id]
    defender = battle.pokemon[defender_id]
    if attacker_hp is not None:
        attacker.hp = attacker_hp
    before = defender.hp
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0)), battle


class AuditBatch7MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_double_iron_bash_flinch_15(self):
        move = MoveSpec(
            name="Double Iron Bash",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Double Strike",
            effects_text="Double Iron Bash Flinches the targets on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))
        self.assertEqual(strike_count(move), 2)

    def test_double_kick_double_strike_range(self):
        move = MoveSpec(
            name="Double Kick",
            type="Fighting",
            category="Physical",
            db=5,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Double Strike",
        )
        self.assertEqual(strike_count(move), 2)

    def test_dragon_claw_base_damage(self):
        move = MoveSpec(name="Dragon Claw", type="Dragon", category="Physical", db=8, ac=2, range_kind="Melee")
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

    def test_dragon_energy_db_reduces_when_low_hp(self):
        move = MoveSpec(
            name="Dragon Energy",
            type="Dragon",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            range_text="Cone 3 or Line 8",
            effects_text="For each 10% of HP the user is missing, Dragon Energy's Damage Base is reduced by 1.",
        )
        damage_full, battle_full = _damage_from_move(move)
        max_hp = battle_full.pokemon["a-1"].max_hp()
        damage_low, _ = _damage_from_move(move, attacker_hp=max_hp // 2)
        self.assertLess(damage_low, damage_full)

    def test_dragon_pulse_base_damage(self):
        move = MoveSpec(name="Dragon Pulse", type="Dragon", category="Special", db=8, ac=2, range_kind="Ranged", range_value=8)
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

    def test_dragon_rush_flinch_17_and_push(self):
        move = MoveSpec(
            name="Dragon Rush",
            type="Dragon",
            category="Physical",
            db=9,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Dash, Push, Smite",
            effects_text="The target is Pushed 3 Meters. Dragon Rush Flinches the target on 17+.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before_pos = defender.position
        battle.rng = SequenceRNG([17, 20, 20, 20])
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertTrue(defender.has_status("Flinched"))
        self.assertNotEqual(defender.position, before_pos)

    def test_drain_punch_drains(self):
        move = MoveSpec(name="Drain Punch", type="Fighting", category="Physical", db=6, ac=2, range_kind="Melee")
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

    def test_draining_kiss_drains(self):
        move = MoveSpec(name="Draining Kiss", type="Fairy", category="Special", db=6, ac=2, range_kind="Melee")
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

    def test_dream_eater_requires_sleep_and_drains(self):
        move = MoveSpec(name="Dream Eater", type="Psychic", category="Special", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=defender,
            status="Sleep",
            effect="status",
            description="Test sleep",
            roll=20,
        )
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        self.assertGreater(attacker.hp, before)

    def test_drill_peck_base_damage(self):
        move = MoveSpec(name="Drill Peck", type="Flying", category="Physical", db=8, ac=2, range_kind="Melee")
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
