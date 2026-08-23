from __future__ import annotations

import random

import pytest

from auto_ptu.career.catalogs import REGIONS, all_region_encounters
from auto_ptu.career.ptu_builds import build_career_pokemon_spec
from auto_ptu.csv_repository import PTUCsvRepository


@pytest.mark.parametrize("region", sorted(REGIONS))
def test_every_career_encounter_species_builds_a_battle_spec(region: str) -> None:
    """Every species exposed by Career scouting must be battle-buildable.

    This guards the browser career against data-boundary crashes where a valid
    encounter can be captured but later fails while preparing a scheduled battle.
    """
    repo = PTUCsvRepository(rng=random.Random(8128))
    failures: list[str] = []

    for species in all_region_encounters(region):
        try:
            spec = build_career_pokemon_spec(repo, species, 30)
        except Exception as exc:  # collect the whole broken surface in one run
            failures.append(f"{species}: {type(exc).__name__}: {exc}")
            continue
        if not spec.moves:
            failures.append(f"{species}: built without a legal battle move")

    assert not failures, f"{region} encounter build failures:\n" + "\n".join(failures)
