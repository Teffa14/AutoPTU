import csv
import json

from auto_ptu.rules import item_catalog


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def _write_foundry_item(path, name, description):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": name,
        "system": {"description": f"<p>{description}</p>", "traits": []},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_weapons(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


def _set_catalog_paths(monkeypatch, tmp_path):
    csv_item = tmp_path / "item_data.csv"
    csv_inv = tmp_path / "inv_data.csv"
    csv_inventory = tmp_path / "inventory.csv"
    foundry_dir = tmp_path / "core-gear"
    weapons_path = tmp_path / "weapons.json"

    monkeypatch.setattr(item_catalog, "CSV_ITEM_PATH", csv_item)
    monkeypatch.setattr(item_catalog, "CSV_INV_PATH", csv_inv)
    monkeypatch.setattr(item_catalog, "CSV_INVENTORY_PATH", csv_inventory)
    monkeypatch.setattr(item_catalog, "FOUNDRY_GEAR_DIR", foundry_dir)
    monkeypatch.setattr(item_catalog, "WEAPONS_PATH", weapons_path)

    # Minimal CSV headers + one empty row to satisfy positional parsing.
    _write_csv(csv_item, [["Food", "FoodBuff", "Held", "HeldDesc"], ["", "", "", ""]])
    _write_csv(csv_inv, [["Name", "Price", "Desc"], ["", "", ""]])
    _write_csv(csv_inventory, [["Name", "Price", "Desc"], ["", "", ""]])

    item_catalog._CATALOG_CACHE = None
    return csv_item, foundry_dir, weapons_path


def test_ptu_description_is_authoritative_over_foundry(monkeypatch, tmp_path):
    csv_item, foundry_dir, _ = _set_catalog_paths(monkeypatch, tmp_path)
    ptu_desc = "Raise Accuracy Combat Stage by +1."
    foundry_desc = "Foundry flavor text that should not override PTU core."
    _write_csv(
        csv_item,
        [
            ["Food", "FoodBuff", "Held", "HeldDesc"],
            ["", "", "X Accuracy", ptu_desc],
        ],
    )
    _write_foundry_item(foundry_dir / "x-accuracy.json", "X Accuracy", foundry_desc)

    entry = item_catalog.get_item_entry("X Accuracy")
    assert entry is not None
    assert entry.description == ptu_desc


def test_foundry_description_used_when_ptu_missing(monkeypatch, tmp_path):
    _, foundry_dir, _ = _set_catalog_paths(monkeypatch, tmp_path)
    foundry_desc = "Grants a tactical benefit."
    _write_foundry_item(foundry_dir / "test-gear.json", "Test Gear", foundry_desc)

    entry = item_catalog.get_item_entry("Test Gear")
    assert entry is not None
    assert entry.description == foundry_desc


def test_alias_resolution_prefers_ptu_text(monkeypatch, tmp_path):
    csv_item, foundry_dir, _ = _set_catalog_paths(monkeypatch, tmp_path)
    ptu_desc = "Raises Accuracy by one Combat Stage."
    foundry_desc = "Alternative punctuation alias text from Foundry."
    _write_csv(
        csv_item,
        [
            ["Food", "FoodBuff", "Held", "HeldDesc"],
            ["", "", "X Accuracy", ptu_desc],
        ],
    )
    _write_foundry_item(foundry_dir / "x-accuracy.json", "X-Accuracy", foundry_desc)

    entry = item_catalog.get_item_entry("X-Accuracy")
    assert entry is not None
    assert entry.description == ptu_desc


def test_foundry_is_last_resort_when_other_sources_exist(monkeypatch, tmp_path):
    _, foundry_dir, weapons_path = _set_catalog_paths(monkeypatch, tmp_path)
    _write_foundry_item(foundry_dir / "coil-whip.json", "Coil Whip", "Foundry fallback text.")
    _write_weapons(
        weapons_path,
        [{"name": "Coil Whip", "description": "Primary non-Foundry source text.", "tags": []}],
    )

    entry = item_catalog.get_item_entry("Coil Whip")
    assert entry is not None
    assert entry.description == "Primary non-Foundry source text."
