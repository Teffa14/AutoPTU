"""HTTP routes for local Ollama campaign and battle agents."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from .campaign_agents import CampaignAgentRuntime


def _token(authorization: Optional[str], fallback: object = "") -> str:
    value = str(authorization or fallback or "").strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc).strip("'"))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    raise HTTPException(status_code=400, detail=str(exc))


def build_campaign_agent_router(runtime: CampaignAgentRuntime, battle_access: Any = None) -> APIRouter:
    router = APIRouter(tags=["campaign-agents"])

    @router.get("/api/agents/ollama")
    def ollama_status() -> Dict[str, Any]:
        return runtime.status()

    @router.get("/api/campaigns/{campaign_id}/agents")
    def campaign_agents(
        campaign_id: str,
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            runtime._authorize_agent_host(campaign_id, _token(authorization))
            state = runtime.campaign_service.require_campaign(campaign_id)
            return {
                "agents": [entry.public_dict() for entry in runtime._agents(state)],
                "ollama": runtime.status(),
            }
        except Exception as exc:
            _raise_http(exc)

    @router.post("/api/campaigns/{campaign_id}/agents/step")
    def campaign_agent_step(
        campaign_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            return runtime.step(
                campaign_id,
                _token(authorization, payload.get("token")),
                agent_id=str(payload.get("agent_id") or ""),
                model_override=str(payload.get("model") or ""),
            )
        except Exception as exc:
            _raise_http(exc)

    @router.post("/api/campaigns/{campaign_id}/agents/round")
    def campaign_agent_round(
        campaign_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            return runtime.round(
                campaign_id,
                _token(authorization, payload.get("token")),
                gm_model=str(payload.get("gm_model") or ""),
                player_model=str(payload.get("player_model") or ""),
                include_gm=bool(payload.get("include_gm", True)),
            )
        except Exception as exc:
            _raise_http(exc)

    @router.post("/api/campaigns/{campaign_id}/agents/advance")
    def campaign_agent_advance(
        campaign_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            return runtime.advance(
                campaign_id,
                _token(authorization, payload.get("token")),
                model_override=str(payload.get("model") or ""),
            )
        except Exception as exc:
            _raise_http(exc)

    @router.post("/api/campaigns/{campaign_id}/agents/battle/step")
    def campaign_battle_agent_step(
        campaign_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            token = _token(authorization, payload.get("token"))
            result = runtime.battle_step(
                campaign_id,
                token,
                model_override=str(payload.get("model") or ""),
            )
            if battle_access is not None and isinstance(result.get("battle"), dict):
                result["battle"]["battle_identity"] = (
                    battle_access.identity(token) if battle_access.bound else battle_access.identity("")
                )
            return result
        except Exception as exc:
            _raise_http(exc)

    @router.post("/api/campaigns/{campaign_id}/agents/npc/reply")
    def campaign_npc_reply(
        campaign_id: str,
        payload: Dict[str, Any],
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        try:
            return runtime.npc_reply(
                campaign_id,
                _token(authorization, payload.get("token")),
                dialogue_id=str(payload.get("dialogue_id") or ""),
                model_override=str(payload.get("model") or ""),
            )
        except Exception as exc:
            _raise_http(exc)

    return router
