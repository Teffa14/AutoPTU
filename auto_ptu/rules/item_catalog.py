"""Item catalog utilities for PTU gear and consumables."""
from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

ROOT = Path(__file__).resolve().parents[2]
CSV_ITEM_PATH = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Item Data.csv"
CSV_INV_PATH = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv"
CSV_INVENTORY_PATH = ROOT / "files" / "Fancy PTU 1.05 Sheet - Version Hisui - Inventory.csv"
FOUNDRY_GEAR_DIR = (
    ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-gear"
)
WEAPONS_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "weapons.json"
SUPPLEMENTAL_ITEMS_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "item_catalog_overrides.json"


@dataclass
class ItemEntry:
    name: str
    description: str = ""
    traits: Set[str] = field(default_factory=set)
    sources: Set[str] = field(default_factory=set)

    def normalized_name(self) -> str:
        return self.name.strip().lower()


_CATALOG_CACHE: Optional[Dict[str, ItemEntry]] = None
_CATALOG_CACHE_SIGNATURE: Optional[tuple[str, str, str, str, str, str]] = None


def _catalog_signature() -> tuple[str, str, str, str, str, str]:
    return (
        str(CSV_ITEM_PATH),
        str(CSV_INV_PATH),
        str(CSV_INVENTORY_PATH),
        str(FOUNDRY_GEAR_DIR),
        str(WEAPONS_PATH),
        str(SUPPLEMENTAL_ITEMS_PATH),
    )


def _compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _source_priority(sources: Set[str]) -> int:
    # Higher number wins when selecting authoritative description text.
    priority = 0
    for source in sources:
        label = str(source or "").strip().lower()
        if label.startswith("ptu core rulebook"):
            priority = max(priority, 500)
        elif label.startswith("ptu dataset"):
            priority = max(priority, 450)
        elif label.startswith("csv "):
            priority = max(priority, 400)
        elif label.startswith("compiled weapons"):
            priority = max(priority, 300)
        elif label.startswith("foundry core-gear"):
            priority = max(priority, 100)
        elif label:
            priority = max(priority, 200)
    return priority


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load_csv_items(path: Path) -> Dict[str, ItemEntry]:
    entries: Dict[str, ItemEntry] = {}
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return entries
    headers = rows[0]
    # Expected columns: Food Item, Digestion/Food Buff, Held Item, Description, Capability, Description, Weather, Effect
    # Use positional indices to avoid duplicate "Description" header collisions.
    idx_food = 0
    idx_food_buff = 1
    idx_held = 2
    idx_held_desc = 3
    for row in rows[1:]:
        if not row:
            continue
        if len(row) < max(idx_held_desc, idx_food_buff) + 1:
            row += [""] * (max(idx_held_desc, idx_food_buff) + 1 - len(row))
        food_name = row[idx_food].strip()
        food_buff = row[idx_food_buff].strip()
        held_name = row[idx_held].strip()
        held_desc = row[idx_held_desc].strip()
        if food_name:
            entry = entries.setdefault(food_name.lower(), ItemEntry(name=food_name))
            entry.sources.add("CSV Food")
            entry.traits.add("food")
            if food_buff:
                entry.description = entry.description or food_buff
        if held_name:
            entry = entries.setdefault(held_name.lower(), ItemEntry(name=held_name))
            entry.sources.add("CSV Held")
            entry.traits.add("held")
            if held_desc:
                entry.description = entry.description or held_desc
    return entries


def _looks_like_price(raw: str) -> bool:
    if raw is None:
        return False
    text = str(raw).strip()
    if not text:
        return False
    if text in {"--", "-", "—"}:
        return True
    if "$" in text:
        return True
    return any(ch.isdigit() for ch in text)


def _load_inventory_items(path: Path) -> Dict[str, ItemEntry]:
    entries: Dict[str, ItemEntry] = {}
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return entries
    for row in rows[1:]:
        if not row:
            continue
        for idx in range(0, len(row), 3):
            if idx >= len(row):
                continue
            name = row[idx].strip()
            price = row[idx + 1].strip() if idx + 1 < len(row) else ""
            desc = row[idx + 2].strip() if idx + 2 < len(row) else ""
            if not name or not _looks_like_price(price):
                continue
            entry = entries.setdefault(name.lower(), ItemEntry(name=name))
            entry.sources.add("CSV Inventory")
            if desc:
                entry.description = entry.description or desc
    return entries


def _load_foundry_items(path: Path) -> Dict[str, ItemEntry]:
    entries: Dict[str, ItemEntry] = {}
    if not path.exists():
        return entries
    for entry_path in path.glob("*.json"):
        if entry_path.name == "_folders.json":
            continue
        try:
            data = json.loads(entry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        name = str(data.get("name") or "").strip()
        if not name:
            continue
        system = data.get("system", {}) if isinstance(data, dict) else {}
        desc = _strip_html(str(system.get("description") or ""))
        traits = system.get("traits") or []
        trait_set: Set[str] = set()
        if isinstance(traits, str):
            trait_set.add(traits.strip().lower())
        elif isinstance(traits, Iterable):
            for trait in traits:
                if trait:
                    trait_set.add(str(trait).strip().lower())
        entry = entries.setdefault(name.lower(), ItemEntry(name=name))
        entry.sources.add("Foundry core-gear")
        entry.traits.update(trait_set)
        if desc:
            entry.description = entry.description or desc
    return entries


def _load_weapon_items(path: Path) -> Dict[str, ItemEntry]:
    entries: Dict[str, ItemEntry] = {}
    if not path.exists():
        return entries
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return entries
    if not isinstance(data, list):
        return entries
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        desc = str(entry.get("description") or "").strip()
        tags = entry.get("tags") or []
        trait_set: Set[str] = set()
        if isinstance(tags, str):
            trait_set.add(tags.strip().lower())
        elif isinstance(tags, Iterable):
            for tag in tags:
                if tag:
                    trait_set.add(str(tag).strip().lower())
        item = entries.setdefault(name.lower(), ItemEntry(name=name))
        item.sources.add("Compiled weapons")
        item.traits.update(trait_set)
        if desc:
            item.description = item.description or desc
    return entries


def _load_supplemental_items(path: Path) -> Dict[str, ItemEntry]:
    entries: Dict[str, ItemEntry] = {}
    if not path.exists():
        return entries
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return entries
    rows = payload.get("items", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return entries
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        desc = str(row.get("description") or "").strip()
        tags = row.get("tags") or []
        tag_set: Set[str] = set()
        if isinstance(tags, str):
            tag_set.add(tags.strip().lower())
        elif isinstance(tags, Iterable):
            for tag in tags:
                if tag:
                    tag_set.add(str(tag).strip().lower())
        source = str(row.get("source") or "").strip()
        entry = entries.setdefault(name.lower(), ItemEntry(name=name))
        if source:
            entry.sources.add(source)
        else:
            entry.sources.add("Official PTU Core Rules Supplemental")
        entry.traits.update(tag_set)
        if desc:
            entry.description = entry.description or desc
    return entries


def load_item_catalog() -> Dict[str, ItemEntry]:
    global _CATALOG_CACHE, _CATALOG_CACHE_SIGNATURE
    signature = _catalog_signature()
    if _CATALOG_CACHE is not None and _CATALOG_CACHE_SIGNATURE == signature:
        return _CATALOG_CACHE
    catalog: Dict[str, ItemEntry] = {}
    for payload in (
        _load_csv_items(CSV_ITEM_PATH),
        _load_inventory_items(CSV_INV_PATH),
        _load_inventory_items(CSV_INVENTORY_PATH),
        _load_foundry_items(FOUNDRY_GEAR_DIR),
        _load_weapon_items(WEAPONS_PATH),
        _load_supplemental_items(SUPPLEMENTAL_ITEMS_PATH),
    ):
        for key, entry in payload.items():
            existing = catalog.setdefault(key, entry)
            if existing is entry:
                continue
            existing_priority = _source_priority(existing.sources)
            incoming_priority = _source_priority(entry.sources)
            existing.sources.update(entry.sources)
            existing.traits.update(entry.traits)
            if entry.description:
                existing_text = (existing.description or "").strip()
                incoming = entry.description.strip()
                if not existing_text:
                    existing.description = incoming
                elif not incoming:
                    continue
                elif incoming.lower() in existing_text.lower():
                    continue
                elif incoming_priority > existing_priority:
                    existing.description = incoming
                elif incoming_priority < existing_priority:
                    # Lower priority sources (e.g. Foundry) are fallback only.
                    continue
                else:
                    existing.description = f"{existing_text} {incoming}"
    # Normalize punctuation variants (e.g. "X Accuracy" vs "X-Accuracy") so
    # whichever spelling a dataset uses still resolves to the richest metadata.
    compact_groups: Dict[str, list[ItemEntry]] = {}
    for entry in catalog.values():
        compact = _compact_key(entry.name)
        if not compact:
            continue
        compact_groups.setdefault(compact, []).append(entry)
    for entries in compact_groups.values():
        if len(entries) <= 1:
            continue
        merged_sources: Set[str] = set()
        merged_traits: Set[str] = set()
        best_priority = -1
        best_description = ""
        for entry in entries:
            merged_sources.update(entry.sources)
            merged_traits.update(entry.traits)
            desc = (entry.description or "").strip()
            priority = _source_priority(entry.sources)
            if not desc:
                continue
            if priority > best_priority or (priority == best_priority and len(desc) > len(best_description)):
                best_priority = priority
                best_description = desc
        for entry in entries:
            entry.sources.update(merged_sources)
            entry.traits.update(merged_traits)
            if best_description:
                entry.description = best_description
    _CATALOG_CACHE = catalog
    _CATALOG_CACHE_SIGNATURE = signature
    return catalog


def get_item_entry(name: str) -> Optional[ItemEntry]:
    if not name:
        return None
    catalog = load_item_catalog()
    key = name.strip().lower()
    entry = catalog.get(key)
    if entry is not None:
        return entry
    # Fallback: normalize punctuation/spaces for loose matches.
    compact = _compact_key(key)
    for candidate, entry in catalog.items():
        if _compact_key(candidate) == compact:
            return entry
    return None


__all__ = ["ItemEntry", "get_item_entry", "load_item_catalog"]
