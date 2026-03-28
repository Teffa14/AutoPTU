import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, UseMoveAction


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
    items=None,
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
        items=items or [],
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


class AuditBatch64AbilityTests(unittest.TestCase):
    def test_queenly_majesty_blocks_priority_moves(self):
        priority = MoveSpec(
            name="Quick Attack",
            type="Normal",
            category="Physical",
            db=6,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
            priority=1,
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[priority], atk=14)
        defender_spec = _pokemon_spec("Queen", abilities=["Queenly Majesty"], moves=[priority])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        action = UseMoveAction(actor_id=attacker_id, move_name=priority.name, target_id=defender_id)
        with self.assertRaises(ValueError):
            action.validate(battle)

    def test_radiant_beam_converts_grass_move_to_line(self):
        leaf = MoveSpec(
            name="Leaf Blade",
            type="Grass",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Radiant", abilities=["Radiant Beam"], moves=[leaf], atk=14)
        defender_spec = _pokemon_spec("Target", moves=[leaf])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        action = UseMoveAction(actor_id=attacker_id, move_name=leaf.name, target_id=defender_id)
        converted = action._apply_ability_move_tweaks(battle, attacker, leaf, consume=False)
        self.assertEqual(converted.range_kind, "Self")
        self.assertEqual(converted.target_kind, "Self")
        self.assertEqual((converted.area_kind or "").lower(), "line")
        self.assertEqual(converted.area_value, 4)

    def test_rks_system_memory_sets_type_and_resists(self):
        shadow = MoveSpec(
            name="Shadow Claw",
            type="Ghost",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        defender_spec = _pokemon_spec(
            "RKS",
            abilities=["RKS System"],
            moves=[shadow],
            items=[{"name": "Fire Memory"}],
            types=["Normal"],
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[shadow], atk=14)
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        defender = battle.pokemon[defender_id]
        self.assertEqual(defender.spec.types, ["Fire"])
        before = defender.hp
        battle.resolve_move_targets(attacker_id, shadow, defender_id, defender.position)
        self.assertEqual(defender.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "RKS System"
                for event in battle.log
            )
        )
