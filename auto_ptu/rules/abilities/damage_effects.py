"""Ability damage-pipeline helpers extracted from battle_state."""

from __future__ import annotations

import math
from typing import Dict, List, TYPE_CHECKING

from ..move_traits import move_has_keyword
from ..abilities.ability_variants import has_ability_exact
from ... import ptu_engine

if TYPE_CHECKING:
    from ...data_models import MoveSpec
    from ..battle_state import BattleState, PokemonState


def _remove_crit_bonus(result: Dict[str, object], attacker: "PokemonState") -> None:
    crit_extra = int(result.get("crit_extra_roll", 0) or 0)
    if crit_extra <= 0:
        return
    extra = crit_extra * (2 if attacker.has_ability("Sniper") else 1)
    pre_type = int(result.get("pre_type_damage", result.get("damage", 0) or 0) or 0)
    new_pre = max(0, pre_type - extra)
    type_mult = float(result.get("type_multiplier", 1.0) or 1.0)
    result["pre_type_damage"] = new_pre
    result["damage"] = int(math.floor(new_pre * type_mult))
    result["crit_extra_roll"] = 0


def apply_defender_pre_damage_abilities(
    battle: "BattleState",
    *,
    attacker_id: str,
    attacker: "PokemonState",
    defender_id: str,
    defender: "PokemonState",
    move: "MoveSpec",
    effective_move: "MoveSpec",
    result: Dict[str, object],
    events: List[dict],
) -> bool:
    """Handle defender abilities that can cancel a damaging hit."""
    hit = bool(result.get("hit"))
    if attacker.get_temporary_effects("ignore_ability_immunity") or attacker.has_ability("Mold Breaker"):
        return hit
    if (
        hit
        and (effective_move.category or "").strip().lower() != "status"
        and defender.has_ability("Soundproof")
        and move_has_keyword(effective_move, "sonic")
    ):
        hit = False
        result["hit"] = False
        result["damage"] = 0
        payload = {
            "type": "ability",
            "actor": defender_id,
            "target": attacker_id,
            "ability": "Soundproof",
            "move": effective_move.name,
            "effect": "block_sonic",
            "description": "Soundproof blocks Sonic moves.",
            "target_hp": defender.hp,
        }
        events.append(payload)
        battle.log_event(payload)
        return hit
    if (
        hit
        and (effective_move.category or "").strip().lower() != "status"
        and defender.has_ability("Glisten")
        and (effective_move.type or "").strip().lower() == "fairy"
    ):
        hit = False
        result["hit"] = False
        result["damage"] = 0
        stat = "def"
        if defender.spec.spdef < defender.spec.defense:
            stat = "spdef"
        battle._apply_combat_stage(
            events,
            attacker_id=defender_id,
            target_id=defender_id,
            move=move,
            target=defender,
            stat=stat,
            delta=1,
            effect="glisten",
            description="Glisten hardens against Fairy attacks.",
        )
        payload = {
            "type": "ability",
            "actor": defender_id,
            "target": attacker_id,
            "ability": "Glisten",
            "move": effective_move.name,
            "effect": "immune",
            "description": "Glisten blocks Fairy-type moves.",
            "target_hp": defender.hp,
        }
        events.append(payload)
        battle.log_event(payload)
        return hit
    if (
        hit
        and (effective_move.category or "").strip().lower() != "status"
        and defender.has_ability("Wonder Guard")
    ):
        move_type = (effective_move.type or "").strip()
        type_mult = ptu_engine.type_multiplier(move_type, defender.spec.types)
        if type_mult <= 1.0 and _defender_has_weakness(defender):
            hit = False
            result["hit"] = False
            result["damage"] = 0
            payload = {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Wonder Guard",
                "move": effective_move.name,
                "effect": "immune",
                "description": "Wonder Guard blocks non-super-effective attacks.",
                "target_hp": defender.hp,
            }
            events.append(payload)
            battle.log_event(payload)
            return hit
    if (
        hit
        and (effective_move.category or "").strip().lower() != "status"
        and defender.has_ability("Dodge")
        and not defender.has_temporary_effect("dodge_used")
    ):
        defender.add_temporary_effect("dodge_used")
        hit = False
        result["hit"] = False
        result["damage"] = 0
        payload = {
            "type": "ability",
            "actor": defender_id,
            "target": attacker_id,
            "ability": "Dodge",
            "move": effective_move.name,
            "effect": "avoid",
            "description": "Dodge avoids a damaging move once per scene.",
            "target_hp": defender.hp,
        }
        events.append(payload)
        battle.log_event(payload)
        return hit
    if hit and (effective_move.category or "").strip().lower() != "status" and move_has_keyword(
        effective_move, "sonic"
    ):
        if has_ability_exact(defender, "Drown Out [Errata]"):
            used_entry = next(iter(defender.get_temporary_effects("drown_out_errata_used")), None)
            used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
            if used_count < 2:
                if used_entry is None:
                    defender.add_temporary_effect("drown_out_errata_used", count=used_count + 1)
                else:
                    used_entry["count"] = used_count + 1
                hit = False
                result["hit"] = False
                result["damage"] = 0
                payload = {
                    "type": "ability",
                    "actor": defender_id,
                    "target": attacker_id,
                    "ability": "Drown Out [Errata]",
                    "move": effective_move.name,
                    "effect": "block_sonic",
                    "description": "Drown Out [Errata] blocks a Sonic move.",
                    "target_hp": defender.hp,
                }
                events.append(payload)
                battle.log_event(payload)
                return hit
            return hit
        if defender.has_ability("Drown Out"):
            hit = False
            result["hit"] = False
            result["damage"] = 0
            payload = {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Drown Out",
                "move": effective_move.name,
                "effect": "block_sonic",
                "description": "Drown Out blocks Sonic moves.",
                "target_hp": defender.hp,
            }
            events.append(payload)
            battle.log_event(payload)
            return hit
    return hit


def _defender_has_weakness(defender: "PokemonState") -> bool:
    move_types = {t for (t, _) in ptu_engine.TYPE_STEPS.keys()}
    for move_type in move_types:
        if ptu_engine.type_multiplier(move_type, defender.spec.types) > 1.0:
            return True
    return False


def apply_defender_immunity_abilities(
    battle: "BattleState",
    *,
    attacker_id: str,
    defender_id: str,
    defender: "PokemonState",
    move: "MoveSpec",
    effective_move: "MoveSpec",
    result: Dict[str, object],
) -> None:
    immune_to = str(result.get("immune_to") or "").strip()
    attacker = battle.pokemon.get(attacker_id)
    ignore_immunity = bool(attacker and (attacker.get_temporary_effects("ignore_ability_immunity") or attacker.has_ability("Mold Breaker")))
    if immune_to.lower() == "levitate" and defender.has_ability("Levitate") and not ignore_immunity:
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Levitate",
                "move": move.name,
                "effect": "immune",
                "description": "Levitate blocks Ground-type moves.",
                "target_hp": defender.hp,
            }
        )
    if result.get("crit") and defender.has_ability("Battle Armor"):
        _remove_crit_bonus(result, attacker)
        result["crit"] = False
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Battle Armor",
                "move": move.name,
                "effect": "crit_block",
                "description": "Battle Armor prevents critical hits.",
                "target_hp": defender.hp,
            }
        )
    if result.get("crit") and defender.has_ability("Shell Armor"):
        _remove_crit_bonus(result, attacker)
        result["crit"] = False
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Shell Armor",
                "move": move.name,
                "effect": "crit_block",
                "description": "Shell Armor prevents critical hits.",
                "target_hp": defender.hp,
            }
        )
    if result.get("crit") and defender.has_status("Curled Up"):
        _remove_crit_bonus(result, attacker)
        result["crit"] = False
        battle.log_event(
            {
                "type": "status",
                "actor": defender_id,
                "target": attacker_id,
                "status": "Curled Up",
                "move": move.name,
                "effect": "crit_block",
                "description": "Curled Up blocks critical hits.",
                "target_hp": defender.hp,
            }
        )
    if result.get("crit") and defender.has_status("Lucky Chant"):
        for entry in list(defender.statuses):
            name = entry.get("name") if isinstance(entry, dict) else entry
            if str(name).strip().lower() != "lucky chant":
                continue
            charges = int(entry.get("charges", 0) or 0) if isinstance(entry, dict) else 0
            if charges:
                charges -= 1
                if charges <= 0 and entry in defender.statuses:
                    defender.statuses.remove(entry)
                elif isinstance(entry, dict):
                    entry["charges"] = charges
            _remove_crit_bonus(result, attacker)
            result["crit"] = False
            battle.log_event(
                {
                    "type": "status",
                    "actor": defender_id,
                    "target": attacker_id,
                    "status": "Lucky Chant",
                    "move": move.name,
                    "effect": "crit_block",
                    "description": "Lucky Chant blocks a critical hit.",
                    "target_hp": defender.hp,
                }
            )
            break
    if defender.has_ability("Flying Fly Trap") and (move.category or "").strip().lower() != "status" and not ignore_immunity:
        move_type = (effective_move.type or "").strip().lower()
        if move_type in {"ground", "bug"}:
            result["hit"] = False
            result["damage"] = 0
            result["type_multiplier"] = 0.0
            battle.log_event(
                {
                    "type": "ability",
                    "actor": defender_id,
                    "target": attacker_id,
                    "ability": "Flying Fly Trap",
                    "move": move.name,
                    "effect": "immune",
                    "description": "Flying Fly Trap blocks Ground and Bug moves.",
                    "target_hp": defender.hp,
                }
            )
