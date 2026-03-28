"""Quest rules and objective state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QuestObjective:
    id: str
    description: str
    completed: bool = False


@dataclass
class QuestState:
    id: str
    name: str
    status: str = "active"
    objectives: List[QuestObjective] = field(default_factory=list)
    reward_text: str = ""
    notes: str = ""

    def complete_objective(self, objective_id: str) -> Optional[str]:
        for obj in self.objectives:
            if obj.id == objective_id:
                obj.completed = True
                return f"quest_objective_complete:{self.id}:{objective_id}"
        return None

    def set_status(self, status: str) -> str:
        self.status = status
        return f"quest_status:{self.id}:{status}"
