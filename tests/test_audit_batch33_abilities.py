import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, ShiftAction, TrainerState
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
    weight=5,
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
        weight=weight,
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


class AuditBatch33AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_leaf_guard_blocks_status_in_sun(self):
        burn_move = MoveSpec(
            name="Flame Wheel",
            type="Fire",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            effects_text="Flame Wheel Burns the target on 15+.",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[burn_move], atk=14)
        defender_spec = _pokemon_spec("Defender", ability="Leaf Guard", moves=[burn_move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sun"
        battle.rng = SequenceRNG([20] * 200)
        battle.resolve_move_targets(attacker_id, burn_move, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[defender_id].has_status("Burned"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Leaf Guard"
                and event.get("effect") == "status_block"
                for event in battle.log
            )
        )

    def test_leaf_rush_grants_priority_and_damage_bonus(self):
        leaf_rush = MoveSpec(
            name="Leaf Rush",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        strike = MoveSpec(
            name="Razor Leaf",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", ability="Leaf Rush", moves=[leaf_rush, strike], spd=12)
        defender_spec = _pokemon_spec("Target", moves=[strike])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, leaf_rush, defender_id, battle.pokemon[defender_id].position)
        battle.log = []
        battle.rng = SequenceRNG([20] * 200)
        battle.resolve_move_targets(attacker_id, strike, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Leaf Rush"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_leafy_cloak_grants_chosen_abilities(self):
        leafy_cloak = MoveSpec(
            name="Leafy Cloak",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Cloaker", ability="Leafy Cloak", moves=[leafy_cloak])
        defender_spec = _pokemon_spec("Target", moves=[leafy_cloak])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect("leafy_cloak_choice", choices=["Chlorophyll", "Overcoat"])
        battle.resolve_move_targets(attacker_id, leafy_cloak, defender_id, attacker.position)
        granted = attacker.get_temporary_effects("ability_granted")
        granted_names = {entry.get("ability") for entry in granted}
        self.assertEqual(granted_names, {"Chlorophyll", "Overcoat"})
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Leafy Cloak"
                and event.get("effect") == "grant"
                for event in battle.log
            )
        )

    def test_life_force_heals_tick(self):
        life_force = MoveSpec(
            name="Life Force",
            type="Normal",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Healer", ability="Life Force", moves=[life_force])
        defender_spec = _pokemon_spec("Target", moves=[life_force])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.hp - attacker.tick_value())
        before = attacker.hp
        battle.resolve_move_targets(attacker_id, life_force, defender_id, attacker.position)
        self.assertGreater(attacker.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Life Force"
                and event.get("effect") == "heal"
                for event in battle.log
            )
        )

    def test_light_metal_reduces_weight_class(self):
        spec = _pokemon_spec("Light", ability="Light Metal", weight=5)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(mon.weight_class(), 3)

    def test_lightning_kicks_grants_kick_priority(self):
        lightning_kicks = MoveSpec(
            name="Lightning Kicks",
            type="Electric",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        kick = MoveSpec(
            name="Double Kick",
            type="Fighting",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Kicker", ability="Lightning Kicks", moves=[lightning_kicks, kick])
        defender_spec = _pokemon_spec("Target", moves=[kick])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, lightning_kicks, defender_id, battle.pokemon[defender_id].position)
        battle.log = []
        battle.rng = SequenceRNG([20] * 200)
        battle.resolve_move_targets(attacker_id, kick, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lightning Kicks"
                and event.get("effect") == "priority"
                for event in battle.log
            )
        )

    def test_lightning_rod_redirects_and_absorbs(self):
        thunder = MoveSpec(
            name="Thunderbolt",
            type="Electric",
            category="Special",
            db=10,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        trainer_a = TrainerState(identifier="a", name="A", team="players")
        trainer_b = TrainerState(identifier="b", name="B", team="foes")
        attacker = PokemonState(
            spec=_pokemon_spec("Attacker", moves=[thunder]),
            controller_id="a",
            position=(2, 2),
            active=True,
        )
        target = PokemonState(
            spec=_pokemon_spec("Target", moves=[thunder]),
            controller_id="b",
            position=(2, 3),
            active=True,
        )
        rod = PokemonState(
            spec=_pokemon_spec("Rod", ability="Lightning Rod", moves=[thunder]),
            controller_id="b",
            position=(2, 4),
            active=True,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": attacker, "b-1": target, "b-2": rod},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)
        battle.round = 1
        rod_before = rod.hp
        target_before = target.hp
        battle.resolve_move_targets("a-1", thunder, "b-1", target.position)
        self.assertEqual(target.hp, target_before)
        self.assertEqual(rod.hp, rod_before)
        self.assertEqual(rod.combat_stages.get("spatk"), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lightning Rod"
                and event.get("effect") == "redirect"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lightning Rod"
                and event.get("effect") == "absorb"
                for event in battle.log
            )
        )

    def test_line_charge_blocks_diagonal_shift(self):
        trainer = TrainerState(identifier="a", name="A")
        spec = _pokemon_spec("Shifter", ability="Line Charge")
        mon = PokemonState(spec=spec, controller_id="a", position=(2, 2), active=True)
        battle = BattleState(
            trainers={"a": trainer},
            pokemon={"a-1": mon},
            grid=GridState(width=10, height=10),
        )
        action = ShiftAction(actor_id="a-1", destination=(3, 3))
        with self.assertRaises(ValueError):
            action.validate(battle)

    def test_liquid_ooze_reverses_drain(self):
        absorb = MoveSpec(
            name="Absorb",
            type="Grass",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Drainer", moves=[absorb], spatk=14)
        defender_spec = _pokemon_spec("Ooze", ability="Liquid Ooze", moves=[absorb])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = attacker.max_hp()
        before = attacker.hp
        battle.rng = SequenceRNG([20] * 200)
        battle.resolve_move_targets(attacker_id, absorb, defender_id, battle.pokemon[defender_id].position)
        self.assertLess(attacker.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Liquid Ooze"
                and event.get("effect") in {"drain_reversal", "drain_reverse"}
                for event in battle.log
            )
        )

    def test_lunchbox_grants_temp_hp_on_food_buff(self):
        spec = _pokemon_spec("Snacker", ability="Lunchbox")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.food_buffs.append({"effect": "Restores 30 HP"})
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        mon.hp = max(1, mon.max_hp() // 2)
        before = mon.temp_hp
        events = battle._apply_food_buff_start("a-1")
        self.assertEqual(mon.temp_hp, before + 5)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Lunchbox"
                and event.get("effect") == "temp_hp"
                for event in events
            )
        )
