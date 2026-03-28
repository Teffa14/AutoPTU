import copy
import random
import unittest
from unittest import mock

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase, UseMoveAction, ActionType
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


class AuditBatch37AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_ragelope_enrages_and_boosts(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Rage", ability="Ragelope", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.has_status("Enraged"))
        self.assertEqual(attacker.combat_stages.get("spd"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Ragelope"
                and event.get("effect") == "enrage"
                for event in battle.log
            )
        )

    def test_rain_dish_heals_in_rain(self):
        spec = _pokemon_spec("Rain", ability="Rain Dish")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Rain"
        mon.hp = max(1, mon.hp - mon.tick_value())
        before = mon.hp
        events = mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertGreater(mon.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rain Dish"
                and event.get("effect") == "heal"
                for event in events
            )
        )

    def test_rain_dish_errata_requires_action(self):
        move = MoveSpec(
            name="Rain Dish [Errata]",
            type="Water",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Rain", abilities=["Rain Dish [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() // 2)
        battle.resolve_move_targets(attacker_id, move, defender_id, attacker.position)
        self.assertGreater(attacker.hp, max(1, attacker.max_hp() // 2))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rain Dish [Errata]"
                and event.get("effect") == "heal"
                for event in battle.log
            )
        )

    def test_rally_shifts_ally(self):
        rally = MoveSpec(
            name="Rally",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Leader", ability="Rally", moves=[rally])
        defender_spec = _pokemon_spec("Ally", moves=[rally])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=defender_spec, controller_id="a", position=(2, 4), active=True)
        foe = PokemonState(spec=_pokemon_spec("Foe", moves=[rally]), controller_id="b", position=(2, 6), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "a-2": ally, "b-1": foe},
            grid=GridState(width=10, height=10),
        )
        origin = ally.position
        battle.resolve_move_targets("a-1", rally, "a-1", attacker.position)
        self.assertNotEqual(ally.position, origin)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rally"
                and event.get("effect") == "shift"
                for event in battle.log
            )
        )

    def test_rally_errata_disengages(self):
        rally = MoveSpec(
            name="Rally [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Leader", abilities=["Rally [Errata]"], moves=[rally])
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(spec=attacker_spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=_pokemon_spec("Ally", moves=[rally]), controller_id="a", position=(2, 4), active=True)
        foe = PokemonState(spec=_pokemon_spec("Foe", moves=[rally]), controller_id="b", position=(2, 6), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "a-2": ally, "b-1": foe},
            grid=GridState(width=10, height=10),
        )
        origin = ally.position
        battle.resolve_move_targets("a-1", rally, "a-1", attacker.position)
        self.assertNotEqual(ally.position, origin)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rally [Errata]"
                and event.get("effect") == "disengage"
                for event in battle.log
            )
        )

    def test_rattled_errata_raises_speed_on_dark_hit(self):
        move = MoveSpec(
            name="Bite",
            type="Dark",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Defender", abilities=["Rattled [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("spd"), 1)

    def test_razor_edge_increases_crit_range(self):
        move = MoveSpec(
            name="Slash",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Edge", ability="Razor Edge", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        captured = []
        original = copy.deepcopy

        def spy(obj):
            cloned = original(obj)
            if isinstance(cloned, MoveSpec) and cloned.name == "Slash":
                captured.append(cloned)
            return cloned

        with mock.patch("auto_ptu.rules.battle_state.copy.deepcopy", side_effect=spy):
            battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)

        self.assertTrue(any((entry.crit_range or 20) <= 18 for entry in captured))

    def test_receiver_copies_ally_ability_on_faint(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        receiver_spec = _pokemon_spec("Receiver", ability="Receiver", moves=[move])
        ally_spec = _pokemon_spec("Ally", abilities=["Overgrow"], moves=[move], hp_stat=1)
        attacker_spec = _pokemon_spec("Foe", moves=[move], atk=14)
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        receiver = PokemonState(spec=receiver_spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 3), active=True)
        foe = PokemonState(spec=attacker_spec, controller_id="b", position=(2, 4), active=True)
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": receiver, "a-2": ally, "b-1": foe},
            grid=GridState(width=10, height=10),
        )
        foe.hp = foe.max_hp()
        ally.hp = 1
        battle.rng = SequenceRNG([20] + [3] * 50)
        battle.resolve_move_targets("b-1", move, "a-2", ally.position)
        granted = receiver.get_temporary_effects("granted_ability")
        self.assertTrue(granted)
        self.assertEqual(granted[0].get("ability"), "Overgrow")
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Receiver"
                and event.get("effect") == "gain_ability"
                for event in battle.log
            )
        )

    def test_reckless_increases_damage_for_recoil_move(self):
        move = MoveSpec(
            name="Double-Edge",
            type="Normal",
            category="Physical",
            db=10,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target, Recoil 1/3",
            effects_text="Double-Edge deals recoil damage equal to 1/3 of the damage dealt.",
        )
        attacker_spec = _pokemon_spec("Reckless", ability="Reckless", moves=[move], atk=20)
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.rng = SequenceRNG([20] + [3] * 50)
        defender = battle.pokemon[defender_id]
        before_defender = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        reckless_damage = before_defender - defender.hp

        normal_spec = _pokemon_spec("Normal", moves=[move], atk=20)
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        defender2 = battle2.pokemon[d2]
        before_defender2 = defender2.hp
        battle2.resolve_move_targets(a2, move, d2, battle2.pokemon[d2].position)
        normal_damage = before_defender2 - defender2.hp

        self.assertGreater(reckless_damage, normal_damage)

    def test_regal_challenge_slows_on_hit(self):
        move = MoveSpec(
            name="Regal Challenge",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Regal", ability="Regal Challenge", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Slowed"))
        self.assertEqual(defender.combat_stages.get("spd"), -1)

    def test_regal_challenge_errata_deference(self):
        move = MoveSpec(
            name="Regal Challenge [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Regal", abilities=["Regal Challenge [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.action_consumed_detail(ActionType.SHIFT))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Regal Challenge [Errata]"
                and event.get("effect") == "deference"
                for event in battle.log
            )
        )
