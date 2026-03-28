"""Build compiled data artifacts from PTU CSV/PDF sources."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from ..config import FILES_DIR
from ..csv_repository import PTUCsvRepository


def _default_output_dir() -> Path:
    """Return the default compiled data directory inside the package."""
    return Path(__file__).resolve().parents[1] / "data" / "compiled"


def build_from_csv(files_root: Path | None = None, output_dir: Path | None = None) -> Dict[str, int]:
    """
    Compile CSV data (species, moves, weapons) into JSON payloads.

    Returns a dict with record counts for logging/testing.
    """
    repo = PTUCsvRepository(root=files_root or FILES_DIR)
    dest = output_dir or _default_output_dir()
    dest.mkdir(parents=True, exist_ok=True)

    species = [record.to_dict() for record in repo.iter_species()]
    moves = [record.to_dict() for record in repo.iter_moves()]
    weapons = [record.to_dict() for record in repo.iter_weapons()]

    (dest / "species.json").write_text(json.dumps(species, indent=2, sort_keys=True))
    (dest / "moves.json").write_text(json.dumps(moves, indent=2, sort_keys=True))
    (dest / "weapons.json").write_text(json.dumps(weapons, indent=2, sort_keys=True))

    return {"species": len(species), "moves": len(moves), "weapons": len(weapons)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compiled PTU data files.")
    parser.add_argument(
        "--files-root",
        type=Path,
        default=None,
        help="Override the PTU files directory (defaults to files/).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write compiled JSON (defaults to auto_ptu/data/compiled).",
    )
    args = parser.parse_args()

    counts = build_from_csv(files_root=args.files_root, output_dir=args.output_dir)
    print(
        f"Wrote {counts['species']} species entries, {counts['moves']} move entries, "
        f"and {counts['weapons']} weapon entries."
    )


if __name__ == "__main__":
    main()
