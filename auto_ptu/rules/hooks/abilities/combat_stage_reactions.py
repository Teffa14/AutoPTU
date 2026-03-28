"""Combat stage reaction hooks (Defiant, Competitive, Minus [SwSh])."""

from __future__ import annotations

from ....data_models import MoveSpec
from ..combat_stage_hooks import CombatStageHookContext, register_combat_stage_hook


@register_combat_stage_hook("post_apply")
def _minus_swsh(ctx: CombatStageHookContext) -> None:
    if ctx.applied_delta >= 0:
        return
    if ctx.skip_minus_swsh:
        return
    if ctx.attacker_id == ctx.target_id:
        return
    if ctx.target.position is None:
        return
    holders = [
        pid for pid in ctx.battle._ability_in_radius(ctx.target.position, "Minus [SwSh]", 10)
        if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.target_id)
    ]
    if not holders:
        return
    minus_move = MoveSpec(name="Minus [SwSh]", type="Electric", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=holders[0],
        target_id=ctx.target_id,
        move=minus_move,
        target=ctx.target,
        stat=ctx.stat,
        delta=-1,
        description="Minus [SwSh] intensifies the stat drop.",
        effect="minus_swsh",
        skip_minus_swsh=True,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": holders[0],
            "target": ctx.target_id,
            "ability": "Minus [SwSh]",
            "move": ctx.move.name,
            "effect": "extra_drop",
            "stat": ctx.stat,
            "amount": -1,
            "description": "Minus [SwSh] triggers an extra stat drop.",
            "target_hp": ctx.target.hp,
        }
    )


@register_combat_stage_hook("post_apply")
def _plus_swsh(ctx: CombatStageHookContext) -> None:
    if ctx.applied_delta <= 0:
        return
    if ctx.skip_plus_swsh:
        return
    if ctx.target.position is None:
        return
    holders = [
        pid for pid in ctx.battle._ability_in_radius(ctx.target.position, "Plus [SwSh]", 10)
        if ctx.battle._team_for(pid) == ctx.battle._team_for(ctx.target_id)
        and pid != ctx.target_id
    ]
    if not holders:
        return
    plus_move = MoveSpec(name="Plus [SwSh]", type="Electric", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=holders[0],
        target_id=ctx.target_id,
        move=plus_move,
        target=ctx.target,
        stat=ctx.stat,
        delta=1,
        description="Plus [SwSh] intensifies the stat raise.",
        effect="plus_swsh",
        skip_plus_swsh=True,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": holders[0],
            "target": ctx.target_id,
            "ability": "Plus [SwSh]",
            "move": ctx.move.name,
            "effect": "extra_raise",
            "stat": ctx.stat,
            "amount": 1,
            "description": "Plus [SwSh] triggers an extra stat raise.",
            "target_hp": ctx.target.hp,
        }
    )


@register_combat_stage_hook("post_apply")
def _defiant(ctx: CombatStageHookContext) -> None:
    if ctx.applied_delta >= 0:
        return
    move_name = (ctx.move.name or "").strip().lower()
    if move_name == "defiant":
        return
    if ctx.target_id == ctx.attacker_id:
        return
    if not ctx.target.has_ability("Defiant"):
        return
    defiant_bonus = 2 + abs(ctx.applied_delta)
    defiant_move = MoveSpec(name="Defiant", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.target_id,
        target_id=ctx.target_id,
        move=defiant_move,
        target=ctx.target,
        stat="atk",
        delta=defiant_bonus,
        description="Defiant raises Attack by +2 CS.",
        effect="defiant",
    )


@register_combat_stage_hook("post_apply")
def _competitive(ctx: CombatStageHookContext) -> None:
    if ctx.applied_delta >= 0:
        return
    move_name = (ctx.move.name or "").strip().lower()
    if move_name == "competitive":
        return
    if ctx.target_id == ctx.attacker_id:
        return
    if not ctx.target.has_ability("Competitive"):
        return
    competitive_move = MoveSpec(name="Competitive", type="Normal", category="Status")
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.target_id,
        target_id=ctx.target_id,
        move=competitive_move,
        target=ctx.target,
        stat="spatk",
        delta=2,
        description="Competitive raises Special Attack by +2 CS.",
        effect="competitive",
    )


@register_combat_stage_hook("post_apply")
def _simple_doubles_stage_changes(ctx: CombatStageHookContext) -> None:
    if ctx.applied_delta == 0:
        return
    if not getattr(ctx.target, "has_ability", None):
        return
    if not ctx.target.has_ability("Simple"):
        return
    current = int(ctx.target.combat_stages.get(ctx.stat, 0) or 0)
    new_stage = max(-6, min(6, current + ctx.applied_delta))
    applied = new_stage - current
    if applied == 0:
        return
    ctx.target.combat_stages[ctx.stat] = new_stage
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.target_id,
            "target": ctx.target_id,
            "ability": "Simple",
            "move": ctx.move.name,
            "effect": "simple",
            "stat": ctx.stat,
            "amount": applied,
            "description": "Simple doubles combat stage changes.",
            "target_hp": ctx.target.hp,
        }
    )
