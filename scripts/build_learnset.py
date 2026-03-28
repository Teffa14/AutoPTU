"""Generate ``files/pokedex_learnset.csv`` from the PTU Database YAML."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import yaml


DATABASE_PATH = Path("PTUDatabase-main/Data/ptu.1.05.yaml")
OUTPUT_PATH = Path("files/pokedex_learnset.csv")


def _canonical_species_name(base: str, form_name: str | None) -> str:
    if not form_name:
        return base
    normalized = form_name.strip()
    if not normalized:
        return base
    lower = normalized.lower()
    if lower in {"normal", "base", base.lower()}:
        return base
    return f"{base} {normalized}"


def _required_level(move_entry: dict) -> int:
    requirement = str(move_entry.get("RequirementType") or "").strip().lower()
    if requirement == "level":
        level = move_entry.get("RequiredLevel")
        if isinstance(level, int):
            return level
        try:
            return int(level)
        except (TypeError, ValueError):
            return 0
    return 0


def build_learnset(database_path: Path) -> Dict[Tuple[str, str], int]:
    data = yaml.safe_load(database_path.read_text(encoding="utf-8"))
    learnset: Dict[Tuple[str, str], int] = {}
    for species in data.get("Species", []):
        base_name = str(species.get("Name") or "").strip()
        if not base_name:
            continue
        for form in species.get("Forms", []):
            form_name = form.get("Name")
            species_name = _canonical_species_name(base_name, form_name)
            for move_entry in form.get("Moves", []):
                move = move_entry.get("Move")
                if not isinstance(move, dict):
                    continue
                move_name = str(move.get("Name") or "").strip()
                if not move_name:
                    continue
                level = _required_level(move_entry)
                key = (species_name, move_name)
                existing = learnset.get(key)
                if existing is None or level < existing:
                    learnset[key] = max(level, 0)
    return learnset


def write_csv(learnset: Dict[Tuple[str, str], int], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["species", "move", "level"])
        for (species_name, move_name), level in sorted(
            learnset.items(), key=lambda item: (item[0][0].casefold(), item[0][1].casefold(), item[1])
        ):
            writer.writerow([species_name, move_name, level])


def main() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit(f"PTU database missing at {DATABASE_PATH}")
    learnset = build_learnset(DATABASE_PATH)
    write_csv(learnset, OUTPUT_PATH)
    print(f"Generated {OUTPUT_PATH} with {len(learnset)} entries.")


if __name__ == "__main__":
    main()
