"""Helpers for validating move ranges, areas, and target legality."""
from __future__ import annotations

import re
from typing import Optional, Sequence, Set, Tuple, TYPE_CHECKING

from ..data_models import MoveSpec

if TYPE_CHECKING:
    from .battle_state import GridState

GridCoord = Tuple[int, int]

_FOOTPRINT_BY_SIZE = {
    "small": 1,
    "medium": 1,
    "large": 2,
    "huge": 3,
    "gigantic": 4,
}


def _normalize_kind(value: Optional[str], default: str = "ranged") -> str:
    text = (value or default or "").lower()
    for match in re.finditer(r"[a-z]+", text):
        token = match.group(0)
        if token:
            return token
    return (default or "ranged").lower()


def normalized_target_kind(move: MoveSpec) -> str:
    return _normalize_kind(move.target_kind or move.range_kind, "ranged")


def normalized_area_kind(move: MoveSpec) -> str:
    if not move.area_kind:
        return ""
    return _normalize_kind(move.area_kind)


def move_requires_target(move: MoveSpec) -> bool:
    kind = normalized_target_kind(move)
    area = normalized_area_kind(move)
    if kind in {"field"}:
        return False
    if area in {"cone", "line", "closeblast"}:
        # Need a direction anchor even if the move centers on the user.
        return True
    if kind in {"self"}:
        return False
    return True


def move_range_distance(move: MoveSpec) -> int:
    kind = normalized_target_kind(move)
    defaults = {"melee": 1, "ranged": 6}
    if kind in {"self", "field"}:
        return 0
    if move.target_range not in (None, 0):
        try:
            return max(1, int(move.target_range))
        except (TypeError, ValueError):
            pass
    if move.range_value not in (None, 0):
        try:
            return max(1, int(move.range_value))
        except (TypeError, ValueError):
            pass
    return defaults.get(kind, 6)


def chebyshev_distance(a: GridCoord, b: GridCoord) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def footprint_side_for_size(size_label: object) -> int:
    label = str(size_label or "").strip().lower()
    return max(1, int(_FOOTPRINT_BY_SIZE.get(label, 1)))


def footprint_tiles(
    anchor: GridCoord,
    size_label: object,
    grid: Optional["GridState"] = None,
) -> Set[GridCoord]:
    return _square_tiles(anchor, footprint_side_for_size(size_label), grid)


def footprint_distance(
    a_anchor: GridCoord,
    a_size: object,
    b_anchor: GridCoord,
    b_size: object,
    grid: Optional["GridState"] = None,
) -> int:
    a_tiles = footprint_tiles(a_anchor, a_size, grid)
    b_tiles = footprint_tiles(b_anchor, b_size, grid)
    if not a_tiles or not b_tiles:
        return chebyshev_distance(a_anchor, b_anchor)
    return min(chebyshev_distance(a_tile, b_tile) for a_tile in a_tiles for b_tile in b_tiles)


def is_target_in_range(
    attacker_pos: GridCoord,
    target_pos: GridCoord,
    move: MoveSpec,
    *,
    attacker_size: object = None,
    target_size: object = None,
    grid: Optional["GridState"] = None,
) -> bool:
    kind = normalized_target_kind(move)
    area = normalized_area_kind(move)
    if attacker_size is not None or target_size is not None:
        distance = footprint_distance(
            attacker_pos,
            attacker_size or "Medium",
            target_pos,
            target_size or "Medium",
            grid,
        )
    else:
        distance = chebyshev_distance(attacker_pos, target_pos)
    if kind == "self":
        if area in {"line", "cone"}:
            max_distance = max(1, int(move.area_value or move.target_range or move.range_value or 1))
            return 0 < distance <= max_distance
        if area == "closeblast":
            return distance == 1
        return attacker_pos == target_pos
    if kind == "field":
        return True
    max_distance = move_range_distance(move)
    if kind == "melee":
        return distance == 1
    return distance <= max_distance


def affected_tiles(
    grid: Optional["GridState"],
    attacker_pos: GridCoord,
    target_pos: Optional[GridCoord],
    move: MoveSpec,
) -> Set[GridCoord]:
    area_kind = normalized_area_kind(move)
    if not area_kind:
        center = target_pos if target_pos is not None else attacker_pos
        return {center}
    if area_kind == "field":
        return _all_tiles(grid)
    radius = max(0, int(move.area_value or 0))
    if area_kind == "burst":
        center = target_pos if target_pos is not None and normalized_target_kind(move) not in {"self"} else attacker_pos
        return _burst_tiles(center, radius, grid)
    if area_kind == "blast":
        # PTU Core 1.05 p.343: Blast Y forms a Y×Y square centered on the target.
        center = target_pos if target_pos is not None else attacker_pos
        return _square_tiles(center, radius, grid)
    if area_kind == "closeblast":
        # PTU Core 1.05 p.343: Close Blast X is an X×X square adjacent to the user.
        anchor = target_pos if target_pos is not None else attacker_pos
        return _close_blast_tiles(attacker_pos, anchor, radius, grid)
    if area_kind == "line":
        if target_pos is None:
            return _burst_tiles(attacker_pos, 0, grid)
        return _line_tiles(attacker_pos, target_pos, max(1, radius), grid)
    if area_kind == "cone":
        if target_pos is None:
            return _burst_tiles(attacker_pos, radius, grid)
        return _cone_tiles(attacker_pos, target_pos, max(1, radius), grid)
    return {target_pos or attacker_pos}


def target_anchor_tiles(
    grid: Optional["GridState"],
    origin: GridCoord,
    move: MoveSpec,
) -> Set[GridCoord]:
    """Return every tile the user may target when declaring the move."""
    area = normalized_area_kind(move)
    if area in {"cone", "line"}:
        max_distance = max(1, int(move.area_value or 1))
        tiles: Set[GridCoord] = set()
        for x in range(origin[0] - max_distance, origin[0] + max_distance + 1):
            for y in range(origin[1] - max_distance, origin[1] + max_distance + 1):
                coord = (x, y)
                if grid and not grid.in_bounds(coord):
                    continue
                if coord == origin:
                    continue
                if chebyshev_distance(origin, coord) <= max_distance:
                    tiles.add(coord)
        return tiles
    if area == "closeblast":
        tiles: Set[GridCoord] = set()
        for x in range(origin[0] - 1, origin[0] + 2):
            for y in range(origin[1] - 1, origin[1] + 2):
                coord = (x, y)
                if coord == origin:
                    continue
                if grid and not grid.in_bounds(coord):
                    continue
                if chebyshev_distance(origin, coord) == 1:
                    tiles.add(coord)
        return tiles
    kind = normalized_target_kind(move)
    if kind in {"self"}:
        return {origin}
    if kind in {"field"}:
        return _all_tiles(grid)
    max_distance = move_range_distance(move)
    tiles: Set[GridCoord] = set()
    for x in range(origin[0] - max_distance, origin[0] + max_distance + 1):
        for y in range(origin[1] - max_distance, origin[1] + max_distance + 1):
            coord = (x, y)
            if grid and not grid.in_bounds(coord):
                continue
            if coord == origin and kind == "melee":
                continue
            if chebyshev_distance(origin, coord) <= max_distance:
                tiles.add(coord)
    return tiles


def line_of_sight_clear(
    grid: Optional["GridState"],
    origin: GridCoord,
    target: GridCoord,
    blocking: Optional[Set[GridCoord]] = None,
) -> bool:
    """Return True if nothing blocks a straight line between two tiles."""
    if grid is None or origin == target:
        return True
    blockers = set(blocking or set())
    for coord in _bresenham_cells(origin, target)[1:]:
        if coord == target:
            break
        if coord in blockers:
            return False
    return True


def _bresenham_cells(start: GridCoord, end: GridCoord) -> Sequence[GridCoord]:
    """Return every grid coordinate the line between two points touches."""
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1 if x0 > x1 else 0
    sy = 1 if y0 < y1 else -1 if y0 > y1 else 0
    err = dx - dy
    x, y = x0, y0
    cells = [(x, y)]
    while (x, y) != (x1, y1):
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
        cells.append((x, y))
    return cells


def _all_tiles(grid: Optional["GridState"]) -> Set[GridCoord]:
    if grid is None:
        return set()
    return {(x, y) for x in range(grid.width) for y in range(grid.height)}


def _burst_tiles(center: GridCoord, radius: int, grid: Optional["GridState"]) -> Set[GridCoord]:
    tiles: Set[GridCoord] = set()
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            coord = (center[0] + dx, center[1] + dy)
            if grid and not grid.in_bounds(coord):
                continue
            if chebyshev_distance(center, coord) <= radius:
                tiles.add(coord)
    tiles.add(center)
    return tiles


def _square_tiles(center: GridCoord, size: int, grid: Optional["GridState"]) -> Set[GridCoord]:
    side = max(1, int(size))
    offset_min = -((side - 1) // 2)
    offset_max = side // 2
    tiles: Set[GridCoord] = set()
    for dx in range(offset_min, offset_max + 1):
        for dy in range(offset_min, offset_max + 1):
            coord = (center[0] + dx, center[1] + dy)
            if grid and not grid.in_bounds(coord):
                continue
            tiles.add(coord)
    return tiles


def _line_tiles(
    origin: GridCoord,
    target: GridCoord,
    length: int,
    grid: Optional["GridState"],
) -> Set[GridCoord]:
    tiles: Set[GridCoord] = set()
    step = _direction_step(origin, target)
    if step == (0, 0):
        return {origin}
    for distance in range(1, length + 1):
        coord = (origin[0] + step[0] * distance, origin[1] + step[1] * distance)
        if grid and not grid.in_bounds(coord):
            break
        tiles.add(coord)
    return tiles


def _close_blast_tiles(
    origin: GridCoord,
    target: GridCoord,
    size: int,
    grid: Optional["GridState"],
) -> Set[GridCoord]:
    side = max(1, int(size))
    step = _direction_step(origin, target)
    if step == (0, 0):
        return _square_tiles(origin, side, grid)
    perp = (step[1], -step[0])
    offset_min = -((side - 1) // 2)
    offset_max = side // 2
    tiles: Set[GridCoord] = set()
    for distance in range(1, side + 1):
        base = (origin[0] + step[0] * distance, origin[1] + step[1] * distance)
        for offset in range(offset_min, offset_max + 1):
            coord = (base[0] + perp[0] * offset, base[1] + perp[1] * offset)
            if grid and not grid.in_bounds(coord):
                continue
            tiles.add(coord)
    return tiles


def _cone_tiles(
    origin: GridCoord,
    target: GridCoord,
    radius: int,
    grid: Optional["GridState"],
) -> Set[GridCoord]:
    tiles: Set[GridCoord] = set()
    step = _direction_step(origin, target)
    if step == (0, 0):
        return _burst_tiles(origin, radius, grid)
    # PTU Core 1.05 p.343: Cones extend in 3‑meter wide rows from the user.
    perp = (step[1], -step[0])
    for distance in range(1, radius + 1):
        center = (origin[0] + step[0] * distance, origin[1] + step[1] * distance)
        for offset in (-1, 0, 1):
            coord = (center[0] + perp[0] * offset, center[1] + perp[1] * offset)
            if grid and not grid.in_bounds(coord):
                continue
            tiles.add(coord)
    return tiles


def _direction_step(origin: GridCoord, target: GridCoord) -> GridCoord:
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    return (_sign(dx), _sign(dy))


def _sign(value: int) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


__all__ = [
    "affected_tiles",
    "chebyshev_distance",
    "footprint_distance",
    "footprint_side_for_size",
    "footprint_tiles",
    "is_target_in_range",
    "move_range_distance",
    "move_requires_target",
    "normalized_area_kind",
    "normalized_target_kind",
    "target_anchor_tiles",
    "line_of_sight_clear",
]
