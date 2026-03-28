"""Attacker-side held item modifiers for damage calculations."""

from __future__ import annotations

from ...item_effects import parse_item_effects
from ...move_traits import move_has_contact_trait, move_has_keyword
from ....learnsets import normalize_species_key
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


@register_item_hook("attacker_modifiers")
def _attacker_item_modifiers(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    attacker = ctx.holder
    move = ctx.move
    context = ctx.attack_context
    if context is None:
        return
    if battle._magic_room_active():
        return
    holder_types = {t.lower().strip() for t in attacker.spec.types if t}
    species_name = str(getattr(attacker.spec, "species", "") or "")
    species_key = normalize_species_key(species_name).replace("'", "").replace("\u2019", "")
    move_type = (move.type or "").strip().lower()
    held_items = sorted(battle._iter_held_items(attacker), key=lambda row: row[0], reverse=True)
    for idx, item, entry in held_items:
        normalized = entry.normalized_name()
        effects = parse_item_effects(entry)
        bonus = effects.get("type_damage_bonus")
        if bonus:
            bonus_type, amount = bonus
            if move_type and move_type == bonus_type.lower():
                context.add_modifier(
                    slug=f"item-{entry.normalized_name()}",
                    kind="power",
                    value=amount,
                    source=_item_name_text(item),
                )
        scalars = []
        scalar = effects.get("type_damage_scalar")
        if scalar:
            scalars.append(scalar)
        scalars.extend(effects.get("type_damage_scalars") or [])
        for scalar_type, multiplier in scalars:
            if move_type and move_type == str(scalar_type).lower():
                context.add_modifier(
                    slug=f"item-{entry.normalized_name()}-scalar",
                    kind="damage_scalar",
                    value=multiplier,
                    source=_item_name_text(item),
                )
                if effects.get("trigger_declare_type") or effects.get("consumable"):
                    battle._consume_held_item(
                        ctx.holder_id,
                        attacker,
                        idx,
                        item,
                        "consume_on_attack",
                        f"{_item_name_text(item)} boosts attack power.",
                        ctx.events,
                    )
                    break
        category_scalars = effects.get("category_damage_scalars") or []
        move_category = (move.category or "").strip().lower()
        for category, multiplier in category_scalars:
            if move_category and move_category == str(category).lower():
                context.add_modifier(
                    slug=f"item-{entry.normalized_name()}-category-scalar",
                    kind="damage_scalar",
                    value=multiplier,
                    source=_item_name_text(item),
                )
        flat_bonus = effects.get("type_damage_flat")
        if flat_bonus and (move.category or "").lower() != "status":
            flat_type, amount = flat_bonus
            if move_type and move_type == flat_type.lower():
                context.add_modifier(
                    slug=f"item-{entry.normalized_name()}-flat",
                    kind="damage_flat",
                    value=amount,
                    source=_item_name_text(item),
                )
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "damage_flat",
                        "amount": amount,
                        "target_hp": attacker.hp,
                    }
                )
        if normalized == "pink pearl" and (move.category or "").lower() != "status":
            if move_type == "psychic":
                context.add_modifier(
                    slug="item-pink-pearl-flat",
                    kind="damage_flat",
                    value=5,
                    source=_item_name_text(item),
                )
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "damage_flat",
                        "amount": 5,
                        "target_hp": attacker.hp,
                    }
                )
        hit_bonus = effects.get("damage_bonus_on_hit")
        if hit_bonus and (move.category or "").lower() != "status":
            context.add_modifier(
                slug=f"item-{entry.normalized_name()}-hit-bonus",
                kind="damage_flat",
                value=int(hit_bonus),
                source=_item_name_text(item),
            )
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "item": _item_name_text(item),
                    "effect": "damage_bonus",
                    "amount": int(hit_bonus),
                    "target_hp": attacker.hp,
                }
            )
        move_category = (move.category or "").strip().lower()
        incense_rules = {
            "sea incense": ("water", "physical"),
            "rock incense": ("rock", "physical"),
            "odd incense": ("psychic", "special"),
            "rose incense": ("grass", "special"),
        }
        rule = incense_rules.get(normalized)
        if rule:
            required_type, required_category = rule
            if required_type in holder_types and move_category == required_category:
                context.add_modifier(
                    slug=f"item-{normalized}-incense",
                    kind="damage_scalar",
                    value=1.1,
                    source=_item_name_text(item),
                )
            if normalized == "sea incense" and species_key in {"azurill", "marill", "azumarill"}:
                if move_has_contact_trait(move):
                    context.add_modifier(
                        slug="item-sea-incense-contact",
                        kind="damage_scalar",
                        value=1.3,
                        source=_item_name_text(item),
                    )
        if normalized in {"scroll of darkness", "scroll of waters"}:
            required_type = "dark" if normalized == "scroll of darkness" else "water"
            if move_type == required_type:
                multiplier = 1.2
                if "urshifu" in species_name.lower():
                    multiplier = 1.3
                context.add_modifier(
                    slug=f"item-{normalized}-scroll",
                    kind="damage_scalar",
                    value=multiplier,
                    source=_item_name_text(item),
                )
        if normalized == "megaphone" and move_has_keyword(move, "sonic"):
            context.add_modifier(
                slug="item-megaphone-sonic",
                kind="damage_scalar",
                value=1.2,
                source=_item_name_text(item),
            )
        if normalized in {"type booster", "type boosters", "type plates"}:
            item_type = battle._item_type_from_item(item)
            if item_type and move_type == item_type.lower() and (move.category or "").lower() != "status":
                if normalized == "type booster":
                    context.add_modifier(
                        slug="item-type-booster-scalar",
                        kind="damage_scalar",
                        value=1.1,
                        source=_item_name_text(item),
                    )
                else:
                    context.add_modifier(
                        slug="item-type-booster-flat",
                        kind="damage_flat",
                        value=5,
                        source=_item_name_text(item),
                    )
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "type_boost",
                        "target_hp": attacker.hp,
                    }
                )
        if normalized == "type gem":
            item_type = battle._item_type_from_item(item)
            if item_type and move_type == item_type.lower() and (move.category or "").lower() != "status":
                context.add_modifier(
                    slug="item-type-gem",
                    kind="power",
                    value=3,
                    source=_item_name_text(item),
                )
                battle._consume_held_item(
                    ctx.holder_id,
                    attacker,
                    idx,
                    item,
                    "consume_on_attack",
                    f"{_item_name_text(item)} boosts attack power.",
                    ctx.events,
                )
        if normalized == "loaded dice" and move_has_keyword(move, "x-strike"):
            if "loaded-dice" in context.roll_options:
                continue
            context.add_roll_option("loaded-dice")
            context.add_modifier(
                slug="item-loaded-dice-power",
                kind="power",
                value=5,
                source=_item_name_text(item),
            )
            base_range = int(move.crit_range or 20)
            move.crit_range = max(2, base_range - 1)
            ctx.events.append(
                {
                    "type": "item",
                    "actor": ctx.holder_id,
                    "item": _item_name_text(item),
                    "effect": "x_strike_bonus",
                    "power_bonus": 5,
                    "crit_range": move.crit_range,
                    "target_hp": attacker.hp,
                }
            )
        if normalized == "metronome" and (move.category or "").strip().lower() != "status":
            current_name = str(move.name or "").strip().lower()
            chain_entries = attacker.get_temporary_effects("metronome_chain")
            prev_move = ""
            prev_count = 0
            if chain_entries:
                last = chain_entries[-1]
                if isinstance(last, dict):
                    prev_move = str(last.get("move") or "").strip().lower()
                    try:
                        prev_count = int(last.get("count", 0) or 0)
                    except (TypeError, ValueError):
                        prev_count = 0
            count = min(prev_count + 1, 5) if current_name and current_name == prev_move else 1
            while attacker.remove_temporary_effect("metronome_chain"):
                continue
            attacker.add_temporary_effect(
                "metronome_chain",
                move=move.name,
                count=count,
                round=battle.round,
                source=_item_name_text(item),
            )
            if count > 1:
                multiplier = 1.0 + (0.2 * (count - 1))
                context.add_modifier(
                    slug="item-metronome-clock",
                    kind="damage_scalar",
                    value=multiplier,
                    source=_item_name_text(item),
                )
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": _item_name_text(item),
                        "effect": "metronome_power",
                        "count": count,
                        "multiplier": multiplier,
                        "target_hp": attacker.hp,
                    }
                )
