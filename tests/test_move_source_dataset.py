import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOVE_SOURCE_PATH = ROOT / "auto_ptu" / "api" / "static" / "pokemon_move_sources.json"


def _entries() -> dict:
    payload = json.loads(MOVE_SOURCE_PATH.read_text(encoding="utf-8"))
    return payload.get("entries", {})


def test_weavile_move_sources_are_split_between_tm_and_tutor():
    entry = _entries()["Weavile"]

    assert "Dark Pulse" in entry["tm"]
    assert "Dark Pulse" in entry["tutor"]
    assert "Icy Wind" in entry["tutor"]


def test_natural_tutor_moves_are_preserved_in_dataset():
    entry = _entries()["Weezing Galar"]

    assert "Defog" in entry["natural"]
    assert "Heat Wave" in entry["natural"]
