import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules import calculations, targeting


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


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(3, 2)):
    trainer_a = TrainerState(identifier="a", name="A", team="players")
    trainer_b = TrainerState(identifier="b", name="B", team="players")
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
    battle.rng = SequenceRNG([19] * 50)
    return battle, "a-1", "b-1"


class AuditBatch58AbilityTests(unittest.TestCase):
    def test_perception_errata_adds_evasion(self):
        errata_spec = _pokemon_spec("Watcher", abilities=["Perception [Errata]"], spd=10)
        base_spec = _pokemon_spec("Base", spd=10)
        errata = PokemonState(spec=errata_spec, controller_id="a", position=(0, 0), active=True)
        base = PokemonState(spec=base_spec, controller_id="a", position=(0, 0), active=True)
        errata_value = calculations.evasion_value(errata, "physical")
        base_value = calculations.evasion_value(base, "physical")
        self.assertEqual(errata_value, base_value + 1)

    def test_perception_errata_disengages_on_ally_aoe(self):
        move = MoveSpec(
            name="Surf",
            type="Water",
            category="Special",
            db=8,
            ac=2,
            range_kind="Burst",
            range_value=1,
            area_kind="Burst",
            area_value=1,
            target_kind="Self",
            target_range=0,
            range_text="Burst 1",
        )
        attacker_spec = _pokemon_spec("Ally", moves=[move])
        defender_spec = _pokemon_spec("Watcher", abilities=["Perception [Errata]"], moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        origin = battle.pokemon[defender_id].position
        battle.resolve_move_targets(attacker_id, move, defender_id, origin)
        defender = battle.pokemon[defender_id]
        tiles = targeting.affected_tiles(
            battle.grid, battle.pokemon[attacker_id].position, origin, move
        )
        self.assertNotEqual(defender.position, origin)
        self.assertNotIn(defender.position, tiles)
        self.assertEqual(targeting.chebyshev_distance(origin, defender.position), 1)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Perception [Errata]"
                and event.get("effect") == "disengage"
                for event in battle.log
            )
        )


if __name__ == "__main__":
    unittest.main()
