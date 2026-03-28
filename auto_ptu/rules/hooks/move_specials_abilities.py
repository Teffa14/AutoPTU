"""Ability-focused move special handlers."""

from __future__ import annotations

from typing import Optional

from .. import movement, targeting
from ..abilities.ability_variants import has_ability_exact
from .move_specials import (
    MoveSpecialContext,
    register_move_special,
    register_global_move_special,
)


@register_move_special("empower")
def _empower(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Empower"):
        return
    ctx.attacker.add_temporary_effect(
        "action_override",
        action="free",
        self_status=True,
        move_category="status",
        source="Empower",
        round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Empower",
            "move": ctx.move.name,
            "effect": "action_override",
            "description": "Empower readies a self-targeting status move as a Free Action.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("heal bell")
def _soothing_tone_errata_heal(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Soothing Tone [Errata]"):
        return
    healed_any = False
    for pid, mon in ctx.battle.pokemon.items():
        if mon.hp is None or mon.hp <= 0:
            continue
        if ctx.battle._team_for(pid) != ctx.battle._team_for(ctx.attacker_id):
            continue
        before = mon.hp or 0
        mon.heal(mon.tick_value())
        healed = max(0, (mon.hp or 0) - before)
        if healed <= 0:
            continue
        healed_any = True
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "target": pid,
                "ability": "Soothing Tone",
                "move": ctx.move.name,
                "effect": "heal",
                "amount": healed,
                "description": "Soothing Tone restores HP when Heal Bell rings.",
                "target_hp": mon.hp,
            }
        )
    if not healed_any:
        return


@register_move_special("sun blanket [errata]")
def _sun_blanket_errata(ctx: MoveSpecialContext) -> None:
    if not has_ability_exact(ctx.attacker, "Sun Blanket [Errata]"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("sun_blanket_errata_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 5:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Sun Blanket [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Sun Blanket has no uses remaining today.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    max_hp = ctx.attacker.max_hp()
    hp = ctx.attacker.hp or 0
    weather = (ctx.battle.effective_weather() or "").strip().lower()
    sunny = "sun" in weather
    if hp * 2 > max_hp and not sunny:
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.attacker_id,
                "ability": "Sun Blanket [Errata]",
                "move": ctx.move.name,
                "effect": "fail",
                "description": "Sun Blanket requires sunlight or being below half HP.",
                "target_hp": ctx.attacker.hp,
            }
        )
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("sun_blanket_errata_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    heal_amount = ctx.attacker.tick_value()
    before = ctx.attacker.hp or 0
    ctx.attacker.heal(heal_amount)
    healed = max(0, (ctx.attacker.hp or 0) - before)
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
        "ability": "Sun Blanket [Errata]",
            "move": ctx.move.name,
            "effect": "heal",
            "amount": healed,
            "description": "Sun Blanket restores a tick of HP.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("unnerve [errata]")
def _unnerve_errata(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.defender_id is None:
        return
    if not has_ability_exact(ctx.attacker, "Unnerve [Errata]"):
        return
    if ctx.attacker.position is None or ctx.defender.position is None:
        return
    if targeting.chebyshev_distance(ctx.attacker.position, ctx.defender.position) > 6:
        return
    ctx.defender.add_temporary_effect(
        "unnerved",
        source="Unnerve [Errata]",
        ability="Unnerve [Errata]",
        source_id=ctx.attacker_id,
        expires_round=ctx.battle.round + 1,
    )
    ctx.defender.add_temporary_effect(
        "digestion_blocked",
        source="Unnerve [Errata]",
        ability="Unnerve [Errata]",
        source_id=ctx.attacker_id,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
        "ability": "Unnerve [Errata]",
            "move": ctx.move.name,
            "effect": "suppression",
            "description": "Unnerve prevents positive combat stages and digestion trades.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_global_move_special(phase="pre_damage")
def _unnerve_capture_snapshot(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.result is None:
        return
    if not ctx.defender.get_temporary_effects("unnerved"):
        return
    ctx.result["unnerved_snapshot"] = dict(ctx.defender.combat_stages)


@register_global_move_special(phase="post_damage")
def _unnerve_block_positive(ctx: MoveSpecialContext) -> None:
    if ctx.defender is None or ctx.result is None:
        return
    entry = next(iter(ctx.defender.get_temporary_effects("unnerved")), None)
    if entry is None:
        return
    snapshot = ctx.result.get("unnerved_snapshot")
    if not isinstance(snapshot, dict):
        return
    changed = False
    for stat, before in snapshot.items():
        try:
            before_val = int(before)
        except (TypeError, ValueError):
            continue
        current = int(ctx.defender.combat_stages.get(stat, 0) or 0)
        if current > before_val:
            ctx.defender.combat_stages[stat] = before_val
            changed = True
    if not changed:
        return
    ability_name = str(entry.get("ability") or "Unnerve")
    source_id = entry.get("source_id") or ctx.attacker_id
    ctx.events.append(
        {
            "type": "ability",
            "actor": source_id,
            "target": ctx.defender_id,
            "ability": ability_name,
            "move": ctx.move.name,
            "effect": "block_positive_cs",
            "description": "Unnerve blocks positive combat stage gains.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("spinning dance")
def _spinning_dance_action(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Spinning Dance"):
        return
    if ctx.attacker.has_status("Paralyzed") or ctx.attacker.has_status("Paralyze"):
        return
    if ctx.attacker.has_status("Sleep") or ctx.attacker.has_status("Asleep"):
        return
    ctx.attacker.add_temporary_effect(
        "evasion_bonus",
        amount=1,
        scope="all",
        expires_round=ctx.battle.round,
        source="Spinning Dance",
    )
    origin = ctx.attacker.position
    destination = None
    if ctx.battle.grid is not None and origin is not None:
        options = [coord for coord in movement.legal_shift_tiles(ctx.battle, ctx.attacker_id)]
        options = [coord for coord in options if targeting.chebyshev_distance(origin, coord) == 1]
        options.sort()
        if options:
            destination = options[0]
            ctx.attacker.position = destination
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Spinning Dance",
            "move": ctx.move.name,
            "effect": "shift",
            "from": origin,
            "to": destination,
            "description": "Spinning Dance grants evasion and a quick shift.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("heliovolt")
def _heliovolt_action(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Heliovolt"):
        return
    ctx.attacker.add_temporary_effect(
        "heliovolt_active",
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
    )
    ctx.attacker.add_temporary_effect(
        "evasion_bonus",
        amount=1,
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 1,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Heliovolt",
            "move": ctx.move.name,
            "effect": "evasion_bonus",
            "amount": 1,
            "description": "Heliovolt grants evasion and sunny resonance.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("gorilla tactics")
def _gorilla_tactics_action(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Gorilla Tactics"):
        return
    if ctx.attacker.get_temporary_effects("gorilla_tactics_active"):
        return
    used_moves = ctx.battle._moves_used_this_scene(ctx.attacker_id)
    ctx.attacker.add_temporary_effect(
        "gorilla_tactics_active",
        allowed_moves=sorted(used_moves),
        round=ctx.battle.round,
        expires_round=ctx.battle.round + 999,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Gorilla Tactics",
            "move": ctx.move.name,
            "effect": "activate",
            "allowed_moves": sorted(used_moves),
            "description": "Gorilla Tactics locks the user into previously used moves.",
            "target_hp": ctx.attacker.hp,
        }
    )


@register_move_special("psionic screech")
def _psionic_screech_action(ctx: MoveSpecialContext) -> None:
    if not ctx.attacker.has_ability("Psionic Screech"):
        return
    used_entry = next(iter(ctx.attacker.get_temporary_effects("psionic_screech_used")), None)
    used_count = int(used_entry.get("count", 0) or 0) if used_entry else 0
    if used_count >= 2:
        return
    if used_entry is None:
        ctx.attacker.add_temporary_effect("psionic_screech_used", count=1)
    else:
        used_entry["count"] = used_count + 1
    ctx.attacker.add_temporary_effect(
        "psionic_screech_pending",
        round=ctx.battle.round,
    )
    ctx.events.append(
        {
            "type": "ability",
            "actor": ctx.attacker_id,
            "ability": "Psionic Screech",
            "move": ctx.move.name,
            "effect": "type_shift_ready",
            "description": "Psionic Screech readies a Psychic conversion.",
            "target_hp": ctx.attacker.hp,
        }
    )
