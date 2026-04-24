"""Defender resistance ability hooks."""

from __future__ import annotations

import math

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ... import targeting
from .... import ptu_engine
from ...move_traits import move_has_keyword
from ...abilities.ability_variants import has_errata


def _apply_damage_resist(
    ctx: AbilityHookContext,
    *,
    ability: str,
    description: str,
    new_damage: int,
    effect: str = "resist",
) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    before = int(ctx.result.get("damage", 0) or 0)
    ctx.result["damage"] = new_damage
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability,
            "move": ctx.move.name,
            "effect": effect,
            "amount": max(0, before - new_damage),
            "description": description,
            "target_hp": ctx.defender.hp,
        }
    )


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


def _shift_type_multiplier(
    ctx: AbilityHookContext,
    *,
    ability: str,
    description: str,
    delta: int,
) -> None:
    if ctx.result is None:
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    base_step = _multiplier_to_step(raw_mult)
    if base_step is None:
        return
    new_step = max(-2, min(2, base_step + delta))
    new_mult = _step_to_multiplier(new_step)
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability,
            "move": ctx.move.name,
            "effect": "type_shift",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": description,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


def _shift_type_multiplier_down(ctx: AbilityHookContext, *, ability: str, description: str) -> None:
    if ctx.result is None:
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    base_step = _multiplier_to_step(raw_mult)
    if base_step is None:
        return
    new_step = max(-2, base_step - 1)
    new_mult = _step_to_multiplier(new_step)
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability,
            "move": ctx.move.name,
            "effect": "type_resist",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": description,
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_ability_hook(phase="post_result", ability="Shell Armor", holder="defender")
def _shell_armor_blocks_crits(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if not ctx.result.get("crit"):
        return
    crit_extra = int(ctx.result.get("crit_extra_roll", 0) or 0)
    pre_type = int(ctx.result.get("pre_type_damage", ctx.result.get("damage", 0) or 0) or 0)
    extra = crit_extra
    if ctx.attacker is not None and ctx.attacker.has_ability("Sniper"):
        extra *= 2
    new_pre = max(0, pre_type - extra)
    type_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    ctx.result["crit"] = False
    ctx.result["pre_type_damage"] = new_pre
    ctx.result["damage"] = int(math.floor(new_pre * type_mult))
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Shell Armor",
            "move": ctx.move.name,
            "effect": "crit_block",
            "description": "Shell Armor blocks critical hits.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Bulletproof", holder="defender")
def _bulletproof_resists_ranged(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if targeting.normalized_target_kind(ctx.effective_move) != "ranged":
        return
    before = int(ctx.result.get("damage", 0) or 0)
    resisted = int(before * 0.5)
    _apply_damage_resist(
        ctx,
        ability="Bulletproof",
        description="Bulletproof resists ranged attacks.",
        new_damage=resisted,
    )


@register_ability_hook(phase="post_result", ability="Cave Crasher", holder="defender")
def _cave_crasher_resists_ground(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "ground":
        return
    before = int(ctx.result.get("damage", 0) or 0)
    resisted = int(before * 0.5)
    _apply_damage_resist(
        ctx,
        ability="Cave Crasher",
        description="Cave Crasher resists Ground-type attacks.",
        new_damage=resisted,
    )


@register_ability_hook(phase="post_result", ability="Thick Fat", holder="defender")
def _thick_fat_resists_fire_ice(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"fire", "ice"}:
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Thick Fat",
        description="Thick Fat further resists Fire and Ice moves.",
    )


@register_ability_hook(phase="post_result", ability="Sun Blanket", holder="defender")
def _sun_blanket_resists_fire(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    if has_errata(ctx.defender, "Sun Blanket"):
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Sun Blanket",
        description="Sun Blanket resists Fire-type moves.",
    )


@register_ability_hook(phase="post_result", ability="Water Bubble", holder="defender")
def _water_bubble_resists_fire(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Water Bubble",
        description="Water Bubble further resists Fire-type attacks.",
    )
    ctx.result.setdefault("immune_to", "burn")


@register_ability_hook(phase="post_result", ability="Ice Scales", holder="defender")
def _ice_scales_resists_special(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() != "special":
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Ice Scales",
        description="Ice Scales resists special attacks.",
    )


@register_ability_hook(phase="post_result", ability="Punk Rock", holder="defender")
def _punk_rock_resists_sonic(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if not move_has_keyword(ctx.effective_move, "sonic"):
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Punk Rock",
        description="Punk Rock further resists Sonic moves.",
    )


@register_ability_hook(phase="post_result", ability="Tochukaso", holder="defender")
def _tochukaso_resists_bug_poison(ctx: AbilityHookContext) -> None:
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"bug", "poison"}:
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Tochukaso",
        description="Tochukaso further resists Bug and Poison damage.",
    )


@register_ability_hook(phase="post_result", ability="Prism Armor", holder="defender")
def _prism_armor_reduces_super_effective(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    type_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_mult <= 1.0:
        return
    before = int(ctx.result.get("damage", 0) or 0)
    reduced = max(0, before - 5)
    if reduced == before:
        return
    _apply_damage_resist(
        ctx,
        ability="Prism Armor",
        description="Prism Armor reduces super-effective damage.",
        new_damage=reduced,
    )


@register_ability_hook(phase="post_result", ability="Mud Dweller", holder="defender")
def _mud_dweller_resists_ground_water(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"ground", "water"}:
        return
    before = int(ctx.result.get("damage", 0) or 0)
    resisted = int(before * 0.5)
    _apply_damage_resist(
        ctx,
        ability="Mud Dweller",
        description="Mud Dweller resists Ground and Water moves.",
        new_damage=resisted,
    )


@register_ability_hook(phase="post_result", ability="Courage", holder="defender")
def _courage_reduces_damage_at_low_hp(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    defender = ctx.defender
    if defender.hp is None or defender.max_hp() <= 0:
        return
    if defender.hp * 3 > defender.max_hp():
        return
    before = int(ctx.result.get("damage", 0) or 0)
    reduced = min(before, 1)
    _apply_damage_resist(
        ctx,
        ability="Courage",
        description="Courage reduces damage taken at low HP.",
        new_damage=reduced,
    )


@register_ability_hook(phase="post_result", ability="Kampfgeist [Errata]", holder="defender")
def _kampfgeist_errata_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"bug", "dark", "rock"}:
        return
    if ctx.defender.get_temporary_effects("kampfgeist_errata_used"):
        return
    ctx.defender.add_temporary_effect("kampfgeist_errata_used")
    _shift_type_multiplier_down(
        ctx,
        ability="Kampfgeist [Errata]",
        description="Kampfgeist [Errata] resists the triggering damage.",
    )


@register_ability_hook(phase="post_result", ability="Multiscale", holder="defender")
def _multiscale_halves_damage_at_full_hp(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    defender = ctx.defender
    if defender.hp is None or defender.max_hp() <= 0:
        return
    if defender.hp < defender.max_hp():
        return
    before = int(ctx.result.get("damage", 0) or 0)
    resisted = int(before * 0.5)
    _apply_damage_resist(
        ctx,
        ability="Multiscale",
        description="Multiscale halves damage at full HP.",
        new_damage=resisted,
    )


@register_ability_hook(phase="post_result", ability="Multiscale [Errata]", holder="defender")
def _multiscale_errata_resists_at_full_hp(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    defender = ctx.defender
    if defender.hp is None or defender.max_hp() <= 0:
        return
    if defender.hp < defender.max_hp():
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Multiscale [Errata]",
        description="Multiscale [Errata] resists damage at full HP.",
    )


@register_ability_hook(phase="post_result", ability="Shadow Shield", holder="defender")
def _shadow_shield_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    defender = ctx.defender
    if defender.hp is None or defender.max_hp() <= 0:
        return
    if defender.hp < defender.max_hp():
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Shadow Shield",
        description="Shadow Shield reduces damage at full HP.",
    )


@register_ability_hook(phase="post_result", ability="Liquid Ooze [Errata]", holder="defender")
def _liquid_ooze_errata_poison_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "poison":
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Liquid Ooze [Errata]",
        description="Liquid Ooze [Errata] resists Poison-type damage.",
    )


@register_ability_hook(phase="post_result", ability="Fluffy", holder="defender")
def _fluffy_adjusts_damage(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    delta = 0
    if targeting.normalized_target_kind(ctx.effective_move) == "melee":
        delta -= 1
    if (ctx.effective_move.type or "").strip().lower() == "fire":
        delta += 1
    if delta == 0:
        return
    _shift_type_multiplier(
        ctx,
        ability="Fluffy",
        description="Fluffy adjusts damage for melee and Fire attacks.",
        delta=delta,
    )


@register_ability_hook(phase="post_result", ability="Sacred Bell", holder="defender")
def _sacred_bell_resist(ctx: AbilityHookContext) -> None:
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type not in {"dark", "ghost"}:
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Sacred Bell",
        description="Sacred Bell resists Dark and Ghost damage.",
    )


@register_ability_hook(phase="post_result", ability="Steelworker", holder="defender")
def _steelworker_defensive(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None or ctx.defender_id is None:
        return
    if not ctx.battle.has_anchor_token(ctx.defender_id):
        return
    move_type = (ctx.effective_move.type or "").strip()
    if not move_type:
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    new_mult = float(ptu_engine.type_multiplier(move_type, ["Steel"]))
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Steelworker",
            "move": ctx.move.name,
            "effect": "type_resist",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": "Steelworker resists damage near the anchor.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="RKS System", holder="defender")
def _rks_system_shift(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if (ctx.effective_move.category or "").strip().lower() == "status":
        return
    used = next(iter(ctx.defender.get_temporary_effects("rks_system_used")), None)
    if used is not None:
        return
    ctx.defender.add_temporary_effect("rks_system_used", expires_round=ctx.battle.round + 999)
    move_type = (ctx.effective_move.type or "").strip()
    if not move_type:
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    defender_types = [t.strip().lower() for t in ctx.defender.spec.types if t]
    if "normal" in defender_types:
        _shift_type_multiplier_down(
            ctx,
            ability="RKS System",
            description="RKS System further resists damage.",
        )
        return
    new_mult = float(ptu_engine.type_multiplier(move_type, ["Normal"]))
    if new_mult == raw_mult:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", 0) or 0)
    ctx.result["type_multiplier"] = new_mult
    ctx.result["damage"] = int(pre_type_damage * new_mult)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "RKS System",
            "move": ctx.move.name,
            "effect": "type_shift",
            "from_multiplier": raw_mult,
            "to_multiplier": new_mult,
            "description": "RKS System treats the user as Normal-type.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Permafrost", holder="defender")
def _permafrost_super_effective_dr(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if has_errata(ctx.defender, "Permafrost"):
        return
    type_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_mult <= 1.0:
        return
    before = int(ctx.result.get("damage", 0) or 0)
    reduced = max(0, before - 5)
    if reduced == before:
        return
    _apply_damage_resist(
        ctx,
        ability="Permafrost",
        description="Permafrost reduces super-effective damage.",
        new_damage=reduced,
    )


@register_ability_hook(phase="post_result", ability="Solid Rock", holder="defender")
def _solid_rock_reduces_super_effective(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    type_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if type_mult <= 1.0:
        return
    before = int(ctx.result.get("damage", 0) or 0)
    if type_mult >= 2.0:
        reduced = int(before * 0.75)
    else:
        reduced = int(before * (1.25 / 1.5))
    if ctx.defender.has_ability("Filter"):
        reduced = max(0, reduced - 5)
    _apply_damage_resist(
        ctx,
        ability="Solid Rock",
        description="Solid Rock reduces super-effective damage.",
        new_damage=reduced,
    )


@register_ability_hook(phase="post_result", ability="Tolerance", holder="defender")
def _tolerance_resists_further(ctx: AbilityHookContext) -> None:
    if ctx.result is None:
        return
    raw_mult = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    if raw_mult >= 1.0:
        return
    _shift_type_multiplier_down(
        ctx,
        ability="Tolerance",
        description="Tolerance further reduces resisted damage.",
    )
    if ctx.defender is not None and ctx.defender.get_temporary_effects("duelist_manual_ability"):
        _shift_type_multiplier_down(
            ctx,
            ability="Tolerance",
            description="Duelist's Manual doubles Tolerance's resisted-damage step.",
        )


@register_ability_hook(phase="post_result", ability="Enduring Rage", holder="defender")
def _enduring_rage_reduces_damage(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if not ctx.defender.has_status("Enraged"):
        return
    before = int(ctx.result.get("damage", 0) or 0)
    reduced = max(0, before - 5)
    if reduced == before:
        return
    _apply_damage_resist(
        ctx,
        ability="Enduring Rage",
        description="Enduring Rage reduces damage while enraged.",
        new_damage=reduced,
    )
