"""
Build evolution minimum-level profiles for the builder.

The builder keeps two useful views of "minimum level obtainable by evolution":

1. Official PTU core profile:
   - friendship methods are treated as level 10
   - item / stone methods are treated as level 15
   - known PTU-specific species corrections can be patched
   - all other methods keep the raw source behavior

2. Foundry compatibility profile:
   - level methods use their listed level
   - item / stone / trade / other methods are treated as obtainable at level 1

Official PTU is the default canonical profile in the builder. The Foundry view
remains available as an explicit compatibility option.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDRY_SPECIES = ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-species"
COMPILED_DIR = ROOT / "auto_ptu" / "data" / "compiled"
OUT_PATH = COMPILED_DIR / "evolution_min_levels.json"

NO_LEVEL_GATE_TYPES = frozenset({"item", "stone", "trade", "other"})
PTU_OVERRIDE_METHOD_LEVELS = {
    "friendship": 10,
    "item": 15,
    "stone": 15,
}
PTU_SPECIES_MIN_LEVEL_OVERRIDES = {
    "togetic": 10,
    "alakazam": 35,
    "gengar": 35,
    "vileplume": 30,
    "politoed": 30,
    "porygon-z": 25,
    "rhyperior": 50,
}


def _normalize(name: str) -> str:
    return (name or "").strip().lower()


def _min_level_for_evolution_methods(methods: list[dict]) -> dict[str, int]:
    """
    Return min-level values for each supported builder profile.
    """
    if not methods:
        return {"foundry_default": 1, "ptu_builder_105": 1}

    foundry_candidates: list[int] = []
    ptu_candidates: list[int] = []

    for method in methods:
        method_type = (method.get("type") or "").strip().lower()
        if method_type in NO_LEVEL_GATE_TYPES:
            foundry_candidates.append(1)
            ptu_candidates.append(PTU_OVERRIDE_METHOD_LEVELS.get(method_type, 1))
            continue
        if method_type in PTU_OVERRIDE_METHOD_LEVELS:
            foundry_candidates.append(1)
            ptu_candidates.append(PTU_OVERRIDE_METHOD_LEVELS[method_type])
            continue
        if method_type == "level" and method.get("level") is not None:
            try:
                level_value = int(method["level"])
            except (TypeError, ValueError):
                continue
            foundry_candidates.append(level_value)
            ptu_candidates.append(level_value)

    if not foundry_candidates:
        foundry_candidates.append(1)
    if not ptu_candidates:
        ptu_candidates.append(1)

    return {
        "foundry_default": min(foundry_candidates),
        "ptu_builder_105": min(ptu_candidates),
    }


def _merge_lineage(existing: list[str] | None, incoming: list[str]) -> list[str]:
    if not existing:
        return list(incoming)
    if len(incoming) < len(existing):
        return list(incoming)
    if len(incoming) > len(existing):
        return list(existing)
    return list(existing)


def _walk_evolutions(
    node: dict,
    min_levels: dict[str, int],
    out: dict[str, dict[str, int]],
    lineage: dict[str, list[str]],
    ancestors: list[str] | None = None,
) -> None:
    """Recursively walk evolution tree; record min level for each species/profile."""
    ancestors = list(ancestors or [])
    name = _normalize(node.get("name") or "")
    if name:
        for profile_id, min_level in min_levels.items():
            profile_map = out.setdefault(profile_id, {})
            profile_map[name] = min(profile_map.get(name, 999), min_level)
        lineage[name] = _merge_lineage(lineage.get(name), ancestors)
    for child in node.get("evolutions") or []:
        edge_levels = _min_level_for_evolution_methods(child.get("methods") or [])
        next_min_levels = {
            profile_id: max(int(min_levels.get(profile_id, 1) or 1), int(edge_levels.get(profile_id, 1) or 1))
            for profile_id in set(min_levels) | set(edge_levels)
        }
        next_ancestors = [name, *ancestors] if name else list(ancestors)
        _walk_evolutions(child, next_min_levels, out, lineage, next_ancestors)


def build_evolution_min_levels(species_dir: Path | None = None) -> dict[str, object]:
    species_dir = species_dir or FOUNDRY_SPECIES
    profiles: dict[str, dict[str, int]] = {
        "foundry_default": {},
        "ptu_builder_105": {},
    }
    lineage: dict[str, list[str]] = {}
    if not species_dir.exists():
        return {"profiles": {}}
    for path in species_dir.glob("*.json"):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        items = raw if isinstance(raw, list) else [raw]
        for data in items:
            if not isinstance(data, dict):
                continue
            system = data.get("system") or {}
            evo = system.get("evolutions")
            if not evo or not isinstance(evo, dict):
                continue
            _walk_evolutions(evo, {"foundry_default": 1, "ptu_builder_105": 1}, profiles, lineage)
    ptu_levels = {
        **profiles["ptu_builder_105"],
        **PTU_SPECIES_MIN_LEVEL_OVERRIDES,
    }
    return {
        "generated_from": "Official PTU core evolution policy + Foundry PTR compatibility trees",
        "lineage": dict(sorted(lineage.items())),
        "profiles": {
            "ptu_builder_105": {
                "label": "Official PTU Core Rules",
                "source": "PTU 1.05 core evolution policy + local official overrides",
                "version": "Default: Friendship=10, Item/Stone=15, known official species corrections",
                "notes": "This is the builder default. Friendship and item/stone methods follow official PTU builder policy, and known PTU-specific source mismatches can be patched per species. Other methods keep the compatible source behavior.",
                "levels": ptu_levels,
            },
            "foundry_default": {
                "label": "Foundry Compatibility Dataset",
                "source": "Foundry PTR core-species",
                "version": "Compatibility: Foundry-derived raw evolution gating",
                "notes": "Optional compatibility profile. Level methods use listed levels. Item, stone, trade, and other methods are treated as obtainable at level 1.",
                "levels": profiles["foundry_default"],
            },
        },
        **ptu_levels,
    }


def main() -> None:
    levels = build_evolution_min_levels()
    COMPILED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(levels, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote evolution min-level profiles to {OUT_PATH}")


if __name__ == "__main__":
    main()
