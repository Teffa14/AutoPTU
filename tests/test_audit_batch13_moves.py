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


def _pokemon_spec(name, move, *, spd=10, weight=1):
    return PokemonSpec(
        species=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=12,
        defense=10,
        spatk=12,
        spdef=10,
        spd=spd,
        moves=[move],
        movement={"overland": 4},
        weight=weight,
    )


def _build_battle(move, *, attacker_spd=10, defender_spd=10, attacker_weight=1, defender_weight=1):
    trainer_a = TrainerState(identifier="a", name="A")
    trainer_b = TrainerState(identifier="b", name="B")
    attacker = PokemonState(
        spec=_pokemon_spec("Attacker", move, spd=attacker_spd, weight=attacker_weight),
        controller_id="a",
        position=(0, 0),
        active=True,
    )
    defender = PokemonState(
        spec=_pokemon_spec("Defender", move, spd=defender_spd, weight=defender_weight),
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


def _build_battle_with_grid(move, *, attacker_spd=10, defender_spd=10, attacker_weight=1, defender_weight=1):
    battle, attacker_id, defender_id = _build_battle(
        move,
        attacker_spd=attacker_spd,
        defender_spd=defender_spd,
        attacker_weight=attacker_weight,
        defender_weight=defender_weight,
    )
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


def _effective_db_from_move(move, *, attacker_spd=10, defender_spd=10, attacker_weight=1, defender_weight=1):
    battle, attacker_id, defender_id = _build_battle_with_grid(
        move,
        attacker_spd=attacker_spd,
        defender_spd=defender_spd,
        attacker_weight=attacker_weight,
        defender_weight=defender_weight,
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


class AuditBatch13MoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_heal_bell_cures_status(self):
        move = MoveSpec(name="Heal Bell", type="Normal", category="Status", db=0, ac=None, range_kind="Burst", range_value=3)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, defender.position)
        self.assertFalse(defender.statuses)

    def test_heal_order_heals_half(self):
        move = MoveSpec(name="Heal Order", type="Bug", category="Status", db=0, ac=None, range_kind="Self")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 10)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, attacker_id, None)
        self.assertGreater(attacker.hp, before)

    def test_heat_crash_db_scales_with_weight(self):
        move = MoveSpec(name="Heat Crash", type="Fire", category="Physical", db=8, ac=2, range_kind="Melee")
        base_db, _ = _effective_db_from_move(move, attacker_weight=2, defender_weight=2)
        boosted_db, _ = _effective_db_from_move(move, attacker_weight=4, defender_weight=1)
        self.assertGreater(boosted_db, base_db)

    def test_heat_wave_burns_18(self):
        move = MoveSpec(
            name="Heat Wave",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="CloseBlast",
            range_value=3,
            effects_text="Heat Wave Burns all Legal Targets on 18+.",
        )
        battle, result = _resolve_with_roll(move, 18)
        self.assertTrue(battle.pokemon["b-1"].has_status("Burned"))

    def test_helping_hand_accuracy_bonus(self):
        move = MoveSpec(name="Helping Hand", type="Normal", category="Status", db=0, ac=None, range_kind="Ranged", range_value=4)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.get_temporary_effects("accuracy_bonus"))

    def test_hex_db_boost_when_statused(self):
        move = MoveSpec(name="Hex", type="Ghost", category="Special", db=8, ac=2, range_kind="Ranged", range_value=6)
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        last_event = battle.log[-1] if battle.log else {}
        self.assertGreaterEqual(last_event.get("effective_db", 0), 13)

    def test_high_horsepower_smite_on_sprint(self):
        move = MoveSpec(name="High Horsepower", type="Ground", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect("sprint")
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        smite_events = [event for event in battle.log if event.get("type") == "smite"]
        self.assertTrue(smite_events)

    def test_horn_attack_gore_crit_range(self):
        move = MoveSpec(name="Horn Attack", type="Normal", category="Physical", db=6, ac=2, range_kind="Melee")
        battle, result = _resolve_with_roll(move, 18)
        self.assertIn("crit", result)

    def test_horn_leech_drains(self):
        move = MoveSpec(name="Horn Leech", type="Grass", category="Physical", db=8, ac=2, range_kind="Melee")
        battle, attacker_id, defender_id = _build_battle_with_grid(move)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 6)
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(attacker.hp, before)

    def test_hurricane_confusion_15(self):
        move = MoveSpec(
            name="Hurricane",
            type="Flying",
            category="Special",
            db=10,
            ac=2,
            range_kind="Burst",
            range_value=1,
            effects_text="Hurricane Confuses its target on 15+.",
        )
        battle, result = _resolve_with_roll(move, 15)
        self.assertTrue(battle.pokemon["b-1"].has_status("Confused"))
