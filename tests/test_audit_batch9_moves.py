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


class AuditBatch9MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_eternabeam_exhausts(self):
        move = MoveSpec(
            name="Eternabeam",
            type="Dragon",
            category="Special",
            db=12,
            ac=2,
            range_kind="Line",
            range_value=6,
            range_text="Line 6, Smite, Exhaust",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("exhaust_next_turn"))

    def test_ew_adept_no_crash(self):
        move = MoveSpec(name="EW Adept", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)

    def test_ew_expert_no_crash(self):
        move = MoveSpec(name="EW Expert", type="Normal", category="Status", db=0, ac=None, range_kind="Self")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("hit", result)

    def test_explosion_sets_hp_below_zero(self):
        move = MoveSpec(name="Explosion", type="Normal", category="Physical", db=15, ac=2, range_kind="Burst", range_value=2)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        max_hp = attacker.max_hp()
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        loss_event = None
        for event in reversed(battle.log):
            if event.get("effect") == "self_destruct":
                loss_event = event
                break
        self.assertIsNotNone(loss_event)
        self.assertGreaterEqual(loss_event.get("amount", 0), max_hp + max_hp // 2)

    def test_extrasensory_flinch_19(self):
        move = MoveSpec(
            name="Extrasensory",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=5,
            effects_text="Extrasensory Flinches the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))

    def test_extreme_speed_base_damage(self):
        move = MoveSpec(name="Extreme Speed", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee")
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

    def test_false_surrender_cannot_miss(self):
        move = MoveSpec(
            name="False Surrender",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            effects_text="False Surrender cannot Miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_feint_attack_cannot_miss(self):
        move = MoveSpec(
            name="Feint Attack",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="Feint Attack Cannot Miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))

    def test_fell_stinger_raises_attack_on_ko(self):
        move = MoveSpec(
            name="Fell Stinger",
            type="Bug",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="If the user successfully knocks out the target with Fell Stinger, raise the user's Attack by +2 CS.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.hp = 1
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=defender.position,
        )
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("atk"), 2)
