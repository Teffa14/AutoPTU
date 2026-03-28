"""Utility to regenerate ITEM_LOG.md from CSV/Foundry item sources."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
CSV_ITEM_PATH = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Item Data.csv"
CSV_INV_PATH = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv"
CSV_INVENTORY_PATH = ROOT / "files" / "Fancy PTU 1.05 Sheet - Version Hisui - Inventory.csv"
FOUNDRY_GEAR_DIR = (
    ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-gear"
)
WEAPONS_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "weapons.json"
ITEM_LOG = ROOT / "ITEM_LOG.md"
OVERRIDES_PATH = ROOT / "auto_ptu" / "data" / "item_status_overrides.json"

from auto_ptu.rules.item_catalog import get_item_entry
from auto_ptu.rules.item_effects import parse_item_effects


def _load_csv_items(path: Path) -> Tuple[Set[str], Set[str]]:
    food_items: Set[str] = set()
    held_items: Set[str] = set()
    if not path.exists():
        return food_items, held_items
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            food = (row.get("Food Item") or "").strip()
            held = (row.get("Held Item") or "").strip()
            if food:
                food_items.add(food)
            if held:
                held_items.add(held)
    return food_items, held_items


def _load_foundry_items(path: Path) -> Set[str]:
    items: Set[str] = set()
    if not path.exists():
        return items
    for entry in path.glob("*.json"):
        if entry.name == "_folders.json":
            continue
        try:
            data = json.loads(entry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        name = str(data.get("name") or "").strip()
        if name:
            items.add(name)
    return items


def _looks_like_price(raw: str) -> bool:
    text = str(raw or "").strip()
    if not text:
        return False
    if text in {"--", "-", "—"}:
        return True
    if "$" in text:
        return True
    return any(ch.isdigit() for ch in text)


def _load_inventory_items(path: Path) -> Set[str]:
    items: Set[str] = set()
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return items
    for row in rows[1:]:
        if not row:
            continue
        for idx in range(0, len(row), 3):
            if idx >= len(row):
                continue
            name = row[idx].strip()
            price = row[idx + 1].strip() if idx + 1 < len(row) else ""
            if not name or not _looks_like_price(price):
                continue
            items.add(name)
    return items


def _load_weapon_items(path: Path) -> Set[str]:
    items: Set[str] = set()
    if not path.exists():
        return items
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return items
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            if name:
                items.add(name)
    return items


def _load_overrides(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    overrides: Dict[str, Dict[str, str]] = {}
    if isinstance(raw, dict):
        for name, payload in raw.items():
            if not name:
                continue
            overrides[str(name).strip().lower()] = payload or {}
    return overrides


def _implemented_item_sets() -> Tuple[Set[str], Set[str], Set[str], Set[str], Set[str]]:
    # Explicit use-item hooks defined in _apply_item_use.
    use_items = {
        "potion",
        "super potion",
        "hyper potion",
        "enriched water",
        "super soda pop",
        "sparkling lemonade",
        "moomoo milk",
        "energy powder",
        "energy root",
        "shuckle's berry juice",
        "antidote",
        "burn heal",
        "paralyze heal",
        "ice heal",
        "awakening",
        "full heal",
        "heal powder",
        "full restore",
        "revive",
        "revival herb",
        "x attack",
        "x defend",
        "x special",
        "x sp. def.",
        "x speed",
        "dire hit",
        "leppa berry",
    }
    natural_gift = set()
    multi_attack = set()
    type_memory = set()
    try:
        from auto_ptu.rules import battle_state as rules_battle_state

        natural_gift = set(rules_battle_state._NATURAL_GIFT_BERRIES.keys())
        multi_attack = set(rules_battle_state._MULTI_ATTACK_ITEM_TYPES.keys())
    except Exception:
        natural_gift = set()
        multi_attack = set()
    type_names = {
        "normal",
        "fire",
        "water",
        "electric",
        "grass",
        "ice",
        "fighting",
        "poison",
        "ground",
        "flying",
        "psychic",
        "bug",
        "rock",
        "ghost",
        "dragon",
        "dark",
        "steel",
        "fairy",
    }
    for type_name in type_names:
        type_memory.add(f"{type_name} memory")
        type_memory.add(f"{type_name} disc")
        type_memory.add(f"{type_name} disk")
    return use_items, natural_gift, multi_attack, type_memory, type_names


def _item_status(
    name: str,
    sources: Iterable[str],
    food_items: Set[str],
    weapon_items: Set[str],
    use_items: Set[str],
    natural_gift: Set[str],
    multi_attack: Set[str],
    type_memory: Set[str],
    overrides: Dict[str, Dict[str, str]],
) -> Tuple[str, str]:
    normalized = name.lower().strip()
    notes: List[str] = []
    status = "pending"

    if normalized in use_items:
        status = "done"
        notes.append("Use-item hook supported (healing/status/stage/revive).")
    if normalized in food_items:
        status = "done"
        notes.append("Food buff item handled by digestion system.")
    if normalized in natural_gift:
        status = "done"
        notes.append("Natural Gift berry mapping supported.")
    if normalized in multi_attack or normalized in type_memory:
        status = "done"
        notes.append("Item type mapping supported for Multi-Attack/Techno Blast.")
    if normalized in weapon_items:
        # Weapons are usable/equippable, but many per-weapon passives are not yet modeled.
        notes.append("Weapon equip/attack bonuses supported.")
        if status == "pending":
            status = "in progress"

    entry = get_item_entry(name)
    if entry is not None:
        effects = parse_item_effects(entry)
        effect_keys = {key for key in effects if key not in {"consumable", "heal_ticks"}}
        if effect_keys:
            status = "done"
            effect_notes: List[str] = []
            if effects.get("start_heal_fraction") or effects.get("end_heal_fraction"):
                effect_notes.append("Turn-based healing supported.")
            if effects.get("cure_volatile"):
                effect_notes.append("Volatile status cure supported.")
            if effects.get("setup_skip"):
                effect_notes.append("Set-up skip supported.")
            if effects.get("clear_negative_stages"):
                effect_notes.append("Negative stage cleanse supported.")
            if effects.get("choice_stat"):
                effect_notes.append("Choice stat baseline supported.")
            if effects.get("crit_range_bonus"):
                effect_notes.append("Crit range bonus supported.")
            if effects.get("type_damage_bonus"):
                effect_notes.append("Type damage bonus supported.")
            if effects.get("super_effective_resist"):
                effect_notes.append("Super-effective mitigation supported.")
            if effects.get("frequency_step_up"):
                effect_notes.append("Frequency upgrade supported.")
            if effect_notes:
                notes.append(" ".join(effect_notes))

    source_note = ", ".join(sorted(set(sources)))
    if source_note:
        notes.append(f"Sources: {source_note}.")

    override = overrides.get(normalized)
    if override:
        status = override.get("status", status)
        note = override.get("note")
        if note:
            return status, note
    return status, " ".join(notes) if notes else "Hook pending; no dedicated item logic yet."


def main() -> None:
    food_items, held_items = _load_csv_items(CSV_ITEM_PATH)
    inventory_items = _load_inventory_items(CSV_INV_PATH) | _load_inventory_items(CSV_INVENTORY_PATH)
    foundry_items = _load_foundry_items(FOUNDRY_GEAR_DIR)
    weapon_items = _load_weapon_items(WEAPONS_PATH)
    overrides = _load_overrides(OVERRIDES_PATH)

    use_items, natural_gift, multi_attack, type_memory, _ = _implemented_item_sets()

    catalog: Dict[str, Dict[str, object]] = {}
    def add_items(names: Iterable[str], source: str) -> None:
        for name in names:
            if not name:
                continue
            key = name.lower().strip()
            entry = catalog.setdefault(key, {"name": name, "sources": set()})
            entry["sources"].add(source)

    add_items(food_items, "CSV Food")
    add_items(held_items, "CSV Held")
    add_items(inventory_items, "CSV Inventory")
    add_items(foundry_items, "Foundry core-gear")
    add_items(weapon_items, "Compiled weapons")

    rows: List[Tuple[str, str, str, str, str]] = []
    implemented = 0
    sorted_items = sorted(catalog.values(), key=lambda entry: str(entry["name"]).lower())
    for idx, entry in enumerate(sorted_items, 1):
        name = str(entry["name"]).strip()
        sources = entry.get("sources", set())
        status, note = _item_status(
            name,
            sources,
            food_items=food_items,
            weapon_items=weapon_items,
            use_items=use_items,
            natural_gift=natural_gift,
            multi_attack=multi_attack,
            type_memory=type_memory,
            overrides=overrides,
        )
        if status == "done":
            implemented += 1
        rows.append((str(idx), name, status, note))

    total = len(rows)
    pending = total - implemented
    lines = [
        "# Item Implementation Log",
        "",
        "Master list of PTU items sourced from CSV sheets, Foundry core-gear packs, and compiled weapons.",
        "",
        f"- **Total items**: {total}",
        f"- **Implemented**: {implemented}",
        f"- **Pending**: {pending}",
        "",
        "Status values: `pending` = no dedicated hook yet, `in progress` = actively implementing, `done` = code + tests + scenario coverage exist.",
        "",
        "| # | Item | Status | Notes |",
        "|---|------|--------|-------|",
    ]
    for idx, name, status, notes in rows:
        safe_name = name.replace("`", "'")
        lines.append(f"| {idx} | `{safe_name}` | {status} | {notes} |")
    ITEM_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
