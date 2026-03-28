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


class AuditBatch63AbilityTests(unittest.TestCase):
    def test_quick_draw_interrupts_and_penalizes_accuracy(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", moves=[tackle], atk=14)
        defender_spec = _pokemon_spec("Quick", abilities=["Quick Draw"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        attacker = battle.pokemon[attacker_id]
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertTrue(battle.pokemon[defender_id].get_temporary_effects("quick_draw_used"))
        penalties = attacker.get_temporary_effects("accuracy_penalty")
        self.assertTrue(any(entry.get("amount") == 2 for entry in penalties))
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Quick Draw"
                and event.get("effect") == "interrupt"
                for event in battle.log
            )
        )

    def test_unseen_fist_blocks_quick_draw_interrupt(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", abilities=["Unseen Fist"], moves=[tackle], atk=14)
        defender_spec = _pokemon_spec("Quick", abilities=["Quick Draw"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        self.assertFalse(battle.pokemon[defender_id].get_temporary_effects("quick_draw_used"))
        self.assertFalse(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Quick Draw"
                for event in battle.log
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Unseen Fist"
                and event.get("effect") == "interrupt_block"
                for event in battle.log
            )
        )

    def test_wandering_spirit_swaps_abilities_on_melee_hit(self):
        tackle = MoveSpec(
            name="Tackle",
            type="Normal",
            category="Physical",
            db=8,
            ac=2,
            range_kind="Melee",
            range_text="Melee, 1 Target",
        )
        attacker_spec = _pokemon_spec("Attacker", abilities=["Stench"], moves=[tackle], atk=14)
        defender_spec = _pokemon_spec("Wanderer", abilities=["Wandering Spirit"], moves=[tackle])
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        battle.resolve_move_targets(attacker_id, tackle, defender_id, battle.pokemon[defender_id].position)
        attacker = battle.pokemon[attacker_id]
        defender = battle.pokemon[defender_id]
        self.assertTrue(
            any(
                entry.get("ability") == "Wandering Spirit"
                for entry in attacker.get_temporary_effects("entrained_ability")
            )
        )
        self.assertTrue(
            any(
                entry.get("ability") == "Stench"
                for entry in defender.get_temporary_effects("entrained_ability")
            )
        )
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Wandering Spirit"
                for event in battle.log
            )
        )
