"""Progress clocks and ticking rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Clock:
    """Progress clock tracked in scenes or quests."""

    id: str
    name: str
    max_segments: int
    filled: int = 0

    def tick(self, amount: int = 1) -> List[str]:
        if amount <= 0:
            return []
        before = self.filled
        self.filled = min(self.max_segments, self.filled + amount)
        events = [f"clock_tick:{self.id}:{before}->{self.filled}"]
        if self.filled >= self.max_segments:
            events.append(f"clock_complete:{self.id}")
        return events

    def reset(self) -> None:
        self.filled = 0
