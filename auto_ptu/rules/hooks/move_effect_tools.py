"""Reusable helpers for move specials to avoid per-move spaghetti."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple, TYPE_CHECKING

from ...data_models import MoveSpec
from ..move_traits import move_has_keyword

if TYPE_CHECKING:
    from ..battle_state import BattleState, PokemonState


def apply_trap_status(
    battle: BattleState,
    *,
    attacker_id: str,
    target_id: str,
    move: MoveSpec,
    stuck: bool = True,
    trapped: bool = True,
    remaining: Optional[int] = None,
    effect: str = "trap",
    description: str = "The target is trapped.",
    roll: Optional[int] = None,
) -> None:
    target = battle.pokemon.get(target_id)
    if target is None:
        return
    if stuck:
        battle._apply_status(
            [],
            attacker_id=attacker_id,
            target_id=target_id,
            move=move,
            target=target,
            status="Stuck",
            effect=effect,
            description=description,
            roll=roll,
            remaining=remaining,
        )
    if trapped:
        battle._apply_status(
            [],
            attacker_id=attacker_id,
            target_id=target_id,
            move=move,
            target=target,
            status="Trapped",
            effect=effect,
            description=description,
            roll=roll,
            remaining=remaining,
        )


def apply_follow_me(attacker: PokemonState, *, expires_round: int) -> None:
    attacker.add_temporary_effect("follow_me", until_round=expires_round)


def disable_items(target: PokemonState, *, expires_round: Optional[int] = None) -> None:
    target.add_temporary_effect("items_disabled", expires_round=expires_round)


def disable_ability(target: PokemonState, ability_name: Optional[str], *, expires_round: Optional[int] = None) -> None:
    target.add_temporary_effect(
        "ability_disabled",
        ability=(ability_name or "").strip(),
        expires_round=expires_round,
    )


def disable_move(target: PokemonState, move_name: str, *, remaining: Optional[int] = None) -> None:
    entry = {"name": "Disabled", "move": move_name}
    if remaining is not None:
        entry["remaining"] = remaining
    target.statuses.append(entry)


def schedule_delayed_hit(
    battle: BattleState,
    *,
    attacker_id: str,
    move: MoveSpec,
    target_id: Optional[str],
    target_position: Optional[Tuple[int, int]],
    trigger_round: int,
    effect: str,
) -> None:
    battle.delayed_hits.append(
        {
            "attacker_id": attacker_id,
            "move": move,
            "target_id": target_id,
            "target_position": target_position,
            "trigger_round": trigger_round,
            "effect": effect,
        }
    )


def resolve_delayed_hits(battle: BattleState) -> None:
    if not battle.delayed_hits:
        return
    remaining = []
    for entry in battle.delayed_hits:
        trigger_round = entry.get("trigger_round")
        if trigger_round is None or int(trigger_round) > battle.round:
            remaining.append(entry)
            continue
        attacker_id = str(entry.get("attacker_id") or "")
        move = entry.get("move")
        if not attacker_id or not isinstance(move, MoveSpec):
            continue
        battle.resolve_move_targets(
            attacker_id=attacker_id,
            move=move,
            target_id=entry.get("target_id"),
            target_position=entry.get("target_position"),
        )
    battle.delayed_hits = remaining


def swap_hazards(battle: BattleState) -> None:
    if battle.grid is None:
        return
    for coord, tile in battle.grid.tiles.items():
        if not isinstance(tile, dict):
            continue
        hazards = tile.get("hazards")
        if not hazards:
            continue
        # Hazards are stored per-tile; swapping sides is equivalent to no-op for grid hazards.
        # Keep this hook for future side-based hazard tracking.
        tile["hazards"] = hazards


def clear_hazards(battle: BattleState) -> None:
    if battle.grid is None:
        return
    for coord, tile in battle.grid.tiles.items():
        if not isinstance(tile, dict):
            continue
        if "hazards" in tile:
            tile["hazards"] = {}


def clear_hazards_around(
    battle: BattleState,
    center: Optional[Tuple[int, int]],
    *,
    radius: int = 1,
) -> None:
    if battle.grid is None or center is None:
        return
    cx, cy = center
    for coord, tile in battle.grid.tiles.items():
        if not isinstance(tile, dict):
            continue
        x, y = coord
        if abs(int(x) - int(cx)) > radius or abs(int(y) - int(cy)) > radius:
            continue
        if "hazards" in tile:
            tile["hazards"] = {}


def set_terrain(battle: BattleState, name: str, *, rounds: Optional[int] = None) -> None:
    terrain = {"name": name}
    if rounds is not None:
        terrain["remaining"] = rounds
    battle.terrain = terrain


def set_weather(battle: BattleState, name: str) -> None:
    battle.weather = name


def allowed_to_hit_semi_invulnerable(move: MoveSpec, mode: str) -> bool:
    mode = (mode or "").strip().lower()
    if not mode:
        return True
    if mode == "underground":
        return move_has_keyword(move, "groundshaper")
    if mode == "underwater":
        return move_has_keyword(move, "water") or move_has_keyword(move, "sonic")
    if mode == "airborne":
        return move_has_keyword(move, "sky") or move_has_keyword(move, "interrupt")
    if mode == "phantom":
        return move_has_keyword(move, "ghost") or move_has_keyword(move, "interrupt")
    return False


def add_restore_on_switch(
    target: "PokemonState",
    *,
    types: Optional[list[str]] = None,
    moves: Optional[list[MoveSpec]] = None,
    abilities: Optional[list[object]] = None,
) -> None:
    entry = {"kind": "restore_on_switch"}
    if types is not None:
        entry["types"] = list(types)
    if moves is not None:
        entry["moves"] = list(moves)
    if abilities is not None:
        entry["abilities"] = list(abilities)
    target.temporary_effects.append(entry)


def restore_on_switch(target: "PokemonState") -> None:
    if not target.temporary_effects:
        return
    remaining = []
    for entry in target.temporary_effects:
        if entry.get("kind") != "restore_on_switch":
            remaining.append(entry)
            continue
        if "types" in entry:
            target.spec.types = list(entry["types"])
        if "moves" in entry:
            target.spec.moves = list(entry["moves"])
        if "abilities" in entry:
            target.spec.abilities = list(entry["abilities"])
        while target.remove_temporary_effect("entrained_ability"):
            continue
    target.temporary_effects = remaining
