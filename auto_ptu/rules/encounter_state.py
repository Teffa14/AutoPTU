"""Encounter wrapper for in-combat state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .battle_state import BattleState


@dataclass
class EncounterState:
    """Active encounter state plus metadata."""

    battle: BattleState
    encounter_id: Optional[str] = None
