import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, calculations
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
    abilities=None,
    types=None,
    moves=None,
    hp_stat=10,
    atk=12,
    defense=10,
    spatk=12,
    spdef=10,
    spd=10,
    weight=1,
    items=None,
):
    ability_list = [{"name": ability} for ability in (abilities or [])]
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
        abilities=ability_list,
        items=items or [],
        movement={"overland": 4},
        weight=weight,
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


class AuditBatch31AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_handyman_selects_item_index(self):
        spec = _pokemon_spec(
            "Pidgey",
            abilities=["Handyman"],
            items=[{"name": "Potion"}, {"name": "Oran Berry"}],
        )
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon.add_temporary_effect("handyman_choice", item_index=1)
        idx = battle._delivery_bird_item_index(mon, mon.spec.items)
        self.assertEqual(idx, 1)

    def test_heatproof_halves_fire_damage(self):
        fire = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[fire], types=["Fire"])
        defender_spec = _pokemon_spec("Target", moves=[fire])
        heatproof_spec = _pokemon_spec("Target", abilities=["Heatproof"], moves=[fire])

        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_normal.rng = SequenceRNG([20] + [3] * 50)
        before = battle_normal.pokemon[d_id].hp
        battle_normal.resolve_move_targets(a_id, fire, d_id, battle_normal.pokemon[d_id].position)
        normal_damage = before - battle_normal.pokemon[d_id].hp

        battle_heat, a2_id, d2_id = _build_battle(attacker_spec, heatproof_spec)
        battle_heat.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle_heat.pokemon[d2_id].hp
        battle_heat.resolve_move_targets(a2_id, fire, d2_id, battle_heat.pokemon[d2_id].position)
        heat_damage = before2 - battle_heat.pokemon[d2_id].hp

        self.assertEqual(heat_damage * 2, normal_damage)

    def test_heavy_metal_increases_weight_class(self):
        spec = _pokemon_spec("Steel", abilities=["Heavy Metal"], weight=3)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(mon.weight_class(), 5)

    def test_heliovolt_grants_evasion_bonus(self):
        move = MoveSpec(
            name="Heliovolt",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Helio", abilities=["Heliovolt"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("heliovolt_active"))
        self.assertTrue(attacker.get_temporary_effects("evasion_bonus"))

    def test_honey_paws_turns_honey_into_food_buff(self):
        spec = _pokemon_spec("Vespiquen", abilities=["Honey Paws"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        events = battle.item_system.apply_item_use("a-1", "a-1", {"name": "Honey"})
        self.assertTrue(mon.food_buffs)
        self.assertTrue(any(event.get("ability") == "Honey Paws" for event in events))

    def test_horde_break_cures_all_statuses(self):
        spec = _pokemon_spec("Wishiwashi", abilities=["Schooling", "Horde Break"], hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.hp = mon.max_hp() // 2
        mon.statuses.append({"name": "Burned"})
        mon.add_temporary_effect("schooling_active", form="school")
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertFalse(mon.statuses)

    def test_huge_power_doubles_attack(self):
        base_spec = _pokemon_spec("Azumarill", abilities=[], atk=10)
        huge_spec = _pokemon_spec("Azumarill", abilities=["Huge Power"], atk=10)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        huge = PokemonState(spec=huge_spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(calculations.offensive_stat(huge, "physical"), calculations.offensive_stat(base, "physical") * 2)

    def test_hustle_lowers_accuracy(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        base_spec = _pokemon_spec("Base", abilities=[], moves=[move])
        hustle_spec = _pokemon_spec("Hustle", abilities=["Hustle"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move], defense=5)
        battle, attacker_id, defender_id = _build_battle(base_spec, defender_spec)
        base = battle.pokemon[attacker_id]
        hustle = PokemonState(spec=hustle_spec, controller_id="a", position=(0, 0), active=True)
        defender = battle.pokemon[defender_id]
        battle.rng = SequenceRNG([10])
        base_needed = calculations.attack_hits(battle.rng, base, defender, move).get("needed")
        battle.rng = SequenceRNG([10])
        hustle_needed = calculations.attack_hits(battle.rng, hustle, defender, move).get("needed")
        self.assertEqual(hustle_needed, base_needed + 2)

    def test_hydration_cures_in_rain(self):
        spec = _pokemon_spec("Lapras", abilities=["Hydration"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Burned"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Rain"
        mon._handle_ability_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertFalse(mon.has_status("Burned"))

    def test_ice_body_heals_in_hail(self):
        spec = _pokemon_spec("Glaceon", abilities=["Ice Body"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.weather = "Hail"
        mon.hp = max(1, mon.hp - mon.tick_value())
        before = mon.hp
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertGreater(mon.hp, before)
