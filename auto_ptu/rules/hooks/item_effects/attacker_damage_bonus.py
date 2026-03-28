"""Attacker held items that add bonus damage on hit."""

from __future__ import annotations

from ...item_effects import parse_item_effects
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


@register_item_hook("attacker_damage_bonus")
def _attacker_damage_bonus(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    attacker = ctx.holder
    move = ctx.move
    result = ctx.result
    if battle._magic_room_active():
        return
    if not result.get("hit") or (move.category or "").lower() == "status":
        return
    type_multiplier = float(result.get("type_multiplier", 1.0) or 1.0)
    held_items = sorted(battle._iter_held_items(attacker), key=lambda row: row[0], reverse=True)
    for _idx, item, entry in held_items:
        effects = parse_item_effects(entry)
        bonus = effects.get("damage_bonus_on_super_effective")
        if bonus and type_multiplier > 1.0:
            result["damage"] = int(result.get("damage", 0) or 0) + int(bonus)
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "item": _item_name_text(item),
                    "effect": "super_effective_bonus",
                    "amount": int(bonus),
                    "target_hp": attacker.hp,
                }
            )
