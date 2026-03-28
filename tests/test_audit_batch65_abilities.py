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


class AuditBatch65AbilityTests(unittest.TestCase):
    def test_water_compaction_raises_defense_on_water_hit(self):
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
        defender_spec = _pokemon_spec("Compaction", abilities=["Water Compaction"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("def"), 2)

    def test_wily_adds_extra_status_target(self):
        status_move = MoveSpec(
            name="Wily Poison",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Melee",
            range_value=1,
            target_kind="Melee",
            target_range=1,
            range_text="Melee, 1 Target",
            effects_text="The target is Poisoned.",
        )
        attacker_spec = _pokemon_spec("Wily", abilities=["Wily"], moves=[status_move])
        defender_spec = _pokemon_spec("Target", moves=[status_move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        extra = PokemonState(
            spec=defender_spec,
            controller_id="b",
            position=(3, 2),
            active=True,
        )
        battle.pokemon["b-2"] = extra
        battle.resolve_move_targets(attacker_id, status_move, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Poisoned"))
        self.assertTrue(extra.has_status("Poisoned"))

    def test_neutralizing_gas_suppresses_abilities_in_burst(self):
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
        defender_spec = _pokemon_spec("Compaction", abilities=["Water Compaction"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        neutralizer = PokemonState(
            spec=_pokemon_spec("Gas", abilities=["Neutralizing Gas"], moves=[move]),
            controller_id="b",
            position=(2, 2),
            active=True,
        )
        battle.pokemon["b-2"] = neutralizer
        battle.resolve_move_targets(attacker_id, move, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.combat_stages.get("def", 0), 0)
