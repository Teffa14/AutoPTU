import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARACTER_CREATION = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "character_creation.json"
MASTER_DATASET = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "master_dataset.json"
FILTERED_FAKEMON = {
    "Automateon",
    "Aviateon",
    "Champeon",
    "Companeon",
    "Corroseon",
    "Draconeon",
    "Dungeon",
    "Illuseon",
    "Obsideon",
    "Scorpeon",
}


def test_filtered_fakemon_not_present_in_character_creation_species():
    payload = json.loads(CHARACTER_CREATION.read_text(encoding="utf-8"))
    species = payload.get("pokemon", {}).get("species", [])
    names = {entry.get("name") for entry in species}
    assert FILTERED_FAKEMON.isdisjoint(names)


def test_filtered_fakemon_not_present_in_master_dataset_species():
    payload = json.loads(MASTER_DATASET.read_text(encoding="utf-8"))
    species = payload.get("pokemon", {}).get("species", [])
    names = {entry.get("name") for entry in species}
    assert FILTERED_FAKEMON.isdisjoint(names)
