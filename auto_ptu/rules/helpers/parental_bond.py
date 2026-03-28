"""Helpers for Parental Bond baby management."""

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING
import copy

from ...data_models import PokemonSpec
from .. import targeting

if TYPE_CHECKING:
    from ..battle_state import BattleState, PokemonState


def _baby_id_for(mother_id: str, battle: "BattleState") -> str:
    base = f"{mother_id}-baby"
    if base not in battle.pokemon:
        return base
    idx = 2
    while f"{base}-{idx}" in battle.pokemon:
        idx += 1
    return f"{base}-{idx}"


def _baby_position(battle: "BattleState", mother: "PokemonState") -> Optional[Tuple[int, int]]:
    if mother.position is None:
        return None
    if battle.grid is None:
        return mother.position
    occupied = {
        mon.position
        for pid, mon in battle.pokemon.items()
        if mon.position is not None and mon.hp is not None and mon.hp > 0
    }
    x0, y0 = mother.position
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            candidate = (x0 + dx, y0 + dy)
            if not battle.grid.in_bounds(candidate):
                continue
            if candidate in battle.grid.blockers:
                continue
            tile = battle.grid.tiles.get(candidate, {})
            tile_type = str(tile.get("type", "")).lower() if isinstance(tile, dict) else str(tile).lower()
            if any(token in tile_type for token in ("wall", "blocker", "blocking", "void")):
                continue
            if candidate in occupied:
                continue
            return candidate
    return mother.position


def _build_baby_spec(mother: "PokemonState") -> PokemonSpec:
    source = mother._source_spec or mother.spec
    base = copy.deepcopy(source)
    base.name = f"Baby {source.species}"
    base.abilities = []
    base.items = []
    base.capabilities = [cap for cap in base.capabilities if str(cap).lower() != "marsupial"]
    base.hp_stat = max(1, int(base.hp_stat) - 5)
    base.atk = max(1, int(base.atk) - 5)
    base.defense = max(1, int(base.defense) - 5)
    base.spatk = max(1, int(base.spatk) - 5)
    base.spdef = max(1, int(base.spdef) - 5)
    base.spd = max(1, int(base.spd) - 5)
    return base


def _find_existing_baby_id(battle: "BattleState", mother_id: str) -> Optional[str]:
    mother = battle.pokemon.get(mother_id)
    if mother is not None:
        for entry in mother.get_temporary_effects("parental_bond_child"):
            baby_id = entry.get("baby_id")
            if baby_id in battle.pokemon:
                return baby_id
    for pid, mon in battle.pokemon.items():
        for entry in mon.get_temporary_effects("parental_bond_child"):
            if entry.get("mother_id") == mother_id:
                return pid
    return None


def ensure_parental_bond_baby(battle: "BattleState", mother_id: str) -> Tuple[Optional[str], bool]:
    mother = battle.pokemon.get(mother_id)
    if mother is None:
        return None, False
    if not mother.has_ability("Parental Bond"):
        return None, False
    if not mother.has_capability("Marsupial"):
        return None, False
    existing = _find_existing_baby_id(battle, mother_id)
    if existing:
        return existing, False
    from ..battle_state import PokemonState

    baby_spec = _build_baby_spec(mother)
    baby_id = _baby_id_for(mother_id, battle)
    baby = PokemonState(
        spec=baby_spec,
        controller_id=mother.controller_id,
        position=_baby_position(battle, mother),
        active=True,
    )
    baby.add_temporary_effect("parental_bond_child", mother_id=mother_id)
    baby.add_temporary_effect("parental_bond_leash", mother_id=mother_id, max_range=10)
    baby.add_temporary_effect("damage_reduction", amount=10, consume=False, source="Parental Bond")
    battle.pokemon[baby_id] = baby
    mother.add_temporary_effect("parental_bond_child", baby_id=baby_id)
    setattr(baby, "_battle_id", baby_id)
    setattr(baby, "_injury_stage_loss_rng", battle.rng)
    setattr(baby, "_injury_stage_loss_enabled", getattr(battle, "injury_stage_loss_enabled", False))
    setattr(baby, "_injury_stage_loss_logger", battle.log_event)
    return baby_id, True


def reset_parental_bond_turn(battle: "BattleState", mother_id: str) -> Optional[str]:
    baby_id = _find_existing_baby_id(battle, mother_id)
    if not baby_id:
        return None
    baby = battle.pokemon.get(baby_id)
    if baby is None:
        return None
    if baby.fainted or not baby.active:
        return baby_id
    baby.reset_actions()
    baby.add_temporary_effect("parental_bond_turn", round=battle.round, mother_id=mother_id)
    return baby_id


def apply_parental_bond_enrage(battle: "BattleState", mother_id: str, baby_id: str) -> bool:
    mother = battle.pokemon.get(mother_id)
    baby = battle.pokemon.get(baby_id)
    if mother is None or baby is None:
        return False
    if not baby.fainted:
        return False
    if mother.get_temporary_effects("parental_bond_enraged"):
        return False
    mother.add_temporary_effect("parental_bond_enraged", source="Parental Bond")
    mother.add_temporary_effect("damage_reduction", amount=5, consume=False, source="Parental Bond")
    mother.add_temporary_effect("damage_bonus", amount=5, consume=False, source="Parental Bond")
    if not mother.has_status("Enraged"):
        mother.statuses.append({"name": "Enraged"})
    return True


def parental_bond_child_for_turn(battle: "BattleState", child_id: str, mother_id: str) -> bool:
    child = battle.pokemon.get(child_id)
    if child is None:
        return False
    for entry in child.get_temporary_effects("parental_bond_child"):
        if entry.get("mother_id") == mother_id:
            return True
    return False


def parental_bond_leash_violation(
    battle: "BattleState", child_id: str, destination: Tuple[int, int]
) -> Optional[str]:
    child = battle.pokemon.get(child_id)
    if child is None:
        return None
    entry = next(iter(child.get_temporary_effects("parental_bond_leash")), None)
    if entry is None:
        return None
    mother_id = entry.get("mother_id")
    mother = battle.pokemon.get(mother_id) if mother_id else None
    if mother is None or mother.position is None:
        return None
    max_range = int(entry.get("max_range", 10) or 10)
    distance = targeting.chebyshev_distance(destination, mother.position)
    if distance > max_range:
        return mother_id
    return None
