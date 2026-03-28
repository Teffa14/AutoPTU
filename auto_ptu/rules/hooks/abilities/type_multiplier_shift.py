"""Ability hooks that shift type effectiveness for a hit."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook


def _multiplier_to_step(mult: float) -> int | None:
    if mult == 0.25:
        return -2
    if mult == 0.5:
        return -1
    if mult == 1.0:
        return 0
    if mult == 1.5:
        return 1
    if mult >= 2.0:
        return 2
    return None


def _step_to_multiplier(step: int) -> float:
    if step <= -2:
        return 0.25
    if step == -1:
        return 0.5
    if step == 0:
        return 1.0
    if step == 1:
        return 1.5
    return 2.0


def _consume_limited_use(pokemon, kind: str, limit: int) -> bool:
    entry = next(iter(pokemon.get_temporary_effects(kind)), None)
    count = int(entry.get("count", 0) or 0) if entry else 0
    if count >= limit:
        return False
    if entry is not None:
        entry["count"] = count + 1
    else:
        pokemon.add_temporary_effect(kind, count=1)
    return True


def _shift_type_multiplier(
    ctx: AbilityHookContext,
    *,
    ability: str,
    move_type: str | None,
    kind: str,
) -> None:
    if ctx.result is None or ctx.attacker is None or ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    if move_type and (ctx.effective_move.type or "").strip().lower() != move_type:
        return
    if not _consume_limited_use(ctx.attacker, kind, limit=2):
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    base_step = -2 if raw_mult == 0 else _multiplier_to_step(raw_mult)
    if base_step is None:
        return
    new_step = min(2, base_step + 1)
    new_mult = _step_to_multiplier(new_step)
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": ability,
            "move": ctx.move.name,
            "effect": "type_shift",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": f"{ability} makes the target more vulnerable.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Dragon's Maw")
@register_ability_hook(phase="post_result", ability="Dragon’s Maw")
def _dragons_maw(ctx: AbilityHookContext) -> None:
    if ctx.attacker is None:
        return
    if ctx.attacker.get_temporary_effects("dragons_maw_hook_applied"):
        return
    ctx.attacker.add_temporary_effect("dragons_maw_hook_applied", round=getattr(ctx.battle, "round", None))
    ability_name = "Dragon’s Maw" if ctx.attacker.has_ability("Dragon’s Maw") else "Dragon's Maw"
    _shift_type_multiplier(ctx, ability=ability_name, move_type=None, kind="dragons_maw_used")


@register_ability_hook(phase="post_result", ability="Transistor")
def _transistor(ctx: AbilityHookContext) -> None:
    _shift_type_multiplier(ctx, ability="Transistor", move_type="electric", kind="transistor_used")


@register_ability_hook(phase="post_result", ability="Tinted Lens")
def _tinted_lens(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.attacker is None or ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    base_step = -2 if raw_mult == 0 else _multiplier_to_step(raw_mult)
    if base_step is None or base_step >= 0:
        return
    new_step = min(2, base_step + 1)
    new_mult = _step_to_multiplier(new_step)
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Tinted Lens",
            "move": ctx.move.name,
            "effect": "type_shift",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": "Tinted Lens pushes resisted hits toward neutral.",
            "target_hp": ctx.defender.hp,
        }
    )

