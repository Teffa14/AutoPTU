"""Defender hooks that run before applying damage."""

from __future__ import annotations

import math

from ..ability_hooks import AbilityHookContext, register_ability_hook


@register_ability_hook(phase="pre_apply_damage", ability="Desert Weather", holder="defender")
@register_ability_hook(phase="pre_apply_damage", ability="Desert Weather [Errata]", holder="defender")
def _desert_weather_fire_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    incoming_damage = int(ctx.result.get("damage", 0) or 0)
    if incoming_damage <= 0:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    weather_name = (ctx.battle.effective_weather() or "").strip().lower()
    if "sun" not in weather_name:
        return
    reduced = int(incoming_damage * 0.5)
    incoming_damage = max(0, reduced)
    ctx.result["damage"] = incoming_damage
    ability_name = "Desert Weather [Errata]" if ctx.defender.has_ability("Desert Weather [Errata]") else "Desert Weather"
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "fire_resist",
            "amount": incoming_damage,
            "description": f"{ability_name} reduces Fire damage in sunny weather.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_apply_damage", ability="Sturdy", holder="defender")
def _sturdy_prevents_ko(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    incoming_damage = int(ctx.result.get("damage", 0) or 0)
    defender = ctx.defender
    if incoming_damage <= 0:
        return
    if (defender.hp or 0) != defender.max_hp():
        return
    massive_threshold = max(1, defender.max_hp() // 2)
    if incoming_damage < (defender.hp or 0) and incoming_damage < massive_threshold:
        return
    incoming_damage = max(1, (defender.hp or 0) - 1)
    ctx.result["damage"] = incoming_damage
    ctx.result["sturdy_triggered"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Sturdy",
            "move": ctx.move.name,
            "effect": "survive",
            "description": "Sturdy prevents a full-HP knockout.",
            "target_hp": defender.hp,
        }
    )


@register_ability_hook(phase="pre_apply_damage", ability="Delayed Reaction", holder="defender")
def _delayed_reaction_stores_damage(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    incoming_damage = int(ctx.result.get("damage", 0) or 0)
    if incoming_damage <= 0:
        return
    ctx.defender.add_temporary_effect(
        "delayed_reaction",
        amount=incoming_damage,
        trigger_round=ctx.battle.round,
    )
    ctx.result["damage"] = 0
    ctx.result["skip_apply_damage"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Delayed Reaction",
            "move": ctx.move.name,
            "effect": "delay_damage",
            "amount": incoming_damage,
            "description": "Delayed Reaction stores damage for later.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_apply_damage", ability="Wash Away")
def _wash_away(ctx: AbilityHookContext) -> None:
    if ctx.defender is None or ctx.defender_id is None or ctx.attacker is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("wash_away_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 1:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("wash_away_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    for stat in ctx.defender.combat_stages:
        ctx.defender.combat_stages[stat] = 0
    removed = []
    coat_names = {
        "aqua ring",
        "reflect",
        "light screen",
        "safeguard",
        "mist",
        "lucky chant",
        "aurora veil",
        "mud sport",
    }
    for entry in list(ctx.defender.statuses):
        name = ctx.defender._normalized_status_name(entry)
        if name in coat_names:
            ctx.defender.statuses.remove(entry)
            removed.append(name)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "ability": "Wash Away",
            "move": ctx.move.name,
            "effect": "wash_away",
            "removed": removed,
            "description": "Wash Away resets combat stages and clears coats.",
            "target_hp": ctx.defender.hp,
        }
    )


def _shift_type_stage(ctx: AbilityHookContext, delta: int) -> None:
    if ctx.result is None:
        return
    pre_type_damage = int(ctx.result.get("pre_type_damage", ctx.result.get("damage", 0) or 0) or 0)
    type_multiplier = float(ctx.result.get("type_multiplier", 1.0) or 1.0)
    stage = ctx.battle._type_stage_from_multiplier(type_multiplier)
    boosted = ctx.battle._multiplier_from_stage(stage + delta)
    ctx.result["type_multiplier"] = boosted
    ctx.result["pre_type_damage"] = pre_type_damage
    ctx.result["damage"] = int(math.floor(pre_type_damage * boosted))


@register_ability_hook(phase="pre_apply_damage", ability="Full Guard", holder="defender")
def _full_guard_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if int(ctx.result.get("damage", 0) or 0) <= 0:
        return
    if ctx.defender.temp_hp <= 0:
        return
    for entry in list(ctx.defender.get_temporary_effects("full_guard_ready")):
        expires_round = entry.get("expires_round")
        if expires_round is not None and ctx.battle.round > int(expires_round):
            ctx.defender.remove_temporary_effect("full_guard_ready")
            continue
        _shift_type_stage(ctx, -1)
        ctx.defender.remove_temporary_effect("full_guard_ready")
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Full Guard",
                "move": ctx.move.name,
                "effect": "resist",
                "description": "Full Guard resists the incoming damage.",
                "target_hp": ctx.defender.hp,
            }
        )
        break


@register_ability_hook(phase="pre_apply_damage", ability="Innards Out", holder="defender")
def _innards_out_resist(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if int(ctx.result.get("damage", 0) or 0) <= 0:
        return
    used_entry = next(iter(ctx.defender.get_temporary_effects("innards_out_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 2:
        return
    _shift_type_stage(ctx, -1)
    ctx.defender.add_temporary_effect("innards_out_used", count=used_count + 1)
    ctx.defender.add_temporary_effect("innards_out_pending", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Innards Out",
            "move": ctx.move.name,
            "effect": "resist",
            "description": "Innards Out resists the triggering attack.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_apply_damage", ability="Disguise", holder="defender")
@register_ability_hook(phase="pre_apply_damage", ability="DIsguise", holder="defender")
def _disguise_blocks_hit(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    if int(ctx.result.get("damage", 0) or 0) <= 0:
        return
    if ctx.defender.get_temporary_effects("disguise_used"):
        return
    ctx.defender.add_temporary_effect("disguise_used")
    stat_choice = "def"
    for entry in list(ctx.defender.get_temporary_effects("disguise_choice")):
        choice = str(entry.get("stat") or "").strip().lower()
        if choice in {"atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"}:
            stat_choice = choice
        ctx.defender.remove_temporary_effect("disguise_choice")
        break
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["skip_apply_damage"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Disguise",
            "move": ctx.move.name,
            "effect": "block",
            "description": "Disguise nullifies the hit.",
            "target_hp": ctx.defender.hp,
        }
    )
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat=stat_choice,
        delta=1,
        description="Disguise grants a combat stage bonus.",
        effect="disguise_boost",
    )


@register_ability_hook(phase="pre_apply_damage", ability="Windveiled", holder="defender")
def _windveiled_immunity(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "flying":
        return
    incoming = int(ctx.result.get("damage", 0) or 0)
    if incoming <= 0:
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["immune_to"] = "Windveiled"
    ctx.defender.add_temporary_effect("windveiled_boost", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Windveiled",
            "move": ctx.move.name,
            "effect": "immunity",
            "description": "Windveiled negates Flying damage and charges a bonus.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="pre_apply_damage", ability="Winter's Kiss", holder="defender")
def _winters_kiss_immunity(ctx: AbilityHookContext) -> None:
    if ctx.result is None or ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "ice":
        return
    incoming = int(ctx.result.get("damage", 0) or 0)
    if incoming <= 0:
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["immune_to"] = "Winter's Kiss"
    healed = ctx.defender._apply_tick_heal(1)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Winter's Kiss",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Winter's Kiss negates Ice damage and restores a tick.",
            "target_hp": ctx.defender.hp,
        }
    )
