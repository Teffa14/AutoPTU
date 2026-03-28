import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER_DATASET = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "master_dataset.json"


def _species_entry(name: str) -> dict:
    payload = json.loads(MASTER_DATASET.read_text(encoding="utf-8"))
    entries = payload.get("pokemon", {}).get("species", [])
    return next(entry for entry in entries if entry.get("name") == name)


def test_species_supplemental_sources_for_swsh_and_hisui_forms():
    weezing_galar = _species_entry("Weezing Galar")
    decidueye_hisuian = _species_entry("Decidueye Hisuian")

    assert any(
        item.get("source") == "swsh_galardex_json"
        for item in weezing_galar.get("supplemental_sources", [])
    )
    assert any(
        item.get("source") == "hisuidex_json"
        for item in decidueye_hisuian.get("supplemental_sources", [])
    )


def test_playtest_item_and_move_provenance_present():
    payload = json.loads(MASTER_DATASET.read_text(encoding="utf-8"))
    inventory = payload.get("items", {}).get("inventory", [])
    moves = payload.get("pokemon", {}).get("moves", [])

    combat_medic = next(entry for entry in inventory if entry.get("name") == "Combat Medic's Primer [9-15 Playtest]")
    defense_curl = next(entry for entry in moves if entry.get("name") == "Defense Curl")

    assert combat_medic.get("source") == "september_2015_playtest_packet"
    assert combat_medic.get("version") == "PTU September 2015 Playtest Packet"
    assert any(
        item.get("source") == "september_2015_playtest_packet"
        for item in defense_curl.get("supplemental_sources", [])
    )


def test_porygon_dream_and_game_of_throhs_trainer_provenance_present():
    payload = json.loads(MASTER_DATASET.read_text(encoding="utf-8"))
    trainer = payload.get("trainer", {})

    engineer = next(entry for entry in trainer.get("features", []) if entry.get("name") == "Engineer")
    berserker = next(entry for entry in trainer.get("features", []) if entry.get("name") == "Berserker")
    glitched_existence = next(entry for entry in trainer.get("edges", []) if entry.get("name") == "Glitched Existence")
    elemental_connection = next(entry for entry in trainer.get("edges", []) if entry.get("name") == "Elemental Connection")
    digital_avatar = next(entry for entry in trainer.get("poke_edges", []) if entry.get("name") == "Digital Avatar")

    assert engineer.get("source") == "porygon_dream_of_mareep"
    assert engineer.get("version") == "Do Porygon Dream of Mareep?"
    assert berserker.get("source") == "game_of_throhs"
    assert berserker.get("version") == "Game of Throhs"
    assert glitched_existence.get("source") == "porygon_dream_of_mareep"
    assert elemental_connection.get("source") == "game_of_throhs"
    assert digital_avatar.get("source") == "porygon_dream_of_mareep"


def test_blessed_and_damned_trainer_provenance_present():
    payload = json.loads(MASTER_DATASET.read_text(encoding="utf-8"))
    trainer = payload.get("trainer", {})

    touched = next(entry for entry in trainer.get("edges", []) if entry.get("name") == "Touched")
    signer = next(entry for entry in trainer.get("features", []) if entry.get("name") == "Signer")
    messiah = next(entry for entry in trainer.get("features", []) if entry.get("name") == "Messiah")
    usurper = next(entry for entry in trainer.get("features", []) if entry.get("name") == "Usurper")

    assert touched.get("source") == "blessed_and_damned"
    assert touched.get("version") == "Blessed and the Damned"
    assert signer.get("source") == "blessed_and_damned"
    assert messiah.get("source") == "blessed_and_damned"
    assert usurper.get("source") == "blessed_and_damned"
