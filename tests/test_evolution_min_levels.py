import json
from pathlib import Path


def test_stage_three_item_evolutions_keep_minimum_levels() -> None:
    path = Path(__file__).resolve().parents[1] / "auto_ptu" / "data" / "compiled" / "evolution_min_levels.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["alakazam"] == 35
    assert payload["gengar"] == 35
    assert payload["vileplume"] == 30
    assert payload["politoed"] == 30
    assert payload["porygon-z"] == 25
    assert payload["rhyperior"] == 50
