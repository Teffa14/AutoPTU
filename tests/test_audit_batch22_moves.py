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


class AuditBatch22MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_steam_eruption_burn_15(self):
        move = MoveSpec(
            name="Steam Eruption",
            type="Water",
            category="Special",
            db=11,
            ac=2,
            range_kind="CloseBlast",
            range_value=3,
            effects_text="Steam Eruption Burns all legal targets on a 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_tackle_pushes(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Dash, Push",
            effects_text="The target is Pushed 2 Meters.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.position
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertNotEqual(defender.position, before)

    def test_tackle_sm_pushes(self):
        move = MoveSpec(
            name="Tackle [SM]",
            type="Normal",
            category="Physical",
            db=4,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Dash, Push",
            effects_text="The target is Pushed 2 Meters.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.position
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertNotEqual(defender.position, before)

    def test_tail_slap_five_strike(self):
        move = MoveSpec(name="Tail Slap", type="Normal", category="Physical", db=3, ac=2, range_kind="Melee", range_text="Melee, 1 Target, Five Strike")
        self.assertEqual(strike_count(move), 5)

    def test_twineedle_poison_18(self):
        move = MoveSpec(
            name="Twineedle",
            type="Bug",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="Twineedle Poisons the target on 18+.",
        )
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(battle.pokemon["b-1"].has_status("Poisoned"))

    def test_venom_drench_lowers_poisoned_stats(self):
        move = MoveSpec(
            name="Venom Drench",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Cone",
            range_value=2,
            effects_text="All Poisoned targets have their Attack, Special Attack, and Speed lowered by -1 CS. Venom Drench cannot miss.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Poisoned"})
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(defender.combat_stages.get("atk"), -1)
        self.assertEqual(defender.combat_stages.get("spatk"), -1)
        self.assertEqual(defender.combat_stages.get("spd"), -1)

    def test_volt_tackle_paralyze_19(self):
        move = MoveSpec(
            name="Volt Tackle",
            type="Electric",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            effects_text="Volt Tackle Paralyzes the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Paralyzed"))

    def test_water_shuriken_five_strike(self):
        move = MoveSpec(name="Water Shuriken", type="Water", category="Physical", db=2, ac=2, range_kind="Ranged", range_value=6, range_text="6, 1 Target, Five Strike, Priority")
        self.assertEqual(strike_count(move), 5)

    def test_water_shuriken_sm_five_strike(self):
        move = MoveSpec(name="Water Shuriken [SM]", type="Water", category="Physical", db=2, ac=2, range_kind="Ranged", range_value=6, range_text="6, 1 Target, Five Strike, Priority")
        self.assertEqual(strike_count(move), 5)

    def test_wave_crash_recoil(self):
        move = MoveSpec(
            name="Wave Crash",
            type="Water",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Priority, Recoil 1/4",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(attacker.hp, before)
