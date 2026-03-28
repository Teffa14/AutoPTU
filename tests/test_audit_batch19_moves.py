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


class AuditBatch19MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_power_gem_base_damage(self):
        move = MoveSpec(name="Power Gem", type="Rock", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)

    def test_power_trip_db_scales(self):
        move = MoveSpec(name="Power Trip", type="Dark", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        attacker.combat_stages["atk"] = 2
        attacker.combat_stages["def"] = 1
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 10)

    def test_precipice_blades_smite(self):
        move = MoveSpec(
            name="Precipice Blades",
            type="Ground",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Burst",
            range_value=1,
            range_text="Burst 1, Smite",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        smite_events = [event for event in battle.log if event.get("type") == "smite"]
        self.assertTrue(smite_events)

    def test_prismatic_laser_exhausts(self):
        move = MoveSpec(
            name="Prismatic Laser",
            type="Psychic",
            category="Special",
            db=13,
            ac=2,
            range_kind="Line",
            range_value=8,
            range_text="Line 8, Smite, Exhaust",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("exhaust_next_turn"))

    def test_psych_up_cannot_miss(self):
        move = MoveSpec(
            name="Psych Up",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Psych Up cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_psycho_boost_lowers_spatk(self):
        move = MoveSpec(
            name="Psycho Boost",
            type="Psychic",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Lower the user's Special Attack by -2 Combat Stages after damage is resolved.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("spatk"), -2)

    def test_psycho_cut_crit_18(self):
        move = MoveSpec(name="Psycho Cut", type="Psychic", category="Physical", db=7, ac=2, range_kind="Ranged", range_value=6)
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_punishment_db_scales(self):
        move = MoveSpec(name="Punishment", type="Dark", category="Physical", db=4, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.combat_stages["atk"] = 2
        defender.combat_stages["def"] = 1
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 7)

    def test_razor_leaf_crit_18(self):
        move = MoveSpec(name="Razor Leaf", type="Grass", category="Physical", db=6, ac=2, range_kind="Cone", range_value=2)
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_rock_throw_base_damage(self):
        move = MoveSpec(name="Rock Throw", type="Rock", category="Physical", db=5, ac=2, range_kind="Ranged", range_value=6)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)
