import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase, calculations


class SequenceRNG(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)

    def randint(self, a, b):
        if self._values:
            return self._values.pop(0)
        return b

    def choice(self, seq):
        return seq[0]


def _pokemon_spec(
    name,
    *,
    ability=None,
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=10,
    defense=10,
    spatk=10,
    spdef=10,
    spd=10,
    level=20,
    movement=None,
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
        movement=movement or {"overland": 4},
        weight=5,
        gender="",
    )


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(2, 3)):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="foes")
    attacker = PokemonState(
        spec=attacker_spec,
        controller_id=trainer_a.identifier,
        position=attacker_pos,
        active=True,
    )
    defender = PokemonState(
        spec=defender_spec,
        controller_id=trainer_b.identifier,
        position=defender_pos,
        active=True,
    )
    battle = BattleState(
        trainers={trainer_a.identifier: trainer_a, trainer_b.identifier: trainer_b},
        pokemon={"a-1": attacker, "b-1": defender},
        grid=GridState(width=10, height=10),
    )
    battle.rng = SequenceRNG([20] * 50)
    return battle, "a-1", "b-1"


class AuditBatch62AbilityTests(unittest.TestCase):
    def test_sap_sipper_errata_absorbs_and_boosts_choice(self):
        move = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], atk=14)
        defender_spec = _pokemon_spec("Sipper", abilities=["Sap Sipper [Errata]"], moves=[move], spatk=12)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        defender.add_temporary_effect("sap_sipper_errata_choice", stat="spatk")
        before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertEqual(defender.combat_stages.get("spatk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sap Sipper [Errata]"
                for event in battle.log
            )
        )

    def test_sand_veil_errata_evasion_and_immunity(self):
        spec = _pokemon_spec("Veil", abilities=["Sand Veil [Errata]"])
        ally_spec = _pokemon_spec("Ally")
        mon = PokemonState(spec=spec, controller_id="a", position=(2, 2), active=True)
        ally = PokemonState(spec=ally_spec, controller_id="a", position=(2, 3), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon, "a-2": ally},
            grid=GridState(width=6, height=6),
        )
        base = PokemonState(
            spec=_pokemon_spec("Base"),
            controller_id="a",
            position=(1, 1),
            active=True,
        )
        base_value = calculations.evasion_value(base, "physical")
        errata_value = calculations.evasion_value(mon, "physical")
        self.assertEqual(errata_value, base_value + 1)

        battle.weather = "Sandstorm"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        sand_value = calculations.evasion_value(mon, "physical")
        self.assertEqual(sand_value, base_value + 2)
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

    def test_spray_down_errata_grounds_airborne_target(self):
        move = MoveSpec(
            name="Gust",
            type="Flying",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_value=6,
            target_kind="Ranged",
            target_range=6,
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Sprayer", abilities=["Spray Down [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Bird", moves=[move], movement={"sky": 4})
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.can_fly())
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertTrue(defender.get_temporary_effects("spray_down"))
        self.assertTrue(defender.get_temporary_effects("force_grounded"))
        used = battle.pokemon[attacker_id].get_temporary_effects("spray_down_used")
        self.assertTrue(used)
        self.assertEqual(used[0].get("count"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Spray Down [Errata]"
                for event in battle.log
            )
        )
