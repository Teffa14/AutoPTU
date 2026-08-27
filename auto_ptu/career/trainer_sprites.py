from __future__ import annotations

import re
from typing import Dict, List

from .models import CareerRun


# These entries are the compact regional defaults returned by the Career API.
# The web client can expose the broader Pokemon Showdown archive without making
# every sprite part of this payload. Persisted appearance remains a presentation
# choice and is therefore validated as a safe Showdown sprite slug.
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
    {"id": "calem", "label": "Calem", "region": "kalos"},
    {"id": "serena", "label": "Serena", "region": "kalos"},
    {"id": "elio", "label": "Elio", "region": "alola"},
    {"id": "selene", "label": "Selene", "region": "alola"},
    {"id": "victor", "label": "Victor", "region": "galar"},
    {"id": "gloria", "label": "Gloria", "region": "galar"},
    {"id": "florian-s", "label": "Florian", "region": "paldea"},
    {"id": "juliana-s", "label": "Juliana", "region": "paldea"},
)

DEFAULT_TRAINER_SPRITE = "red"
_SAFE_SPRITE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def trainer_sprite_catalog() -> List[Dict[str, str]]:
    return [dict(entry) for entry in TRAINER_SPRITES]


def normalize_trainer_sprite(value: object) -> str:
    if not isinstance(value, str):
        return DEFAULT_TRAINER_SPRITE
    candidate = value.strip().lower()
    return candidate if _SAFE_SPRITE_ID.fullmatch(candidate) else DEFAULT_TRAINER_SPRITE


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
