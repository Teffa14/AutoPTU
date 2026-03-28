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


def _pokemon_spec(name, move, *, weight=1):
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
        weight=weight,
    )


def _build_battle(move, *, attacker_weight=1, defender_weight=1):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, weight=attacker_weight),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, weight=defender_weight),
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


def _build_battle_with_grid(move, *, attacker_weight=1, defender_weight=1):
    battle, attacker_id, defender_id = _build_battle(move, attacker_weight=attacker_weight, defender_weight=defender_weight)
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


def _effective_db_from_move(move, *, attacker_weight=1, defender_weight=1):
    battle, attacker_id, defender_id = _build_battle_with_grid(move, attacker_weight=attacker_weight, defender_weight=defender_weight)
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


class AuditBatch14MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_hydro_pump_pushes(self):
        move = MoveSpec(
            name="Hydro Pump",
            type="Water",
            category="Special",
            db=11,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="6, 1 Target, Push",
            effects_text="The target is pushed away from the user 3 meters.",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.position
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertNotEqual(defender.position, before)

    def test_hyper_voice_smite(self):
        move = MoveSpec(
            name="Hyper Voice",
            type="Normal",
            category="Special",
            db=9,
            ac=2,
            range_kind="CloseBlast",
            range_value=3,
            range_text="Close Blast 3, Sonic, Smite",
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        smite_events = [event for event in battle.log if event.get("type") == "smite"]
        self.assertTrue(smite_events)

    def test_ice_beam_freeze_19(self):
        move = MoveSpec(
            name="Ice Beam",
            type="Ice",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=4,
            effects_text="Ice Beam Freezes on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Frozen"))

    def test_ice_punch_freeze_19(self):
        move = MoveSpec(
            name="Ice Punch",
            type="Ice",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            effects_text="Ice Punch Freezes the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Frozen"))

    def test_ice_shard_base_damage(self):
        move = MoveSpec(name="Ice Shard", type="Ice", category="Physical", db=4, ac=2, range_kind="Ranged", range_value=4)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)

    def test_icicle_crash_flinch_15(self):
        move = MoveSpec(
            name="Icicle Crash",
            type="Ice",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Icicle Crash Flinches the target on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))

    def test_imprison_cannot_miss_and_locks(self):
        move = MoveSpec(
            name="Imprison",
            type="Psychic",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=10,
            effects_text="Imprison cannot miss.",
        )
        battle, result = _resolve_with_roll(move, 1)
        self.assertTrue(result.get("hit"))
        defender = battle.pokemon["b-1"]
        self.assertTrue(defender.get_temporary_effects("imprisoned_moves"))

    def test_inferno_burns(self):
        move = MoveSpec(
            name="Inferno",
            type="Fire",
            category="Special",
            db=9,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Inferno Burns the target.",
        )
        battle, result = _resolve_with_roll(move, 10)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_iron_defense_raises_def(self):
        move = MoveSpec(
            name="Iron Defense",
            type="Steel",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            effects_text="Raise the user's Defense by +2 CS.",
        )
        battle, attacker_id, defender_id = _build_battle(move)
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        attacker = battle.pokemon[attacker_id]
        self.assertEqual(attacker.combat_stages.get("def"), 2)

    def test_iron_head_flinch_15(self):
        move = MoveSpec(
            name="Iron Head",
            type="Steel",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            effects_text="Iron Head Flinches the target on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))
