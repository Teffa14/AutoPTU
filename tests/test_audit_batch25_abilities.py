import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.battle_state import TurnPhase
from auto_ptu.rules.hooks import move_specials


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b


def _pokemon_spec(
    name,
    *,
    ability=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
):
    abilities = [{"name": ability}] if ability else []
    return PokemonSpec(
        species=name,
        level=20,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=abilities,
        movement={"overland": 4},
    )


def _build_battle(attacker_spec, defender_spec, *, grid=True):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id="a",
        position=(2, 2),
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id="b",
        position=(2, 3),
        active=True,
    )
    battle = BattleState(
        trainers={"a": trainer_a, "b": trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10) if grid else None,
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch25AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_aura_storm_adds_injury_scaled_bonus(self):
        move = MoveSpec(
            name="Aura Strike",
            type="Fighting",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            keywords=["Aura"],
        )
        attacker_spec = _pokemon_spec("Aurist", ability="Aura Storm", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.injuries = 2
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Aura Storm"
            and event.get("effect") == "damage_bonus"
        ]
        self.assertTrue(events)
        self.assertEqual(events[-1].get("amount"), 9)

    def test_bad_dreams_ticks_sleeping_targets(self):
        attacker_spec = _pokemon_spec("Darkrai", ability="Bad Dreams")
        defender_spec = _pokemon_spec("Sleeper")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Sleep"})
        before = defender.hp
        events = battle.pokemon[attacker_id]._handle_ability_phase_effects(
            battle, TurnPhase.COMMAND, attacker_id
        )
        self.assertLess(defender.hp, before)
        self.assertTrue(any(event.get("ability") == "Bad Dreams" for event in events))

    def test_ball_fetch_shifts_on_switch_in(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        outgoing = PokemonState(
            spec=_pokemon_spec("Outgoing", moves=[move]),
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        replacement = PokemonState(
            spec=_pokemon_spec("Replacement", moves=[move]),
            controller_id="a",
            position=None,
            active=False,
        )
        fetcher = PokemonState(
            spec=_pokemon_spec("Fetcher", ability="Ball Fetch", moves=[move]),
            controller_id="a",
            position=(5, 2),
            active=True,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": outgoing, "a-2": replacement, "a-3": fetcher},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)
        battle.round = 1
        before = fetcher.position
        battle._apply_switch(
            outgoing_id="a-1",
            replacement_id="a-2",
            initiator_id="a",
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        self.assertNotEqual(fetcher.position, before)
        self.assertLess(
            abs(fetcher.position[0] - replacement.position[0]) + abs(fetcher.position[1] - replacement.position[1]),
            abs(before[0] - replacement.position[0]) + abs(before[1] - replacement.position[1]),
        )

    def test_battery_boosts_next_special_attack(self):
        battery = MoveSpec(
            name="Battery",
            type="Electric",
            category="Status",
            db=0,
            ac=None,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
        )
        thunderbolt = MoveSpec(
            name="Thunderbolt",
            type="Electric",
            category="Special",
            db=9,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        charger_spec = _pokemon_spec("Charger", ability="Battery", moves=[battery])
        attacker_spec = _pokemon_spec("Ally", moves=[thunderbolt], types=["Electric"])
        defender_spec = _pokemon_spec("Target", moves=[thunderbolt])
        battle, charger_id, defender_id = _build_battle(charger_spec, defender_spec)
        ally = PokemonState(
            spec=attacker_spec,
            controller_id="a",
            position=(2, 1),
            active=True,
        )
        battle.pokemon["a-2"] = ally
        battle.resolve_move_targets(charger_id, battery, "a-2", ally.position)
        self.assertTrue(ally.get_temporary_effects("battery_boost"))
        battle.rng = SequenceRNG([20] + [1] * 50)
        battle.resolve_move_targets("a-2", thunderbolt, defender_id, battle.pokemon[defender_id].position)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Battery"
            and event.get("effect") == "damage_bonus"
        ]
        self.assertTrue(events)
        self.assertEqual(events[-1].get("amount"), 9)

    def test_beast_boost_raises_highest_stat_on_ko(self):
        move = MoveSpec(
            name="Power Hit",
            type="Normal",
            category="Physical",
            db=12,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Nihilego",
            ability="Beast Boost",
            moves=[move],
            atk=16,
            defense=8,
            spatk=10,
            spdef=8,
            spd=8,
        )
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.hp = 1
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(battle.pokemon[attacker_id].combat_stages.get("atk"), 1)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Beast Boost"
            and event.get("effect") == "stat_raise"
        ]
        self.assertTrue(events)

    def test_beautiful_clears_enraged_adjacent(self):
        attacker_spec = _pokemon_spec("Beaut", ability="Beautiful")
        defender_spec = _pokemon_spec("Rager")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.statuses.append({"name": "Enraged"})
        events = battle.pokemon[attacker_id]._handle_ability_phase_effects(
            battle, TurnPhase.START, attacker_id
        )
        self.assertFalse(defender.has_status("Enraged"))
        self.assertTrue(any(event.get("ability") == "Beautiful" for event in events))

    def test_berserk_triggers_below_half_hp(self):
        move = MoveSpec(
            name="Strike",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=18)
        defender_spec = _pokemon_spec("Berserker", ability="Berserk", moves=[move], hp_stat=1)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.hp = 20
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(defender.combat_stages.get("spatk"), 1)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Berserk"
            and event.get("effect") == "spatk_raise"
        ]
        self.assertTrue(events)

    def test_blow_away_whirlwind_tick(self):
        move = MoveSpec(
            name="Whirlwind",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Blower", ability="Blow Away", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], hp_stat=10)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertLess(defender.hp, before)
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Blow Away"
            and event.get("effect") == "tick"
        ]
        self.assertTrue(events)

    def test_bodyguard_intercepts_and_halves_damage(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=16)
        defender_spec = _pokemon_spec("Target", moves=[move])
        bodyguard_spec = _pokemon_spec("Guard", ability="Bodyguard", moves=[move])

        baseline_battle, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        baseline_battle.rng = SequenceRNG([20] + [3] * 50)
        baseline_hp = baseline_battle.pokemon[d_id].hp
        baseline_battle.resolve_move_targets(a_id, move, d_id, baseline_battle.pokemon[d_id].position)
        baseline_damage = baseline_hp - baseline_battle.pokemon[d_id].hp

        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        guard = PokemonState(
            spec=bodyguard_spec,
            controller_id="b",
            position=(3, 3),
            active=True,
        )
        battle.pokemon["b-2"] = guard
        battle.rng = SequenceRNG([20] + [3] * 50)
        guard_hp = guard.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        reduced_damage = guard_hp - guard.hp
        self.assertLessEqual(reduced_damage, max(0, baseline_damage // 2))
        events = [
            event
            for event in battle.log
            if event.get("type") == "ability"
            and event.get("ability") == "Bodyguard"
            and event.get("effect") == "resist"
        ]
        self.assertTrue(events)

    def test_bone_lord_bone_club_flinch(self):
        move = MoveSpec(
            name="Bone Club",
            type="Ground",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Cubone", ability="Bone Lord", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Flinch"))
