"""Dialogue nodes and choice resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DialogueChoice:
    id: str
    text: str
    next_node: Optional[str] = None
    effects: Dict[str, object] = field(default_factory=dict)


@dataclass
class DialogueNode:
    id: str
    text: str
    choices: List[DialogueChoice] = field(default_factory=list)

    def resolve_choice(self, choice_id: str) -> Optional[DialogueChoice]:
        for choice in self.choices:
            if choice.id == choice_id:
                return choice
        return None
