"""Attacker held items that trigger after dealing damage."""

from __future__ import annotations

import math

from ...item_effects import parse_item_effects
from ...battle_state import MoveSpec
from ...move_traits import move_has_contact_trait, move_has_keyword
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


@register_item_hook("attacker_post_damage")
def _attacker_post_damage(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    attacker = ctx.holder
    move = ctx.move
    damage_dealt = int(ctx.damage_dealt or 0)
    if battle._magic_room_active():
        return
    if damage_dealt <= 0 or (move.category or "").lower() == "status":
        return
    roll = ctx.result.get("roll")
    try:
        roll_value = int(roll) if roll is not None else None
    except (TypeError, ValueError):
        roll_value = None
    defender = ctx.target
    defender_id = ctx.target_id
    held_items = sorted(battle._iter_held_items(attacker), key=lambda row: row[0], reverse=True)
    for _idx, item, entry in held_items:
        effects = parse_item_effects(entry)
        name = _item_name_text(item).strip()
        normalized = entry.normalized_name()
        self_damage = effects.get("self_damage_fraction")
        if self_damage:
            numerator, denominator = self_damage
            recoil_amount = int(math.floor(attacker.max_hp() * numerator / max(1, denominator)))
            if recoil_amount > 0:
                attacker.apply_damage(recoil_amount)
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "self_damage",
                        "amount": recoil_amount,
                        "target_hp": attacker.hp,
                    }
                )
        temp_hp_tick = effects.get("temp_hp_on_damage_tick")
        if temp_hp_tick:
            gained = attacker.add_temp_hp(attacker.tick_value() * int(temp_hp_tick))
            if gained:
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "temp_hp",
                        "amount": gained,
                        "temp_hp": attacker.temp_hp,
                        "target_hp": attacker.hp,
                    }
                )
        if normalized == "black augurite":
            if defender is None or defender_id is None:
                continue
            if defender.has_status("Splinter"):
                continue
            if not move_has_contact_trait(move):
                continue
            chance = 30 if move_has_keyword(move, "sharp") else 10
            roll = battle.rng.randint(1, 100)
            if roll > chance:
                continue
            battle._apply_status(
                ctx.events,
                attacker_id=ctx.holder_id,
                target_id=defender_id,
                move=MoveSpec(name="Black Augurite", type="Rock", category="Status"),
                target=defender,
                status="Splinter",
                effect="item_status",
                description="Black Augurite splinters the target on contact.",
                remaining=5,
                roll=roll,
            )
            continue
        if normalized == "pure incense":
            species_name = str(getattr(attacker.spec, "species", "") or "").strip().lower()
            if species_name in {"chingling", "chimecho"} and move_has_keyword(move, "sonic"):
                roll = battle.rng.randint(1, 100)
                if roll <= 10:
                    for stat in ("atk", "def", "spatk", "spdef", "spd", "accuracy", "evasion"):
                        battle._apply_combat_stage(
                            ctx.events,
                            attacker_id=ctx.holder_id,
                            target_id=ctx.holder_id,
                            move=MoveSpec(name="Pure Incense", type="Normal", category="Status"),
                            target=attacker,
                            stat=stat,
                            delta=1,
                            description="Pure Incense grants an Omniboost.",
                            effect="item_stage",
                            roll=roll,
                        )
                    ctx.events.append(
                        {
                            "type": "item",
                            "actor": ctx.holder_id,
                            "item": name,
                            "effect": "omniboost",
                            "roll": roll,
                            "target_hp": attacker.hp,
                        }
                    )
            continue
        if roll_value is None or roll_value < 19 or defender is None or defender_id is None:
            continue
        if normalized == "king's rock":
            effect_text = (move.effects_text or "").lower()
            if "flinch" in effect_text:
                continue
            if defender.has_status("Flinch") or defender.has_status("Flinched"):
                continue
            battle._apply_status(
                ctx.events,
                attacker_id=ctx.holder_id,
                target_id=defender_id,
                move=move,
                target=defender,
                status="Flinched",
                effect="item_status",
                description=f"{name} causes flinch on a high accuracy roll.",
                roll=roll_value,
                remaining=1,
                allow_reflect=False,
            )
        elif normalized == "razor fang":
            defender.injuries = max(0, int(defender.injuries or 0)) + 1
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "target": defender_id,
                    "item": name,
                    "effect": "injury",
                    "amount": 1,
                    "injuries": defender.injuries,
                    "target_hp": defender.hp,
                }
            )
        elif normalized == "binding band":
            if not defender.has_status("Bound"):
                continue
            if not defender.has_status("Bleed"):
                battle._apply_status(
                    ctx.events,
                    attacker_id=ctx.holder_id,
                    target_id=defender_id,
                    move=MoveSpec(name="Binding Band", type="Normal", category="Status"),
                    target=defender,
                    status="Bleed",
                    effect="item_status",
                    description="Binding Band inflicts Bleed on a bound target.",
                    remaining=3,
                )
