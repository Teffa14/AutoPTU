from __future__ import annotations

import json
import unittest
from pathlib import Path

from auto_ptu.data_models import MoveSpec, PokemonSpec
from auto_ptu.api.engine_facade import EngineFacade
from auto_ptu.rules import InitiativeEntry, TrainerState
from auto_ptu.rules.battle_state import BattleState, GridState, PokemonState
from auto_ptu.rules.hooks import move_specials
from auto_ptu.rules.move_traits import has_range_keyword, move_has_keyword


def _pokemon_spec(name: str, moves: list[MoveSpec]) -> PokemonSpec:
    return PokemonSpec(
        species=name,
        name=name,
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        moves=moves,
    )


def _hazard_moves_from_compiled() -> list[MoveSpec]:
    path = Path("auto_ptu/data/compiled/moves.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    hazards: list[MoveSpec] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        spec = MoveSpec.from_dict(entry)
        if move_has_keyword(spec, "Hazard") or has_range_keyword(spec, "Hazard"):
            hazards.append(spec)
    return hazards


def _advance_to_pokemon_turn(battle: BattleState) -> InitiativeEntry:
    entry = battle.advance_turn()
    while entry and entry.actor_id in battle.trainers:
        battle.end_turn()
        entry = battle.advance_turn()
    if entry is None:
        raise AssertionError("Expected an active Pokemon turn.")
    return entry


class HazardMoveTests(unittest.TestCase):
    def test_compiled_hazard_moves_present(self) -> None:
        move_specials.initialize_move_specials()
        hazards = _hazard_moves_from_compiled()
        names = sorted({move.name for move in hazards})
        print(f"Hazard moves (compiled): {names}")
        expected = sorted(["Barrier", "Spikes", "Stealth Rock", "Sticky Web", "Toxic Spikes"])
        self.assertEqual(names, expected)
        for move in hazards:
            with self.subTest(move=move.name):
                has_handler = move_specials._has_specific_handler(move.name.lower())
                print(f"Handler check: {move.name} -> {has_handler}")
                self.assertTrue(has_handler)

    def test_hazard_moves_apply_grid_effects(self) -> None:
        move_specials.initialize_move_specials()
        hazards = {move.name: move for move in _hazard_moves_from_compiled()}
        grid = GridState(width=3, height=3)
        attacker = PokemonState(spec=_pokemon_spec("Hazarder", list(hazards.values())), controller_id="ash", position=(1, 1))
        battle = BattleState(trainers={}, pokemon={"ash-1": attacker}, grid=grid)
        expected_hazards = {
            "Stealth Rock": "stealth_rock",
            "Spikes": "spikes",
            "Sticky Web": "sticky_web",
            "Toxic Spikes": "toxic_spikes",
        }

        for move_name, hazard_key in expected_hazards.items():
            with self.subTest(move=move_name):
                move = hazards[move_name]
                battle.grid.tiles.clear()
                events = battle._handle_move_special_effects(
                    attacker_id="ash-1",
                    attacker=attacker,
                    defender_id=None,
                    defender=None,
                    move=move,
                    result={"hit": True},
                    damage_dealt=0,
                )
                tile = battle.grid.tiles.get((1, 1), {})
                tile_hazards = tile.get("hazards", {}) if isinstance(tile, dict) else {}
                print(f"{move_name} hazards: {tile_hazards}")
                self.assertIn(hazard_key, tile_hazards)
                self.assertTrue([evt for evt in events if evt.get("effect") == hazard_key])

        barrier = hazards["Barrier"]
        battle.grid.tiles.clear()
        battle.grid.blockers.clear()
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=barrier,
            result={"hit": True},
            damage_dealt=0,
        )
        blockers = sorted(battle.grid.blockers)
        print(f"Barrier blockers: {blockers}")
        self.assertEqual(len(blockers), 4)
        self.assertTrue([evt for evt in events if evt.get("effect") == "barrier"])

    def test_hazard_clearing_moves_and_swap(self) -> None:
        move_specials.initialize_move_specials()
        grid = GridState(
            width=4,
            height=4,
            tiles={
                (1, 1): {"hazards": {"spikes": 1, "toxic_spikes": 2}},
                (2, 2): {"hazards": {"stealth_rock": 1}},
            },
        )
        attacker = PokemonState(
            spec=_pokemon_spec(
                "Cleaner",
                [
                    MoveSpec(name="Defog", type="Flying", category="Status", ac=None),
                    MoveSpec(name="Steel Roller", type="Steel", category="Physical", db=8, ac=2),
                    MoveSpec(name="Rapid Spin", type="Normal", category="Physical", db=2, ac=2),
                    MoveSpec(name="Court Change", type="Normal", category="Status", ac=None),
                ],
            ),
            controller_id="ash",
            position=(1, 1),
        )
        battle = BattleState(trainers={}, pokemon={"ash-1": attacker}, grid=grid)

        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker.spec.moves[0],
            result={"hit": True},
            damage_dealt=0,
        )
        remaining = {coord: meta.get("hazards") for coord, meta in battle.grid.tiles.items()}
        print(f"Defog hazards after clear: {remaining}")
        self.assertTrue(all(not entry for entry in remaining.values()))
        self.assertTrue([evt for evt in events if evt.get("effect") == "defog"])

        battle.grid.tiles[(1, 1)] = {"hazards": {"spikes": 1}}
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker.spec.moves[1],
            result={"hit": True},
            damage_dealt=0,
        )
        remaining = {coord: meta.get("hazards") for coord, meta in battle.grid.tiles.items()}
        print(f"Steel Roller hazards after clear: {remaining}")
        self.assertTrue(all(not entry for entry in remaining.values()))
        self.assertTrue([evt for evt in events if evt.get("effect") == "steel_roller"])

        battle.grid.tiles[(1, 1)] = {"hazards": {"sticky_web": 1}}
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker.spec.moves[2],
            result={"hit": True},
            damage_dealt=0,
        )
        remaining = {coord: meta.get("hazards") for coord, meta in battle.grid.tiles.items()}
        print(f"Rapid Spin hazards after clear: {remaining}")
        self.assertTrue(all(not entry for entry in remaining.values()))
        self.assertTrue([evt for evt in events if evt.get("effect") == "rapid_spin"])

        battle.grid.tiles[(1, 1)] = {"hazards": {"spikes": 2}}
        events = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker,
            defender_id=None,
            defender=None,
            move=attacker.spec.moves[3],
            result={"hit": True},
            damage_dealt=0,
        )
        remaining = {coord: meta.get("hazards") for coord, meta in battle.grid.tiles.items()}
        print(f"Court Change hazards after swap: {remaining}")
        self.assertEqual(remaining[(1, 1)], {"spikes": 2})
        self.assertTrue([evt for evt in events if evt.get("effect") == "court_change"])

    def test_pledge_combo_creates_fire_hazards(self) -> None:
        move_specials.initialize_move_specials()
        grid = GridState(width=4, height=4)
        attacker_a = PokemonState(
            spec=_pokemon_spec(
                "FireUser",
                [MoveSpec(name="Fire Pledge", type="Fire", category="Special", db=6, ac=2)],
            ),
            controller_id="ash",
            position=(1, 1),
        )
        attacker_b = PokemonState(
            spec=_pokemon_spec(
                "GrassUser",
                [MoveSpec(name="Grass Pledge", type="Grass", category="Special", db=6, ac=2)],
            ),
            controller_id="ash",
            position=(1, 2),
        )
        defender = PokemonState(
            spec=_pokemon_spec("Target", [MoveSpec(name="Tackle", type="Normal", category="Physical", db=4, ac=2)]),
            controller_id="foe",
            position=(2, 2),
        )
        battle = BattleState(
            trainers={},
            pokemon={
                "ash-1": attacker_a,
                "ash-2": attacker_b,
                "foe-1": defender,
            },
            grid=grid,
        )
        battle.round = 1
        attacker_a.active = True
        attacker_b.active = True
        defender.active = True
        events_a = battle._handle_move_special_effects(
            attacker_id="ash-1",
            attacker=attacker_a,
            defender_id="foe-1",
            defender=defender,
            move=attacker_a.spec.moves[0],
            result={"hit": True},
            damage_dealt=0,
        )
        events_b = battle._handle_move_special_effects(
            attacker_id="ash-2",
            attacker=attacker_b,
            defender_id="foe-1",
            defender=defender,
            move=attacker_b.spec.moves[0],
            result={"hit": True},
            damage_dealt=0,
        )
        hazard_coords = []
        for coord, meta in battle.grid.tiles.items():
            if isinstance(meta, dict) and meta.get("hazards", {}).get("fire_hazards"):
                hazard_coords.append(coord)
        print(f"Pledge fire hazards at: {sorted(hazard_coords)}")
        self.assertTrue(hazard_coords)
        self.assertTrue([evt for evt in events_a + events_b if evt.get("effect") == "pledge_fire_hazards"])

    def test_ui_snapshot_includes_hazards(self) -> None:
        facade = EngineFacade()
        facade.start_encounter(
            campaign="keyword_demos/hazard_demo",
            team_size=1,
            ai_mode="player",
        )
        battle = facade.battle
        assert battle is not None
        battle._place_hazard((1, 1), "spikes", 1)
        snapshot = facade.snapshot()
        tiles = snapshot.get("grid", {}).get("tiles", [])
        hazard_tiles = [tile for tile in tiles if isinstance(tile, list) and len(tile) > 3 and tile[3]]
        print(f"UI hazard tiles: {hazard_tiles[:4]}")
        self.assertTrue(hazard_tiles)

    def test_hazard_triggers_on_standing_tile(self) -> None:
        trainer = TrainerState(identifier="ash", name="Ash")
        target = PokemonState(spec=_pokemon_spec("Onix", []), controller_id=trainer.identifier, position=(0, 0), active=True)
        grid = GridState(width=1, height=1, tiles={(0, 0): {"hazards": {"spikes": 1}}})
        battle = BattleState(trainers={trainer.identifier: trainer}, pokemon={"ash-1": target}, grid=grid)
        battle.start_round()
        _advance_to_pokemon_turn(battle)
        hazard_events = [
            evt for evt in battle.log if evt.get("type") == "hazard" and evt.get("hazard") == "spikes"
        ]
        print(f"Hazard trigger events: {hazard_events[:1]}")
        self.assertTrue(hazard_events)
        self.assertLess(target.hp or 0, target.max_hp())
