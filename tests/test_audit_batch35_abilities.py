import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import (
    BattleState,
    GridState,
    PokemonState,
    TrainerState,
    UseMoveAction,
    ShiftAction,
    ActionType,
)
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
    capabilities=None,
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
        capabilities=capabilities or [],
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


class AuditBatch35AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_parental_bond_adds_extra_damage(self):
        strike = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Kanga", ability="Parental Bond", moves=[strike], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        battle.resolve_move_targets(attacker_id, strike, defender_id, defender.position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Parental Bond"
                and event.get("effect") == "extra_hit"
                for event in battle.log
            )
        )

    def test_parental_bond_spawns_baby_and_allows_action(self):
        strike = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Kanga",
            ability="Parental Bond",
            moves=[strike],
            spatk=14,
            spd=12,
            capabilities=["Marsupial"],
        )
        defender_spec = _pokemon_spec("Target", moves=[strike], spd=6)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.current_actor_id = attacker_id
        events = battle.pokemon[attacker_id].handle_phase_effects(
            battle, battle.phase, attacker_id
        )
        for payload in events:
            battle.log_event(payload)
        baby_id = next(
            pid
            for pid, mon in battle.pokemon.items()
            if any(
                entry.get("mother_id") == attacker_id
                for entry in mon.get_temporary_effects("parental_bond_child")
            )
        )
        baby = battle.pokemon[baby_id]
        self.assertTrue(
            any(
                entry.get("kind") == "damage_reduction"
                and int(entry.get("amount", 0) or 0) == 10
                for entry in baby.get_temporary_effects("damage_reduction")
            )
        )
        battle.queue_action(UseMoveAction(actor_id=baby_id, move_name="Water Gun", target_id=defender_id))
        battle.resolve_next_action()
        move_events = [evt for evt in battle.log if evt.get("type") == "move" and evt.get("actor") == baby_id]
        self.assertTrue(move_events)

    def test_parental_bond_baby_leash_blocks_far_shift(self):
        strike = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Kanga",
            ability="Parental Bond",
            moves=[strike],
            spd=12,
            capabilities=["Marsupial"],
        )
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.grid = GridState(width=30, height=30)
        battle.current_actor_id = attacker_id
        events = battle.pokemon[attacker_id].handle_phase_effects(
            battle, battle.phase, attacker_id
        )
        for payload in events:
            battle.log_event(payload)
        baby_id = next(
            pid
            for pid, mon in battle.pokemon.items()
            if any(
                entry.get("mother_id") == attacker_id
                for entry in mon.get_temporary_effects("parental_bond_child")
            )
        )
        baby = battle.pokemon[baby_id]
        far_destination = (20, 20)
        with self.assertRaises(ValueError):
            ShiftAction(actor_id=baby_id, destination=far_destination).validate(battle)

    def test_parental_bond_mother_enrages_on_baby_faint(self):
        strike = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Kanga",
            ability="Parental Bond",
            moves=[strike],
            spd=12,
            capabilities=["Marsupial"],
        )
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.current_actor_id = attacker_id
        events = battle.pokemon[attacker_id].handle_phase_effects(
            battle, battle.phase, attacker_id
        )
        for payload in events:
            battle.log_event(payload)
        baby_id = next(
            pid
            for pid, mon in battle.pokemon.items()
            if any(
                entry.get("mother_id") == attacker_id
                for entry in mon.get_temporary_effects("parental_bond_child")
            )
        )
        baby = battle.pokemon[baby_id]
        baby.hp = 0
        events = battle.pokemon[attacker_id].handle_phase_effects(
            battle, battle.phase, attacker_id
        )
        for payload in events:
            battle.log_event(payload)
        mother = battle.pokemon[attacker_id]
        self.assertTrue(mother.has_status("Enraged"))
        self.assertTrue(
            any(
                entry.get("kind") == "damage_reduction"
                and int(entry.get("amount", 0) or 0) == 5
                for entry in mother.get_temporary_effects("damage_reduction")
            )
        )
        self.assertTrue(
            any(
                entry.get("kind") == "damage_bonus"
                and int(entry.get("amount", 0) or 0) == 5
                for entry in mother.get_temporary_effects("damage_bonus")
            )
        )

    def test_perception_shifts_out_of_burst(self):
        perception = MoveSpec(
            name="Perception",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        burst = MoveSpec(
            name="Flame Burst",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Burst",
            area_kind="Burst",
            area_value=1,
            range_text="Burst 1",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[burst])
        defender_spec = _pokemon_spec("Watcher", ability="Perception", moves=[perception])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(defender_id, perception, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        origin = defender.position
        battle.resolve_move_targets(attacker_id, burst, defender_id, origin)
        self.assertNotEqual(defender.position, origin)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Perception"
                and event.get("effect") == "shift"
                for event in battle.log
            )
        )

    def test_perish_body_applies_perish_song(self):
        strike = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[strike], atk=14)
        defender_spec = _pokemon_spec("Cursed", ability="Perish Body", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(defender.get_temporary_effects("perish_song"))
        self.assertTrue(attacker.get_temporary_effects("perish_song"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Perish Body"
                and event.get("effect") == "perish_body"
                for event in battle.log
            )
        )

    def test_permafrost_reduces_super_effective_damage(self):
        move = MoveSpec(
            name="Flame Thrower",
            type="Fire",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14, types=["Fire"])
        defender_spec = _pokemon_spec("Target", ability="Permafrost", moves=[move], types=["Grass"])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        reduced = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[move], types=["Grass"])
        battle2, a2, d2 = _build_battle(attacker_spec, normal_spec)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal = before2 - battle2.pokemon[d2].hp

        self.assertLess(reduced, normal)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Permafrost"
                and event.get("effect") == "resist"
                for event in battle.log
            )
        )

    def test_photosynthesis_heals_in_sun(self):
        spec = _pokemon_spec("Sun", ability="Photosynthesis")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sun"
        mon.hp = max(1, mon.hp - mon.tick_value())
        before = mon.hp
        mon._handle_ability_phase_effects(battle, "start", "a-1")
        self.assertGreater(mon.hp, before)

    def test_plus_boosts_gear_up(self):
        gear_up = MoveSpec(
            name="Gear Up",
            type="Steel",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Plus", ability="Plus", moves=[gear_up])
        defender_spec = _pokemon_spec("Ally", ability="Plus", moves=[gear_up])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, gear_up, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("atk"), 1)
        self.assertEqual(defender.combat_stages.get("spatk"), 1)

    def test_poltergeist_damages_with_items(self):
        spec = _pokemon_spec("Haunter", ability="Poltergeist")
        spec.items.append({"name": "Oran Berry"})
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        before = mon.hp
        mon._handle_ability_phase_effects(battle, "start", "a-1")
        self.assertLess(mon.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "status"
                and event.get("status") == "Poltergeist"
                and event.get("effect") == "tick"
                for event in battle.log
            )
        )

    def test_polycephaly_makes_struggle_swift(self):
        move = MoveSpec(
            name="Struggle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Hydra", ability="Polycephaly", moves=[move])
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": attacker},
            grid=GridState(width=6, height=6),
        )
        action = UseMoveAction(actor_id="a-1", move_name="Struggle")
        move = attacker.spec.moves[0]
        self.assertEqual(action._resolve_action_type(attacker, move), ActionType.SWIFT)

    def test_power_construct_grants_temp_hp_and_form(self):
        power = MoveSpec(
            name="Power Construct",
            type="Dragon",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Zygarde", ability="Power Construct", moves=[power])
        defender_spec = _pokemon_spec("Target", moves=[power])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() // 2)
        battle.resolve_move_targets(attacker_id, power, defender_id, attacker.position)
        self.assertTrue(attacker.get_temporary_effects("temp_hp_locked"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Power Construct"
                and event.get("effect") == "temp_hp"
                for event in battle.log
            )
        )

    def test_power_of_alchemy_copies_ability(self):
        alchemy = MoveSpec(
            name="Power of Alchemy",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Alchemist", ability="Power of Alchemy", moves=[alchemy])
        defender_spec = _pokemon_spec("Target", abilities=["Overgrow"], moves=[alchemy])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, alchemy, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        granted = attacker.get_temporary_effects("ability_granted")
        self.assertTrue(granted)
        self.assertEqual(granted[0].get("ability"), "Overgrow")
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Power of Alchemy"
                and event.get("effect") == "ability_copy"
                for event in battle.log
            )
        )
