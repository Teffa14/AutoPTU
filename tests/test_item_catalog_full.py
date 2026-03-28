from __future__ import annotations

from auto_ptu.rules import item_catalog
from auto_ptu.tools import generate_item_log


def _load_all_source_items() -> set[str]:
    food_items, held_items = generate_item_log._load_csv_items(generate_item_log.CSV_ITEM_PATH)
    inventory_items = generate_item_log._load_inventory_items(generate_item_log.CSV_INV_PATH)
    inventory_items |= generate_item_log._load_inventory_items(generate_item_log.CSV_INVENTORY_PATH)
    foundry_items = generate_item_log._load_foundry_items(generate_item_log.FOUNDRY_GEAR_DIR)
    weapon_items = generate_item_log._load_weapon_items(generate_item_log.WEAPONS_PATH)
    return set().union(food_items, held_items, inventory_items, foundry_items, weapon_items)


def test_item_catalog_resolves_all_sources() -> None:
    all_items = _load_all_source_items()
    catalog = item_catalog.load_item_catalog()
    missing: list[str] = []
    no_sources: list[str] = []
    for name in sorted(all_items):
        entry = catalog.get(name.lower())
        if entry is None:
            entry = item_catalog.get_item_entry(name)
        if entry is None:
            missing.append(name)
            continue
        if not entry.sources:
            no_sources.append(name)

    print(f"Item catalog sources: {len(all_items)}")
    print(f"Catalog entries: {len(catalog)}")
    print(f"Missing entries: {len(missing)}")
    print(f"Entries without sources: {len(no_sources)}")

    assert not missing, f"Missing item entries: {missing[:10]}"
    assert not no_sources, f"Items missing source tags: {no_sources[:10]}"
