"""Super-effective and DR-piercing bonuses."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook


@register_ability_hook(phase="post_result_super_effective", ability=None)
def _pierce_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_name = (ctx.move.name or "").strip().lower()
    if move_name != "pierce!":
        return
    for entry in ctx.defender.get_temporary_effects("damage_reduction"):
        try:
            amount = int(entry.get("amount", 0) or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            continue
        bonus = amount * 2
        ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + bonus
        ctx.result["pierce_bonus"] = bonus
        break


@register_ability_hook(phase="post_result_super_effective", ability="Exploit")
def _exploit_bonus(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    ctx.result["damage"] = int(ctx.result.get("damage", 0) or 0) + 15
    ctx.result["exploit_bonus"] = 15
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Exploit",
            "move": ctx.move.name,
            "effect": "damage_bonus",
            "amount": 15,
            "description": "Exploit adds damage on super-effective hits.",
            "target_hp": ctx.defender.hp,
        }
    )
