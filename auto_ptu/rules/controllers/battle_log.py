"""Logging helpers and event normalization boundary.

This is a placeholder boundary for extracting logging from BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from ..battle_state import BattleState


@dataclass
class BattleLog:
    battle: BattleState

    def log_event(self, payload: Dict) -> None:
        self.battle._log_event_raw(payload)

    def extend(self, events: Iterable[Dict]) -> None:
        for payload in events:
            self.battle.log_event(payload)
