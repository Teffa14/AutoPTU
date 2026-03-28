import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase
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


class AuditBatch41AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_snow_cloak_errata_adds_evasion_bonus_in_hail(self):
        spec = _pokemon_spec("Snowy", abilities=["Snow Cloak [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Hail"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        bonus = mon.get_temporary_effects("evasion_bonus")
        self.assertTrue(any(entry.get("amount") == 2 for entry in bonus))

    def test_snow_cloak_adds_evasion_bonus_in_hail(self):
        spec = _pokemon_spec("Snowy", ability="Snow Cloak")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Hail"
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        bonus = mon.get_temporary_effects("evasion_bonus")
        self.assertTrue(any(entry.get("amount") == 2 for entry in bonus))
        self.assertTrue(
            any(
                entry.get("weather") == "hail"
                for entry in mon.get_temporary_effects("weather_immunity")
            )
        )

    def test_snow_warning_sets_hail(self):
        snow_warning = MoveSpec(
            name="Snow Warning",
            type="Ice",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Caster", ability="Snow Warning", moves=[snow_warning])
        defender_spec = _pokemon_spec("Target", moves=[snow_warning])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, snow_warning, defender_id, battle.pokemon[defender_id].position)
        weather = str(battle.effective_weather() or "").lower()
        self.assertIn("hail", weather)

    def test_snuggle_grants_temp_hp_to_both(self):
        snuggle = MoveSpec(
            name="Snuggle",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Giver", ability="Snuggle", moves=[snuggle])
        defender_spec = _pokemon_spec("Buddy", moves=[snuggle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, snuggle, defender_id, battle.pokemon[defender_id].position)
        self.assertGreater(battle.pokemon[attacker_id].temp_hp, 0)
        self.assertGreater(battle.pokemon[defender_id].temp_hp, 0)

    def test_sol_veil_adds_accuracy_penalty(self):
        move = MoveSpec(
            name="Vine Whip",
            type="Grass",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Veiled", ability="Sol Veil", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sunny"
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Sol Veil"
                and event.get("effect") == "accuracy_penalty"
                for event in battle.log
            )
        )

    def test_solar_power_boosts_spatk_and_drains_hp_in_sun(self):
        spec = _pokemon_spec("Solar", ability="Solar Power")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Sunny"
        before_hp = mon.hp
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("spatk"), 2)
        self.assertLess(mon.hp, before_hp)

    def test_solar_power_errata_ready_and_bonus_damage(self):
        solar_power = MoveSpec(
            name="Solar Power [Errata]",
            type="Fire",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Solar", abilities=["Solar Power [Errata]"], moves=[solar_power, strike])
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, solar_power, attacker_id, battle.pokemon[attacker_id].position)
        ready = battle.pokemon[attacker_id].get_temporary_effects("solar_power_errata_ready")
        self.assertTrue(ready)

        battle.rng = SequenceRNG([20] + [3] * 20)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(battle.pokemon[defender_id].hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Solar Power [Errata]"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_solid_rock_reduces_super_effective_damage(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Rocky", ability="Solid Rock", moves=[move], types=["Fire"])
        battle_solid, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_solid.rng = SequenceRNG([19] + [3] * 50)
        before = battle_solid.pokemon[defender_id].hp
        battle_solid.resolve_move_targets(attacker_id, move, defender_id, battle_solid.pokemon[defender_id].position)
        damage_solid = before - battle_solid.pokemon[defender_id].hp

        base_defender_spec = _pokemon_spec("Rocky", moves=[move], types=["Fire"])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_solid, damage_base)

    def test_solid_rock_errata_reduces_super_effective_damage(self):
        move = MoveSpec(
            name="Water Gun",
            type="Water",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=14)
        defender_spec = _pokemon_spec("Rocky", abilities=["Solid Rock [Errata]"], moves=[move], types=["Fire"])
        battle_solid, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle_solid.rng = SequenceRNG([19] + [3] * 50)
        before = battle_solid.pokemon[defender_id].hp
        battle_solid.resolve_move_targets(attacker_id, move, defender_id, battle_solid.pokemon[defender_id].position)
        damage_solid = before - battle_solid.pokemon[defender_id].hp

        base_defender_spec = _pokemon_spec("Rocky", moves=[move], types=["Fire"])
        battle_base, attacker_base_id, defender_base_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([19] + [3] * 50)
        before_base = battle_base.pokemon[defender_base_id].hp
        battle_base.resolve_move_targets(attacker_base_id, move, defender_base_id, battle_base.pokemon[defender_base_id].position)
        damage_base = before_base - battle_base.pokemon[defender_base_id].hp

        self.assertLess(damage_solid, damage_base)

    def test_sonic_courtship_errata_expands_attract(self):
        sonic = MoveSpec(
            name="Sonic Courtship [Errata]",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attract = MoveSpec(
            name="Attract",
            type="Fairy",
            category="Status",
            db=0,
            ac=None,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Singer", abilities=["Sonic Courtship [Errata]"], moves=[sonic, attract])
        defender_spec = _pokemon_spec("Foe", moves=[attract])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].position = (2, 3)
        extra = PokemonState(
            spec=_pokemon_spec("Extra", moves=[attract]),
            controller_id="b",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        battle.resolve_move_targets(attacker_id, sonic, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, attract, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Infatuated"))
        self.assertTrue(extra.has_status("Infatuated"))

    def test_soothing_tone_adds_evasion_bonus(self):
        spec = _pokemon_spec("Calm", ability="Soothing Tone")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        bonus = mon.get_temporary_effects("evasion_bonus")
        self.assertTrue(bonus)
