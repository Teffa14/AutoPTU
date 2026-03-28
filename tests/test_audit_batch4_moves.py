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


def _damage_from_move(move, *, defender_cs=None, defender_effects=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(move)
    defender = battle.pokemon[defender_id]
    if defender_cs:
        defender.combat_stages.update(defender_cs)
    if defender_effects:
        for entry in defender_effects:
            defender.add_temporary_effect(entry.get("kind", ""), **{k: v for k, v in entry.items() if k != "kind"})
    before = defender.hp
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=defender.position,
    )
    after = defender.hp
    return max(0, int(before or 0) - int(after or 0))


class AuditBatch4MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_cheap_shot_cannot_miss(self):
        move = MoveSpec(name="Cheap Shot", type="Normal", category="Physical", db=5, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_chip_away_ignores_defense_and_dr(self):
        move = MoveSpec(name="Chip Away", type="Normal", category="Physical", db=6, ac=2, range_kind="Melee")
        base = _damage_from_move(move)
        boosted = _damage_from_move(
            move,
            defender_cs={"def": 2, "spdef": 2},
            defender_effects=[{"kind": "damage_reduction", "category": "physical", "amount": 5}],
        )
        self.assertEqual(base, boosted)

    def test_close_combat_lowers_defenses(self):
        move = MoveSpec(name="Close Combat", type="Fighting", category="Physical", db=10, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        self.assertEqual(attacker.combat_stages.get("def"), -1)
        self.assertEqual(attacker.combat_stages.get("spdef"), -1)

    def test_comet_punch_base_damage(self):
        move = MoveSpec(name="Comet Punch", type="Normal", category="Physical", db=6, ac=2, range_kind="Melee")
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

    def test_confide_lowers_spatk(self):
        move = MoveSpec(name="Confide", type="Normal", category="Status", db=0, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 20)
        defender = battle.pokemon["b-1"]
        self.assertEqual(defender.combat_stages.get("spatk"), -1)

    def test_confusion_confuses_19(self):
        move = MoveSpec(name="Confusion", type="Psychic", category="Special", db=6, ac=2, range_kind="Ranged")
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Confused"))

    def test_crabhammer_crit_18(self):
        move = MoveSpec(name="Crabhammer", type="Water", category="Physical", db=8, ac=2, range_kind="Melee")
        _, result = _resolve_with_roll(move, 18)
        self.assertTrue(result.get("crit"))

    def test_cross_chop_crit_16(self):
        move = MoveSpec(name="Cross Chop", type="Fighting", category="Physical", db=9, ac=2, range_kind="Melee")
        _, result = _resolve_with_roll(move, 16)
        self.assertTrue(result.get("crit"))

    def test_cross_poison_poison_19(self):
        move = MoveSpec(name="Cross Poison", type="Poison", category="Physical", db=7, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Poisoned"))

    def test_crunch_lowers_defense_17(self):
        move = MoveSpec(name="Crunch", type="Dark", category="Physical", db=7, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 17)
        defender = battle.pokemon["b-1"]
        self.assertEqual(defender.combat_stages.get("def"), -1)

