from __future__ import annotations

import json
from pathlib import Path

from auto_ptu.hisui_rulebook_parser import HISUIDEX_OUT, REFERENCES_OUT, parse_hisuidex, parse_hisui_references


def test_parse_hisuidex_species_examples() -> None:
    payload = parse_hisuidex()
    assert payload["species_count"] >= 20

    decidueye = payload["entries"]["Decidueye Hisuian"]
    assert decidueye["types"] == ["Grass", "Fighting"]
    assert decidueye["abilities"]["high"] == ["Thick Fat"]
    assert decidueye["moves"]["level_up"][0]["move"] == "Rock Smash"

    wyrdeer = payload["entries"]["Wyrdeer"]
    assert "Psyshield Bash" in [entry["move"] for entry in wyrdeer["moves"]["level_up"]]


def test_parse_hisui_references_examples() -> None:
    payload = parse_hisui_references()
    assert payload["move_count"] >= 15
    assert payload["ability_count"] >= 2

    ceaseless_edge = payload["moves"]["Ceaseless Edge"]
    assert ceaseless_edge["type"] == "Dark"
    assert ceaseless_edge["frequency"] == "Scene x2"

    victory_dance = payload["moves"]["Victory Dance"]
    assert victory_dance["class"] == "Status"

    psionic_screech = payload["abilities"]["Psionic Screech"]
    assert psionic_screech["frequency"] == "Scene x2 - Free Action"


def test_compiled_hisui_outputs_and_static_builder_payload() -> None:
    hisuidex = json.loads(HISUIDEX_OUT.read_text(encoding="utf-8"))
    references = json.loads(REFERENCES_OUT.read_text(encoding="utf-8"))
    assert hisuidex["entries"]["Kleavor"]["moves"]["tutor"][0] == "Aerial Ace"
    assert references["moves"]["Infernal Parade"]["type"] == "Ghost"

    path = Path(r"C:\Users\tefa1\AutoPTU\auto_ptu\api\static\AutoPTUCharacter\pokedex_learnset.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "wyrdeer" in payload
    assert any(entry["move"] == "Psyshield Bash" for entry in payload["wyrdeer"])


def test_static_builder_learnset_payload_includes_old_species_hisui_additions() -> None:
    path = Path(r"C:\Users\tefa1\AutoPTU\auto_ptu\api\static\AutoPTUCharacter\pokedex_learnset.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "stantler" in payload
    assert any(entry["move"] == "Psyshield Bash" for entry in payload["stantler"])
    assert "scyther" in payload
    assert any(entry["move"] == "Double Hit" for entry in payload["scyther"])
