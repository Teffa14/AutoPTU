from __future__ import annotations

from pathlib import Path
import json
import re
import threading
from typing import Any, Dict, Optional
import tkinter as tk
from tkinter import filedialog

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from .engine_facade import EngineFacade
from .roleplay_api import router as roleplay_router
from .terrain_mapper_store import TerrainMapperStore
from ..config import IMPLEMENTATION_DIR, REPORTS_DIR
from ..gameplay import list_ai_models, select_ai_model, branch_ai_model, update_ai_model_settings
from ..sprites import sprite_cache_dir, start_download_all, download_status, ensure_sprite_filename
from ..sprites import sprite_url_for
from ..pokeapi_assets import (
    type_icon_path,
    item_icon_path,
    cry_path,
    move_metadata,
    ability_metadata,
    item_metadata,
)


app = FastAPI(title="AutoPTU API")
engine = EngineFacade()
app.include_router(roleplay_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
GEN9_UI_DIR = IMPLEMENTATION_DIR / "Generation 9 Pack v3.3.4" / "Graphics" / "UI"
GEN9_MOVE_ANIM_DIR = (
    IMPLEMENTATION_DIR
    / "Generation 9 Pack v3.3.4"
    / "Graphics"
    / "Battle animations"
)
STATIC_MOVE_ANIM_DIR = STATIC_DIR / "assets" / "gen9" / "move-anims"
SPRITE_DIR = sprite_cache_dir()
SPRITE_DIR.mkdir(parents=True, exist_ok=True)
TERRAIN_MAPS_DIR = REPORTS_DIR / "terrain_maps"
TERRAIN_MAPS_IMAGES_DIR = TERRAIN_MAPS_DIR / "images"
TERRAIN_EXPORTS_DIR = REPORTS_DIR / "terrain_exports"
SAVED_BATTLEFIELDS_DIR = REPORTS_DIR / "battlefields"
SAVED_ROSTERS_DIR = REPORTS_DIR / "rosters"
TERRAIN_WORKSPACE_DRAFT_PATH = TERRAIN_MAPS_DIR / "_workspace_draft.json"
TERRAIN_MAPS_STARTER_DIR = Path(__file__).resolve().parents[1] / "data" / "terrain_maps" / "starter"
TERRAIN_MAPPER_STORE = TerrainMapperStore(TERRAIN_MAPS_DIR, starter_dir=TERRAIN_MAPS_STARTER_DIR)
TERRAIN_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
SAVED_BATTLEFIELDS_DIR.mkdir(parents=True, exist_ok=True)
SAVED_ROSTERS_DIR.mkdir(parents=True, exist_ok=True)


def _choose_save_json_path(initial_filename: str, title: str) -> Optional[Path]:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=initial_filename,
        )
    finally:
        root.destroy()
    if not selected:
        return None
    return Path(selected)


def _slugify_filename(value: str, fallback: str = "battlefield") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip("-.")
    return slug or fallback


def _battlefield_path(battlefield_id: str) -> Path:
    return SAVED_BATTLEFIELDS_DIR / f"{_slugify_filename(battlefield_id)}.json"


def _battlefield_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(record.get("id") or "").strip(),
        "name": str(record.get("name") or "Saved Battlefield").strip() or "Saved Battlefield",
        "source_name": str(record.get("source_name") or "").strip(),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
    }


def _roster_path(roster_id: str) -> Path:
    return SAVED_ROSTERS_DIR / f"{_slugify_filename(roster_id, 'roster')}.json"


def _roster_summary(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(record.get("id") or "").strip(),
        "name": str(record.get("name") or "Saved Roster").strip() or "Saved Roster",
        "source_name": str(record.get("source_name") or "").strip(),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "players": int(record.get("players") or 0),
        "foes": int(record.get("foes") or 0),
        "side_count": int(record.get("side_count") or 0),
        "team_size": int(record.get("team_size") or 0),
    }

_MOVE_ANIM_INDEX: Dict[str, str] = {}
_MOVE_ANIM_INDEX_LOCK = threading.Lock()
_MOVE_ANIM_MAP: Optional[Dict[str, str]] = None
_MOVE_ANIM_MAP_LOCK = threading.Lock()
def _normalize_move_anim_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _canonical_move_anim_key(value: str) -> str:
    stem = Path(str(value or "")).stem.strip().lower()
    stem = re.sub(r"^(?:gen\d+\s*[-_]\s*|pras\s*[-_]\s*|custom\s*[-_]\s*)", "", stem)
    stem = re.sub(r"^(?:\d{3}\s*[-_]\s*)", "", stem)
    stem = re.sub(r"\b(?:fg|bg|opp|old|ally|filesheet|sheet)\b", "", stem)
    stem = re.sub(r"[_-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return _normalize_move_anim_key(stem)


def _is_generic_move_anim_filename(filename: str) -> bool:
    stem = Path(str(filename or "")).stem.lower().strip()
    if not stem or stem in {"!"}:
        return True
    if re.match(r"^\d{3}-", stem):
        return True
    canonical = _canonical_move_anim_key(stem)
    generic_terms = {
        "animsheet",
        "attack",
        "burst",
        "weapon",
        "state",
        "stats",
        "strike",
        "slash",
        "emotion",
        "firefangs",
        "elementalfangs",
    }
    return canonical in generic_terms


def _load_move_anim_map() -> Dict[str, str]:
    global _MOVE_ANIM_MAP
    if _MOVE_ANIM_MAP is not None:
        return _MOVE_ANIM_MAP
    with _MOVE_ANIM_MAP_LOCK:
        if _MOVE_ANIM_MAP is not None:
            return _MOVE_ANIM_MAP
        path = Path(__file__).resolve().parents[1] / "data" / "move_anim_map.json"
        loaded: Dict[str, str] = {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            entries = payload.get("map") if isinstance(payload, dict) else None
            if isinstance(entries, dict):
                for raw_key, raw_file in entries.items():
                    key = _normalize_move_anim_key(raw_key)
                    file_name = str(raw_file or "").strip()
                    if key and file_name:
                        loaded[key] = file_name
        except Exception:
            loaded = {}
        _MOVE_ANIM_MAP = loaded
        return _MOVE_ANIM_MAP


def _move_anim_dirs() -> list[Path]:
    # Prefer the external implementation folder during local development,
    # but fall back to bundled static assets in packaged builds.
    candidates = [GEN9_MOVE_ANIM_DIR, STATIC_MOVE_ANIM_DIR]
    resolved: list[Path] = []
    seen: set[Path] = set()
    for directory in candidates:
        try:
            normalized = directory.resolve()
        except Exception:
            normalized = directory
        if normalized in seen:
            continue
        seen.add(normalized)
        if directory.exists() and directory.is_dir():
            resolved.append(directory)
    return resolved


def _move_anim_exists(filename: str) -> bool:
    for directory in _move_anim_dirs():
        if (directory / filename).exists():
            return True
    return False


def _find_move_anim_file(filename: str) -> Optional[Path]:
    for directory in _move_anim_dirs():
        candidate = (directory / filename).resolve()
        root = directory.resolve()
        if root not in candidate.parents and candidate != root:
            continue
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _refresh_move_anim_index() -> None:
    global _MOVE_ANIM_INDEX
    if _MOVE_ANIM_INDEX:
        return
    with _MOVE_ANIM_INDEX_LOCK:
        if _MOVE_ANIM_INDEX:
            return
        index: Dict[str, str] = {}
        for directory in _move_anim_dirs():
            for candidate in directory.iterdir():
                if not candidate.is_file() or candidate.suffix.lower() != ".png":
                    continue
                key = _canonical_move_anim_key(candidate.stem)
                if key and key not in index:
                    index[key] = candidate.name
        _MOVE_ANIM_INDEX = index


def _resolve_move_anim_file(move_name: str) -> Optional[str]:
    _refresh_move_anim_index()
    key = _normalize_move_anim_key(move_name)
    if not key or not _MOVE_ANIM_INDEX:
        return None
    indexed = _MOVE_ANIM_INDEX.get(key)
    if indexed and _move_anim_exists(indexed) and not _is_generic_move_anim_filename(indexed):
        return indexed
    mapped = _load_move_anim_map().get(key)
    if mapped and _move_anim_exists(mapped) and not _is_generic_move_anim_filename(mapped):
        return mapped
    return None


@app.post("/api/battle/new")
def battle_new(payload: Dict[str, Any]) -> dict:
    try:
        return engine.start_encounter(
            campaign=payload.get("campaign"),
            team_size=int(payload.get("team_size", 1)),
            matchup_index=int(payload.get("matchup_index", 0)),
            seed=payload.get("seed"),
            random_battle=bool(payload.get("random_battle", False)),
            min_level=int(payload.get("min_level", 20)),
            max_level=int(payload.get("max_level", 40)),
            csv_root=payload.get("csv_root"),
            roster_csv=payload.get("roster_csv"),
            roster_csv_path=payload.get("roster_csv_path"),
            ai_mode=str(payload.get("ai_mode", "player")),
            step_ai=bool(payload.get("step_ai", False)),
            active_slots=payload.get("active_slots"),
            trainer_profile=payload.get("trainer_profile"),
            side_names=payload.get("side_names"),
            deployment_overrides=payload.get("deployment_overrides"),
            item_choice_overrides=payload.get("item_choice_overrides"),
            grid=payload.get("grid"),
            side_count=int(payload.get("side_count", 2)),
            battle_royale=bool(payload.get("battle_royale", False)),
            circle_interval=int(payload.get("circle_interval", 3)),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/state")
def get_state() -> dict:
    return engine.snapshot()


@app.get("/api/battle/log/export")
def export_battle_log() -> dict:
    return engine.export_battle_log()


@app.post("/api/battle/clear")
def clear_battle() -> dict:
    try:
        return engine.clear_battle()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/terrain/load_battle")
def terrain_load_battle() -> dict:
    try:
        return engine.load_battle_grid_for_mapper()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/terrain/apply")
def terrain_apply(payload: Dict[str, Any]) -> dict:
    try:
        return engine.apply_terrain_layout(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/terrain/maps")
def terrain_maps() -> dict:
    return {"maps": TERRAIN_MAPPER_STORE.list_maps()}


@app.get("/api/terrain/maps/{map_id}")
def terrain_map_load(map_id: str) -> dict:
    try:
        payload = TERRAIN_MAPPER_STORE.get_map(map_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Terrain map not found")
    image_name = str(payload.get("image") or "").strip()
    image_url = f"/api/terrain/maps/image/{image_name}" if image_name else None
    return {"map": payload, "image_url": image_url}


@app.post("/api/terrain/maps/save")
def terrain_map_save(payload: Dict[str, Any]) -> dict:
    try:
        record = TERRAIN_MAPPER_STORE.save_map(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    image_name = str(record.get("image") or "").strip()
    return {
        "status": "ok",
        "map": {
            "id": record.get("id"),
            "name": record.get("name"),
            "image": image_name or None,
            "path": str(TERRAIN_MAPPER_STORE._record_path(str(record.get("id") or ""))),
            "profile_id": record.get("profile_id") or "",
            "tags": list(record.get("tags") or []),
        },
    }


@app.post("/api/terrain/export")
def terrain_export(payload: Dict[str, Any]) -> dict:
    export_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    filename = str(payload.get("filename") or "terrain-battle-grid.json").strip()
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-.") or "terrain-battle-grid.json"
    if not filename.lower().endswith(".json"):
        filename = f"{filename}.json"
    target = TERRAIN_EXPORTS_DIR / filename
    target.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "filename": filename,
        "path": str(target),
        "directory": str(TERRAIN_EXPORTS_DIR),
    }


@app.get("/api/terrain/workspace")
def terrain_workspace_load() -> dict:
    if not TERRAIN_WORKSPACE_DRAFT_PATH.exists():
        return {"status": "empty"}
    payload = json.loads(TERRAIN_WORKSPACE_DRAFT_PATH.read_text(encoding="utf-8"))
    image_name = str(payload.get("image") or payload.get("image_name") or "").strip()
    image_url = f"/api/terrain/maps/image/{image_name}" if image_name else None
    return {
        "status": "ok",
        "map": payload,
        "path": str(TERRAIN_WORKSPACE_DRAFT_PATH),
        "image_url": image_url,
    }


@app.post("/api/terrain/workspace")
def terrain_workspace_save(payload: Dict[str, Any]) -> dict:
    TERRAIN_MAPS_DIR.mkdir(parents=True, exist_ok=True)
    TERRAIN_WORKSPACE_DRAFT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "path": str(TERRAIN_WORKSPACE_DRAFT_PATH),
    }


@app.post("/api/terrain/workspace/clear")
def terrain_workspace_clear() -> dict:
    if TERRAIN_WORKSPACE_DRAFT_PATH.exists():
        TERRAIN_WORKSPACE_DRAFT_PATH.unlink()
    return {"status": "ok"}


@app.post("/api/terrain/save_as")
def terrain_save_as(payload: Dict[str, Any]) -> dict:
    export_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    filename = str(payload.get("filename") or "terrain.json").strip()
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-.") or "terrain.json"
    if not filename.lower().endswith(".json"):
        filename = f"{filename}.json"
    title = str(payload.get("title") or "Save Terrain JSON").strip() or "Save Terrain JSON"
    target = _choose_save_json_path(filename, title)
    if target is None:
        return {"status": "cancelled"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "filename": target.name,
        "path": str(target),
        "directory": str(target.parent),
    }


@app.get("/api/battlefields")
def battlefields_list() -> dict:
    entries: list[dict[str, Any]] = []
    for path in sorted(SAVED_BATTLEFIELDS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                entries.append(_battlefield_summary(payload))
        except Exception:
            continue
    entries.sort(key=lambda entry: str(entry.get("updated_at") or ""), reverse=True)
    return {"battlefields": entries}


@app.get("/api/battlefields/{battlefield_id}")
def battlefield_load(battlefield_id: str) -> dict:
    path = _battlefield_path(battlefield_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Saved battlefield not found")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Saved battlefield is invalid")
    return {"battlefield": payload}


@app.post("/api/battlefields/save")
def battlefield_save(payload: Dict[str, Any]) -> dict:
    grid = payload.get("grid")
    if not isinstance(grid, dict):
        raise HTTPException(status_code=400, detail="grid is required")
    requested_name = str(payload.get("name") or payload.get("source_name") or "Saved Battlefield").strip() or "Saved Battlefield"
    battlefield_id = _slugify_filename(str(payload.get("id") or requested_name), "battlefield")
    target = _battlefield_path(battlefield_id)
    existing: Dict[str, Any] = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except Exception:
            existing = {}
    record = {
        "id": battlefield_id,
        "name": requested_name,
        "source_name": str(payload.get("source_name") or "").strip(),
        "created_at": existing.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "grid": grid,
    }
    if not record["created_at"]:
        from datetime import datetime, timezone

        record["created_at"] = datetime.now(timezone.utc).isoformat()
    if not record["updated_at"]:
        from datetime import datetime, timezone

        record["updated_at"] = datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "battlefield": _battlefield_summary(record),
        "path": str(target),
    }


@app.delete("/api/battlefields/{battlefield_id}")
def battlefield_delete(battlefield_id: str) -> dict:
    path = _battlefield_path(battlefield_id)
    if path.exists():
        path.unlink()
    return {"status": "ok"}


@app.get("/api/rosters")
def rosters_list() -> dict:
    entries: list[dict[str, Any]] = []
    for path in sorted(SAVED_ROSTERS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                entries.append(_roster_summary(payload))
        except Exception:
            continue
    entries.sort(key=lambda entry: str(entry.get("updated_at") or ""), reverse=True)
    return {"rosters": entries}


@app.get("/api/rosters/{roster_id}")
def roster_load(roster_id: str) -> dict:
    path = _roster_path(roster_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Saved roster not found")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Saved roster is invalid")
    return {"roster": payload}


@app.post("/api/rosters/save")
def roster_save(payload: Dict[str, Any]) -> dict:
    csv_text = str(payload.get("csv_text") or "").strip()
    if not csv_text:
        raise HTTPException(status_code=400, detail="csv_text is required")
    requested_name = str(payload.get("name") or payload.get("source_name") or "Saved Roster").strip() or "Saved Roster"
    roster_id = _slugify_filename(str(payload.get("id") or requested_name), "roster")
    target = _roster_path(roster_id)
    existing: Dict[str, Any] = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except Exception:
            existing = {}
    record = {
        "id": roster_id,
        "name": requested_name,
        "source_name": str(payload.get("source_name") or "").strip(),
        "created_at": existing.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "csv_text": csv_text,
        "players": int(payload.get("players") or existing.get("players") or 0),
        "foes": int(payload.get("foes") or existing.get("foes") or 0),
        "side_count": int(payload.get("side_count") or existing.get("side_count") or 0),
        "team_size": int(payload.get("team_size") or existing.get("team_size") or 0),
    }
    if not record["created_at"]:
        from datetime import datetime, timezone
        record["created_at"] = datetime.now(timezone.utc).isoformat()
    if not record["updated_at"]:
        from datetime import datetime, timezone
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {
        "status": "ok",
        "roster": _roster_summary(record),
        "path": str(target),
    }


@app.delete("/api/rosters/{roster_id}")
def roster_delete(roster_id: str) -> dict:
    path = _roster_path(roster_id)
    if path.exists():
        path.unlink()
    return {"status": "ok"}


@app.get("/api/terrain/profiles")
def terrain_profiles() -> dict:
    return {"profiles": TERRAIN_MAPPER_STORE.list_profiles()}


@app.get("/api/terrain/profiles/{profile_id}")
def terrain_profile_load(profile_id: str) -> dict:
    try:
        return {"profile": TERRAIN_MAPPER_STORE.get_profile(profile_id)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Terrain profile not found")


@app.post("/api/terrain/profiles/save")
def terrain_profile_save(payload: Dict[str, Any]) -> dict:
    try:
        profile = TERRAIN_MAPPER_STORE.save_profile(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok", "profile": TERRAIN_MAPPER_STORE.profile_summary(profile)}


@app.post("/api/terrain/predict")
def terrain_predict(payload: Dict[str, Any]) -> dict:
    try:
        return TERRAIN_MAPPER_STORE.predict_tiles(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/terrain/maps/image/{filename}")
def terrain_map_image(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid terrain map image path")
    target = TERRAIN_MAPS_IMAGES_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Terrain map image not found")
    media = "image/png"
    suffix = target.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        media = "image/jpeg"
    return FileResponse(target, media_type=media, headers={"Cache-Control": "no-store"})


@app.post("/api/battle/stop")
def stop_battle() -> dict:
    try:
        return engine.stop_battle()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/action")
def post_action(payload: Dict[str, Any]) -> dict:
    try:
        return engine.commit_action(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/end_turn")
def end_turn() -> dict:
    try:
        return engine.commit_action({"type": "end_turn"})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/ai/step")
def ai_step() -> dict:
    try:
        return engine.ai_step()
    except ValueError as exc:
        if str(exc) == "Not in AI vs AI mode.":
            snapshot = engine.snapshot()
            snapshot["warning"] = str(exc)
            return snapshot
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/ai/models")
def ai_models() -> dict:
    try:
        return list_ai_models()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/ai/models/select")
def ai_models_select(payload: Dict[str, Any]) -> dict:
    try:
        model_id = payload.get("model_id")
        return select_ai_model(str(model_id or ""))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/ai/models/branch")
def ai_models_branch(payload: Dict[str, Any]) -> dict:
    try:
        return branch_ai_model(str(payload.get("label") or ""))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/ai/models/settings")
def ai_models_settings(payload: Dict[str, Any]) -> dict:
    try:
        drift_threshold = payload.get("drift_threshold")
        min_updates = payload.get("min_updates")
        check_every = payload.get("check_every")
        return update_ai_model_settings(
            drift_threshold=float(drift_threshold) if drift_threshold is not None else None,
            min_updates=int(min_updates) if min_updates is not None else None,
            check_every=int(check_every) if check_every is not None else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/undo")
def undo() -> dict:
    try:
        return engine.undo()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/prompts/resolve")
def resolve_prompts(payload: Dict[str, Any]) -> dict:
    answers = payload.get("answers", {})
    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="answers must be an object")
    return engine.resolve_prompts(answers)


@app.post("/api/sprites/download_all")
def sprites_download_all() -> dict:
    return start_download_all()


@app.get("/api/sprites/status")
def sprites_status() -> dict:
    return download_status()


@app.get("/api/sprites/pokemon")
def pokemon_sprite(name: str) -> RedirectResponse:
    url = sprite_url_for(name, allow_download=True)
    if not url:
        raise HTTPException(status_code=404, detail="Sprite not found")
    return RedirectResponse(url=url, status_code=307, headers={"Cache-Control": "no-store"})


@app.get("/api/poke/type_icon/{type_name}")
def get_type_icon(type_name: str) -> dict:
    path = type_icon_path(type_name)
    if not path:
        return {"available": False}
    return {"available": True, "url": f"/poke/type-icons/{path.name}"}


@app.get("/api/poke/move/{move_name}")
def get_move_meta(move_name: str) -> dict:
    data = move_metadata(move_name)
    if not data:
        return {"available": False}
    move_type = data.get("type")
    icon = type_icon_path(str(move_type)) if move_type else None
    payload = dict(data)
    payload["available"] = True
    payload["type_icon_url"] = f"/poke/type-icons/{icon.name}" if icon else None
    return payload


@app.get("/api/poke/ability/{ability_name}")
def get_ability_meta(ability_name: str) -> dict:
    data = ability_metadata(ability_name)
    if not data:
        return {"available": False}
    payload = dict(data)
    payload["available"] = True
    return payload


@app.get("/api/poke/item/{item_name}")
def get_item_meta(item_name: str) -> dict:
    data = item_metadata(item_name)
    if not data:
        return {"available": False}
    icon = item_icon_path(item_name)
    payload = dict(data)
    payload["available"] = True
    payload["icon_url"] = f"/poke/item-icons/{icon.name}" if icon else None
    return payload


@app.get("/api/poke/cry/{pokemon_name}")
def get_cry_meta(pokemon_name: str) -> dict:
    path = cry_path(pokemon_name)
    if not path:
        return {"available": False}
    return {"available": True, "url": f"/poke/cries/{path.name}"}


@app.get("/api/classes/graph")
def get_class_graph() -> dict:
    path = REPORTS_DIR / "trainer_class_graph.json"
    if not path.exists():
        return {"classes": [], "nodes": [], "edges": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"classes": [], "nodes": [], "edges": []}


@app.get("/api/character_creation")
def get_character_creation() -> dict:
    path = REPORTS_DIR / "character_creation.json"
    if not path.exists():
        return {"classes": [], "nodes": [], "edges": [], "features": [], "edges_catalog": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"classes": [], "nodes": [], "edges": [], "features": [], "edges_catalog": []}


@app.get("/sprites/{filename}")
def get_sprite(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid sprite path")
    if not filename.lower().endswith(".png"):
        raise HTTPException(status_code=404, detail="Invalid sprite type")
    path = SPRITE_DIR / filename
    ensure_sprite_filename(filename)
    if path.exists():
        return FileResponse(path, headers={"Cache-Control": "no-store"})
    raise HTTPException(status_code=404, detail="Sprite not found")


@app.get("/poke/type-icons/{filename}")
def get_type_icon_file(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid icon path")
    slug = filename[:-4] if filename.lower().endswith(".png") else filename
    path = type_icon_path(slug)
    if path and path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Type icon not found")


@app.get("/poke/item-icons/{filename}")
def get_item_icon_file(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid icon path")
    slug = Path(filename).stem
    path = item_icon_path(slug)
    if path and path.exists():
        return FileResponse(path, headers={"Cache-Control": "no-store"})
    raise HTTPException(status_code=404, detail="Item icon not found")


@app.get("/poke/cries/{filename}")
def get_cry_file(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid cry path")
    stem = Path(filename).stem
    path = cry_path(stem)
    if path and path.exists():
        suffix = path.suffix.lower()
        media = "audio/mpeg" if suffix == ".mp3" else "audio/ogg"
        return FileResponse(path, media_type=media)
    raise HTTPException(status_code=404, detail="Cry not found")


@app.get("/assets/gen9/ui/{asset_path:path}")
def get_gen9_ui_asset(asset_path: str) -> FileResponse:
    raw = str(asset_path or "").strip()
    if not raw:
        raise HTTPException(status_code=404, detail="Missing UI asset path")
    target = (GEN9_UI_DIR / raw).resolve()
    root = GEN9_UI_DIR.resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=404, detail="Invalid UI asset path")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="UI asset not found")
    suffix = target.suffix.lower()
    media = "image/png" if suffix == ".png" else "application/octet-stream"
    return FileResponse(target, media_type=media)


@app.get("/api/move_anim/{move_name}")
def get_move_anim_meta(move_name: str) -> dict:
    # Only resolve animation sheets for real move names.
    if not move_metadata(move_name):
        return {"available": False}
    filename = _resolve_move_anim_file(move_name)
    if not filename:
        return {"available": False}
    return {"available": True, "url": f"/assets/gen9/move-anims/{filename}"}


@app.get("/assets/gen9/move-anims/{filename}")
def get_gen9_move_anim_file(filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Invalid move animation path")
    target = _find_move_anim_file(filename)
    if not target:
        raise HTTPException(status_code=404, detail="Move animation asset not found")
    media = "image/png" if target.suffix.lower() == ".png" else "application/octet-stream"
    return FileResponse(target, media_type=media)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/create")
def create() -> FileResponse:
    return FileResponse(STATIC_DIR / "create.html", headers={"Cache-Control": "no-store"})


@app.get("/terrain-mapper")
def terrain_mapper() -> FileResponse:
    return FileResponse(STATIC_DIR / "terrain-mapper.html", headers={"Cache-Control": "no-store"})


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
