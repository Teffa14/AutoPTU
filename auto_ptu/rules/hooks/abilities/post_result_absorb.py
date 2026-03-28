"""Post-result absorb/immunity ability hooks."""

from __future__ import annotations

from ..ability_hooks import AbilityHookContext, register_ability_hook
from ...abilities.ability_variants import has_ability_exact, has_errata


@register_ability_hook(phase="post_result", ability="Flash Fire")
def _flash_fire_damage_boost(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    if not ctx.attacker or not ctx.attacker.get_temporary_effects("flash_fire"):
        return
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Flash Fire",
            "move": ctx.move.name,
            "effect": "damage_bonus",
            "description": "Flash Fire powers up Fire-type moves.",
            "target_hp": ctx.defender.hp if ctx.defender else None,
        }
    )


@register_ability_hook(phase="post_result", ability="Water Absorb", holder="defender")
def _water_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    healed = ctx.defender._apply_tick_heal(1)
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Water Absorb",
            "move": ctx.move.name,
            "effect": "absorb",
            "amount": healed,
            "description": "Water Absorb restores HP instead of taking damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Dry Skin", holder="defender")
def _dry_skin_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    healed = ctx.defender._apply_tick_heal(1)
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Dry Skin",
            "move": ctx.move.name,
            "effect": "absorb",
            "amount": healed,
            "description": "Dry Skin restores HP from Water-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Volt Absorb", holder="defender")
def _volt_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "electric":
        return
    healed = ctx.defender._apply_tick_heal(1)
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Volt Absorb",
            "move": ctx.move.name,
            "effect": "absorb",
            "amount": healed,
            "description": "Volt Absorb restores HP instead of taking damage.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Storm Drain", holder="defender")
def _storm_drain_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    ability_name = "Storm Drain"
    if any(
        str(name or "").strip().lower() == "storm drain [errata]" for name in ctx.defender.ability_names()
    ):
        ability_name = "Storm Drain [Errata]"
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "water":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=1,
        effect="storm_drain",
        description="Storm Drain boosts Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Storm Drain absorbs Water-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Lightning Rod", holder="defender")
def _lightning_rod_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    if has_ability_exact(ctx.defender, "Lightning Rod [Errata]"):
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "electric":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=1,
        effect="lightning_rod",
        description="Lightning Rod boosts Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Lightning Rod",
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Lightning Rod absorbs Electric-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Lightning Rod [Errata]", holder="defender")
def _lightning_rod_errata_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "electric":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="spatk",
        delta=1,
        effect="lightning_rod",
        description="Lightning Rod [Errata] boosts Special Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Lightning Rod [Errata]",
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Lightning Rod [Errata] absorbs Electric-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Motor Drive", holder="defender")
def _motor_drive_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "electric":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.defender.combat_stages["spd"] = ctx.defender.combat_stages.get("spd", 0) + 1
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Motor Drive",
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Motor Drive absorbs Electric-type moves and boosts Speed.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Sap Sipper", holder="defender")
def _sap_sipper_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    if has_errata(ctx.defender, "Sap Sipper"):
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "grass":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat="atk",
        delta=1,
        effect="sap_sipper",
        description="Sap Sipper boosts Attack.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Sap Sipper",
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Sap Sipper absorbs Grass-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Sap Sipper [Errata]", holder="defender")
def _sap_sipper_errata_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "grass":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True

    stat_choice = None
    for entry in list(ctx.defender.get_temporary_effects("sap_sipper_errata_choice")):
        raw = str(entry.get("stat") or entry.get("choice") or "").strip().lower()
        if raw in {"atk", "spatk"}:
            stat_choice = raw
        ctx.defender.remove_temporary_effect("sap_sipper_errata_choice")
    if stat_choice is None:
        stat_choice = ctx.battle.rng.choice(["atk", "spatk"])

    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat=stat_choice,
        delta=1,
        effect="sap_sipper_errata",
        description=f"Sap Sipper boosts {'Attack' if stat_choice == 'atk' else 'Special Attack'}.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Sap Sipper [Errata]",
            "move": ctx.move.name,
            "effect": "absorb",
            "stat": stat_choice,
            "description": "Sap Sipper absorbs Grass-type moves and boosts a stat.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Flash Fire", holder="defender")
def _flash_fire_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True
    ctx.defender.add_temporary_effect("flash_fire", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Flash Fire",
            "move": ctx.move.name,
            "effect": "absorb",
            "description": "Flash Fire absorbs Fire-type moves.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_ability_hook(phase="post_result", ability="Flash Fire [Errata]", holder="defender")
def _flash_fire_errata_absorb(ctx: AbilityHookContext) -> None:
    if ctx.defender is None:
        return
    move_type = (ctx.effective_move.type or "").strip().lower()
    if move_type != "fire":
        return
    ctx.result["damage"] = 0
    ctx.result["type_multiplier"] = 0.0
    ctx.result["absorbed_damage"] = True

    stat_choice = None
    for entry in list(ctx.defender.get_temporary_effects("flash_fire_errata_choice")):
        raw = str(entry.get("stat") or entry.get("choice") or "").strip().lower()
        if raw in {"atk", "spatk"}:
            stat_choice = raw
        ctx.defender.remove_temporary_effect("flash_fire_errata_choice")
    if stat_choice is None:
        stat_choice = ctx.battle.rng.choice(["atk", "spatk"])

    ctx.battle._apply_combat_stage(
        ctx.events,
        attacker_id=ctx.defender_id,
        target_id=ctx.defender_id,
        move=ctx.move,
        target=ctx.defender,
        stat=stat_choice,
        delta=1,
        effect="flash_fire_errata",
        description=f"Flash Fire boosts {'Attack' if stat_choice == 'atk' else 'Special Attack'}.",
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.defender_id,
            "target": ctx.attacker_id,
            "ability": "Flash Fire [Errata]",
            "move": ctx.move.name,
            "effect": "absorb",
            "stat": stat_choice,
            "description": "Flash Fire absorbs Fire-type moves and boosts a stat.",
            "target_hp": ctx.defender.hp,
        }
    )
