from __future__ import annotations

import json
from pathlib import Path

from auto_ptu.swsh_rulebook_parser import GALARDEX_OUT, REFERENCES_OUT, parse_galardex, parse_swsh_references


def test_parse_galardex_core_species_examples() -> None:
    payload = parse_galardex()
    assert payload["species_count"] >= 110

    grookey = payload["entries"]["Grookey"]
    assert grookey["types"] == ["Grass"]
    assert grookey["abilities"]["basic"] == ["Overgrow", "Frisk"]
    assert grookey["moves"]["egg"][:3] == ["Fake Out", "Growth", "Hammer Arm"]
    assert grookey["moves"]["tutor"][:3] == ["Drain Punch", "Endeavor", "Endure"]

    weezing_galar = payload["entries"]["Weezing Galar"]
    assert weezing_galar["types"] == ["Poison", "Fairy"]
    assert weezing_galar["moves"]["level_up"][0]["requirement"] == "Evo"
    assert weezing_galar["moves"]["level_up"][0]["move"] == "Double Hit"

    indeedee_male = payload["entries"]["Indeedee Male"]
    indeedee_female = payload["entries"]["Indeedee Female"]
    assert "Encore" in [entry["move"] for entry in indeedee_male["moves"]["level_up"]]
    assert "Baton Pass" in [entry["move"] for entry in indeedee_female["moves"]["level_up"]]


def test_parse_swsh_references_examples() -> None:
    payload = parse_swsh_references()
    assert payload["move_count"] >= 60
    assert payload["ability_count"] >= 30
    assert payload["capability_count"] >= 2

    aura_wheel = payload["moves"]["Aura Wheel"]
    assert aura_wheel["type"] == "Electric"
    assert aura_wheel["frequency"] == "Scene x2"
    assert aura_wheel["ac"] == "2"
    assert aura_wheel["damage_base"].startswith("11:")

    body_press = payload["moves"]["Body Press"]
    assert body_press["effect"].startswith("The user’s Defense Stat is added")

    ball_fetch = payload["abilities"]["Ball Fetch"]
    assert ball_fetch["frequency"] == "Scene - Free Action, Reaction"
    assert ball_fetch["trigger"] == "A Pokémon is Released onto the battlefield"

    assert "Mounted" in payload["capabilities"]["As One"]["text"]


def test_compiled_swsh_outputs_exist_and_match_expected_samples() -> None:
    galardex = json.loads(GALARDEX_OUT.read_text(encoding="utf-8"))
    references = json.loads(REFERENCES_OUT.read_text(encoding="utf-8"))

    assert galardex["entries"]["Obstagoon"]["moves"]["tutor"][0] == "Baby-Doll Eyes (N)"
    assert galardex["entries"]["Eternatus"]["moves"]["tutor"] == ["Draco Meteor", "Dragon Pulse", "Endure", "Snore"]

    assert references["moves"]["Steel Beam"]["range"] == "Cone 3, Smite"
    assert references["abilities"]["Mirror Armor"]["frequency"] == "At-Will - Free Action, Reaction"


def test_static_builder_learnset_payload_includes_swsh_species() -> None:
    path = Path(r"C:\Users\tefa1\AutoPTU\auto_ptu\api\static\AutoPTUCharacter\pokedex_learnset.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "grookey" in payload
    assert any(entry["move"] == "Scratch" and int(entry["level"]) == 1 for entry in payload["grookey"])
    assert "bulbasaur" in payload
    assert any(entry["move"] == "Worry Seed" and int(entry["level"]) in {30, 31} for entry in payload["bulbasaur"])
