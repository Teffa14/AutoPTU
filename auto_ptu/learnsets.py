"""Helpers for loading CSV-based learnsets for Fancy PTU CSV battles."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from .config import DATA_DIR, FILES_DIR

LEARNSET_FILE_NAME = "pokedex_learnset.csv"
SWSH_GALARDEX_FILE_NAME = "swsh_galardex.json"
SWSH_LEVELUP_SUPPLEMENT_FILE_NAME = "swsh_levelup_learnsets.json"
HISUIDEX_FILE_NAME = "hisuidex.json"
HISUI_LEVELUP_SUPPLEMENT_FILE_NAME = "hisui_levelup_learnsets.json"
EVOLUTION_MIN_LEVELS_FILE_NAME = "evolution_min_levels.json"


def normalize_species_key(name: str) -> str:
    text = (name or "").strip().lower()
    if not text:
        return ""
    text = text.replace("\u2640", "f").replace("\u2642", "m")
    text = text.replace("♀", "f").replace("♂", "m")
    text = text.replace("(", " ").replace(")", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load_lineage_map() -> Dict[str, List[str]]:
    path = DATA_DIR / "compiled" / EVOLUTION_MIN_LEVELS_FILE_NAME
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    raw_lineage = payload.get("lineage", {}) if isinstance(payload, dict) else {}
    if not isinstance(raw_lineage, dict):
        return {}
    lineage: Dict[str, List[str]] = {}
    for raw_key, raw_value in raw_lineage.items():
        key = normalize_species_key(str(raw_key))
        if not key or not isinstance(raw_value, list):
            continue
        lineage[key] = [normalize_species_key(str(entry)) for entry in raw_value if normalize_species_key(str(entry))]
    return lineage


def _merge_inherited_learnsets(learnsets: Dict[str, List[Tuple[str, int]]]) -> Dict[str, List[Tuple[str, int]]]:
    lineage = _load_lineage_map()
    if not lineage:
        return learnsets

    cache: Dict[str, List[Tuple[str, int]]] = {}

    def collect(species_key: str, visiting: set[str] | None = None) -> List[Tuple[str, int]]:
        if species_key in cache:
            return cache[species_key]
        visiting = set(visiting or ())
        if species_key in visiting:
            return list(learnsets.get(species_key, []))
        visiting.add(species_key)
        own_entries = list(learnsets.get(species_key, []))
        merged = list(own_entries)
        seen = {(name.casefold(), level) for name, level in merged}
        for ancestor in lineage.get(species_key, []):
            if not ancestor or ancestor == species_key:
                continue
            for move_name, level in collect(ancestor, visiting):
                if int(level or 0) <= 0:
                    continue
                dedupe = (str(move_name).casefold(), int(level))
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                merged.append((move_name, int(level)))
        merged.sort(key=lambda pair: (pair[1], pair[0].casefold()))
        cache[species_key] = merged
        return merged

    for species_key in list(learnsets.keys()):
        learnsets[species_key] = collect(species_key)
    return learnsets


def load_learnsets(root: Path | None = None) -> Dict[str, List[Tuple[str, int]]]:
    """Return a species -> [(move_name, level), ...] mapping using the learnset CSV."""
    source = Path(root or FILES_DIR)
    path = source / LEARNSET_FILE_NAME
    if not path.exists():
        return {}
    learnsets: Dict[str, List[Tuple[str, int]]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            species = (row.get("species") or row.get("name") or "").strip()
            move = (row.get("move") or row.get("move_name") or "").strip()
            level_text = (row.get("level") or row.get("learned_at") or "").strip()
            if not species or not move:
                continue
            try:
                level = int(level_text)
            except ValueError:
                level = 0
            key = normalize_species_key(species)
            if not key:
                continue
            learnsets.setdefault(key, []).append((move, max(level, 0)))
    swsh_path = DATA_DIR / "compiled" / SWSH_GALARDEX_FILE_NAME
    if swsh_path.exists():
        try:
            payload = json.loads(swsh_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_entry in entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                species_key = normalize_species_key(str(raw_species))
                if not species_key:
                    continue
                moves_root = raw_entry.get("moves", {})
                level_up = moves_root.get("level_up", []) if isinstance(moves_root, dict) else []
                if not isinstance(level_up, list):
                    continue
                bucket = learnsets.setdefault(species_key, [])
                seen = {(name.casefold(), level) for name, level in bucket}
                for move_entry in level_up:
                    if not isinstance(move_entry, dict):
                        continue
                    move_name = str(move_entry.get("move") or "").strip()
                    if not move_name:
                        continue
                    try:
                        level = int(move_entry.get("level") or 0)
                    except (TypeError, ValueError):
                        level = 0
                    dedupe = (move_name.casefold(), max(level, 0))
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    bucket.append((move_name, max(level, 0)))
    swsh_supplement_path = DATA_DIR / "compiled" / SWSH_LEVELUP_SUPPLEMENT_FILE_NAME
    if swsh_supplement_path.exists():
        try:
            payload = json.loads(swsh_supplement_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_moves in entries.items():
                if not isinstance(raw_moves, list):
                    continue
                species_key = normalize_species_key(str(raw_species))
                if not species_key:
                    continue
                bucket = learnsets.setdefault(species_key, [])
                seen = {(name.casefold(), level) for name, level in bucket}
                for move_entry in raw_moves:
                    if not isinstance(move_entry, dict):
                        continue
                    move_name = str(move_entry.get("move") or "").strip()
                    if not move_name:
                        continue
                    try:
                        level = int(move_entry.get("level") or 0)
                    except (TypeError, ValueError):
                        level = 0
                    dedupe = (move_name.casefold(), max(level, 0))
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    bucket.append((move_name, max(level, 0)))
    hisui_path = DATA_DIR / "compiled" / HISUIDEX_FILE_NAME
    if hisui_path.exists():
        try:
            payload = json.loads(hisui_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_entry in entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                species_key = normalize_species_key(str(raw_species))
                if not species_key:
                    continue
                moves_root = raw_entry.get("moves", {})
                level_up = moves_root.get("level_up", []) if isinstance(moves_root, dict) else []
                if not isinstance(level_up, list):
                    continue
                bucket = learnsets.setdefault(species_key, [])
                seen = {(name.casefold(), level) for name, level in bucket}
                for move_entry in level_up:
                    if not isinstance(move_entry, dict):
                        continue
                    move_name = str(move_entry.get("move") or "").strip()
                    if not move_name:
                        continue
                    try:
                        level = int(move_entry.get("level") or 0)
                    except (TypeError, ValueError):
                        level = 0
                    dedupe = (move_name.casefold(), max(level, 0))
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    bucket.append((move_name, max(level, 0)))
    hisui_supplement_path = DATA_DIR / "compiled" / HISUI_LEVELUP_SUPPLEMENT_FILE_NAME
    if hisui_supplement_path.exists():
        try:
            payload = json.loads(hisui_supplement_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_moves in entries.items():
                if not isinstance(raw_moves, list):
                    continue
                species_key = normalize_species_key(str(raw_species))
                if not species_key:
                    continue
                bucket = learnsets.setdefault(species_key, [])
                seen = {(name.casefold(), level) for name, level in bucket}
                for move_entry in raw_moves:
                    if not isinstance(move_entry, dict):
                        continue
                    move_name = str(move_entry.get("move") or "").strip()
                    if not move_name:
                        continue
                    try:
                        level = int(move_entry.get("level") or 0)
                    except (TypeError, ValueError):
                        level = 0
                    dedupe = (move_name.casefold(), max(level, 0))
                    if dedupe in seen:
                        continue
                    seen.add(dedupe)
                    bucket.append((move_name, max(level, 0)))
    for entries in learnsets.values():
        entries.sort(key=lambda pair: pair[1])
    return _merge_inherited_learnsets(learnsets)


__all__ = ["load_learnsets", "normalize_species_key", "LEARNSET_FILE_NAME"]
