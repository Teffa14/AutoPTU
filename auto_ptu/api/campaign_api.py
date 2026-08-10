"""HTTP contract for full-campaign table play."""

from __future__ import annotations

from typing import Any, Dict, Optional

import asyncio

from fastapi import APIRouter, Header, HTTPException, Query, WebSocket, WebSocketDisconnect

from ..config import REPORTS_DIR
from .campaign_service import CampaignService
from .campaign_realtime import CampaignRealtimeHub


router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])
SERVICE = CampaignService(REPORTS_DIR / "campaign_events.sqlite3")
REALTIME = CampaignRealtimeHub()
SERVICE.add_event_listener(REALTIME.publish)


def _token(authorization: Optional[str], fallback: Optional[str] = None) -> str:
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


@router.get("")
def campaigns_list() -> Dict[str, Any]:
    return {"campaigns": SERVICE.list_campaigns()}


@router.post("")
def campaigns_create(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return SERVICE.create(payload)
    except Exception as exc:
        _raise_http(exc)


@router.post("/starter")
def campaigns_create_starter(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return SERVICE.create_starter(payload)
    except Exception as exc:
        _raise_http(exc)


@router.post("/{campaign_id}/join")
def campaigns_join(campaign_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return SERVICE.join(campaign_id, payload)
    except Exception as exc:
        _raise_http(exc)


@router.get("/{campaign_id}")
def campaigns_get(
    campaign_id: str,
    authorization: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    try:
        return {"campaign": SERVICE.get(campaign_id, _token(authorization, token))}
    except Exception as exc:
        _raise_http(exc)


@router.post("/{campaign_id}/command")
def campaigns_command(
    campaign_id: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    try:
        return SERVICE.command(campaign_id, _token(authorization, payload.get("token")), payload)
    except Exception as exc:
        _raise_http(exc)


@router.get("/{campaign_id}/events")
def campaigns_events(
    campaign_id: str,
    since_seq: int = 0,
    authorization: Optional[str] = Header(default=None),
    token: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    try:
        return {"events": SERVICE.events(campaign_id, _token(authorization, token), since_seq)}
    except Exception as exc:
        _raise_http(exc)


@router.websocket("/{campaign_id}/ws")
async def campaigns_websocket(campaign_id: str, websocket: WebSocket, token: str = Query(default="")) -> None:
    try:
        state = SERVICE.require_campaign(campaign_id)
        participant = SERVICE.require_participant(state, _token(None, token))
    except Exception:
        await websocket.close(code=4403, reason="A valid campaign participant token is required.")
        return
    await websocket.accept()
    subscription = REALTIME.subscribe(campaign_id)
    _loop, queue = subscription
    try:
        await websocket.send_json(
            {
                "type": "campaign.snapshot",
                "campaign_id": campaign_id,
                "campaign": SERVICE.public_state(state, participant),
            }
        )
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=25.0)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "campaign.ping", "revision": state.revision})
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        REALTIME.unsubscribe(campaign_id, subscription)
