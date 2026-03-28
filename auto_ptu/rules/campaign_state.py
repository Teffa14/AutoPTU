"""Out-of-combat and multi-encounter campaign state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CampaignState:
    """Persistent state across encounters."""

    trainer_ids: List[str] = field(default_factory=list)
    notes: Dict[str, str] = field(default_factory=dict)
    current_encounter_id: Optional[str] = None
