"""Server-side campaign identity binding for the singleton tactical board."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .campaign_service import CampaignService


@dataclass
class CampaignBattleAccess:
    campaign_service: CampaignService
    campaign_id: str = ""
    scene_id: str = ""
    actor_owners: Dict[str, str] = field(default_factory=dict)
    trainer_owners: Dict[str, str] = field(default_factory=dict)

    @property
    def bound(self) -> bool:
        return bool(self.campaign_id)

    def bind(self, setup: Dict[str, object]) -> None:
        self.campaign_id = str(setup.get("campaign_id") or "")
        self.scene_id = str(setup.get("scene_id") or "")
        self.actor_owners = {
            str(key): str(value)
            for key, value in dict(setup.get("actor_owners") or {}).items()
        }
        self.trainer_owners = {
            str(key): str(value)
            for key, value in dict(setup.get("trainer_owners") or {}).items()
        }

    def clear(self) -> None:
        self.campaign_id = ""
        self.scene_id = ""
        self.actor_owners = {}
        self.trainer_owners = {}

    def identity(self, token: str) -> Dict[str, object]:
        if not self.bound:
            return {"bound": False, "role": "standalone", "participant_id": None, "owned_actor_ids": [], "owned_trainer_ids": []}
        state = self.campaign_service.require_campaign(self.campaign_id)
        participant = self.campaign_service.require_participant(state, token)
        owned = sorted(actor_id for actor_id, owner_id in self.actor_owners.items() if owner_id == participant.id)
        owned_trainers = sorted(trainer_id for trainer_id, owner_id in self.trainer_owners.items() if owner_id == participant.id)
        return {
            "bound": True,
            "campaign_id": self.campaign_id,
            "scene_id": self.scene_id,
            "role": participant.role,
            "participant_id": participant.id,
            "controller": participant.controller,
            "owned_actor_ids": owned,
            "owned_trainer_ids": owned_trainers,
        }

    def authorize(
        self,
        token: str,
        *,
        actor_id: Optional[str] = None,
        gm: bool = False,
        legacy_role: str = "player",
    ) -> str:
        """Return the authoritative role, falling back only for standalone battles."""
        if not self.bound:
            role = str(legacy_role or "player").strip().lower()
            if role not in {"gm", "player", "spectator"}:
                raise ValueError("Battle role must be gm, player, or spectator.")
            if role == "spectator":
                raise PermissionError("Spectators cannot change battle state.")
            if gm and role != "gm":
                raise PermissionError("Only the GM can use that battle control.")
            return role
        identity = self.identity(token)
        role = str(identity["role"])
        if role == "spectator":
            raise PermissionError("Spectators cannot change battle state.")
        if gm and role != "gm":
            raise PermissionError("Only the campaign GM can use that battle control.")
        if actor_id and role != "gm":
            owner_id = self.actor_owners.get(str(actor_id)) or self.trainer_owners.get(str(actor_id))
            if owner_id != identity["participant_id"]:
                raise PermissionError("That combatant belongs to another campaign participant.")
        return role


__all__ = ["CampaignBattleAccess"]
