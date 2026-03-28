"""Accuracy-related ability helpers extracted from battle_state."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .. import targeting
from ...data_models import MoveSpec
from .ability_variants import has_errata

if TYPE_CHECKING:
    from ..battle_state import BattleState, PokemonState


def apply_accuracy_ability_modifiers(
    battle: "BattleState",
    *,
    attacker_id: str,
    attacker: "PokemonState",
    defender_id: str,
    defender: "PokemonState",
    move: "MoveSpec",
    accuracy_adjust: int,
) -> int:
    if defender.has_ability("Illuminate") and not attacker.has_capability("Blindsense"):
        accuracy_adjust -= 2
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Illuminate",
                "move": move.name,
                "effect": "accuracy_penalty",
                "amount": -2,
                "description": "Illuminate penalizes accuracy for incoming attacks.",
                "target_hp": defender.hp,
            }
        )
    if (
        (move.category or "").strip().lower() == "status"
        and defender.has_ability("Wonder Skin")
    ):
        accuracy_adjust -= 6
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Wonder Skin",
                "move": move.name,
                "effect": "accuracy_penalty",
                "amount": -6,
                "description": "Wonder Skin raises evasion against status moves.",
                "target_hp": defender.hp,
            }
        )
    for entry in list(attacker.get_temporary_effects("forewarn_penalty")):
        moves = entry.get("moves") or []
        if not isinstance(moves, list):
            continue
        if (move.name or "").strip().lower() not in {
            str(name).strip().lower() for name in moves
        }:
            continue
        penalty = int(entry.get("amount", 2) or 2)
        accuracy_adjust -= penalty
        battle.log_event(
            {
                "type": "ability",
                "actor": entry.get("source_id") or attacker_id,
                "target": attacker_id,
                "ability": "Forewarn",
                "move": move.name,
                "effect": "accuracy_penalty",
                "amount": -penalty,
                "description": "Forewarn penalizes accuracy for revealed moves.",
                "target_hp": defender.hp,
            }
        )
        break
    penalty = 0
    penalty_entry: Optional[dict] = None
    for entry in list(attacker.get_temporary_effects("accuracy_penalty")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and battle.round > int(expires_round):
            if entry in attacker.temporary_effects:
                attacker.temporary_effects.remove(entry)
            continue
        try:
            amount = int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        if amount > penalty:
            penalty = amount
            penalty_entry = entry
    if penalty:
        accuracy_adjust -= penalty
        source_id = attacker_id
        ability_name = "Interference"
        if penalty_entry:
            source_id = penalty_entry.get("source_id") or source_id
            ability_name = str(penalty_entry.get("source") or ability_name)
        battle.log_event(
            {
                "type": "ability",
                "actor": source_id,
                "target": attacker_id,
                "ability": ability_name,
                "move": move.name,
                "effect": "accuracy_penalty",
                "amount": -penalty,
                "description": "Accuracy penalties reduce the user's attack accuracy.",
                "target_hp": defender.hp,
            }
        )
    move_type = (move.type or "").strip().lower()
    if move_type in {"grass", "ghost"} and attacker.get_temporary_effects("forest_lord"):
        forest_bonus = False
        for entry in list(attacker.get_temporary_effects("forest_lord")):
            expires_round = entry.get("expires_round")
            if expires_round is not None and battle.round > int(expires_round):
                attacker.temporary_effects.remove(entry)
                continue
            forest_bonus = True
            break
        if forest_bonus:
            accuracy_adjust += 2
            battle.log_event(
                {
                    "type": "ability",
                    "actor": attacker_id,
                    "target": defender_id,
                    "ability": "Forest Lord",
                    "move": move.name,
                    "effect": "accuracy_bonus",
                    "amount": 2,
                    "description": "Forest Lord boosts accuracy for Grass/Ghost moves.",
                    "target_hp": defender.hp,
                }
            )
    if not has_errata(defender, "Starlight"):
        for entry in list(defender.get_temporary_effects("luminous")):
            expires_round = entry.get("expires_round")
            if expires_round is not None and battle.round > int(expires_round):
                if entry in defender.temporary_effects:
                    defender.temporary_effects.remove(entry)
                continue
            accuracy_adjust -= 2
            battle.log_event(
                {
                    "type": "ability",
                    "actor": defender_id,
                    "target": attacker_id,
                    "ability": "Starlight",
                    "move": move.name,
                    "effect": "accuracy_penalty",
                    "amount": -2,
                    "description": "Luminous foes suffer a penalty to accuracy.",
                    "target_hp": defender.hp,
                }
            )
            break
    if defender.has_ability("Sol Veil"):
        weather_name = ""
        if hasattr(battle, "effective_weather"):
            weather_name = str(battle.effective_weather() or "").strip().lower()
        else:
            weather_name = str(getattr(battle, "weather", "") or "").strip().lower()
        terrain_name = str((getattr(battle, "terrain", {}) or {}).get("name") or "").strip().lower()
        penalty = 2 if ("sun" in weather_name or terrain_name.startswith("grassy")) else 1
        accuracy_adjust -= penalty
        battle.log_event(
            {
                "type": "ability",
                "actor": defender_id,
                "target": attacker_id,
                "ability": "Sol Veil",
                "move": move.name,
                "effect": "accuracy_penalty",
                "amount": -penalty,
                "description": "Sol Veil boosts evasion in sun or grass.",
                "target_hp": defender.hp,
            }
        )
    if targeting.normalized_target_kind(move) == "melee":
        defender_pos = getattr(defender, "position", None)
        if defender_pos is not None:
            for pid, mon in battle.pokemon.items():
                if mon.fainted or not mon.active:
                    continue
                if battle._team_for(pid) != battle._team_for(attacker_id):
                    continue
                if not mon.has_ability("Teamwork") or mon.position is None:
                    continue
                if targeting.chebyshev_distance(defender_pos, mon.position) > 1:
                    continue
                accuracy_adjust += 2
                battle.log_event(
                    {
                        "type": "ability",
                        "actor": pid,
                        "target": attacker_id,
                        "ability": "Teamwork",
                        "move": move.name,
                        "effect": "accuracy_bonus",
                        "amount": 2,
                        "description": "Teamwork boosts ally melee accuracy.",
                        "target_hp": defender.hp,
                    }
                )
                break
    for pid, mon in battle.pokemon.items():
        if mon.fainted or not mon.active:
            continue
        if battle._team_for(pid) != battle._team_for(attacker_id):
            continue
        if not mon.has_ability("Victory Star"):
            continue
        accuracy_adjust += 2
        battle.log_event(
            {
                "type": "ability",
                "actor": pid,
                "target": attacker_id,
                "ability": "Victory Star",
                "move": move.name,
                "effect": "accuracy_bonus",
                "amount": 2,
                "description": "Victory Star boosts allied accuracy.",
                "target_hp": defender.hp,
            }
        )
        break
    return accuracy_adjust
