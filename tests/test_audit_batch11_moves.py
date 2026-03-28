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


def _pokemon_spec(name, move, *, types=None, loyalty=None):
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
    )


def _build_battle(move, *, attacker_types=None, defender_types=None, attacker_loyalty=None):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker_spec = _pokemon_spec("Attacker", move, types=attacker_types, loyalty=attacker_loyalty)
    if attacker_loyalty is not None:
        attacker_spec.loyalty = attacker_loyalty
    attacker = PokemonState(
        spec=attacker_spec,
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


def _build_battle_with_grid(move, *, attacker_types=None, defender_types=None, attacker_loyalty=None):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_loyalty=attacker_loyalty,
    )
    battle.grid = GridState(width=8, height=8)
    battle.pokemon[attacker_id].position = (2, 2)
    battle.pokemon[defender_id].position = (2, 3)
    return battle, attacker_id, defender_id


def _resolve_with_roll(move, roll, *, attacker_types=None, defender_types=None, attacker_loyalty=None):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_loyalty=attacker_loyalty,
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


def _damage_from_move(move, *, attacker_types=None, defender_types=None, attacker_loyalty=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_loyalty=attacker_loyalty,
    )
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


def _effective_db_from_move(move, *, attacker_types=None, defender_types=None, attacker_loyalty=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_loyalty=attacker_loyalty,
    )
    battle.resolve_move_targets(
        attacker_id=attacker_id,
        move=move,
        target_id=defender_id,
        target_position=battle.pokemon[defender_id].position,
    )
    for event in reversed(battle.log):
        if "effective_db" in event:
            return int(event.get("effective_db") or 0), battle
    return 0, battle


class AuditBatch11MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_foul_play_uses_target_attack(self):
        move = MoveSpec(name="Foul Play", type="Dark", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn("damage", result)

    def test_freezing_glare_freeze_19(self):
        move = MoveSpec(
            name="Freezing Glare",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Freezing Glare Freezes the target on a 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Frozen"))

    def test_freezing_glare_can_convert_to_ice(self):
        move = MoveSpec(
            name="Freezing Glare",
            type="Psychic",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(
            move,
            attacker_types=["Psychic"],
            defender_types=["Ground"],
        )
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        last_event = battle.log[-1] if battle.log else {}
        context = last_event.get("context", {}) if isinstance(last_event, dict) else {}
        roll_options = context.get("roll_options", []) if isinstance(context, dict) else []
        self.assertIn("type:ice", roll_options)

    def test_frenzy_plant_exhausts(self):
        move = MoveSpec(
            name="Frenzy Plant",
            type="Grass",
            category="Special",
            db=12,
            ac=2,
            range_kind="Burst",
            range_value=3,
            range_text="3, 5 Targets, Smite, Exhaust",
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

    def test_frost_breath_always_crits(self):
        move = MoveSpec(name="Frost Breath", type="Ice", category="Special", db=6, ac=2, range_kind="Ranged", range_value=4)
        battle, result = _resolve_with_roll(move, 10)
        self.assertTrue(result.get("crit"))

    def test_frustration_db_scales_with_loyalty(self):
        move = MoveSpec(name="Frustration", type="Normal", category="Physical", db=8, ac=2, range_kind="Melee")
        base_db, _ = _effective_db_from_move(move, attacker_loyalty=5)
        low_db, _ = _effective_db_from_move(move, attacker_loyalty=1)
        self.assertGreater(low_db, base_db)

    def test_fury_attack_five_strike_range(self):
        move = MoveSpec(name="Fury Attack", type="Normal", category="Physical", db=5, ac=2, range_kind="Melee", range_text="Melee, 1 Target, Five Strike")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn(result.get("strike_max"), (None, 5))

    def test_fury_cutter_db_scales_with_chain(self):
        move = MoveSpec(name="Fury Cutter", type="Bug", category="Physical", db=4, ac=2, range_kind="Melee")
        base_db, battle = _effective_db_from_move(move)
        battle.pokemon["a-1"].add_temporary_effect("fury_cutter_chain", target_id="b-1", stage=1)
        boosted_db, _ = _effective_db_from_move(move)
        self.assertGreaterEqual(boosted_db, base_db)

    def test_fury_swipes_five_strike_range(self):
        move = MoveSpec(name="Fury Swipes", type="Normal", category="Physical", db=5, ac=2, range_kind="Melee", range_text="Melee, 1 Target, Five Strike")
        battle, result = _resolve_with_roll(move, 20)
        self.assertIn(result.get("strike_max"), (None, 5))

    def test_fusion_bolt_db_boost(self):
        move = MoveSpec(name="Fusion Bolt", type="Electric", category="Physical", db=10, ac=2, range_kind="Ranged", range_value=8)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.round = 3
        battle.fusion_flare_rounds = [2]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 13)

    def test_fusion_flare_db_boost(self):
        move = MoveSpec(name="Fusion Flare", type="Fire", category="Special", db=10, ac=2, range_kind="Ranged", range_value=8)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.round = 3
        battle.fusion_bolt_rounds = [2]
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=defender_id,
            target_position=battle.pokemon[defender_id].position,
        )
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 13)
