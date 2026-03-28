"""Mega Launcher ability hook."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ....data_models import MoveSpec


@register_ability_hook(phase="pre_damage", ability="Mega Launcher")
def _mega_launcher_db_bonus(ctx: AbilityHookContext) -> None:
    move_name = (ctx.effective_move.name or "").strip().lower()
    if move_name not in {"aura sphere", "dark pulse", "dragon pulse", "water pulse"}:
        return
    copy_move = MoveSpec(**ctx.effective_move.__dict__)
    copy_move.db = min(20, int(copy_move.db or 0) + 2)
    ctx.effective_move = copy_move
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Mega Launcher",
            "move": ctx.move.name,
            "effect": "db_bonus",
            "amount": 2,
            "description": "Mega Launcher boosts pulse move damage bases.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_ability_hook(phase="pre_damage", ability="Mega Launcher [Errata]")
def _mega_launcher_errata_db_bonus(ctx: AbilityHookContext) -> None:
    move_name = (ctx.effective_move.name or "").strip().lower()
    if move_name not in {"aura sphere", "dark pulse", "dragon pulse", "water pulse"}:
        return
    copy_move = MoveSpec(**ctx.effective_move.__dict__)
    copy_move.db = min(20, int(copy_move.db or 0) + 3)
    ctx.effective_move = copy_move
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Mega Launcher [Errata]",
            "move": ctx.move.name,
            "effect": "db_bonus",
            "amount": 3,
            "description": "Mega Launcher [Errata] boosts pulse move damage bases.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )
