from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from ..config import DATA_DIR
from ..learnsets import normalize_species_key


_EVOLUTION_PATH = DATA_DIR / "compiled" / "evolution_min_levels.json"
_SPECIES_PATH = DATA_DIR / "compiled" / "species.json"
_REGIONAL_FORMS = {
    "alola": ("alolan",),
    "galar": ("galar", "galarian"),
    "hisui": ("hisui", "hisuian"),
    "paldea": ("paldea", "paldean"),
}


@lru_cache(maxsize=1)
def _catalog() -> tuple[Dict[str, List[Tuple[str, int]]], Dict[str, str]]:
    """Return canonical immediate evolution edges from the compiled PTU data."""
    payload = json.loads(_EVOLUTION_PATH.read_text(encoding="utf-8"))
    profile = payload.get("profiles", {}).get("ptu_builder_105", {})
    levels = profile.get("levels", {}) if isinstance(profile, dict) else {}
    if not isinstance(levels, dict) or not levels:
        levels = {key: value for key, value in payload.items() if isinstance(value, int)}
    lineage = payload.get("lineage", {}) if isinstance(payload, dict) else {}

    canonical: Dict[str, str] = {}
    try:
        species_rows = json.loads(_SPECIES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        species_rows = []
    for row in species_rows if isinstance(species_rows, list) else []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        key = normalize_species_key(name)
        if name and key and key not in canonical:
            canonical[key] = name

    children: Dict[str, List[Tuple[str, int]]] = {}
    for raw_child, raw_ancestors in lineage.items() if isinstance(lineage, dict) else []:
        child_key = normalize_species_key(str(raw_child))
        if not child_key or not isinstance(raw_ancestors, list) or not raw_ancestors:
            continue
        parent_key = normalize_species_key(str(raw_ancestors[0]))
        if not parent_key or parent_key == child_key:
            continue
        try:
            threshold = max(1, int(levels.get(raw_child, levels.get(child_key, 1))))
        except (TypeError, ValueError):
            threshold = 1
        child_name = canonical.get(child_key, str(raw_child).replace("-", " ").title())
        children.setdefault(parent_key, []).append((child_name, threshold))
    for entries in children.values():
        entries.sort(key=lambda item: (item[1], normalize_species_key(item[0])))
    return children, canonical


def next_evolution(
    species: str,
    *,
    seed: int,
    region: str = "",
    level: int | None = None,
) -> tuple[str, int] | None:
    """Choose one deterministic immediate PTU evolution, optionally gated by level."""
    children, _ = _catalog()
    candidates = list(children.get(normalize_species_key(species), ()))
    if not candidates:
        return None

    regional_tokens = _REGIONAL_FORMS.get(str(region).strip().lower(), ())
    if regional_tokens:
        regional = [entry for entry in candidates if any(token in normalize_species_key(entry[0]) for token in regional_tokens)]
        if regional:
            candidates = regional
        else:
            standard = [entry for entry in candidates if not any(
                token in normalize_species_key(entry[0])
                for tokens in _REGIONAL_FORMS.values()
                for token in tokens
            )]
            if standard:
                candidates = standard
    else:
        standard = [entry for entry in candidates if not any(
            token in normalize_species_key(entry[0])
            for tokens in _REGIONAL_FORMS.values()
            for token in tokens
        )]
        if standard:
            candidates = standard

    if level is not None:
        candidates = [entry for entry in candidates if int(level) >= entry[1]]
    if not candidates:
        return None

    digest = hashlib.sha256(f"{int(seed)}:{normalize_species_key(species)}:evolution".encode("utf-8")).digest()
    return candidates[int.from_bytes(digest[:4], "big") % len(candidates)]


def evolve_species_for_level(species: str, level: int, *, seed: int, region: str = "") -> str:
    """Advance a generated rival through every evolution legal at its PTU level."""
    current = str(species)
    visited = {normalize_species_key(current)}
    while True:
        target = next_evolution(current, seed=seed, region=region, level=level)
        if target is None:
            return current
        evolved, _ = target
        key = normalize_species_key(evolved)
        if not key or key in visited:
            return current
        visited.add(key)
        current = evolved
