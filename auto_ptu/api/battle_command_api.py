"""HTTP routes for the battle command center."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from .battle_commands import BattleCommandService
from .campaign_battle_access import CampaignBattleAccess


def build_battle_command_router(service: BattleCommandService, access: Optional[CampaignBattleAccess] = None) -> APIRouter:
    router = APIRouter(prefix="/api/battle/commands", tags=["battle-commands"])

    def guard(callback):
        try:
            return callback()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc).strip("'"))
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    def bearer(value: Optional[str]) -> str:
        token = str(value or "").strip()
        return token[7:].strip() if token.lower().startswith("bearer ") else token

    def role_for(authorization: Optional[str], requested: str, *, actor_id: str = "", gm: bool = False) -> str:
        if access is None:
            return requested
        return access.authorize(bearer(authorization), actor_id=actor_id or None, gm=gm, legacy_role=requested)

    @router.get("")
    def command_state(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        payload = service.state()
        if access is not None:
            payload["identity"] = guard(lambda: access.identity(bearer(authorization))) if access.bound else access.identity("")
        return payload

    @router.post("")
    def command_stage(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        action = dict(payload.get("action") or payload)
        actor_id = str(action.get("actor_id") or getattr(service.facade.battle, "current_actor_id", "") or "")
        return guard(lambda: service.stage(action, role=role_for(authorization, str(payload.get("role") or "player"), actor_id=actor_id)))

    @router.delete("")
    def command_clear(role: str = "player", authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        def perform():
            authoritative = role_for(authorization, role)
            if access is not None and access.bound and authoritative != "gm":
                for entry in service.queue:
                    access.authorize(bearer(authorization), actor_id=entry.actor_id, legacy_role=role)
            return service.clear(role=authoritative)
        return guard(perform)

    @router.delete("/{command_id}")
    def command_remove(command_id: str, role: str = "player", authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        command = next((entry for entry in service.queue if entry.id == command_id), None)
        actor_id = command.actor_id if command else ""
        return guard(lambda: service.remove(command_id, role=role_for(authorization, role, actor_id=actor_id)))

    @router.patch("/{command_id}")
    def command_reorder(command_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        command = next((entry for entry in service.queue if entry.id == command_id), None)
        actor_id = command.actor_id if command else ""
        requested = str(payload.get("role") or "player")
        return guard(lambda: service.reorder(command_id, int(payload.get("index") or 0), role=role_for(authorization, requested, actor_id=actor_id)))

    @router.post("/resolve")
    def command_resolve(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        actor_id = service.queue[0].actor_id if service.queue else ""
        requested = str(payload.get("role") or "player")
        return guard(lambda: service.resolve(mode=str(payload.get("mode") or "next"), role=role_for(authorization, requested, actor_id=actor_id)))

    @router.post("/pause")
    def command_pause(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "gm")
        return guard(lambda: service.pause(bool(payload.get("paused", True)), role=role_for(authorization, requested, gm=True)))

    @router.post("/interrupt/open")
    def interrupt_open(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "gm")
        return guard(lambda: service.open_interrupt(payload, role=role_for(authorization, requested, gm=True)))

    @router.post("/interrupt/respond")
    def interrupt_respond(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "player")
        actor_id = str(payload.get("actor_id") or "")
        return guard(lambda: service.respond_interrupt(payload, role=role_for(authorization, requested, actor_id=actor_id)))

    @router.post("/interrupt/resolve")
    def interrupt_resolve(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "gm")
        return guard(lambda: service.resolve_interrupt(role=role_for(authorization, requested, gm=True)))

    @router.post("/interrupt/close")
    def interrupt_close(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "gm")
        return guard(lambda: service.close_interrupt(role=role_for(authorization, requested, gm=True)))

    @router.post("/reactions")
    def reaction_register(payload: Dict[str, Any], authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        requested = str(payload.get("role") or "gm")
        return guard(lambda: service.register_reaction(payload, role=role_for(authorization, requested, gm=True)))

    @router.delete("/reactions/{reaction_id}")
    def reaction_remove(reaction_id: str, role: str = "gm", authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
        return guard(lambda: service.remove_reaction(reaction_id, role=role_for(authorization, role, gm=True)))

    return router
