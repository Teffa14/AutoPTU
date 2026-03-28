from __future__ import annotations

import json
from pathlib import Path

from auto_ptu.tools.build_data import build_from_csv


def test_build_from_csv(tmp_path: Path) -> None:
    counts = build_from_csv(output_dir=tmp_path)
    assert counts["species"] > 0
    assert counts["moves"] > 0
    assert counts["weapons"] >= 0

    species_path = tmp_path / "species.json"
    moves_path = tmp_path / "moves.json"
    weapons_path = tmp_path / "weapons.json"
    assert species_path.exists()
    assert moves_path.exists()
    assert weapons_path.exists()

    species_entries = json.loads(species_path.read_text())
    moves_entries = json.loads(moves_path.read_text())
    weapons_entries = json.loads(weapons_path.read_text())

    assert isinstance(species_entries, list)
    assert isinstance(moves_entries, list)
    assert isinstance(weapons_entries, list)
    assert species_entries[0]["name"]
    assert moves_entries[0]["name"]
