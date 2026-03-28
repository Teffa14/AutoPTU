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


def _pokemon_spec(name, move, *, types=None):
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=10,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=10,
        moves=[move],
        movement={"overland": 4},
        items=[{"name": "Potion"}],
    )


def _build_battle(move, *, attacker_types=None, defender_types=None):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, types=attacker_types),
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


def _build_battle_with_grid(move, *, attacker_types=None, defender_types=None):
    battle, attacker_id, defender_id = _build_battle(move, attacker_types=attacker_types, defender_types=defender_types)
    battle.grid = GridState(width=8, height=8)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll, *, attacker_types=None, defender_types=None):
    battle, attacker_id, defender_id = _build_battle(move, attacker_types=attacker_types, defender_types=defender_types)
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


class AuditBatch15MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_icy_wind_lowers_speed(self):
        move = MoveSpec(
            name="Icy Wind",
            type="Ice",
            category="Special",
            db=6,
            ac=2,
            range_kind="Cone",
            range_value=2,
            effects_text="All Legal Targets have their Speed lowered 1 Combat Stage.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spd"), -1)

    def test_incinerate_drops_item(self):
        move = MoveSpec(name="Incinerate", type="Fire", category="Special", db=6, ac=2, range_kind="Line", range_value=3)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.spec.items)
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertFalse(defender.spec.items)

    def test_infernal_parade_burn_17(self):
        move = MoveSpec(
            name="Infernal Parade",
            type="Ghost",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=8,
            effects_text="Legal targets hit by Infernal Parade are Burned on a 17+.",
        )
        battle, result = _resolve_with_roll(move, 17, attacker_types=["Ghost"], defender_types=["Psychic"])
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_infernal_parade_db_boost(self):
        move = MoveSpec(name="Infernal Parade", type="Ghost", category="Special", db=8, ac=2, range_kind="Ranged", range_value=8)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 12)

    def test_infestation_vortex(self):
        move = MoveSpec(name="Infestation", type="Bug", category="Special", db=4, ac=2, range_kind="Ranged", range_value=3)
        battle, result = _resolve_with_roll(move, 20)
        self.assertTrue(battle.pokemon["b-1"].has_status("Vortex"))

    def test_ingrain_applies_status(self):
        move = MoveSpec(name="Ingrain", type="Grass", category="Status", db=0, ac=None, range_kind="Self")
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.has_status("Ingrain"))

    def test_jaw_lock_grapple(self):
        move = MoveSpec(name="Jaw Lock", type="Dark", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Grappled") or defender.has_status("Grabbed"))

    def test_karate_chop_crit_17(self):
        move = MoveSpec(name="Karate Chop", type="Fighting", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 17)
        self.assertTrue(result.get("crit"))

    def test_knock_off_drops_item(self):
        move = MoveSpec(name="Knock Off", type="Dark", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.spec.items)
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertFalse(defender.spec.items)

    def test_leaf_blade_crit_18(self):
        move = MoveSpec(name="Leaf Blade", type="Grass", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_leech_life_drains(self):
        move = MoveSpec(name="Leech Life", type="Bug", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(attacker.hp, before)
