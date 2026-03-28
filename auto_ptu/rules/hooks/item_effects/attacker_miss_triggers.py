"""Attacker held items that trigger on a miss."""

from __future__ import annotations

from ...item_effects import parse_item_effects
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


@register_item_hook("attacker_miss_triggers")
def _attacker_miss_triggers(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    attacker = ctx.holder
    if battle._magic_room_active():
        return
    held_items = sorted(battle._iter_held_items(attacker), key=lambda row: row[0], reverse=True)
    for idx, item, entry in held_items:
        effects = parse_item_effects(entry)
        if not effects.get("trigger_on_miss"):
            continue
        stage_changes = effects.get("stage_changes") or []
        applied = False
        for stat, amount in stage_changes:
            current = attacker.combat_stages.get(stat, 0)
            new_stage = max(-6, min(6, current + int(amount)))
            if new_stage != current:
                attacker.combat_stages[stat] = new_stage
                applied = True
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "trigger_on_miss",
                        "stat": stat,
                        "amount": new_stage - current,
                        "new_stage": new_stage,
                        "target_hp": attacker.hp,
                    }
                )
        if applied:
            battle._consume_held_item(
                ctx.holder_id,
                attacker,
                idx,
                item,
                "trigger_on_miss",
                f"{_item_name_text(item)} triggers on a miss.",
                ctx.events,
            )
