"""Load PTU species ability pools from Foundry packs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import FOUNDRY_DIR, PROJECT_ROOT
from .learnsets import normalize_species_key


_ABILITY_NAME_CACHE: Optional[Dict[str, str]] = None
_SPECIES_ABILITY_CACHE: Optional[Dict[str, Dict[str, List[str]]]] = None


def _foundry_packs_dir() -> Optional[Path]:
    candidates = [
        FOUNDRY_DIR / "ptr2e-Stable" / "ptr2e-Stable" / "packs",
        PROJECT_ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs",
        PROJECT_ROOT / "foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _title_from_slug(slug: str) -> str:
    text = slug.replace("-", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return " ".join(part.capitalize() for part in text.split())


def load_foundry_ability_names() -> Dict[str, str]:
    global _ABILITY_NAME_CACHE
    if _ABILITY_NAME_CACHE is not None:
        return _ABILITY_NAME_CACHE
    packs_dir = _foundry_packs_dir()
    if packs_dir is None:
        _ABILITY_NAME_CACHE = {}
        return _ABILITY_NAME_CACHE
    abilities_dir = packs_dir / "core-abilities"
    if not abilities_dir.exists():
        _ABILITY_NAME_CACHE = {}
        return _ABILITY_NAME_CACHE
    names: Dict[str, str] = {}
    for path in abilities_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        system = payload.get("system") or {}
        actions = system.get("actions") or []
        slug = None
        if isinstance(system, dict):
            slug = system.get("slug")
        if not slug and actions:
            first = actions[0] if isinstance(actions[0], dict) else {}
            slug = first.get("slug")
        if not slug:
            slug = path.stem
        name = payload.get("name") or None
        if not name and actions:
            first = actions[0] if isinstance(actions[0], dict) else {}
            name = first.get("name")
        if not name:
            name = _title_from_slug(str(slug))
        names[str(slug)] = str(name)
    _ABILITY_NAME_CACHE = names
    return _ABILITY_NAME_CACHE


def load_foundry_species_abilities() -> Dict[str, Dict[str, List[str]]]:
    global _SPECIES_ABILITY_CACHE
    if _SPECIES_ABILITY_CACHE is not None:
        return _SPECIES_ABILITY_CACHE
    packs_dir = _foundry_packs_dir()
    if packs_dir is None:
        _SPECIES_ABILITY_CACHE = {}
        return _SPECIES_ABILITY_CACHE
    species_dir = packs_dir / "core-species"
    if not species_dir.exists():
        _SPECIES_ABILITY_CACHE = {}
        return _SPECIES_ABILITY_CACHE
    ability_names = load_foundry_ability_names()
    pools: Dict[str, Dict[str, List[str]]] = {}
    for path in species_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        name = str(payload.get("name") or "").strip()
        if not name:
            continue
        abilities = (payload.get("system") or {}).get("abilities") or {}
        if not isinstance(abilities, dict):
            continue
        def _collect(key: str) -> List[str]:
            entries = abilities.get(key) or []
            results: List[str] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                slug = str(entry.get("slug") or "").strip()
                if not slug:
                    continue
                results.append(ability_names.get(slug, _title_from_slug(slug)))
            return results

        entry = {
            "starting": _collect("starting"),
            "basic": _collect("basic"),
            "advanced": _collect("advanced"),
            "high": _collect("master"),
        }
        key = normalize_species_key(name)
        if not key:
            continue
        pools[key] = entry
    _SPECIES_ABILITY_CACHE = pools
    return _SPECIES_ABILITY_CACHE


def pick_abilities_for_level(
    pools: Dict[str, List[str]],
    level: int,
    rng,
    existing: Optional[Iterable[str]] = None,
) -> Tuple[List[str], List[str]]:
    existing_list = [name for name in (existing or []) if name]
    existing_lower = {name.lower() for name in existing_list}
    starting = list(dict.fromkeys(pools.get("starting") or []))
    basic = list(dict.fromkeys(pools.get("basic") or []))
    advanced = list(dict.fromkeys(pools.get("advanced") or []))
    high = list(dict.fromkeys(pools.get("high") or []))
    base_pool = starting or basic
    basic_pool = list(dict.fromkeys(starting + basic))
    advanced_pool = list(dict.fromkeys(advanced))
    high_pool = list(dict.fromkeys(high))

    def _pick(pool: List[str]) -> Optional[str]:
        choices = [name for name in pool if name.lower() not in existing_lower]
        if not choices:
            return None
        return rng.choice(choices)

    desired = 1 if level < 20 else 2 if level < 40 else 3
    added: List[str] = []
    current = list(existing_list)

    if len(current) < 1:
        chosen = _pick(base_pool) or _pick(basic_pool) or _pick(advanced_pool) or _pick(high_pool)
        if chosen:
            current.append(chosen)
            existing_lower.add(chosen.lower())
            added.append(chosen)
    if desired >= 2 and len(current) < 2:
        pool = basic_pool + advanced_pool
        chosen = _pick(pool)
        if chosen:
            current.append(chosen)
            existing_lower.add(chosen.lower())
            added.append(chosen)
    if desired >= 3 and len(current) < 3:
        pool = basic_pool + advanced_pool + high_pool
        chosen = _pick(pool)
        if chosen:
            current.append(chosen)
            existing_lower.add(chosen.lower())
            added.append(chosen)

    return current, added


__all__ = ["load_foundry_species_abilities", "pick_abilities_for_level"]
