from auto_ptu.pokedex_loader import load_pokedex_species_abilities


def _lower_set(values):
    return {str(value).strip().lower() for value in values if str(value).strip()}


def test_pokedex_loader_has_core_species_abilities():
    pools = load_pokedex_species_abilities()
    bulbasaur = pools.get("bulbasaur")
    assert bulbasaur is not None
    assert {"confidence", "photosynthesis"} <= _lower_set(bulbasaur["basic"])
    assert "chlorophyll" in _lower_set(bulbasaur["advanced"])
    assert "courage" in _lower_set(bulbasaur["high"])


def test_pokedex_loader_has_galar_and_hisui_species():
    pools = load_pokedex_species_abilities()
    grookey = pools.get("grookey")
    assert grookey is not None
    assert {"overgrow", "frisk"} <= _lower_set(grookey["basic"])
    hisui_decidueye = pools.get("decidueye hisuian")
    assert hisui_decidueye is not None
    assert {"keen eye", "overgrow"} <= _lower_set(hisui_decidueye["basic"])

