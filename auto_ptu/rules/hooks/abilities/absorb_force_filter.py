"""Absorb Force and Filter ability hooks."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...abilities.ability_variants import has_ability_exact


@register_ability_hook(phase="post_result", ability="Absorb Force", holder="defender")
def _absorb_force_reduce_effectiveness(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_multiplier <= 1.0:
        return
    stage = ctx.battle._type_stage_from_multiplier(type_multiplier)
    new_mult = ctx.battle._multiplier_from_stage(stage - 1)
    ctx.result["type_multiplier"] = new_mult
    base_damage = ctx.result.get("pre_type_damage")
    if base_damage is not None:
        ctx.result["damage"] = int(float(base_damage) * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Absorb Force",
            "move": ctx.move.name,
            "effect": "reduce_super",
            "description": "Absorb Force reduces super-effective damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Filter", holder="defender")
def _filter_reduce_effectiveness(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if has_ability_exact(ctx.defender, "Filter [Errata]"):
        return
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_multiplier <= 1.0:
        return
    stage = ctx.battle._type_stage_from_multiplier(type_multiplier)
    new_mult = ctx.battle._multiplier_from_stage(stage - 1)
    ctx.result["type_multiplier"] = new_mult
    base_damage = ctx.result.get("pre_type_damage")
    if base_damage is not None:
        ctx.result["damage"] = int(float(base_damage) * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Filter",
            "move": ctx.move.name,
            "effect": "reduce_super",
            "description": "Filter reduces super-effective damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Filter [Errata]", holder="defender")
def _filter_errata_damage_reduction(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_multiplier <= 1.0:
        return
    ctx.defender.add_temporary_effect("damage_reduction", amount=5, source="Filter [Errata]")
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Filter [Errata]",
            "move": ctx.move.name,
            "effect": "damage_reduction",
            "amount": 5,
            "description": "Filter [Errata] reduces super-effective damage by 5.",
            "target_hp": ctx.defender.hp,
        }
    )
