from auto_ptu.csv_repository import PTUCsvRepository
import random


def _is_damaging(move) -> bool:
    return (move.category or "").strip().lower() != "status" and int(move.db or 0) > 0


def _is_repeatable(move) -> bool:
    freq = (move.freq or "").strip().lower()
    return "at-will" in freq or "eot" in freq or freq in {"standard", "free", "shift", "action"}


def test_csv_repository_loads_abomasnow():
    repo = PTUCsvRepository()
    assert repo.available()
    abomasnow = repo.get_species("Abomasnow")
    assert abomasnow is not None
    assert abomasnow.base_stats["hp"] == 9
    spec = repo.build_pokemon_spec("Abomasnow", level=30)
    assert spec.level == 30
    assert spec.species == "Abomasnow"
    assert spec.moves, "auto-selected type-matching moves should not be empty"


def test_csv_repository_assigns_abilities_for_variant_forms():
    repo = PTUCsvRepository()
    zygarde = repo.build_pokemon_spec("Zygarde 10%", level=30, assign_abilities=True)
    assert zygarde.abilities, "Variant forms should resolve to ability pools."
    gourgeist = repo.build_pokemon_spec("Gourgeist Su", level=30, assign_abilities=True)
    assert gourgeist.abilities, "Short-form CSV variant names should resolve abilities."
    lycanroc = repo.build_pokemon_spec("Lycanroc (Night)", level=30, assign_abilities=True)
    assert lycanroc.abilities, "Day/night aliases should resolve to Foundry midnight/midday pools."


def test_csv_repository_assigns_custom_eon_fallback_abilities():
    repo = PTUCsvRepository()
    obsideon = repo.build_pokemon_spec("Obsideon", level=30, assign_abilities=True)
    assert obsideon.abilities, "Custom Eeveelutions should inherit fallback ability pools."
    gumshoos = repo.build_pokemon_spec("Gumshoos", level=30, assign_abilities=True)
    assert gumshoos.abilities, "Species outside PDF dexes should still resolve with Foundry fallback pools."


def test_csv_repository_assigns_abilities_for_common_csv_aliases():
    repo = PTUCsvRepository()
    cases = [
        "Wormadam P",
        "Wormadam-Sand",
        "Darmanitan (Zen) Galarian",
        "Deoxys (Attack)",
        "Calyrex (Shadow)",
        "Alolan Raticate",
        "Urshifu (Rapid)",
        "Nidoran (Female)",
        "Basculegion (M)",
        "Indeedee (F)",
        "Enamorus (T)",
        "Landorus (T)",
        "Thundurus (T)",
        "Tornadus (T)",
    ]
    for species in cases:
        spec = repo.build_pokemon_spec(species, level=55, assign_abilities=True)
        assert spec.abilities, f"{species} should resolve to at least one ability."


def test_csv_repository_fallback_moveset_is_repeatable_and_non_suicidal():
    repo = PTUCsvRepository()
    spec = repo.build_pokemon_spec("Passimian", level=60)
    damaging = [move for move in spec.moves if _is_damaging(move)]
    repeatable = [move for move in damaging if _is_repeatable(move)]
    status_count = sum(1 for move in spec.moves if not _is_damaging(move))
    move_names = {(move.name or "").strip().lower() for move in spec.moves}
    assert len(spec.moves) == 4
    assert len(damaging) >= 2
    assert len(repeatable) >= 1
    assert status_count <= 2
    assert "explosion" not in move_names
    assert "self-destruct" not in move_names
    assert "struggle" not in move_names


def test_csv_repository_variant_forms_get_stab_repeatable_damage():
    repo = PTUCsvRepository()
    spec = repo.build_pokemon_spec("Basculegion (Male)", level=60)
    damaging = [move for move in spec.moves if _is_damaging(move)]
    repeatable = [move for move in damaging if _is_repeatable(move)]
    water_hits = [move for move in damaging if (move.type or "").strip().lower() == "water"]
    assert damaging, "Variant forms should still receive usable damaging moves."
    assert repeatable, "Variant forms should avoid burst-only loadouts that force Struggle loops."
    assert water_hits, "Basculegion forms should keep STAB pressure in fallback learnset selection."


def test_csv_repository_collapses_hidden_power_family_in_learnset_pool():
    repo = PTUCsvRepository(rng=random.Random(1))
    records = repo._records_from_learnset(
        [
            ("Hidden Power", 0),
            ("Hidden Power Fire", 0),
            ("Hidden Power Ice", 0),
            ("Thunderbolt", 0),
        ]
    )
    hidden_power = [record for record in records if "hidden power" in (record.name or "").strip().lower()]
    assert len(hidden_power) == 1


def test_csv_repository_resolves_hidden_power_family_to_single_typed_variant():
    repo = PTUCsvRepository(rng=random.Random(1))
    base = repo.get_move("Hidden Power")
    assert base is not None
    resolved = repo._resolve_variant_record(base)
    assert resolved.name != "Hidden Power"
    assert resolved.name.startswith("Hidden Power ")


def test_csv_repository_loads_swsh_species_and_moves_into_main_repository():
    repo = PTUCsvRepository()
    grookey = repo.get_species("Grookey")
    assert grookey is not None
    assert grookey.types[0] == "Grass"
    assert grookey.base_stats["attack"] == 7

    aura_wheel = repo.get_move("Aura Wheel")
    assert aura_wheel is not None
    assert aura_wheel.type == "Electric"
    assert aura_wheel.category == "Physical"
    assert aura_wheel.db == 11


def test_csv_repository_swsh_species_have_learnsets_and_ability_pools():
    repo = PTUCsvRepository()
    spec = repo.build_pokemon_spec("Indeedee Male", level=20, assign_abilities=True)
    move_names = {(move.name or "").strip().lower() for move in spec.moves}
    ability_names = {
        str((ability or {}).get("name") or "").strip().lower()
        for ability in spec.abilities
        if isinstance(ability, dict)
    }
    assert "psybeam" in move_names
    assert ability_names
    assert {"inner focus", "synchronize"} & ability_names


def test_csv_repository_old_species_gain_swsh_level_up_additions():
    repo = PTUCsvRepository()
    repo._ensure_learnsets()
    entries = repo._learnsets.get("bulbasaur", [])
    assert ("Worry Seed", 30) in entries or ("Worry Seed", 31) in entries


def test_csv_repository_loads_hisui_species_and_moves_into_main_repository():
    repo = PTUCsvRepository()
    wyrdeer = repo.get_species("Wyrdeer")
    assert wyrdeer is not None
    assert wyrdeer.types == ["Normal", "Psychic"]

    infernal_parade = repo.get_move("Infernal Parade")
    assert infernal_parade is not None
    assert infernal_parade.type == "Ghost"
    assert infernal_parade.category == "Special"


def test_csv_repository_hisui_species_have_learnsets_and_ability_pools():
    repo = PTUCsvRepository()
    spec = repo.build_pokemon_spec("Decidueye Hisuian", level=35, assign_abilities=True)
    move_names = {(move.name or "").strip().lower() for move in spec.moves}
    ability_names = {
        str((ability or {}).get("name") or "").strip().lower()
        for ability in spec.abilities
        if isinstance(ability, dict)
    }
    assert {"rock smash", "aura sphere"} & move_names
    assert {"keen eye", "overgrow", "long reach", "technician", "thick fat"} & ability_names
