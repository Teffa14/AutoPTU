"""Movement utilities that respect PTU capabilities and abilities."""
from __future__ import annotations

from heapq import heappop, heappush
import math
from typing import Dict, Iterable, List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .battle_state import BattleState, GridState


def neighboring_tiles(coord: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
    x, y = coord
    yield (x + 1, y)
    yield (x - 1, y)
    yield (x, y + 1)
    yield (x, y - 1)


def _step_toward(origin: Tuple[int, int], destination: Tuple[int, int]) -> Iterable[Tuple[int, int]]:
    x, y = origin
    dest_x, dest_y = destination
    while (x, y) != (dest_x, dest_y):
        if x < dest_x:
            x += 1
        elif x > dest_x:
            x -= 1
        if y < dest_y:
            y += 1
        elif y > dest_y:
            y -= 1
        yield (x, y)


def _blocked_jump_path(
    battle: BattleState,
    actor_id: str,
    origin: Tuple[int, int],
    destination: Tuple[int, int],
) -> bool:
    return _jump_path_blocked_steps(battle, actor_id, origin, destination) > 0


def _jump_path_blocked_steps(
    battle: BattleState,
    actor_id: str,
    origin: Tuple[int, int],
    destination: Tuple[int, int],
) -> int:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 999
    if actor.can_fly() or actor.can_phase() or actor.has_status("Liquefied"):
        return 0
    grid = battle.grid
    if grid is None:
        return 999
    path = list(_step_toward(origin, destination))
    if len(path) <= 1:
        return 0
    blocked_steps = 0
    for coord in path[:-1]:
        tile_info = grid.tiles.get(coord, {})
        tile_type = str(tile_info.get("type", "")).lower() if isinstance(tile_info, dict) else str(tile_info).lower()
        blocked = (
            coord in grid.blockers
            or "wall" in tile_type
            or "blocker" in tile_type
            or "blocking" in tile_type
            or "void" in tile_type
        )
        if blocked:
            blocked_steps += 1
    return blocked_steps


def _skill_rank_for_movement(
    battle: BattleState,
    actor_id: str,
    skill_name: str,
) -> int:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0
    try:
        return int(
            battle._combatant_skill_rank(
                actor,
                skill_name,
                actor_id=actor_id if actor_id in battle.trainers else None,
            )
            or 0
        )
    except Exception:
        return int(actor.skill_rank(skill_name) or 0)


def _effective_jump_limit(
    battle: BattleState,
    actor_id: str,
    mode: str,
) -> int:
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        return 0
    limit = max(0, int(actor.spec.movement.get(mode, 0) or 0))
    if actor.has_trainer_feature("Acrobat"):
        limit += 1
    if actor.is_trainer_combatant() and actor.has_trainer_feature("Traveler"):
        survival_rank = _skill_rank_for_movement(battle, actor_id, "survival")
        fallback_skill = "acrobatics" if mode == "l_jump" else "athletics"
        relevant_rank = _skill_rank_for_movement(battle, actor_id, fallback_skill)
        limit += max(0, survival_rank - relevant_rank)
    return max(0, limit)


def legal_shift_tiles(
    battle: BattleState,
    actor_id: str,
    *,
    limit_penalty: int = 0,
) -> Set[Tuple[int, int]]:
    if battle.grid is None:
        raise ValueError("Battle grid not configured.")
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        raise ValueError(f"Unknown combatant '{actor_id}'")
    penalty = max(0, int(limit_penalty))
    weather = battle.effective_weather_for_actor(actor) if hasattr(battle, "effective_weather_for_actor") else battle.weather
    land_limit = max(0, actor.movement_speed("overland", weather=weather) - penalty)
    swim_limit = max(0, actor.movement_speed("swim", weather=weather) - penalty)
    if actor.has_temporary_effect("sprint"):
        multiplier = 2.0 if actor.has_temporary_effect("coaching_sprint") else 1.5
        land_limit = int(math.ceil(land_limit * multiplier))
        swim_limit = int(math.ceil(swim_limit * multiplier))
    fly = actor.can_fly()
    swim = actor.can_swim()
    burrow = actor.can_burrow()
    phase = actor.can_phase()
    liquefied = actor.has_status("Liquefied")
    wallrunner_limit = 0
    if actor.has_trainer_feature("Wallrunner"):
        wallrunner_limit = max(0, _skill_rank_for_movement(battle, actor_id, "acrobatics"))
    grid = battle.grid
    visited: Dict[Tuple[Tuple[int, int], int], int] = {(actor.position, 0): 0}
    reachable: Set[Tuple[int, int]] = {actor.position}
    heap: List[Tuple[int, Tuple[int, int], int]] = [(0, actor.position, 0)]
    while heap:
        cost, coord, wallrun_used = heappop(heap)
        if cost > visited.get((coord, wallrun_used), 0):
            continue
        for nxt in neighboring_tiles(coord):
            if not grid.in_bounds(nxt):
                continue
            tile_info = grid.tiles.get(nxt, {})
            tile_type = str(tile_info.get("type", "")).lower()
            if "void" in tile_type:
                continue
            is_water = "water" in tile_type
            limit = land_limit
            if is_water and not fly:
                if not swim:
                    continue
                limit = swim_limit
            if limit <= 0:
                continue
            step_cost = 1
            ignores_rough = bool(getattr(battle, "_matches_naturewalk_terrain", lambda _actor: False)(actor))
            if not fly and not liquefied and not ignores_rough and ("difficult" in tile_type or "rough" in tile_type):
                step_cost = 2
            new_cost = cost + step_cost
            if new_cost > limit:
                continue
            blocked = nxt in grid.blockers or "wall" in tile_type or "blocker" in tile_type or "blocking" in tile_type
            next_wallrun_used = wallrun_used
            if blocked and not (fly or burrow or phase or liquefied):
                next_wallrun_used += 1
                if wallrunner_limit <= 0 or next_wallrun_used > wallrunner_limit:
                    continue
            landing_allowed = not blocked or fly or burrow or phase or liquefied
            if landing_allowed and not battle._position_can_fit(actor_id, nxt):
                continue
            state = (nxt, next_wallrun_used)
            if state not in visited or new_cost < visited[state]:
                visited[state] = new_cost
                heappush(heap, (new_cost, nxt, next_wallrun_used))
                if landing_allowed:
                    reachable.add(nxt)
    reachable = {
        coord
        for coord in reachable
        if coord == actor.position or battle._position_can_fit(actor_id, coord)
    }
    return reachable


def legal_long_jump_tiles(
    battle: BattleState,
    actor_id: str,
) -> Set[Tuple[int, int]]:
    if battle.grid is None:
        raise ValueError("Battle grid not configured.")
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        raise ValueError(f"Unknown combatant '{actor_id}'")
    if actor.position is None:
        return set()
    limit = _effective_jump_limit(battle, actor_id, "l_jump")
    if limit <= 0:
        return {actor.position}
    grid = battle.grid
    origin = actor.position
    reachable: Set[Tuple[int, int]] = {origin}
    wallrunner_limit = _skill_rank_for_movement(battle, actor_id, "acrobatics") if actor.has_trainer_feature("Wallrunner") else 0
    max_limit = limit + wallrunner_limit
    for dx in range(-max_limit, max_limit + 1):
        for dy in range(-max_limit, max_limit + 1):
            if dx == 0 and dy == 0:
                continue
            if max(abs(dx), abs(dy)) > max_limit:
                continue
            destination = (origin[0] + dx, origin[1] + dy)
            if not grid.in_bounds(destination):
                continue
            tile_info = grid.tiles.get(destination, {})
            tile_type = str(tile_info.get("type", "")).lower() if isinstance(tile_info, dict) else str(tile_info).lower()
            if "void" in tile_type:
                continue
            blocked = (
                destination in grid.blockers
                or "wall" in tile_type
                or "blocker" in tile_type
                or "blocking" in tile_type
            )
            if blocked and not (actor.can_fly() or actor.can_burrow() or actor.can_phase() or actor.has_status("Liquefied")):
                continue
            is_water = "water" in tile_type
            if is_water and not (actor.can_fly() or actor.can_swim()):
                continue
            if not battle._position_can_fit(actor_id, destination):
                continue
            blocked_steps = _jump_path_blocked_steps(battle, actor_id, origin, destination)
            if blocked_steps:
                if blocked_steps > wallrunner_limit:
                    continue
            elif max(abs(dx), abs(dy)) > limit:
                continue
            reachable.add(destination)
    return reachable


def legal_high_jump_tiles(
    battle: BattleState,
    actor_id: str,
) -> Set[Tuple[int, int]]:
    if battle.grid is None:
        raise ValueError("Battle grid not configured.")
    actor = battle.pokemon.get(actor_id)
    if actor is None:
        raise ValueError(f"Unknown combatant '{actor_id}'")
    if actor.position is None:
        return set()
    limit = _effective_jump_limit(battle, actor_id, "h_jump")
    if limit <= 0:
        return {actor.position}
    grid = battle.grid
    origin = actor.position
    reachable: Set[Tuple[int, int]] = {origin}
    for dx in range(-limit, limit + 1):
        for dy in range(-limit, limit + 1):
            if dx == 0 and dy == 0:
                continue
            if max(abs(dx), abs(dy)) > limit:
                continue
            destination = (origin[0] + dx, origin[1] + dy)
            if not grid.in_bounds(destination):
                continue
            tile_info = grid.tiles.get(destination, {})
            tile_type = str(tile_info.get("type", "")).lower() if isinstance(tile_info, dict) else str(tile_info).lower()
            if "void" in tile_type:
                continue
            blocked = (
                destination in grid.blockers
                or "wall" in tile_type
                or "blocker" in tile_type
                or "blocking" in tile_type
            )
            if blocked and not (actor.can_fly() or actor.can_burrow() or actor.can_phase() or actor.has_status("Liquefied")):
                continue
            if not battle._position_can_fit(actor_id, destination):
                continue
            reachable.add(destination)
    return reachable


def legal_jump_tiles(
    battle: BattleState,
    actor_id: str,
) -> Set[Tuple[int, int]]:
    return legal_long_jump_tiles(battle, actor_id)
