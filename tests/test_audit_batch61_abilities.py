import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState


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


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(2, 6)):
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


class AuditBatch61AbilityTests(unittest.TestCase):
    def test_rock_head_errata_adds_charge_bonus(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Ram", abilities=["Rock Head [Errata]"], moves=[tackle], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.add_temporary_effect(
            "rock_head_errata_run",
            round=battle.round,
            dir=(0, 1),
            distance=4,
        )
        battle.rng = SequenceRNG([20] + [3] * 50)
        before = battle.pokemon[defender_id].hp
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        charged_damage = before - battle.pokemon[defender_id].hp

        normal_spec = _pokemon_spec("Normal", moves=[tackle], atk=14)
        battle2, a2, d2 = _build_battle(normal_spec, defender_spec)
        battle2.rng = SequenceRNG([20] + [3] * 50)
        before2 = battle2.pokemon[d2].hp
        battle2.resolve_move_targets(a2, tackle, d2, battle2.pokemon[d2].position)
        normal_damage = before2 - battle2.pokemon[d2].hp

        self.assertGreater(charged_damage, normal_damage)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rock Head [Errata]"
                and event.get("effect") == "damage_bonus"
                for event in battle.log
            )
        )

    def test_rocket_errata_moves_first_next_round(self):
        move = MoveSpec(
            name="Rocket [Errata]",
            type="Flying",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Jet", abilities=["Rocket [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Slowpoke", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        attacker = battle.pokemon[attacker_id]
        self.assertTrue(attacker.get_temporary_effects("rocket_initiative"))
        self.assertTrue(attacker.get_temporary_effects("no_interrupts"))
        battle.start_round()
        first_pokemon_entry = next(
            entry for entry in battle.initiative_order if entry.actor_id not in battle.trainers
        )
        self.assertEqual(first_pokemon_entry.actor_id, attacker_id)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Rocket [Errata]"
                for event in battle.log
            )
        )

    def test_root_down_errata_grants_damage_reduction(self):
        move = MoveSpec(
            name="Root Down [Errata]",
            type="Grass",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Rooter", abilities=["Root Down [Errata]"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.statuses.append({"name": "Ingrain"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, attacker.position)
        reductions = attacker.get_temporary_effects("damage_reduction")
        self.assertTrue(any(entry.get("amount") == 5 for entry in reductions))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Root Down [Errata]"
                and event.get("effect") == "damage_reduction"
                for event in battle.log
            )
        )
