"""Battle-royale-specific AI policy helpers.

This module is intentionally isolated from the base tactical AI so royale
heuristics can evolve independently.
"""
from __future__ import annotations

from typing import Optional, Tuple

from ..rules import BattleState, ShiftAction
from ..rules import movement


Coord = Tuple[int, int]


def _royale_state(battle: BattleState) -> Optional[dict]:
    state = getattr(battle, "_battle_royale_state", None)
    if isinstance(state, dict) and state.get("enabled"):
        return state
    return None


def is_royale_enabled(battle: BattleState) -> bool:
    return _royale_state(battle) is not None


def is_danger_tile(battle: BattleState, coord: Optional[Coord]) -> bool:
    if coord is None or battle.grid is None:
        return False
    meta = battle.grid.tiles.get(coord, {})
    if not isinstance(meta, dict):
        return False
    tile_type = str(meta.get("type") or "").strip().lower()
    zone = str(meta.get("zone") or "").strip().lower()
    return tile_type == "storm" or zone == "danger"


def choose_emergency_shift(battle: BattleState, actor_id: str) -> Optional[ShiftAction]:
    """If actor stands in danger zone, prefer a legal shift to safety."""
    actor = battle.pokemon.get(actor_id)
    if actor is None or actor.fainted or not actor.active or actor.position is None:
        return None
    if not is_danger_tile(battle, actor.position):
        return None
    reachable = movement.legal_shift_tiles(battle, actor_id)
    if not reachable:
        return None
    safe_tiles = [coord for coord in reachable if not is_danger_tile(battle, coord)]
    if not safe_tiles:
        return None
    center = _safe_center(battle)
    safe_tiles.sort(key=lambda coord: _distance(coord, center))
    return ShiftAction(actor_id=actor_id, destination=safe_tiles[0])


def refine_action(battle: BattleState, actor_id: str, action: object) -> object:
    """Refine generic AI action with royale movement constraints."""
    if not is_royale_enabled(battle):
        return action
    if isinstance(action, ShiftAction):
        if is_danger_tile(battle, action.destination):
            fallback = choose_emergency_shift(battle, actor_id)
            if fallback is not None:
                return fallback
    return action


def _safe_center(battle: BattleState) -> Coord:
    state = _royale_state(battle)
    if state and isinstance(state.get("center"), (list, tuple)) and len(state["center"]) == 2:
        return (int(state["center"][0]), int(state["center"][1]))
    if battle.grid is None:
        return (0, 0)
    return (battle.grid.width // 2, battle.grid.height // 2)


def _distance(a: Coord, b: Coord) -> int:
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))

