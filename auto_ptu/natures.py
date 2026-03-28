"""Nature table loading and stat application helpers."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Optional

from .config import FILES_DIR

NATURE_FILE_NAME = "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Nature_Type Data.csv"
_NATURE_STAT_NAMES = {"HP", "ATK", "DEF", "SATK", "SDEF", "SPD"}
_STAT_COLUMN_MAP = {
    "HP": "hp_stat",
    "ATK": "atk",
    "DEF": "defense",
    "SATK": "spatk",
    "SDEF": "spdef",
    "SPD": "spd",
}
_NATURE_CACHE: Dict[str, Dict[str, dict]] = {}
_DEFAULT_NATURE_ROWS = [
    ("Cuddly", {"hp_stat": 1, "atk": -2, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "hp_stat", "atk"),
    ("Distracted", {"hp_stat": 1, "atk": 0, "defense": -2, "spatk": 0, "spdef": 0, "spd": 0}, "hp_stat", "defense"),
    ("Proud", {"hp_stat": 1, "atk": 0, "defense": 0, "spatk": -2, "spdef": 0, "spd": 0}, "hp_stat", "spatk"),
    ("Decisive", {"hp_stat": 1, "atk": 0, "defense": 0, "spatk": 0, "spdef": -2, "spd": 0}, "hp_stat", "spdef"),
    ("Patient", {"hp_stat": 1, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": -2}, "hp_stat", "spd"),
    ("Desperate", {"hp_stat": -1, "atk": 2, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "atk", "hp_stat"),
    ("Lonely", {"hp_stat": 0, "atk": 2, "defense": -2, "spatk": 0, "spdef": 0, "spd": 0}, "atk", "defense"),
    ("Adamant", {"hp_stat": 0, "atk": 2, "defense": 0, "spatk": -2, "spdef": 0, "spd": 0}, "atk", "spatk"),
    ("Naughty", {"hp_stat": 0, "atk": 2, "defense": 0, "spatk": 0, "spdef": -2, "spd": 0}, "atk", "spdef"),
    ("Brave", {"hp_stat": 0, "atk": 2, "defense": 0, "spatk": 0, "spdef": 0, "spd": -2}, "atk", "spd"),
    ("Stark", {"hp_stat": -1, "atk": 0, "defense": 2, "spatk": 0, "spdef": 0, "spd": 0}, "defense", "hp_stat"),
    ("Bold", {"hp_stat": 0, "atk": -2, "defense": 2, "spatk": 0, "spdef": 0, "spd": 0}, "defense", "atk"),
    ("Impish", {"hp_stat": 0, "atk": 0, "defense": 2, "spatk": -2, "spdef": 0, "spd": 0}, "defense", "spatk"),
    ("Lax", {"hp_stat": 0, "atk": 0, "defense": 2, "spatk": 0, "spdef": -2, "spd": 0}, "defense", "spdef"),
    ("Relaxed", {"hp_stat": 0, "atk": 0, "defense": 2, "spatk": 0, "spdef": 0, "spd": -2}, "defense", "spd"),
    ("Curious", {"hp_stat": -1, "atk": 0, "defense": 0, "spatk": 2, "spdef": 0, "spd": 0}, "spatk", "hp_stat"),
    ("Modest", {"hp_stat": 0, "atk": -2, "defense": 0, "spatk": 2, "spdef": 0, "spd": 0}, "spatk", "atk"),
    ("Mild", {"hp_stat": 0, "atk": 0, "defense": -2, "spatk": 2, "spdef": 0, "spd": 0}, "spatk", "defense"),
    ("Rash", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 2, "spdef": -2, "spd": 0}, "spatk", "spdef"),
    ("Quiet", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 2, "spdef": 0, "spd": -2}, "spatk", "spd"),
    ("Dreamy", {"hp_stat": -1, "atk": 0, "defense": 0, "spatk": 0, "spdef": 2, "spd": 0}, "spdef", "hp_stat"),
    ("Calm", {"hp_stat": 0, "atk": -2, "defense": 0, "spatk": 0, "spdef": 2, "spd": 0}, "spdef", "atk"),
    ("Gentle", {"hp_stat": 0, "atk": 0, "defense": -2, "spatk": 0, "spdef": 2, "spd": 0}, "spdef", "defense"),
    ("Careful", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": -2, "spdef": 2, "spd": 0}, "spdef", "spatk"),
    ("Sassy", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 2, "spd": -2}, "spdef", "spd"),
    ("Skittish", {"hp_stat": -1, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 2}, "spd", "hp_stat"),
    ("Timid", {"hp_stat": 0, "atk": -2, "defense": 0, "spatk": 0, "spdef": 0, "spd": 2}, "spd", "atk"),
    ("Hasty", {"hp_stat": 0, "atk": 0, "defense": -2, "spatk": 0, "spdef": 0, "spd": 2}, "spd", "defense"),
    ("Jolly", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": -2, "spdef": 0, "spd": 2}, "spd", "spatk"),
    ("Naive", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": -2, "spd": 2}, "spd", "spdef"),
    ("Hardy", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "atk", "atk"),
    ("Docile", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "defense", "defense"),
    ("Bashful", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "spatk", "spatk"),
    ("Quirky", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "spdef", "spdef"),
    ("Serious", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "spd", "spd"),
    ("Composed", {"hp_stat": 0, "atk": 0, "defense": 0, "spatk": 0, "spdef": 0, "spd": 0}, "hp_stat", "hp_stat"),
]


def _normalize_nature_key(name: str) -> str:
    text = (name or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _safe_int(value: object) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def load_nature_table(root: Path | None = None) -> Dict[str, dict]:
    source = Path(root or FILES_DIR)
    cache_key = str(source.resolve()).lower()
    cached = _NATURE_CACHE.get(cache_key)
    if cached is not None:
        return cached
    path = source / NATURE_FILE_NAME
    table: Dict[str, dict] = {}
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = str(row.get("Nature") or "").strip()
                if not name:
                    continue
                raised = str(row.get("Raise") or "").strip().upper()
                lowered = str(row.get("Lower") or "").strip().upper()
                if raised not in _NATURE_STAT_NAMES or lowered not in _NATURE_STAT_NAMES:
                    continue
                values = {
                    "hp_stat": _safe_int(row.get("HP")),
                    "atk": _safe_int(row.get("ATK")),
                    "defense": _safe_int(row.get("DEF")),
                    "spatk": _safe_int(row.get("SATK")),
                    "spdef": _safe_int(row.get("SDEF")),
                    "spd": _safe_int(row.get("SPD")),
                }
                if any(value is None for value in values.values()):
                    continue
                key = _normalize_nature_key(name)
                if not key:
                    continue
                table[key] = {
                    "name": name,
                    "raise": _STAT_COLUMN_MAP[raised],
                    "lower": _STAT_COLUMN_MAP[lowered],
                    "modifiers": values,
                }
    if not table:
        for name, modifiers, raised, lowered in _DEFAULT_NATURE_ROWS:
            key = _normalize_nature_key(name)
            table[key] = {
                "name": name,
                "raise": raised,
                "lower": lowered,
                "modifiers": dict(modifiers),
            }
    _NATURE_CACHE[cache_key] = table
    return table


def nature_profile(name: str, root: Path | None = None) -> Optional[dict]:
    key = _normalize_nature_key(name)
    if not key:
        return None
    table = load_nature_table(root)
    return table.get(key)


def nature_stat_modifiers(name: str, root: Path | None = None) -> Dict[str, int]:
    profile = nature_profile(name, root=root)
    if not profile:
        return {}
    return dict(profile.get("modifiers", {}))


def pick_random_nature_name(rng, root: Path | None = None) -> str:
    table = load_nature_table(root)
    if not table:
        return ""
    names = sorted({str(entry.get("name") or "").strip() for entry in table.values() if entry.get("name")})
    names = [name for name in names if name]
    if not names:
        return ""
    return str(rng.choice(names))


def apply_nature_to_spec(spec, root: Path | None = None) -> bool:
    if spec is None:
        return False
    if bool(getattr(spec, "_nature_applied", False)):
        return False
    nature_name = str(getattr(spec, "nature", "") or "").strip()
    if not nature_name:
        return False
    profile = nature_profile(nature_name, root=root)
    if not profile:
        return False
    modifiers = dict(profile.get("modifiers", {}))
    for stat in ("hp_stat", "atk", "defense", "spatk", "spdef", "spd"):
        amount = int(modifiers.get(stat, 0) or 0)
        current = int(getattr(spec, stat, 0) or 0)
        setattr(spec, stat, max(1, current + amount))
    canonical_name = str(profile.get("name") or nature_name).strip()
    if canonical_name:
        setattr(spec, "nature", canonical_name)
    setattr(spec, "_nature_applied", True)
    return True


__all__ = [
    "NATURE_FILE_NAME",
    "apply_nature_to_spec",
    "load_nature_table",
    "nature_profile",
    "nature_stat_modifiers",
    "pick_random_nature_name",
]
