"""Faction reputation rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReputationTrack:
    id: str
    name: str
    score: int = 0
    min_score: int = -10
    max_score: int = 10

    def adjust(self, delta: int) -> str:
        before = self.score
        self.score = max(self.min_score, min(self.max_score, self.score + delta))
        return f"reputation_change:{self.id}:{before}->{self.score}"
