from __future__ import annotations

from typing import Dict, List

from .models import CareerRun


# Curated IDs from the canonical Pokemon Showdown 2D trainer sprite set.
# Keep this list intentionally small so the creation screen stays readable.
TRAINER_SPRITES: tuple[dict[str, str], ...] = (
    {"id": "red", "label": "Red", "region": "kanto"},
    {"id": "green", "label": "Green", "region": "kanto"},
    {"id": "ethan", "label": "Ethan", "region": "johto"},
    {"id": "lyra", "label": "Lyra", "region": "johto"},
    {"id": "brendan", "label": "Brendan", "region": "hoenn"},
    {"id": "may", "label": "May", "region": "hoenn"},
    {"id": "lucas", "label": "Lucas", "region": "sinnoh"},
    {"id": "dawn", "label": "Dawn", "region": "sinnoh"},
    {"id": "hilbert", "label": "Hilbert", "region": "unova"},
    {"id": "hilda", "label": "Hilda", "region": "unova"},
    {"id": "nate", "label": "Nate", "region": "unova"},
    {"id": "rosa", "label": "Rosa", "region": "unova"},
    {"id": "serena", "label": "Serena", "region": "kalos"},
    {"id": "selene", "label": "Selene", "region": "alola"},
    {"id": "victor", "label": "Victor", "region": "galar"},
    {"id": "gloria", "label": "Gloria", "region": "galar"},
)

DEFAULT_TRAINER_SPRITE = "red"
_VALID_IDS = {entry["id"] for entry in TRAINER_SPRITES}


def trainer_sprite_catalog() -> List[Dict[str, str]]:
    return [dict(entry) for entry in TRAINER_SPRITES]


def normalize_trainer_sprite(value: object) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in _VALID_IDS else DEFAULT_TRAINER_SPRITE


def apply_trainer_sprite(run: CareerRun, value: object) -> str:
    sprite = normalize_trainer_sprite(value)
    run.timeline = [
        event for event in run.timeline
        if event.get("type") != "trainer.appearance_selected"
    ]
    run.timeline.append(
        {
            "type": "trainer.appearance_selected",
            "season": run.season_number,
            "age": run.age,
            "trainer_sprite": sprite,
            "label": f"{run.build.name} selected trainer sprite {sprite}.",
        }
    )
    return sprite


def trainer_sprite_for_run(run: CareerRun) -> str:
    for event in reversed(run.timeline):
        if event.get("type") == "trainer.appearance_selected":
            return normalize_trainer_sprite(event.get("trainer_sprite"))
    return DEFAULT_TRAINER_SPRITE
