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


class AuditBatch21MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_shadow_punch_cannot_miss(self):
        move = MoveSpec(
            name="Shadow Punch",
            type="Ghost",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Shadow Punch cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_sharpen_raises_attack(self):
        move = MoveSpec(
            name="Sharpen",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Attack by +1 CS.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 1)

    def test_shell_side_arm_uses_highest_stat(self):
        move = MoveSpec(name="Shell Side Arm", type="Poison", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6)
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("attack_value", result)

    def test_shell_smash_stat_changes(self):
        move = MoveSpec(
            name="Shell Smash",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Attack, Special Attack, and Speed by +2 CS each. Lower the user's Defense and Special Defense by -1 CS each.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 2)
        self.assertEqual(attacker.combat_stages.get("spatk"), 2)
        self.assertEqual(attacker.combat_stages.get("spd"), 2)
        self.assertEqual(attacker.combat_stages.get("def"), -1)
        self.assertEqual(attacker.combat_stages.get("spdef"), -1)

    def test_shock_wave_cannot_miss(self):
        move = MoveSpec(
            name="Shock Wave",
            type="Electric",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Shock Wave cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_skull_bash_setup_defense(self):
        move = MoveSpec(
            name="Skull Bash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Dash, Push, Set-Up",
            effects_text="Set-Up Effect: Raise the user's Defense by +1 CS.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("def"), 1)

    def test_smart_strike_cannot_miss(self):
        move = MoveSpec(
            name="Smart Strike",
            type="Steel",
            category="Physical",
            db=7,
            ac=2,
            range_kind="Melee",
            effects_text="Smart Strike cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_smog_poisons_even_roll(self):
        move = MoveSpec(
            name="Smog",
            type="Poison",
            category="Special",
            db=4,
            ac=2,
            range_kind="Line",
            range_value=2,
            effects_text="Smog Poisons all legal targets on an Even-Numbered Roll.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertTrue(battle.pokemon["b-1"].has_status("Poisoned"))

    def test_snore_flinch_15(self):
        move = MoveSpec(
            name="Snore",
            type="Normal",
            category="Special",
            db=6,
            ac=2,
            range_kind="Burst",
            range_value=1,
            effects_text="Snore Flinches all legal targets on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))

    def test_spike_cannon_five_strike_range(self):
        move = MoveSpec(name="Spike Cannon", type="Normal", category="Physical", db=5, ac=2, range_kind="Ranged", range_value=6, range_text="6, 1 Target, Five Strike")
        self.assertEqual(strike_count(move), 5)
