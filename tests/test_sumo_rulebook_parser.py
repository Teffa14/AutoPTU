from __future__ import annotations

import json

from auto_ptu.sumo_rulebook_parser import REFERENCES_OUT, parse_sumo_references


def test_parse_sumo_references_examples() -> None:
    payload = parse_sumo_references()
    assert payload["move_count"] >= 40
    assert payload["ability_count"] >= 30
    assert payload["capability_count"] >= 2

    accelerate = payload["abilities"]["Accelerate"]
    assert accelerate["frequency"] == "Scene x2 - Free Action"

    liquidation = payload["moves"]["Liquidation"]
    assert liquidation["type"] == "Water"

    assert "Viral Fusion" in payload["capabilities"]


def test_compiled_sumo_output_exists() -> None:
    payload = json.loads(REFERENCES_OUT.read_text(encoding="utf-8"))
    assert payload["moves"]["Photon Geyser"]["type"] == "Psychic"
    assert payload["abilities"]["Beast Boost"]["frequency"] == "At-Will - Free Action"
