"""Passive held item effects that modify attacker state."""

from __future__ import annotations

from typing import Callable

from ....learnsets import normalize_species_key
from ..item_hooks import ItemHookContext, register_item_hook


def _normalize_species(name: str) -> str:
    key = normalize_species_key(name)
    key = key.replace("'", "").replace("\u2019", "")
    return key


def _species_key(holder: object) -> str:
    spec = getattr(holder, "spec", None)
    raw = ""
    if spec is not None:
        raw = str(getattr(spec, "species", "") or getattr(spec, "name", "") or "")
    return _normalize_species(raw)


def _is_farfetchd(holder: object) -> bool:
    key = _species_key(holder)
    return key in {"farfetchd", "farfetchd galarian"}


def _is_cubone_line(holder: object) -> bool:
    key = _species_key(holder)
    return key in {"cubone", "marowak", "marowak alolan"}


def _remove_temp_effects(holder: object, kind: str, predicate: Callable[[dict], bool]) -> None:
    entries = getattr(holder, "get_temporary_effects", None)
    if not callable(entries):
        return
    effects = list(entries(kind))
    if not effects:
        return
    temp_list = getattr(holder, "temporary_effects", None)
    if not isinstance(temp_list, list):
        return
    for entry in effects:
        if not isinstance(entry, dict):
            continue
        if predicate(entry) and entry in temp_list:
            temp_list.remove(entry)


@register_item_hook("attacker_modifiers")
def _apply_rare_leek_and_thick_club(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    holder = ctx.holder
    if holder is None:
        return
    if battle._magic_room_active():
        _remove_temp_effects(
            holder,
            "crit_range_bonus",
            lambda entry: entry.get("source") == "Rare Leek",
        )
        _remove_temp_effects(
            holder,
            "ability_granted",
            lambda entry: entry.get("source") == "Thick Club" and entry.get("ability") == "Pure Power",
        )
        return

    has_rare_leek = getattr(holder, "has_item_named", lambda _name: False)("Rare Leek")
    if has_rare_leek and _is_farfetchd(holder):
        context = ctx.attack_context
        if context is not None and "rare-leek" in getattr(context, "roll_options", set()):
            return
        base_range = int(ctx.move.crit_range or 20)
        ctx.move.crit_range = max(2, base_range - 2)
        if context is not None:
            context.add_roll_option("rare-leek")
        ctx.events.append(
            {
                "type": "item",
                "actor": ctx.holder_id,
                "item": "Rare Leek",
                "effect": "crit_range",
                "amount": 2,
                "target_hp": holder.hp,
            }
        )

    has_thick_club = getattr(holder, "has_item_named", lambda _name: False)("Thick Club")
    if has_thick_club and _is_cubone_line(holder):
        if not holder.has_ability("Pure Power"):
            existing = any(
                entry.get("source") == "Thick Club" and entry.get("ability") == "Pure Power"
                for entry in holder.get_temporary_effects("ability_granted")
                if isinstance(entry, dict)
            )
            if not existing:
                holder.add_temporary_effect(
                    "ability_granted",
                    ability="Pure Power",
                    source="Thick Club",
                )
                ctx.events.append(
                    {
                        "type": "item",
                        "actor": ctx.holder_id,
                        "item": "Thick Club",
                        "effect": "grant_ability",
                        "ability": "Pure Power",
                        "target_hp": holder.hp,
                    }
                )
    else:
        _remove_temp_effects(
            holder,
            "ability_granted",
            lambda entry: entry.get("source") == "Thick Club" and entry.get("ability") == "Pure Power",
        )


@register_item_hook("attacker_modifiers")
def _apply_scope_lens(ctx: ItemHookContext) -> None:
    battle = ctx.battle
    holder = ctx.holder
    if holder is None:
        return
    if battle._magic_room_active():
        return
    if not getattr(holder, "has_item_named", lambda _name: False)("Scope Lens"):
        return
    context = ctx.attack_context
    if context is not None and "scope-lens" in getattr(context, "roll_options", set()):
        return
    base_range = int(ctx.move.crit_range or 20)
    ctx.move.crit_range = max(2, base_range - 1)
    if context is not None:
        context.add_roll_option("scope-lens")
    ctx.events.append(
        {
            "type": "item",
            "actor": ctx.holder_id,
            "item": "Scope Lens",
            "effect": "crit_range",
            "amount": 1,
            "target_hp": holder.hp,
        }
    )
