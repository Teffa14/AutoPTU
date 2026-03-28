import random
import unittest

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.rules import BattleState, GridState, PokemonState, TrainerState, TurnPhase
from auto_ptu.rules.battle_state import ActionType


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


def _build_battle(attacker_spec, defender_spec, *, attacker_pos=(2, 2), defender_pos=(4, 2)):
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
        grid=GridState(width=12, height=12),
    )
    battle.rng = SequenceRNG([19] * 50)
    battle.round = 1
    return battle, "a-1", "b-1"


class AuditBatch59AbilityTests(unittest.TestCase):
    def test_permafrost_errata_blocks_status_damage(self):
        spec = _pokemon_spec("Frosty", abilities=["Permafrost [Errata]"])
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        mon.statuses.append({"name": "Burned"})
        mon.mark_action(ActionType.STANDARD, "test")
        battle = BattleState(
            trainers={"a": TrainerState(identifier="a", name="A")},
            pokemon={"a-1": mon},
            grid=GridState(width=6, height=6),
        )
        before = mon.hp
        events = mon._handle_status_phase_effects(battle, TurnPhase.END, "a-1")
        self.assertEqual(mon.hp, before)
        self.assertTrue(
            any(
                event.get("type") == "ability"
                and event.get("ability") == "Permafrost [Errata]"
                and event.get("effect") == "status_block"
                for event in events
            )
        )

    def test_poltergeist_errata_grants_form_ability_and_move(self):
        spec = _pokemon_spec(
            "Rotom Heat",
            abilities=["Poltergeist [Errata]"],
            level=40,
        )
        mon = PokemonState(spec=spec, controller_id="a", position=(0, 0), active=True)
        self.assertTrue(mon.has_ability("Phantom Body"))
        self.assertTrue(
            any((move.name or "").strip().lower() == "overheat" for move in mon.spec.moves)
        )

    def test_pressure_errata_suppresses_nearby_foes(self):
        attacker_spec = _pokemon_spec("Pressor", abilities=["Pressure [Errata]"])
        defender_spec = _pokemon_spec("Target")
        battle, attacker_id, defender_id = _build_battle(attacker_spec, defender_spec)
        far_spec = _pokemon_spec("Far")
        far = PokemonState(
            spec=far_spec,
            controller_id=battle.trainers["b"].identifier,
            position=(10, 2),
            active=True,
        )
        battle.pokemon["b-2"] = far
        move = next(
            mv for mv in battle.pokemon[attacker_id].spec.moves if mv.name == "Pressure [Errata]"
        )
        battle.resolve_move_targets(attacker_id, move, attacker_id, battle.pokemon[attacker_id].position)
        self.assertTrue(battle.pokemon[defender_id].has_status("Suppressed"))
        self.assertFalse(battle.pokemon["b-2"].has_status("Suppressed"))


if __name__ == "__main__":
    unittest.main()
