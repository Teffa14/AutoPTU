"""Frequency parsing / Foundry activation helpers."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


FREQUENCY_SCOPE_BATTLE = "battle"


class FrequencyScope(str):
    """Scope label for a frequency constraint."""

    BATTLE = FREQUENCY_SCOPE_BATTLE
    ROUND = "round"


@dataclass(frozen=True)
class FrequencyDefinition:
    """Describes a move frequency that carries a hard usage cap."""

    slug: str
    limit: Optional[int]
    scope: Optional[str]
    raw: str


ROOT_DIR = Path(__file__).resolve().parents[2]
_FOUNDATION_MOVE_DIR = (
    ROOT_DIR / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-moves"
)


def parse_move_frequency(raw: Optional[str]) -> Optional[FrequencyDefinition]:
    """Return a constraint for walkable frequency strings or None when unlimited."""
    if not raw:
        return None
    token = re.sub(r"\s+", " ", raw.lower().strip())
    scene_match = re.fullmatch(r"scene(?:\s*x\s*(\d+))?", token)
    if scene_match:
        limit = int(scene_match.group(1) or "1")
        return FrequencyDefinition(
            slug="scene",
            limit=limit,
            scope=FrequencyScope.BATTLE,
            raw=raw,
        )
    daily_match = re.fullmatch(r"daily(?:\s*x\s*(\d+))?", token)
    if daily_match:
        limit = int(daily_match.group(1) or "1")
        return FrequencyDefinition(
            slug="daily",
            limit=limit,
            scope=FrequencyScope.BATTLE,
            raw=raw,
        )
    if token == "eot":
        return FrequencyDefinition(
            slug="eot",
            limit=1,
            scope=FrequencyScope.ROUND,
            raw=raw,
        )
    return None


@lru_cache(maxsize=1)
def _foundry_activation_map() -> Dict[str, str]:
    """Map move names (lowercase) to the activation tag Foundry exposes."""
    if not _FOUNDATION_MOVE_DIR.exists():
        return {}
    activation_map: Dict[str, str] = {}
    for path in _FOUNDATION_MOVE_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            name = entry.get("name")
            if not isinstance(name, str):
                continue
            system = entry.get("system")
            if not isinstance(system, dict):
                continue
            for action in system.get("actions", []):
                if not isinstance(action, dict):
                    continue
                cost = action.get("cost", {})
                activation = cost.get("activation")
                if activation:
                    activation_map.setdefault(name.strip().lower(), activation)
    return activation_map


def activation_for_move(name: Optional[str]) -> Optional[str]:
    """Return the Foundry activation recorded for `name`, if known."""
    if not name:
        return None
    return _foundry_activation_map().get(name.strip().lower())
