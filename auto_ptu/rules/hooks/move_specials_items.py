"""Item-transfer move specials extracted from battle_state."""

from __future__ import annotations

from typing import List, Optional

from .move_specials import MoveSpecialContext, register_move_special


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


def _items_list(items: object) -> Optional[List[object]]:
    return items if isinstance(items, list) else None


def _sync_items(*states: Optional[object]) -> None:
    for state in states:
        if state is None:
            continue
        sync = getattr(state, "_sync_source_items", None)
        if callable(sync):
            sync()


def _leek_mastery_blocks_item(holder: Optional[object], item: object) -> bool:
    if holder is None or not getattr(holder, "has_ability", lambda _name: False)("Leek Mastery"):
        return False
    name = _item_name_text(item).lower()
    return "leek" in name or name == "stick"


def _sticky_hold_blocks_item(holder: Optional[object]) -> bool:
    return bool(holder is not None and getattr(holder, "has_ability", lambda _name: False)("Sticky Hold"))


@register_move_special("covet")
def _covet(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = _items_list(ctx.defender.spec.items)
    if attacker_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "covet_failed",
                "description": "Covet fails because the user is already holding an item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if not defender_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "covet_failed",
                "description": "Covet fails because the target has no held items.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
    item = defender_items[item_index]
    if _sticky_hold_blocks_item(ctx.defender):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Sticky Hold",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Sticky Hold prevents item theft.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if _leek_mastery_blocks_item(ctx.defender, item):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Leek Mastery",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Leek Mastery prevents item theft.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = defender_items.pop(item_index)
    attacker_items.append(item)
    _sync_items(ctx.attacker, ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "covet",
            "item": _item_name_text(item),
            "description": "Covet steals the target's held item.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("pluck")
def _pluck(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = _items_list(ctx.defender.spec.items)
    if attacker_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "pluck_failed",
                "description": "Pluck fails because the user is already holding an item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if not defender_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "pluck_failed",
                "description": "Pluck fails because the target has no held items.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
    item = defender_items[item_index]
    if _sticky_hold_blocks_item(ctx.defender):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Sticky Hold",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Sticky Hold prevents item theft.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if _leek_mastery_blocks_item(ctx.defender, item):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Leek Mastery",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Leek Mastery prevents item theft.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = defender_items.pop(item_index)
    attacker_items.append(item)
    _sync_items(ctx.attacker, ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "pluck",
            "item": _item_name_text(item),
            "description": "Pluck steals the target's held item.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("thief")
def _thief(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = ctx.defender.spec.items if isinstance(ctx.defender.spec.items, list) else []
    if attacker_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "thief_failed",
                "description": "Thief fails because the user is already holding an item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if defender_items:
        item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
        stolen = defender_items[item_index]
        if _sticky_hold_blocks_item(ctx.defender):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Sticky Hold",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(stolen),
                    "description": "Sticky Hold prevents item theft.",
                    "target_hp": ctx.defender.hp,
                }
            )
            return
        if _leek_mastery_blocks_item(ctx.defender, stolen):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Leek Mastery",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(stolen),
                    "description": "Leek Mastery prevents item theft.",
                    "target_hp": ctx.defender.hp,
                }
            )
            return
        stolen = defender_items.pop(item_index)
        attacker_items.insert(0, stolen)
        _sync_items(ctx.attacker, ctx.defender)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "thief",
                "item": _item_name_text(stolen),
                "description": "Thief steals the target's held item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "thief_failed",
            "description": "Thief fails because the target has no held item.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("knock off")
def _knock_off(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    defender_items = ctx.defender.spec.items if isinstance(ctx.defender.spec.items, list) else []
    if not defender_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "knock_off_failed",
                "description": "Knock Off fails because the target has no held items.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
    item = defender_items[item_index]
    if _sticky_hold_blocks_item(ctx.defender):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Sticky Hold",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Sticky Hold prevents item loss.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if _leek_mastery_blocks_item(ctx.defender, item):
        ctx.events.append(
            {
                "type": "ability",
                "actor": ctx.defender_id,
                "target": ctx.attacker_id,
                "ability": "Leek Mastery",
                "move": ctx.move.name,
                "effect": "item_block",
                "item": _item_name_text(item),
                "description": "Leek Mastery prevents item loss.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = defender_items.pop(item_index)
    _sync_items(ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "knock_off",
            "item": _item_name_text(item),
            "description": "Knock Off removes the target's held item.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("bestow")
def _bestow(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = _items_list(ctx.defender.spec.items)
    if not attacker_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "bestow_failed",
                "description": "Bestow failed because the user has no held items.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    item = attacker_items.pop(ctx.battle._delivery_bird_item_index(ctx.attacker, attacker_items))
    item_name = item.get("name") if isinstance(item, dict) else item
    if defender_items and len(defender_items) > 0:
        item_events = ctx.battle._apply_item_use(ctx.attacker_id, ctx.defender_id, item)
        if item_events:
            ctx.events.append(
                {
                    "type": "move",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "move": ctx.move.name,
                    "effect": "bestow_use_item",
                    "item": item_name,
                    "description": "Bestow uses the held item on the target.",
                    "target_hp": ctx.defender.hp,
                }
            )
            ctx.events.extend(item_events)
            for payload in item_events:
                ctx.battle.log_event(payload)
            return
        buffs = ctx.battle._food_buffs_from_items(
            [item] if isinstance(item, dict) else [{"name": item_name}]
        )
        if buffs:
            ctx.defender.food_buffs.extend(buffs)
            ctx.events.append(
                {
                    "type": "move",
                    "actor": ctx.attacker_id,
                    "target": ctx.defender_id,
                    "move": ctx.move.name,
                    "effect": "bestow_use_item",
                    "item": item_name,
                    "description": "Bestow uses the held item on the target.",
                    "target_hp": ctx.defender.hp,
                }
            )
            for payload in ctx.battle._apply_food_buff_start(ctx.defender_id):
                ctx.battle.log_event(payload)
            return
        attacker_items.insert(0, item)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "bestow_failed",
                "description": "Bestow failed because the target has no open slot.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    if defender_items is None:
        ctx.defender.spec.items = [item]
    else:
        defender_items.append(item)
    _sync_items(ctx.attacker, ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "bestow_transfer",
            "item": item_name,
            "description": "Bestow transfers a held item to the target.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("switcheroo")
def _switcheroo(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = ctx.defender.spec.items if isinstance(ctx.defender.spec.items, list) else []
    attacker_item = (
        attacker_items.pop(ctx.battle._delivery_bird_item_index(ctx.attacker, attacker_items))
        if attacker_items
        else None
    )
    defender_item = None
    if defender_items:
        item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
        candidate = defender_items[item_index]
        if _sticky_hold_blocks_item(ctx.defender):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Sticky Hold",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Sticky Hold prevents item swapping.",
                    "target_hp": ctx.defender.hp,
                }
            )
            if attacker_item is not None:
                attacker_items.insert(0, attacker_item)
            return
        if _leek_mastery_blocks_item(ctx.defender, candidate):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Leek Mastery",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Leek Mastery prevents item swapping.",
                    "target_hp": ctx.defender.hp,
                }
            )
            if attacker_item is not None:
                attacker_items.insert(0, attacker_item)
            return
        defender_item = defender_items.pop(item_index)
    if attacker_item is not None:
        defender_items.insert(0, attacker_item)
    if defender_item is not None:
        attacker_items.insert(0, defender_item)
    _sync_items(ctx.attacker, ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "switcheroo",
            "description": "Switcheroo swaps held items.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("trick")
def _trick(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    if ctx.defender_id == ctx.attacker_id:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "trick_failed",
                "description": "Trick fails because the target is the user.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    attacker_items = ctx.attacker.spec.items if isinstance(ctx.attacker.spec.items, list) else []
    defender_items = ctx.defender.spec.items if isinstance(ctx.defender.spec.items, list) else []
    if not attacker_items and not defender_items:
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "trick_failed",
                "description": "Trick fails because neither target has a held item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    attacker_item = (
        attacker_items.pop(ctx.battle._delivery_bird_item_index(ctx.attacker, attacker_items))
        if attacker_items
        else None
    )
    defender_item = None
    if defender_items:
        item_index = ctx.battle._delivery_bird_item_index(ctx.defender, defender_items)
        candidate = defender_items[item_index]
        if _sticky_hold_blocks_item(ctx.defender):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Sticky Hold",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Sticky Hold prevents item swapping.",
                    "target_hp": ctx.defender.hp,
                }
            )
            if attacker_item is not None:
                attacker_items.insert(0, attacker_item)
            return
        if _leek_mastery_blocks_item(ctx.defender, candidate):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Leek Mastery",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Leek Mastery prevents item swapping.",
                    "target_hp": ctx.defender.hp,
                }
            )
            if attacker_item is not None:
                attacker_items.insert(0, attacker_item)
            return
        defender_item = defender_items.pop(item_index)
    if attacker_item is not None:
        defender_items.insert(0, attacker_item)
    if defender_item is not None:
        attacker_items.insert(0, defender_item)
    _sync_items(ctx.attacker, ctx.defender)
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "trick",
            "description": "Trick swaps held items.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("incinerate")
def _incinerate(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    dropped = None
    if ctx.defender.spec.items:
        item_index = ctx.battle._delivery_bird_item_index(ctx.defender, ctx.defender.spec.items)
        candidate = ctx.defender.spec.items[item_index]
        if _sticky_hold_blocks_item(ctx.defender):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Sticky Hold",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Sticky Hold prevents item loss.",
                    "target_hp": ctx.defender.hp,
                }
            )
            return
        if _leek_mastery_blocks_item(ctx.defender, candidate):
            ctx.events.append(
                {
                    "type": "ability",
                    "actor": ctx.defender_id,
                    "target": ctx.attacker_id,
                    "ability": "Leek Mastery",
                    "move": ctx.move.name,
                    "effect": "item_block",
                    "item": _item_name_text(candidate),
                    "description": "Leek Mastery prevents item loss.",
                    "target_hp": ctx.defender.hp,
                }
            )
            return
        dropped = ctx.defender.spec.items.pop(item_index)
    if dropped:
        _sync_items(ctx.defender)
        ctx.events.append(
            {
                "type": "move",
                "actor": ctx.attacker_id,
                "target": ctx.defender_id,
                "move": ctx.move.name,
                "effect": "incinerate_drop",
                "item": _item_name_text(dropped),
                "description": "Incinerate forces the target to drop a held item.",
                "target_hp": ctx.defender.hp,
            }
        )
        return
    ctx.events.append(
        {
            "type": "move",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "incinerate_no_item",
            "description": "Incinerate finds no item to drop.",
            "target_hp": ctx.defender.hp,
        }
    )


@register_move_special("poltergeist")
def _poltergeist(ctx: MoveSpecialContext) -> None:
    if not ctx.hit or ctx.defender is None or ctx.defender_id is None:
        return
    items = ctx.defender.spec.items if isinstance(ctx.defender.spec.items, list) else []
    if not items:
        return
    damage = ctx.defender._apply_tick_damage(1)
    ctx.defender.add_temporary_effect("poltergeist", round=ctx.battle.round)
    ctx.events.append(
        {
            "type": "status",
            "actor": ctx.attacker_id,
            "target": ctx.defender_id,
            "move": ctx.move.name,
            "effect": "poltergeist",
            "description": "Poltergeist punishes held items with tick damage.",
            "amount": damage,
            "target_hp": ctx.defender.hp,
        }
    )
