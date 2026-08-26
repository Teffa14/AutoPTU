import math

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun


def test_save_loader_sanitizes_corrupt_pokemon_progress_before_roster_use() -> None:
    run = CareerEngine().new_run(
        player_id="save-pokemon-progress-recovery",
        name="Milo",
        region="kanto",
        starter="Bulbasaur",
        classes=["Ace Trainer"],
        seed=2441,
    )
    payload = run.to_dict()
    pokemon = payload["pokemon"][0]
    pokemon.update({
        "matches": -4,
        "wins": "7",
        "stat_training": {"atk": "3", "spd": float("nan"), "future_stat": 9},
        "career_health": "broken",
        "training_wear": float("inf"),
    })

    restored = CareerRun.from_dict(payload)
    partner = restored.pokemon[0]

    assert partner.matches == 0
    assert partner.wins == 7
    assert partner.stat_training == {"atk": 3, "spd": 0}
    assert partner.career_health == 100
    assert partner.training_wear == 0
    assert restored.active_roster == [partner.id]


def test_save_loader_rejects_boolean_pokemon_progress_coercion() -> None:
    run = CareerEngine().new_run(
        player_id="save-pokemon-progress-bool-recovery",
        name="Nia",
        region="johto",
        starter="Chikorita",
        classes=["Ace Trainer"],
        seed=2477,
    )
    payload = run.to_dict()
    pokemon = payload["pokemon"][0]
    pokemon.update({
        "matches": True,
        "wins": False,
        "stat_training": {"atk": True},
        "career_health": True,
        "training_wear": True,
    })

    restored = CareerRun.from_dict(payload)
    partner = restored.pokemon[0]

    assert partner.matches == 0
    assert partner.wins == 0
    assert partner.stat_training == {"atk": 0}
    assert partner.career_health == 100
    assert partner.training_wear == 0
