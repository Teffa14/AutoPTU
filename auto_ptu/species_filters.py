from __future__ import annotations

import re
from typing import Iterable


_INELIGIBLE_SPECIES_KEYS = {
    "egg",
    "megas",
    "automateon",
    "aviateon",
    "champeon",
    "companeon",
    "corroseon",
    "draconeon",
    "dungeon",
    "illuseon",
    "obsideon",
    "scorpeon",
}


def normalize_species_filter_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name or "").strip().lower())


def is_user_selectable_species_name(name: str) -> bool:
    key = normalize_species_filter_key(name)
    return bool(key) and key not in _INELIGIBLE_SPECIES_KEYS


def filter_user_selectable_species(entries: Iterable[dict]) -> list[dict]:
    filtered: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if is_user_selectable_species_name(str(entry.get("name") or "")):
            filtered.append(entry)
    return filtered
