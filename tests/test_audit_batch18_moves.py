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


def _pokemon_spec(name, move, *, atk=12, spatk=12, types=None):
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=10,
        atk=atk,
        defense=10,
        spatk=spatk,
        spdef=10,
        spd=10,
        moves=[move],
        movement={"overland": 4},
    )


def _build_battle(move, *, attacker_atk=12, attacker_spatk=12, defender_types=None):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, atk=attacker_atk, spatk=attacker_spatk),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, types=defender_types),
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


def _build_battle_with_grid(move, *, attacker_atk=12, attacker_spatk=12, defender_types=None):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_atk=attacker_atk,
        attacker_spatk=attacker_spatk,
        defender_types=defender_types,
    )
    battle.grid = GridState(width=8, height=8)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll, *, attacker_atk=12, attacker_spatk=12, defender_types=None):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_atk=attacker_atk,
        attacker_spatk=attacker_spatk,
        defender_types=defender_types,
    )
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


class AuditBatch18MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_origin_pulse_smite(self):
        move = MoveSpec(
            name="Origin Pulse",
            type="Water",
            category="Special",
            db=12,
            ac=2,
            range_kind="CloseBlast",
            range_value=3,
            range_text="Close Blast 3, Smite",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        smite_events = [event for event in battle.log if event.get("type") == "smite"]
        self.assertTrue(smite_events)

    def test_overdrive_base_damage(self):
        move = MoveSpec(name="Overdrive", type="Electric", category="Special", db=8, ac=2, range_kind="Cone", range_value=2)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)

    def test_overheat_lowers_spatk(self):
        move = MoveSpec(
            name="Overheat",
            type="Fire",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Lower the user's Special Attack 2 Combat Stages after damage.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("spatk"), -2)

    def test_parabolic_charge_drains(self):
        move = MoveSpec(name="Parabolic Charge", type="Electric", category="Special", db=6, ac=2, range_kind="Cone", range_value=2)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(attacker.hp, before)

    def test_parabolic_charge_sm_drains(self):
        move = MoveSpec(name="Parabolic Charge [SM]", type="Electric", category="Special", db=6, ac=2, range_kind="Cone", range_value=2)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(attacker.hp, before)

    def test_peck_base_damage(self):
        move = MoveSpec(name="Peck", type="Flying", category="Physical", db=4, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)

    def test_petal_blizzard_base_damage(self):
        move = MoveSpec(name="Petal Blizzard", type="Grass", category="Physical", db=8, ac=2, range_kind="Burst", range_value=1)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)

    def test_photon_geyser_uses_highest_stat(self):
        move = MoveSpec(name="Photon Geyser", type="Psychic", category="Special", db=10, ac=2, range_kind="Burst", range_value=2)
        battle, result = _resolve_with_roll(move, 20, attacker_atk=18, attacker_spatk=6)
        self.assertEqual(result.get("attack_value"), 18)

    def test_pin_missile_five_strike_range(self):
        move = MoveSpec(name="Pin Missile", type="Bug", category="Physical", db=5, ac=2, range_kind="Ranged", range_value=6, range_text="6, 1 Target, Five Strike")
        self.assertEqual(strike_count(move), 5)

    def test_pound_base_damage(self):
        move = MoveSpec(name="Pound", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)
