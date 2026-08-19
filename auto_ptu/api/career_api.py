from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from ..career.auth import SupabaseIdentityResolver
from ..career.models import CareerRun
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


def _user(authorization: Optional[str], x_career_user: Optional[str]):
    return _identity(authorization or "", x_career_user or "")


@router.get("/catalog")
def career_catalog(locale: str = Query(default="es")) -> dict:
    return SERVICE.catalog(locale)


@router.post("/runs")
def create_run(payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.create_run(identity.user_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/restore")
def restore_unranked_run(payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    """Rehydrate a casual browser run after a serverless cold start.

    Ranked runs never enter this path. Competitive state remains authoritative
    in Postgres and requires a Supabase identity.
    """
    identity = _user(authorization, x_career_user)
    try:
        raw_run = payload.get("run")
        if not isinstance(raw_run, dict):
            raise ValueError("run must be an object")
        run = CareerRun.from_dict(raw_run)
        if run.ranked:
            raise PermissionError("Ranked career state cannot be restored from the browser.")
        if run.player_id != identity.user_id:
            raise PermissionError("Career run belongs to another account.")
        SERVICE.store.save_run(run)
        return run.to_dict()
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/runs/{run_id}")
def get_run(run_id: str, authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.get_run(identity.user_id, run_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/runs/{run_id}/preseason")
def career_preseason(run_id: str, authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.preseason(identity.user_id, run_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/club")
def career_choose_club(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.choose_club(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/sponsor")
def career_choose_sponsor(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.choose_sponsor(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/captures")
def career_capture(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.capture(identity.user_id, run_id, payload)
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
    identity = _user(authorization, x_career_user)
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


@router.post("/runs/{run_id}/lineup")
def career_lineup(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.lineup(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/items/use")
def career_use_item(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.use_item(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/training")
def career_training(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.train(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/market/purchases")
def career_purchase(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.purchase(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/runs/{run_id}/battles/{battle_id}")
def career_battle(run_id: str, battle_id: str, authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.battle(identity.user_id, run_id, battle_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/battles/{battle_id}/finalize")
def career_finalize_battle(run_id: str, battle_id: str, authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.finalize_season(identity.user_id, run_id, battle_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/runs/{run_id}/retire")
def career_retire(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    try:
        return SERVICE.retire(identity.user_id, run_id, payload)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/daily/{day}")
def daily_challenge(day: date) -> dict:
    return SERVICE.daily(day)


@router.post("/daily/{day}/attempts")
def create_daily_attempt(day: date, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
    if not identity.permanent or identity.source != "supabase":
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
def create_share(run_id: str, payload: Dict[str, Any], authorization: Optional[str] = Header(default=""), x_career_user: Optional[str] = Header(default="")) -> dict:
    identity = _user(authorization, x_career_user)
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
