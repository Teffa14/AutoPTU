"""Defender support resistance hooks (Friend Guard, Fur Coat, Grass Pelt)."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...abilities.ability_variants import has_ability_exact


@register_ability_hook(phase="post_mitigation", ability=None)
def _friend_guard_reduces_damage(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender_id is None or ctx.defender is None:
        return
    if not ctx.result.get("damage", 0):
        return
    friend_guard_id = ctx.battle._friend_guard_blocker(ctx.defender_id)
    if not friend_guard_id:
        return
    reduced = int(float(ctx.result.get("damage", 0) or 0) * 0.75)
    ctx.result["damage"] = max(0, reduced)
    ctx.events.append(
        {
            "type": "ability",
            "actor": friend_guard_id,
            "target": ctx.defender_id,
            "ability": "Friend Guard",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "description": "Friend Guard reduces damage for adjacent allies.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_mitigation", ability="Fur Coat", holder="defender")
def _fur_coat_halves_physical(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if (ctx.move.category or "").strip().lower() != "physical":
        return
    reduced = int(float(ctx.result.get("damage", 0) or 0) * 0.5)
    if reduced == ctx.result.get("damage", 0):
        return
    ctx.result["damage"] = max(0, reduced)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Fur Coat",
            "move": ctx.move.name,
            "effect": "resist",
            "description": "Fur Coat halves physical damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_mitigation", ability="Grass Pelt", holder="defender")
def _grass_pelt_reduces_on_grass(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if has_ability_exact(ctx.defender, "Grass Pelt [Errata]"):
        return
    if not ctx.result.get("damage", 0):
        return
    grassy = False
    if ctx.battle.terrain and isinstance(ctx.battle.terrain, dict):
        terrain_name = (ctx.battle.terrain.get("name") or "").strip().lower()
        grassy = terrain_name.startswith("grassy")
    if not grassy and ctx.battle.grid is not None and ctx.defender.position is not None:
        tile = ctx.battle.grid.tiles.get(ctx.defender.position, {})
        tile_type = str(tile.get("type") or "").strip().lower() if isinstance(tile, dict) else ""
        grassy = "grass" in tile_type
    if not grassy:
        return
    reduced = int(float(ctx.result.get("damage", 0) or 0) * 0.75)
    ctx.result["damage"] = max(0, reduced)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Grass Pelt",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "description": "Grass Pelt reduces damage on grassy terrain.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_mitigation", ability="Grass Pelt [Errata]", holder="defender")
def _grass_pelt_errata_reduces_on_grass(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    damage = int(ctx.result.get("damage", 0) or 0)
    if damage <= 0:
        return
    terrain_name = ""
    if ctx.battle.terrain and isinstance(ctx.battle.terrain, dict):
        terrain_name = (ctx.battle.terrain.get("name") or "").strip().lower()
    tile_type = ""
    if ctx.battle.grid is not None and ctx.defender.position is not None:
        tile = ctx.battle.grid.tiles.get(ctx.defender.position, {})
        tile_type = str(tile.get("type") or "").strip().lower() if isinstance(tile, dict) else str(tile).strip().lower()
    grassy_or_leafy = terrain_name.startswith("grassy") or "grass" in tile_type or "leaf" in tile_type
    slow_or_rough = "slow" in tile_type or "rough" in tile_type
    if not (grassy_or_leafy and slow_or_rough):
        return
    reduced = max(0, damage - 5)
    if reduced == damage:
        return
    ctx.result["damage"] = reduced
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Grass Pelt [Errata]",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "amount": 5,
            "description": "Grass Pelt [Errata] reduces damage on grassy terrain.",
            "target_hp": ctx.defender.hp,
        }
    )
