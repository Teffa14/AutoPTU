import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, ShiftAction, TrainerState, TurnPhase
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
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    level=20,
):
    ability_list = abilities if abilities is not None else ([ability] if ability else [])
    return PokemonSpec(
        species=name,
        level=level,
        types=types or ["Normal"],
        hp_stat=hp_stat,
        atk=atk,
        defense=defense,
        spatk=spatk,
        spdef=spdef,
        spd=spd,
        moves=moves or [],
        abilities=[{"name": entry} for entry in ability_list],
        items=[],
        movement={"overland": 4},
        weight=5,
    )


def _build_battle(attacker_spec, defender_spec):
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
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 200)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch38AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_run_away_blocks_slowed(self):
        move = MoveSpec(
            name="Mud Shot",
            type="Ground",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Runner", ability="Run Away", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=defender,
            status="Slowed",
            effect="test",
            description="Test slow",
            remaining=1,
        )
        self.assertFalse(defender.has_status("Slowed"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Run Away"
                and event.get("effect") == "status_block"
                for event in events
            )
        )

    def test_run_away_errata_blocks_slowed(self):
        move = MoveSpec(
            name="Mud Shot",
            type="Ground",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Runner", abilities=["Run Away [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        events = []
        battle._apply_status(
            events,
            attacker_id=attacker_id,
            target_id=defender_id,
            move=move,
            target=defender,
            status="Slowed",
            effect="test",
            description="Test slow",
            remaining=1,
        )
        self.assertFalse(defender.has_status("Slowed"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Run Away"
                and event.get("effect") == "status_block"
                for event in events
            )
        )

    def test_run_up_adds_damage_after_shift(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Runner", ability="Run Up", moves=[tackle], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[tackle])

        battle_shift, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_shift.pokemon[defender_id].position = (2, 4)
        battle_shift.queue_action(ShiftAction(actor_id=attacker_id, destination=(2, 3)))
        battle_shift.resolve_next_action()
        battle_shift.rng = SequenceRNG([20] + [3] * 50)
        before = battle_shift.pokemon[defender_id].hp
        battle_shift.resolve_move_targets(attacker_id, tackle, defender_id, battle_shift.pokemon[defender_id].position)
        shifted_damage = before - battle_shift.pokemon[defender_id].hp

        battle_plain, a2, d2 = _build_battle(attacker_spec, defender_spec)
        battle_plain.pokemon[a2].position = (2, 3)
        battle_plain.pokemon[d2].position = (2, 4)
        battle_plain.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle_plain.pokemon[d2].hp
        battle_plain.resolve_move_targets(a2, tackle, d2, battle_plain.pokemon[d2].position)
        normal_damage = before2 - battle_plain.pokemon[d2].hp

        self.assertGreater(shifted_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Run Up"
                and event.get("effect") == "damage_bonus"
                for event in battle_shift.log
            )
        )

    def test_sacred_bell_reduces_dark_damage(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Bell", ability="Sacred Bell", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        reduced = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[move])
        battle2, a2, d2 = _build_battle(attacker_spec, normal_spec)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal = before2 - battle2.pokemon[d2].hp

        self.assertLess(reduced, normal)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sacred Bell"
                and event.get("effect") == "type_resist"
                for event in battle.log
            )
        )

    def test_sand_force_adds_damage_in_sand(self):
        move = MoveSpec(
            name="Rock Slide",
            type="Rock",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Sand", ability="Sand Force", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sandstorm"
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        boosted = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[move], atk=14)
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.weather = "Sandstorm"
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal = before2 - battle2.pokemon[d2].hp

        self.assertGreater(boosted, normal)

    def test_sand_force_errata_adds_damage_in_sand(self):
        move = MoveSpec(
            name="Rock Slide",
            type="Rock",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Sand", abilities=["Sand Force [Errata]"], moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sandstorm"
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        boosted = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[move], atk=14)
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.weather = "Sandstorm"
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal = before2 - battle2.pokemon[d2].hp

        self.assertGreater(boosted, normal)

    def test_sand_rush_raises_speed_in_sand(self):
        spec = _pokemon_spec("Sand", ability="Sand Rush")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sandstorm"
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spd"), 4)
        self.assertTrue(
            any(
                event.get("type") == "combat_stage"
                and event.get("effect") == "sand rush"
                for event in events
            )
        )

    def test_sand_rush_errata_raises_speed_in_sand(self):
        spec = _pokemon_spec("Sand", abilities=["Sand Rush [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sandstorm"
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spd"), 4)
        self.assertTrue(
            any(
                event.get("type") == "combat_stage"
                and event.get("effect") == "sand rush"
                for event in events
            )
        )

    def test_sand_spit_counters(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Spitter", ability="Sand Spit", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sand Spit"
                and event.get("effect") == "sand_spit"
                for event in battle.log
            )
        )

    def test_sand_stream_summons_weather(self):
        move = MoveSpec(
            name="Sand Stream",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Sand", ability="Sand Stream", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertIn("sand", (battle.weather or "").lower())
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sand Stream"
                and event.get("effect") == "weather"
                for event in battle.log
            )
        )

    def test_sand_veil_grants_evasion_and_immunity(self):
        spec = _pokemon_spec("Veil", ability="Sand Veil")
        ally_spec = _pokemon_spec("Ally")
        mon = PokemonState(spec=spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 3), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon, "a-2": ally},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sandstorm"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        bonuses = mon.get_temporary_effects("evasion_bonus")
        self.assertTrue(any(entry.get("amount") == 2 for entry in bonuses))
        self.assertTrue(
            any(
                entry.get("weather") == "sandstorm"
                for entry in mon.get_temporary_effects("weather_immunity")
            )
        )
        self.assertTrue(
            any(
                entry.get("weather") == "sandstorm"
                for entry in ally.get_temporary_effects("weather_immunity")
            )
        )

    def test_sand_stream_errata_summons_weather_and_immunity(self):
        move = MoveSpec(
            name="Sand Stream [Errata]",
            type="Ground",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Sand", abilities=["Sand Stream [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertIn("sand", (battle.weather or "").lower())
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(
            any(
                entry.get("weather") == "sandstorm"
                for entry in attacker.get_temporary_effects("weather_immunity")
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sand Stream [Errata]"
                and event.get("effect") == "weather"
                for event in battle.log
            )
        )

    def test_sap_sipper_absorbs_grass_and_boosts_attack(self):
        move = MoveSpec(
            name="Absorb",
            type="Grass",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Sipper", ability="Sap Sipper", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 20)
        defender_before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.hp, defender_before)
        self.assertEqual(defender.combat_stages.get("atk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sap Sipper"
                and event.get("effect") == "absorb"
                for event in battle.log
            )
        )

    def test_scrappy_allows_normal_to_hit_ghosts(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Scrap", ability="Scrappy", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Ghost", moves=[move], types=["Ghost"])
        battle_scrappy, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_scrappy.rng = SequenceRNG([20] + [3] * 20)
        before = battle_scrappy.pokemon[defender_id].hp
        battle_scrappy.resolve_move_targets(attacker_id, move, defender_id, battle_scrappy.pokemon[defender_id].position)
        damage_scrappy = before - battle_scrappy.pokemon[defender_id].hp

        base_attacker = _pokemon_spec("Scrap", moves=[move], atk=14)
        battle_base, attacker_base_id, defender_base_id = _build_battle(base_attacker, defender_spec)
        battle_base.rng = SequenceRNG([20] + [3] * 20)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertGreater(damage_scrappy, damage_base)
