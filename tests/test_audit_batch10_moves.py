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


def _pokemon_spec(name, move, *, types=None, injuries=0):
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


def _build_battle(move, *, attacker_types=None, defender_types=None, attacker_injuries=0):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, types=attacker_types, injuries=attacker_injuries),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    attacker.injuries = attacker_injuries
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


def _build_battle_with_grid(move, *, attacker_types=None, defender_types=None, attacker_injuries=0):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_injuries=attacker_injuries,
    )
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


def _damage_from_move(move, *, attacker_injuries=0, attacker_types=None, defender_types=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_injuries=attacker_injuries,
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


def _effective_db_from_move(move, *, attacker_injuries=0, attacker_types=None, defender_types=None):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_types=attacker_types,
        defender_types=defender_types,
        attacker_injuries=attacker_injuries,
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


class AuditBatch10MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_fiery_wrath_flinch_17(self):
        move = MoveSpec(
            name="Fiery Wrath",
            type="Dark",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Fiery Wrath Flinches the target on a 17+.",
        )
        battle, result = _resolve_with_roll(move, 17)
        self.assertTrue(battle.pokemon["b-1"].has_status("Flinched"))

    def test_fiery_wrath_can_convert_to_fire(self):
        move = MoveSpec(
            name="Fiery Wrath",
            type="Dark",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
        )
        battle, attacker_id, defender_id = _build_battle_with_grid(
            move,
            attacker_types=["Dark"],
            defender_types=["Grass"],
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
        self.assertIn("type:fire", roll_options)

    def test_fire_blast_burn_19(self):
        move = MoveSpec(
            name="Fire Blast",
            type="Fire",
            category="Special",
            db=10,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Fire Blast burns the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_fire_lash_lowers_defense(self):
        move = MoveSpec(
            name="Fire Lash",
            type="Fire",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=2,
            effects_text="The target's Defense is lowered by -1 CS.",
        )
        battle, result = _resolve_with_roll(move, 20)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("def"), -1)

    def test_flail_db_increases_with_injuries(self):
        move = MoveSpec(name="Flail", type="Normal", category="Physical", db=4, ac=2, range_kind="Melee")
        base_db, _ = _effective_db_from_move(move, attacker_injuries=0)
        boosted_db, _ = _effective_db_from_move(move, attacker_injuries=3)
        self.assertGreater(boosted_db, base_db)

    def test_flame_wheel_burn_19(self):
        move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="Flame Wheel Burns the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_flare_blitz_burn_19(self):
        move = MoveSpec(
            name="Flare Blitz",
            type="Fire",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            effects_text="Flare Blitz Burns the target on 19+.",
        )
        battle, result = _resolve_with_roll(move, 19)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_flash_cannon_spdef_drop_17(self):
        move = MoveSpec(
            name="Flash Cannon",
            type="Steel",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Flash Cannon lowers the target's Special Defense by -1 CS on 17+.",
        )
        battle, result = _resolve_with_roll(move, 17)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spdef"), -1)

    def test_flatter_raises_spatk_and_confuses(self):
        move = MoveSpec(
            name="Flatter",
            type="Dark",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Raise the target's Special Attack by +1 CS. Flatter Confuses the target.",
        )
        battle, result = _resolve_with_roll(move, 20)
        defender = battle.pokemon["b-1"]
        self.assertEqual(defender.combat_stages.get("spatk"), 1)
        self.assertTrue(defender.has_status("Confused"))

    def test_fleur_cannon_lowers_self_spatk(self):
        move = MoveSpec(
            name="Fleur Cannon",
            type="Fairy",
            category="Special",
            db=12,
            ac=2,
            range_kind="Line",
            range_value=9,
            effects_text="Lower the user's Special Attack 2 Combat Stages after damage.",
        )
        battle, result = _resolve_with_roll(move, 20)
        attacker = battle.pokemon["a-1"]
        self.assertEqual(attacker.combat_stages.get("spatk"), -2)

    def test_focus_blast_spdef_drop_18(self):
        move = MoveSpec(
            name="Focus Blast",
            type="Fighting",
            category="Special",
            db=12,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            effects_text="Focus Blast lowers the target's Special Defense by -1 CS on 18+.",
        )
        battle, result = _resolve_with_roll(move, 18)
        self.assertEqual(battle.pokemon["b-1"].combat_stages.get("spdef"), -1)
