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
        phase="pre_damage",
    )
    return result


class AuditBatch1MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_absorb_drains(self):
        move = MoveSpec(name="Absorb", type="Grass", category="Special", db=4, ac=2, range_kind="Ranged")
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

    def test_aerial_ace_cannot_miss(self):
        move = MoveSpec(name="Aerial Ace", type="Flying", category="Physical", db=6, ac=2, range_kind="Melee")
        result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_aura_sphere_cannot_miss(self):
        move = MoveSpec(name="Aura Sphere", type="Fighting", category="Special", db=8, ac=2, range_kind="Ranged")
        result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_aeroblast_even_roll_crit(self):
        move = MoveSpec(name="Aeroblast", type="Flying", category="Special", db=8, ac=2, range_kind="Ranged")
        result = _resolve_with_roll(move, 20)
        self.assertTrue(result.get("crit"))

    def test_attack_order_crit_18(self):
        move = MoveSpec(name="Attack Order", type="Bug", category="Physical", db=8, ac=2, range_kind="Melee")
        result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_behemoth_bash_scales(self):
        move = MoveSpec(name="Behemoth Bash", type="Steel", category="Physical", db=10, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.combat_stages["atk"] = 2
        defender.combat_stages["def"] = 1
        before = defender.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        after = defender.hp
        self.assertLess(after, before)

    def test_behemoth_blade_scales(self):
        move = MoveSpec(name="Behemoth Blade", type="Steel", category="Physical", db=10, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.combat_stages["atk"] = 2
        defender.combat_stages["def"] = 1
        before = defender.hp
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        after = defender.hp
        self.assertLess(after, before)

    def test_blast_burn_exhausts(self):
        move = MoveSpec(
            name="Blast Burn",
            type="Fire",
            category="Special",
            db=15,
            ac=4,
            range_kind="CloseBlast",
            range_value=3,
            range_text="Close Blast 3, Smite, Exhaust",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        self.assertTrue(attacker.get_temporary_effects("exhaust_next_turn"))

