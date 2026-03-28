"""Defender-side held item mitigation hooks."""

from __future__ import annotations

import math

from ...item_effects import parse_item_effects
from ...move_traits import move_has_keyword
from ....learnsets import normalize_species_key
from ..item_hooks import ItemHookContext, register_item_hook


def _item_name_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return str(item or "").strip()


def _species_key(holder: object) -> str:
    spec = getattr(holder, "spec", None)
    raw = ""
    if spec is not None:
        raw = str(getattr(spec, "species", "") or getattr(spec, "name", "") or "")
    key = normalize_species_key(raw)
    return key.replace("'", "").replace("\u2019", "")


@register_item_hook("defender_mitigation")
def _defender_mitigation(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    defender = ctx.holder
    attacker_id = ctx.attacker_id
    move = ctx.move
    result = ctx.result
    events = ctx.events
    if battle._magic_room_active():
        return
    move_type = (move.type or "").strip().lower()
    type_multiplier = float(result.get("type_multiplier", 1.0) or 1.0)
    incoming = int(result.get("damage", 0) or 0)
    if incoming <= 0:
        return
    max_hp = defender.max_hp()
    before_hp = defender.hp or 0
    held_items = sorted(
        battle._iter_held_items(defender), key=lambda row: row[0], reverse=True
    )
    def _apply_scalar_event(amount: int, item_name: str, effect: str) -> None:
        events.append(
            {
                "type": "item",
                "actor": ctx.holder_id,
                "target": attacker_id,
                "item": item_name,
                "effect": effect,
                "amount": amount,
                "target_hp": defender.hp,
            }
        )

    species_key = _species_key(defender)
    defender_types = {t.lower().strip() for t in defender.spec.types if t}
    for idx, item, entry in held_items:
        name_text = _item_name_text(item)
        effects = parse_item_effects(entry)
        normalized = entry.normalized_name()
        def _apply_flat_reduction(amount: int, effect: str) -> None:
            nonlocal incoming
            if amount <= 0:
                return
            new_damage = max(0, incoming - int(amount))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "target": attacker_id,
                        "item": name_text,
                        "effect": effect,
                        "amount": int(amount),
                        "target_hp": defender.hp,
                    }
                )

        def _apply_percent_scalar(percent: int, effect: str) -> None:
            nonlocal incoming
            if percent == 0:
                return
            multiplier = 1.0 + (float(percent) / 100.0)
            new_damage = int(math.floor(incoming * multiplier))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "target": attacker_id,
                        "item": name_text,
                        "effect": effect,
                        "percent": int(percent),
                        "multiplier": multiplier,
                        "target_hp": defender.hp,
                    }
                )
        incense_rules = {
            "sea incense": ("water", "physical"),
            "rock incense": ("rock", "physical"),
            "odd incense": ("psychic", "special"),
            "rose incense": ("grass", "special"),
        }
        if normalized in {"breastplate", "buff coat"} and (move.category or "").lower() != "status":
            has_missile = move_has_keyword(move, "missile")
            has_sharp = move_has_keyword(move, "sharp")
            has_firearm = move_has_keyword(move, "firearm")
            has_missile_sharp = has_missile or has_sharp
            category = (move.category or "").lower()
            if normalized == "breastplate":
                if category == "physical":
                    _apply_flat_reduction(5, "breastplate_physical_flat")
                    _apply_percent_scalar(-5, "breastplate_physical_percent")
                if has_firearm:
                    _apply_flat_reduction(5, "breastplate_firearm_flat")
                    _apply_percent_scalar(-10, "breastplate_firearm_percent")
                if has_missile_sharp:
                    _apply_flat_reduction(10, "breastplate_missile_sharp_flat")
                    _apply_percent_scalar(-10, "breastplate_missile_sharp_percent")
            elif normalized == "buff coat":
                if category == "physical":
                    _apply_flat_reduction(6, "buff_coat_physical_flat")
                if category == "special":
                    _apply_percent_scalar(-5, "buff_coat_special_percent")
                if has_firearm:
                    _apply_percent_scalar(10, "buff_coat_firearm_percent")
                elif has_missile_sharp:
                    _apply_percent_scalar(-10, "buff_coat_missile_sharp_percent")
        if normalized == "heavy clothing" and (move.category or "").lower() != "status":
            has_contact = move_has_keyword(move, "contact")
            has_sharp = move_has_keyword(move, "sharp")
            has_missile = move_has_keyword(move, "missile")
            if has_contact or has_sharp:
                _apply_flat_reduction(4, "heavy_clothing_contact_sharp_flat")
            if has_missile:
                _apply_percent_scalar(-5, "heavy_clothing_missile_percent")
        if normalized == "husarine plate" and (move.category or "").lower() != "status":
            has_missile = move_has_keyword(move, "missile")
            has_sharp = move_has_keyword(move, "sharp")
            has_firearm = move_has_keyword(move, "firearm")
            category = (move.category or "").lower()
            if category == "physical":
                _apply_flat_reduction(30, "husarine_plate_physical_flat")
            if category == "special":
                _apply_percent_scalar(-15, "husarine_plate_special_percent")
            if has_missile or has_sharp:
                _apply_percent_scalar(-25, "husarine_plate_missile_sharp_percent")
            if has_firearm:
                _apply_percent_scalar(-10, "husarine_plate_firearm_percent")
        if (
            normalized == "lysandre labs fire rescue armour"
            and (move.category or "").lower() != "status"
            and move_type == "fire"
        ):
            new_damage = int(math.floor(incoming * 0.5))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                _apply_scalar_event(incoming, name_text, "fire_rescue_reduction")
        if normalized == "dampening foam":
            if move_has_keyword(move, "sonic"):
                new_damage = int(math.floor(incoming * 0.75))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "sonic_damage_scalar")
            if move_type == "fire":
                new_damage = int(math.floor(incoming * 1.4))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "fire_vulnerability")
        if normalized == "heavy-duty boots" and move_has_keyword(move, "earthbound"):
            new_damage = int(math.floor(incoming * 0.8))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                _apply_scalar_event(incoming, name_text, "earthbound_resistance")
        scalar = effects.get("damage_scalar_on_trigger")
        if scalar:
            new_damage = int(math.floor(incoming * float(scalar)))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                _apply_scalar_event(incoming, name_text, "damage_scalar")
        if normalized == "legend plate" and species_key == "arceus":
            new_damage = int(math.floor(incoming * 0.7))
            if new_damage != incoming:
                result["damage"] = new_damage
                incoming = new_damage
                _apply_scalar_event(incoming, name_text, "legend_plate_damage_scalar")
        type_scalar = effects.get("type_damage_scalar_defender")
        if type_scalar and (move.category or "").lower() != "status" and move_type:
            scalar_type, multiplier = type_scalar
            if move_type == scalar_type.lower():
                new_damage = int(math.floor(incoming * float(multiplier)))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "type_damage_scalar_defender")
        category_scalar = effects.get("category_damage_scalar_defender")
        if category_scalar and (move.category or "").lower() != "status":
            if normalized == "prism scale":
                if (move.category or "").lower() == "special":
                    multiplier = 0.8 if species_key in {"feebas", "milotic"} else 0.9
                elif (move.category or "").lower() == "physical" and species_key in {"feebas", "milotic"}:
                    multiplier = 0.9
                else:
                    multiplier = None
                if multiplier is not None:
                    new_damage = int(math.floor(incoming * float(multiplier)))
                    if new_damage != incoming:
                        result["damage"] = new_damage
                        incoming = new_damage
                        _apply_scalar_event(incoming, name_text, "category_damage_scalar_defender")
                continue
            if normalized == "metal alloy":
                if (move.category or "").lower() == "special":
                    multiplier = 0.8 if "steel" in defender_types else 0.9
                    new_damage = int(math.floor(incoming * float(multiplier)))
                    if new_damage != incoming:
                        result["damage"] = new_damage
                        incoming = new_damage
                        _apply_scalar_event(incoming, name_text, "category_damage_scalar_defender")
                continue
            if normalized == "frosterizer":
                if (move.category or "").lower() == "physical" and species_key in {
                    "smoochum",
                    "jynx",
                    "sopranice",
                }:
                    multiplier = 0.75
                    new_damage = int(math.floor(incoming * float(multiplier)))
                    if new_damage != incoming:
                        result["damage"] = new_damage
                        incoming = new_damage
                        _apply_scalar_event(incoming, name_text, "category_damage_scalar_defender")
                continue
            category, multiplier = category_scalar
            if (move.category or "").lower() == str(category).lower():
                new_damage = int(math.floor(incoming * float(multiplier)))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "category_damage_scalar_defender")
        incense_rule = incense_rules.get(normalized)
        if incense_rule:
            required_type, required_category = incense_rule
            if required_type in defender_types and (move.category or "").lower() == required_category:
                new_damage = int(math.floor(incoming * 0.9))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "category_damage_scalar_defender")
        if normalized in {"type brace", "type plates"}:
            item_type = battle._item_type_from_item(item)
            if item_type and move_type == item_type.lower() and (move.category or "").lower() != "status":
                new_damage = max(0, incoming - 15)
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "type_damage_reduction")
        type_reduction = effects.get("type_damage_reduction")
        if type_reduction and (move.category or "").lower() != "status" and move_type:
            reduction_type, amount = type_reduction
            if move_type == reduction_type.lower():
                new_damage = max(0, incoming - int(amount))
                if new_damage != incoming:
                    result["damage"] = new_damage
                    incoming = new_damage
                    _apply_scalar_event(incoming, name_text, "type_damage_reduction")
        if effects.get("focus_sash") and incoming >= int(math.ceil(max_hp * 0.75)):
            if before_hp > 0 and incoming >= before_hp:
                result["damage"] = max(0, before_hp - 1)
                battle._consume_held_item(
                    ctx.holder_id,
                    defender,
                    idx,
                    item,
                    "focus_sash",
                    f"{_item_name_text(item)} prevents the knockout.",
                    events,
                )
                break
        focus_band_chance = effects.get("focus_band_chance")
        if focus_band_chance and before_hp > 0 and incoming >= before_hp:
            roll = battle.rng.randint(1, 100)
            if roll <= int(focus_band_chance):
                result["damage"] = max(0, before_hp - 1)
                battle._consume_held_item(
                    ctx.holder_id,
                    defender,
                    idx,
                    item,
                    "focus_band",
                    f"{_item_name_text(item)} prevents the knockout.",
                    events,
                )
                events[-1]["roll"] = roll
                break
        if type_multiplier <= 1.0:
            continue
        resist = effects.get("super_effective_resist")
        if not resist:
            continue
        resist_type, percent = resist
        if not move_type or move_type != resist_type.lower():
            continue
        reduction = max(0, int(math.floor(incoming * percent / 100)))
        new_damage = max(0, incoming - reduction)
        if new_damage != incoming:
            result["damage"] = new_damage
            result["item_resist"] = True
            battle._consume_held_item(
                ctx.holder_id,
                defender,
                idx,
                item,
                "super_effective_resist",
                f"{_item_name_text(item)} reduces super effective damage.",
                events,
            )
            break
