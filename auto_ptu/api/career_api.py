from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from ..career.auth import SupabaseIdentityResolver
from ..career.service import CareerService


router = APIRouter(prefix="/api/v1", tags=["career"])
SERVICE = CareerService()
IDENTITIES = SupabaseIdentityResolver()


def _identity(authorization: str, development_user: str):
    try:
        return IDENTITIES.resolve(authorization, development_user)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/catalog")
def career_catalog(locale: str = Query(default="es")) -> dict:
    return SERVICE.catalog(locale)


@router.post("/runs")
def create_run(
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.create_run(identity.user_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.get_run(identity.user_id, run_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/decisions")
def career_decision(
    run_id: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
    idempotency_key: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.decide(identity.user_id, run_id, payload, idempotency_key or "")
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/advance")
def career_advance(
    run_id: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
    idempotency_key: Optional[str] = Header(default=""),
) -> dict:
    return career_decision(run_id, payload, authorization, x_career_user, idempotency_key)


@router.get("/runs/{run_id}/battles/{battle_id}")
def career_battle(
    run_id: str,
    battle_id: str,
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.battle(identity.user_id, run_id, battle_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/retire")
def career_retire(
    run_id: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.retire(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/daily/{day}")
def daily_challenge(day: date) -> dict:
    return SERVICE.daily(day)


@router.post("/daily/{day}/attempts")
def create_daily_attempt(
    day: date,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    if not identity.permanent:
        raise HTTPException(status_code=403, detail="A permanent account is required for ranked daily attempts.")
    try:
        return SERVICE.create_daily_attempt(identity.user_id, payload, day)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/daily/{day}/leaderboards/{mode}")
def daily_leaderboard(day: date, mode: str) -> dict:
    if mode not in {"simple", "advanced"}:
        raise HTTPException(status_code=400, detail="Leaderboard mode must be simple or advanced.")
    return SERVICE.leaderboard(day, mode)


@router.post("/runs/{run_id}/shares")
def create_share(
    run_id: str,
    payload: Dict[str, Any],
    authorization: Optional[str] = Header(default=""),
    x_career_user: Optional[str] = Header(default=""),
) -> dict:
    identity = _identity(authorization or "", x_career_user or "")
    try:
        return SERVICE.share(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/shares/{share_id}")
def get_public_share(share_id: str) -> dict:
    try:
        return SERVICE.public_share(share_id)
    except Exception as exc:
        raise _error(exc) from exc
