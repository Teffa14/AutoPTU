import random

from auto_ptu.csv_repository import PTUCsvRepository
from auto_ptu.data_models import PokemonSpec
from auto_ptu.natures import nature_profile
from auto_ptu.rules.battle_state import PokemonState


def test_nature_table_loads_adamant_profile():
    profile = nature_profile("Adamant")
    assert profile is not None
    assert profile["name"] == "Adamant"
    assert profile["raise"] == "atk"
    assert profile["lower"] == "spatk"
    assert profile["modifiers"]["atk"] == 2
    assert profile["modifiers"]["spatk"] == -2


def test_pokemon_state_applies_nature_modifiers_to_runtime_stats():
    spec = PokemonSpec(
        species="Testmon",
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        nature="Brave",
    )
    state = PokemonState(spec=spec, controller_id="a")
    assert state.spec.atk == 12
    assert state.spec.spd == 8
    assert state.spec.hp_stat == 10
    assert state.hp == state.max_hp()


def test_pokemon_state_applies_hp_nature_to_max_hp():
    spec = PokemonSpec(
        species="Tankmon",
        level=20,
        types=["Normal"],
        hp_stat=10,
        atk=10,
        defense=10,
        spatk=10,
        spdef=10,
        spd=10,
        nature="Cuddly",
    )
    state = PokemonState(spec=spec, controller_id="a")
    # Cuddly grants +1 HP stat, so Max HP uses 11 instead of 10.
    assert state.spec.hp_stat == 11
    assert state.max_hp() == 20 + 3 * 11 + 10


def test_csv_repository_can_assign_random_nature():
    repo = PTUCsvRepository(rng=random.Random(7))
    spec = repo.build_pokemon_spec("Pikachu", level=20, assign_nature=True)
    assert spec.nature
    assert nature_profile(spec.nature, root=repo.root) is not None


def test_pokemon_spec_roundtrip_keeps_nature():
    spec = PokemonSpec.from_dict(
        {
            "species": "Ralts",
            "level": 10,
            "types": ["Psychic", "Fairy"],
            "hp_stat": 5,
            "atk": 4,
            "defense": 4,
            "spatk": 6,
            "spdef": 6,
            "spd": 5,
            "nature": "Calm",
            "moves": [],
        }
    )
    payload = spec.to_engine_dict()
    assert payload["nature"] == "Calm"
