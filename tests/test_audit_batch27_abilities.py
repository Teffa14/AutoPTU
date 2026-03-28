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


class AuditBatch27AbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        move_specials.initialize_move_specials()

    def test_cotton_down_slows_adjacent(self):
        move = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move])
        defender_spec = _pokemon_spec("Defender", ability="Cotton Down", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        ally = PokemonState(
            spec=_pokemon_spec("Ally", moves=[move]),
            controller_id="b",
            position=(3, 3),
            active=True,
        )
        battle.pokemon["b-2"] = ally
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.has_status("Slowed"))
        self.assertEqual(attacker.combat_stages.get("spd"), -1)
        self.assertTrue(ally.has_status("Slowed"))
        self.assertEqual(ally.combat_stages.get("spd"), -1)

    def test_curious_medicine_resets_allies_on_switch(self):
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
        ally = PokemonState(
            spec=_pokemon_spec("Ally", moves=[move]),
            controller_id="a",
            position=(2, 4),
            active=True,
        )
        ally.combat_stages["atk"] = 2
        replacement = PokemonState(
            spec=_pokemon_spec("Curious", ability="Curious Medicine", moves=[move]),
            controller_id="a",
            position=None,
            active=False,
        )
        battle = BattleState(
            trainers={"a": trainer_a, "b": trainer_b},
            pokemon={"a-1": outgoing, "a-2": replacement, "a-3": ally},
            grid=GridState(width=10, height=10),
        )
        battle.rng = SequenceRNG([20] * 200)
        battle.round = 1
        battle._apply_switch(
            outgoing_id="a-1",
            replacement_id="a-2",
            initiator_id="a",
            allow_replacement_turn=False,
            allow_immediate=False,
        )
        self.assertEqual(ally.combat_stages.get("atk"), 0)

    def test_damp_blocks_explosion(self):
        move = MoveSpec(
            name="Explosion",
            type="Normal",
            category="Physical",
            db=15,
            ac=2,
            range_kind="Burst",
            range_text="Burst 2",
        )
        attacker_spec = _pokemon_spec("Boomer", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        damp = PokemonState(
            spec=_pokemon_spec("Damp", ability="Damp", moves=[move]),
            controller_id="b",
            position=(2, 4),
            active=True,
        )
        battle.pokemon["b-2"] = damp
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        attacker_before = attacker.hp
        defender_before = defender.hp
        battle.resolve_move_targets(attacker_id, move, defender_id, defender.position)
        self.assertEqual(attacker.hp, attacker_before)
        self.assertEqual(defender.hp, defender_before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Damp"
                and event.get("effect") == "block"
                for event in battle.log
            )
        )

    def test_dancer_copies_dance_move(self):
        move = MoveSpec(
            name="Feather Dance",
            type="Flying",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
            effects_text="The target's Attack is lowered by -2 Combat Stages.",
        )
        attacker_spec = _pokemon_spec("User", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        dancer = PokemonState(
            spec=_pokemon_spec("Dancer", ability="Dancer", moves=[move]),
            controller_id="b",
            position=(2, 5),
            active=True,
        )
        battle.pokemon["b-2"] = dancer
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        self.assertEqual(battle.pokemon[defender_id].combat_stages.get("atk"), -4)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Dancer"
                and event.get("effect") == "copy"
                for event in battle.log
            )
        )

    def test_dauntless_shield_grants_defense_stage(self):
        spec = _pokemon_spec("Zamazenta", ability="Dauntless Shield")
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertEqual(mon.combat_stages.get("def"), 1)

    def test_dazzling_blocks_priority(self):
        move = MoveSpec(
            name="Dazzling",
            type="Fairy",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Dazzler", ability="Dazzling", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(defender.get_temporary_effects("priority_blocked"))
        self.assertTrue(defender.get_temporary_effects("initiative_penalty"))
        self.assertTrue(attacker.get_temporary_effects("no_interrupts"))

    def test_defeatist_applies_below_half(self):
        spec = _pokemon_spec("Defeat", ability="Defeatist", hp_stat=10)
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.hp = 10
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        battle.round = 1
        mon._handle_ability_phase_effects(battle, TurnPhase.START, "a-1")
        self.assertEqual(mon.combat_stages.get("atk"), -1)
        self.assertEqual(mon.combat_stages.get("spatk"), -1)
        self.assertEqual(mon.combat_stages.get("spd"), 2)

    def test_defy_death_heals_injuries(self):
        move = MoveSpec(
            name="Defy Death",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Life", ability="Defy Death", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.injuries = 3
        battle.resolve_move_targets(attacker_id, move, defender_id, attacker.position)
        self.assertEqual(attacker.injuries, 1)

    def test_desert_weather_reduces_fire_damage_in_sun(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], types=["Fire"])
        defender_spec = _pokemon_spec("Target", moves=[move])
        defender_weather_spec = _pokemon_spec("Target", ability="Desert Weather", moves=[move])

        battle_normal, a_id, d_id = _build_battle(attacker_spec, defender_spec)
        battle_normal.weather = "Sunny"
        battle_normal.rng = SequenceRNG([20] + [3] * 50)
        defender = battle_normal.pokemon[d_id]
        before = defender.hp
        battle_normal.resolve_move_targets(a_id, move, d_id, defender.position)
        normal_damage = before - defender.hp

        battle_weather, a2_id, d2_id = _build_battle(attacker_spec, defender_weather_spec)
        battle_weather.weather = "Sunny"
        battle_weather.rng = SequenceRNG([20] + [3] * 50)
        defender2 = battle_weather.pokemon[d2_id]
        before2 = defender2.hp
        battle_weather.resolve_move_targets(a2_id, move, d2_id, defender2.position)
        weather_damage = before2 - defender2.hp

        self.assertEqual(weather_damage * 2, normal_damage)

    def test_designer_fashion_designer_crafts_item(self):
        move = MoveSpec(
            name="Fashion Designer",
            type="Grass",
            category="Status",
            db=0,
            ac=2,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Designer", ability="Fashion Designer", moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect("fashion_designer_choice", item="Dew Cup")
        battle.resolve_move_targets(attacker_id, move, defender_id, attacker.position)
        self.assertTrue(any(item.get("name") == "Occa Berry" for item in attacker.spec.items))
