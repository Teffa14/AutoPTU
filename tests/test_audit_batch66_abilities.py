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


class AuditBatch66AbilityTests(unittest.TestCase):
    def test_ripen_doubles_berry_heal(self):
        attacker_spec = _pokemon_spec(
            "Ripen",
            abilities=["Ripen"],
            items=[{"name": "Oran Berry", "effect": "Restores 5 Hit Points.", "item": "Oran Berry"}],
            hp_stat=10,
        )
        defender_spec = _pokemon_spec("Target")
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        attacker.hp = max(1, attacker.max_hp() - 10)
        before = attacker.hp
        events = battle._apply_food_buff_start(attacker_id, force=True)
        self.assertEqual(attacker.hp, before + 10)
        self.assertTrue(any(event.get("effect") == "heal_fixed" for event in events))

    def test_screen_cleaner_clears_blessings(self):
        move = MoveSpec(
            name="Screen Cleaner",
            type="Normal",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Field",
        )
        attacker_spec = _pokemon_spec("Cleaner", abilities=["Screen Cleaner"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.pokemon[defender_id].statuses.append({"name": "Blessing"})
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertFalse(battle.pokemon[defender_id].statuses)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Screen Cleaner"
                and event.get("effect") == "blessings_cleared"
                for event in battle.log
            )
        )

    def test_zen_snowed_unlocks_punch_moves(self):
        move = MoveSpec(
            name="Zen Snowed",
            type="Ice",
            category="Status",
            db=0,
            ac=None,
            range_kind="Self",
            range_text="Self",
        )
        attacker_spec = _pokemon_spec("Zen", abilities=["Zen Snowed"], moves=[move])
        defender_spec = _pokemon_spec("Target", moves=[move])
        battle, attacker_id, _ = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        names = {str(mv.name).strip().lower() for mv in battle.pokemon[attacker_id].spec.moves}
        self.assertIn("ice punch", names)
        self.assertIn("fire punch", names)
