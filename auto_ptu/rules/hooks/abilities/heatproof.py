"""Heatproof ability hook."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...abilities.ability_variants import has_ability_exact
from .defender_resists import _shift_type_multiplier_down


@register_ability_hook(phase="post_result", ability="Heatproof", holder="defender")
def _heatproof_reduce_fire_damage(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if has_ability_exact(ctx.defender, "Heatproof [Errata]"):
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    current_damage = float(ctx.result.get("damage", 0) or 0)
    ctx.result["damage"] = int(current_damage * 0.5)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Heatproof",
            "move": ctx.move.name,
            "effect": "resist",
            "description": "Heatproof reduces Fire-type damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Heatproof [Errata]", holder="defender")
def _heatproof_errata_resists_fire(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Heatproof [Errata]",
        description="Heatproof [Errata] resists Fire-type moves.",
    )
