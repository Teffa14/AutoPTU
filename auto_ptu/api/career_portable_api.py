from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..career.models import CareerRun
from ..career.service import CareerService
from ..career.store import CareerStore


router = APIRouter(prefix="/portable", tags=["career-portable"])


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


def _payload(value: object) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _unranked_run(value: object) -> CareerRun:
    if not isinstance(value, dict):
        raise ValueError("A career run snapshot is required.")
    run = CareerRun.from_dict(value)
    if run.ranked:
        raise PermissionError("Ranked careers must use the authoritative account-backed API.")
    return run


def _normalized_run(service: CareerService, player_id: str, run_id: str) -> dict:
    """Return the exact snapshot that the next portable request must use."""
    return service.get_run(player_id, run_id)


def execute_portable_action(request: Dict[str, Any]) -> Any:
    """Run one casual Career action from a complete browser-held snapshot.

    Each call gets an isolated temporary CareerStore. This makes casual play
    independent from serverless instance affinity. Ranked state is rejected.
    """
    action = str(request.get("action") or "").strip().lower()
    payload = _payload(request.get("payload"))

    with tempfile.TemporaryDirectory(prefix="autoptu-career-portable-") as temp_root:
        store = CareerStore(Path(temp_root))
        service = CareerService(store=store)

        if action == "new":
            player_id = str(request.get("player_id") or f"casual-{uuid.uuid4()}")
            created = service.create_run(player_id, payload)
            return _normalized_run(service, player_id, str(created["id"]))

        run = _unranked_run(request.get("run"))
        store.save_run(run)
        player_id = run.player_id
        run_id = run.id

        if action in {"get", "run"}:
            return _normalized_run(service, player_id, run_id)
        if action == "preseason":
            snapshot = service.preseason(player_id, run_id)
            snapshot["run"] = _normalized_run(service, player_id, run_id)
            return snapshot
        if action == "club":
            service.choose_club(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "sponsor":
            service.choose_sponsor(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "capture":
            service.capture(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "lineup":
            service.lineup(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "item":
            service.use_item(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "train":
            service.train(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "purchase":
            service.purchase(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)
        if action == "decide":
            key = str(request.get("idempotency_key") or f"portable:{run_id}:{run.revision}:{payload.get('option_id', '')}")
            response = service.decide(player_id, run_id, payload, key)
            response["run"] = _normalized_run(service, player_id, run_id)
            return response
        if action == "battle":
            return service.battle(player_id, run_id, str(payload.get("battle_id") or ""))
        if action == "finalize":
            service.finalize_season(player_id, run_id, str(payload.get("battle_id") or ""))
            return _normalized_run(service, player_id, run_id)
        if action == "retire":
            service.retire(player_id, run_id, payload)
            return _normalized_run(service, player_id, run_id)

        raise ValueError(f"Unknown portable Career action: {action or '<empty>'}")


@router.post("/action")
def portable_action(request: Dict[str, Any]) -> Any:
    try:
        return execute_portable_action(request)
    except HTTPException:
        raise
    except Exception as exc:
        raise _error(exc) from exc
