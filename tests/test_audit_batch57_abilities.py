import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState
from auto_ptu.rules.battle_state import UseMoveAction


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
    battle.rng = SequenceRNG([19] * 50)
    return battle, "a-1", "b-1"


class AuditBatch57AbilityTests(unittest.TestCase):
    def test_odious_spray_errata_modifies_poison_gas(self):
        poison_gas = MoveSpec(
            name="Poison Gas",
            type="Poison",
            category="Status",
            db=0,
            ac=4,
            range_kind="Burst",
            range_text="Burst 1",
        )
        attacker_spec = _pokemon_spec("Odious", abilities=["Odious Spray [Errata]"], moves=[poison_gas])
        defender_spec = _pokemon_spec("Target", moves=[poison_gas])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(attacker_id, poison_gas.name, defender_id, battle.pokemon[defender_id].position)
        effective = action._apply_ability_move_tweaks(battle, battle.pokemon[attacker_id], poison_gas)
        self.assertEqual(effective.range_kind, "Ranged")
        self.assertEqual(effective.target_kind, "Ranged")
        self.assertEqual(effective.target_range, 8)
        self.assertEqual(effective.ac, 2)

    def test_odious_spray_errata_flinches_poison_gas(self):
        poison_gas = MoveSpec(
            name="Poison Gas",
            type="Poison",
            category="Status",
            db=0,
            ac=2,
            range_kind="Ranged",
            range_text="Range 8, 1 Target",
        )
        attacker_spec = _pokemon_spec("Odious", abilities=["Odious Spray [Errata]"], moves=[poison_gas])
        defender_spec = _pokemon_spec("Target", moves=[poison_gas])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, poison_gas, defender_id, battle.pokemon[defender_id].position)
        defender = battle.pokemon[defender_id]
        self.assertTrue(defender.has_status("Flinch") or defender.has_status("Flinched"))
        self.assertTrue(
            any(
                event.get("type") == "status"
                and event.get("status") in {"Flinch", "Flinched"}
                for event in battle.log
            )
        )


if __name__ == "__main__":
    unittest.main()
