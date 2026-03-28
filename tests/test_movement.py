from __future__ import annotations

import random

import unittest

from auto_ptu.csv_repository import PTUCsvRepository
from auto_ptu.rules import (
    BattleState,
    GridState,
    PokemonState,
    ShiftAction,
    TrainerState,
)
from auto_ptu.rules import movement


def _grid_with_blocker() -> GridState:
    return GridState(
        width=5,
        height=5,
        blockers={(2, 2)},
        tiles={},
    )


class MovementTests(unittest.TestCase):
    def test_overland_blocked_by_wall(self) -> None:
        repo = PTUCsvRepository()
        pikachu = repo.build_pokemon_spec("Pikachu", level=20, move_names=["Quick Attack"])
        trainer = TrainerState(identifier="ash", name="Ash")
        state = PokemonState(spec=pikachu, controller_id=trainer.identifier, position=(1, 2))
        foe = TrainerState(identifier="gary", name="Gary")
        foe_mon = PokemonState(spec=repo.build_pokemon_spec("Eevee", level=18), controller_id=foe.identifier, position=(4, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer, foe.identifier: foe},
            pokemon={"ash-1": state, "gary-1": foe_mon},
            grid=_grid_with_blocker(),
            rng=random.Random(1),
        )
        with self.assertRaises(ValueError):
            battle.queue_action(ShiftAction(actor_id="ash-1", destination=(2, 2)))

    def test_flying_ignores_blockers(self) -> None:
        repo = PTUCsvRepository()
        pidgeotto = repo.build_pokemon_spec("Pidgeotto", level=20)
        trainer = TrainerState(identifier="blue", name="Blue")
        flyer = PokemonState(spec=pidgeotto, controller_id=trainer.identifier, position=(1, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"blue-1": flyer},
            grid=_grid_with_blocker(),
            rng=random.Random(7),
        )
        action = ShiftAction(actor_id="blue-1", destination=(3, 2))
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(flyer.position, (3, 2))

    def test_burrower_can_cross_blockers(self) -> None:
        repo = PTUCsvRepository()
        sandshrew = repo.build_pokemon_spec("Sandshrew", level=15)
        trainer = TrainerState(identifier="brock", name="Brock")
        mon = PokemonState(spec=sandshrew, controller_id=trainer.identifier, position=(1, 2))
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"brock-1": mon},
            grid=_grid_with_blocker(),
        )
        action = ShiftAction(actor_id="brock-1", destination=(3, 2))
        battle.queue_action(action)
        battle.resolve_next_action()
        self.assertEqual(mon.position, (3, 2))

    def test_swift_swim_extends_water_reach(self) -> None:
        repo = PTUCsvRepository()
        squirtle = repo.build_pokemon_spec("Squirtle", level=18)
        squirtle.abilities.append({"name": "Swift Swim"})
        trainer = TrainerState(identifier="ash", name="Ash")
        mon = PokemonState(spec=squirtle, controller_id=trainer.identifier, position=(1, 1))
        water_tiles = {
            (1, y): {"type": "water"}
            for y in range(1, 9)
        }
        grid = GridState(width=3, height=10, tiles=water_tiles)
        battle = BattleState(
            trainers={trainer.identifier: trainer},
            pokemon={"ash-1": mon},
            weather="Clear",
            grid=grid,
        )
        reachable_clear = movement.legal_shift_tiles(battle, "ash-1")
        self.assertNotIn((1, 8), reachable_clear)
        battle.weather = "Rain"
        reachable_rain = movement.legal_shift_tiles(battle, "ash-1")
        self.assertIn((1, 8), reachable_rain)

    def test_shift_destination_cannot_be_occupied(self) -> None:
        repo = PTUCsvRepository()
        attacker = PokemonState(
            spec=repo.build_pokemon_spec("Passimian", level=25),
            controller_id="ash",
            position=(1, 1),
        )
        defender = PokemonState(
            spec=repo.build_pokemon_spec("Stunfisk", level=25),
            controller_id="gary",
            position=(2, 1),
        )
        battle = BattleState(
            trainers={
                "ash": TrainerState(identifier="ash", name="Ash"),
                "gary": TrainerState(identifier="gary", name="Gary"),
            },
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=GridState(width=6, height=6, tiles={}),
            rng=random.Random(3),
        )
        with self.assertRaises(ValueError):
            battle.queue_action(ShiftAction(actor_id="ash-1", destination=(2, 1)))

    def test_legal_shift_tiles_excludes_occupied_tiles(self) -> None:
        repo = PTUCsvRepository()
        attacker = PokemonState(
            spec=repo.build_pokemon_spec("Passimian", level=25),
            controller_id="ash",
            position=(1, 1),
        )
        defender = PokemonState(
            spec=repo.build_pokemon_spec("Stunfisk", level=25),
            controller_id="gary",
            position=(2, 1),
        )
        battle = BattleState(
            trainers={
                "ash": TrainerState(identifier="ash", name="Ash"),
                "gary": TrainerState(identifier="gary", name="Gary"),
            },
            pokemon={"ash-1": attacker, "gary-1": defender},
            grid=GridState(width=6, height=6, tiles={}),
            rng=random.Random(5),
        )
        reachable = movement.legal_shift_tiles(battle, "ash-1")
        self.assertNotIn((2, 1), reachable)
