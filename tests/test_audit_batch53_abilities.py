import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, calculations


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


class AuditBatch53AbilityTests(unittest.TestCase):
    def test_leaf_guard_errata_cures_status(self):
        move = MoveSpec(
            name="Leaf Guard [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Guard", abilities=["Leaf Guard [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.statuses.append({"name": "Burned"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        self.assertFalse(attacker.has_status("Burned"))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Leaf Guard [Errata]"
                and event.get("effect") == "cure"
                for event in battle.log
            )
        )

    def test_leaf_guard_errata_ignores_frequency_in_sun(self):
        move = MoveSpec(
            name="Leaf Guard [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Guard", abilities=["Leaf Guard [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.weather = "Sunny"
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)

    def test_mega_launcher_errata_boosts_pulse_moves(self):
        pulse = MoveSpec(
            name="Water Pulse",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec(
            "Blaster", abilities=["Mega Launcher [Errata]"], moves=[pulse], spatk=14, types=["Water"]
        )
        defender_spec = _pokemon_spec("Target", moves=[pulse])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, pulse, defender_id, battle.pokemon[defender_id].position)
        move_events = [event for event in battle.log if event.get("type") == "move" and event.get("move") == "Water Pulse"]
        self.assertTrue(move_events)
        self.assertEqual(move_events[-1].get("effective_db"), 15)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Mega Launcher [Errata]"
                and event.get("effect") == "db_bonus"
                for event in battle.log
            )
        )

    def test_multiscale_errata_resists_at_full_hp(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[move], spatk=12, types=["Fire"])
        base_defender_spec = _pokemon_spec("Target", moves=[move], types=["Grass"], hp_stat=20)
        errata_defender_spec = _pokemon_spec(
            "Target", abilities=["Multiscale [Errata]"], moves=[move], types=["Grass"], hp_stat=20
        )
        battle_base, attacker_id, defender_id = _build_battle(attacker_spec, base_defender_spec)
        battle_base.rng = SequenceRNG([15] * 40)
        before_base = battle_base.pokemon[defender_id].hp
        battle_base.resolve_move_targets(attacker_id, move, defender_id, battle_base.pokemon[defender_id].position)
        base_damage = before_base - battle_base.pokemon[defender_id].hp

        battle_errata, attacker_id2, defender_id2 = _build_battle(attacker_spec, errata_defender_spec)
        battle_errata.rng = SequenceRNG([15] * 40)
        before_errata = battle_errata.pokemon[defender_id2].hp
        battle_errata.resolve_move_targets(attacker_id2, move, defender_id2, battle_errata.pokemon[defender_id2].position)
        errata_damage = before_errata - battle_errata.pokemon[defender_id2].hp
        self.assertLess(errata_damage, base_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Multiscale [Errata]"
                and event.get("effect") == "type_resist"
                for event in battle_errata.log
            )
        )

    def test_no_guard_errata_accuracy_bonus(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker_with = PokemonState(
            spec=_pokemon_spec("A", abilities=["No Guard [Errata]"], moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        defender = PokemonState(
            spec=_pokemon_spec("D", moves=[move], spdef=30),
            controller_id="b",
            position=(0, 1),
            active=True,
        )
        result_with = calculations.attack_hits(SequenceRNG([5]), attacker_with, defender, move)

        attacker_without = PokemonState(
            spec=_pokemon_spec("A", moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        result_without = calculations.attack_hits(SequenceRNG([5]), attacker_without, defender, move)
        self.assertTrue(result_with.get("hit"))
        self.assertFalse(result_without.get("hit"))

    def test_no_guard_errata_bonus_against_user(self):
        move = MoveSpec(
            name="Ember",
            type="Fire",
            category="Special",
            db=6,
            ac=2,
            range_kind="Ranged",
            range_text="Range 6, 1 Target",
        )
        attacker = PokemonState(
            spec=_pokemon_spec("A", moves=[move]),
            controller_id="a",
            position=(0, 0),
            active=True,
        )
        defender_with = PokemonState(
            spec=_pokemon_spec("D", abilities=["No Guard [Errata]"], moves=[move], spdef=30),
            controller_id="b",
            position=(0, 1),
            active=True,
        )
        defender_without = PokemonState(
            spec=_pokemon_spec("D", moves=[move], spdef=30),
            controller_id="b",
            position=(0, 1),
            active=True,
        )
        hit_with = calculations.attack_hits(SequenceRNG([5]), attacker, defender_with, move)
        hit_without = calculations.attack_hits(SequenceRNG([5]), attacker, defender_without, move)
        self.assertTrue(hit_with.get("hit"))
        self.assertFalse(hit_without.get("hit"))


if __name__ == "__main__":
    unittest.main()
