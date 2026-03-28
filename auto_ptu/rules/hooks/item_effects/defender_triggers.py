"""Defender held items that trigger after being hit."""

from __future__ import annotations

from ...item_effects import parse_item_effects
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


@register_item_hook("defender_triggers")
def _defender_triggers(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    defender = ctx.holder
    attacker = ctx.attacker
    move = ctx.move
    result = ctx.result
    damage_dealt = int(ctx.damage_dealt or 0)
    has_contact = bool(ctx.has_contact)
    if battle._magic_room_active():
        return
    if not result.get("hit") or damage_dealt <= 0:
        return
    move_type = (move.type or "").strip().lower()
    type_multiplier = float(result.get("type_multiplier", 1.0) or 1.0)
    held_items = sorted(battle._iter_held_items(defender), key=lambda row: row[0], reverse=True)
    for idx, item, entry in held_items:
        effects = parse_item_effects(entry)
        if effects.get("air_balloon") and damage_dealt > 0:
            battle._consume_held_item(
                ctx.holder_id,
                defender,
                idx,
                item,
                "air_balloon_popped",
                f"{_item_name_text(item)} pops after taking damage.",
                ctx.events,
            )
            continue
        if entry.normalized_name() == "eject button":
            defender.add_temporary_effect(
                "eject_button_ready",
                expires_round=battle.round + 1,
                source=_item_name_text(item),
            )
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "item": _item_name_text(item),
                    "effect": "eject_button_ready",
                    "expires_round": battle.round + 1,
                    "target_hp": defender.hp,
                }
            )
            battle._consume_held_item(
                ctx.holder_id,
                defender,
                idx,
                item,
                "eject_button_ready",
                f"{_item_name_text(item)} readies a forced switch.",
                ctx.events,
            )
            continue
        trigger_type = effects.get("trigger_hit_type")
        if trigger_type and move_type == trigger_type.lower():
            stage_changes = effects.get("stage_changes") or []
            for stat, amount in stage_changes:
                current = defender.combat_stages.get(stat, 0)
                new_stage = max(-6, min(6, current + int(amount)))
                if new_stage != current:
                    defender.combat_stages[stat] = new_stage
                    ctx.events.append(
                        {
                            "type": "item",
                            "actor": ctx.holder_id,
                            "item": _item_name_text(item),
                            "effect": "trigger_stage",
                            "stat": stat,
                            "amount": new_stage - current,
                            "new_stage": new_stage,
                            "target_hp": defender.hp,
                        }
                    )
            battle._consume_held_item(
                ctx.holder_id,
                defender,
                idx,
                item,
                "trigger_hit_type",
                f"{_item_name_text(item)} triggers on {trigger_type}-type hit.",
                ctx.events,
            )
            continue
        if effects.get("trigger_super_effective") and type_multiplier > 1.0:
            stage_changes = effects.get("stage_changes") or []
            for stat, amount in stage_changes:
                current = defender.combat_stages.get(stat, 0)
                new_stage = max(-6, min(6, current + int(amount)))
                if new_stage != current:
                    defender.combat_stages[stat] = new_stage
                    ctx.events.append(
                        {
                            "type": "item",
                            "actor": ctx.holder_id,
                            "item": _item_name_text(item),
                            "effect": "trigger_super_effective",
                            "stat": stat,
                            "amount": new_stage - current,
                            "new_stage": new_stage,
                            "target_hp": defender.hp,
                        }
                    )
            battle._consume_held_item(
                ctx.holder_id,
                defender,
                idx,
                item,
                "trigger_super_effective",
                f"{_item_name_text(item)} triggers on super effective hit.",
                ctx.events,
            )
            continue
        contact_ticks = effects.get("contact_ticks")
        if contact_ticks and has_contact and attacker is not None:
            amount = int(contact_ticks) * attacker.tick_value()
            if amount < 0:
                attacker.apply_damage(abs(amount))
            else:
                attacker.heal(amount)
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "target": ctx.attacker_id,
                    "item": _item_name_text(item),
                    "effect": "contact_ticks",
                    "amount": amount,
                    "target_hp": attacker.hp,
                }
            )
        if effects.get("desperation_trigger"):
            ctx.events.extend(
                battle._apply_desperation_item_trigger(ctx.holder_id, defender, idx, item)
            )
