"""Interactive and legacy text-mode gameplay for Auto PTU."""
from __future__ import annotations

import copy
import json
import os
import random
import shutil
import string
import math
from datetime import datetime, timezone
import textwrap
import binascii
import subprocess
import sys
from multiprocessing.connection import Listener
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .rich_compat import ensure_rich_unicode

ensure_rich_unicode()

from rich import box
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import ptu_engine
from .battle_state import format_move_event
from .data_models import MatchPlan, MatchupSpec, MoveSpec, TrainerSideSpec
from .config import PROJECT_ROOT, REPORTS_DIR, RUNTIME_ROOT
from .engine import MatchEngine
from .rules.battle_state import Action, ActionType, TrainerAction
from .rules import (
    BattleState as RulesBattleState,
    GridState as RulesGridState,
    PokemonState as RulesPokemonState,
    DelayAction,
    GrappleAction,
    DisengageAction,
    SwitchAction,
    TrainerSwitchAction,
    SprintAction,
    InterceptAction,
    ManipulateAction,
    CreativeAction,
    TakeBreatherAction,
    PickupItemAction,
    EquipWeaponAction,
    UnequipWeaponAction,
    WakeAllyAction,
    TradeStandardForAction,
    UseItemAction,
    ShiftAction,
    TrainerState as RulesTrainerState,
    TurnPhase as RulesTurnPhase,
    UseMoveAction,
    ai as rules_ai,
    ai_hybrid,
    calculations,
)
from .rules import movement, targeting
from .rules.item_catalog import get_item_entry
from .rules.item_effects import parse_item_effects
from .ai import royale_policy, behavior_tree_policy, mcts_policy, model_ratings

_MARKER_CHARS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

MoveSelector = Callable[
    [Sequence[ptu_engine.Move], MatchupSpec, ptu_engine.Combatant, ptu_engine.Combatant],
    ptu_engine.Move,
]

def _seed_runtime_ai_reports() -> None:
    target_reports = REPORTS_DIR
    target_models = target_reports / "ai_models"
    try:
        target_reports.mkdir(parents=True, exist_ok=True)
        target_models.mkdir(parents=True, exist_ok=True)
    except Exception:
        return

    existing_models = list(target_models.glob("model_*.json"))
    if existing_models:
        return

    candidate_reports: list[Path] = []
    legacy_runtime_reports = RUNTIME_ROOT / "reports"
    bundled_reports = PROJECT_ROOT / "reports"
    for candidate in (legacy_runtime_reports, bundled_reports):
        try:
            if candidate.resolve() == target_reports.resolve():
                continue
        except Exception:
            if str(candidate) == str(target_reports):
                continue
        candidate_reports.append(candidate)

    for source_reports in candidate_reports:
        source_models = source_reports / "ai_models"
        model_files = sorted(source_models.glob("model_*.json")) if source_models.exists() else []
        if not model_files:
            continue
        for model_path in model_files:
            target_path = target_models / model_path.name
            if not target_path.exists():
                shutil.copy2(model_path, target_path)
        ratings_path = source_models / "ratings.json"
        if ratings_path.exists() and not (target_models / "ratings.json").exists():
            shutil.copy2(ratings_path, target_models / "ratings.json")
        profile_path = source_reports / "ai_profiles.json"
        if profile_path.exists() and not (target_reports / "ai_profiles.json").exists():
            shutil.copy2(profile_path, target_reports / "ai_profiles.json")
        break


_seed_runtime_ai_reports()
_AI_PROFILE_PATH = REPORTS_DIR / "ai_profiles.json"
_AI_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
_AI_PROFILE_STORE = ai_hybrid.get_profile_store(path=_AI_PROFILE_PATH)
_AI_MODEL_DIR = _AI_PROFILE_PATH.parent / "ai_models"
_AI_MODEL_REGISTRY_PATH = _AI_MODEL_DIR / "registry.json"
_AI_MODEL_RATINGS_PATH = _AI_MODEL_DIR / "ratings.json"
_AI_MODEL_MIN_UPDATES = max(1, int(os.environ.get("AUTOPTU_AI_MODEL_MIN_UPDATES", "250")))
_AI_MODEL_DRIFT_THRESHOLD = max(0.01, float(os.environ.get("AUTOPTU_AI_MODEL_DRIFT_THRESHOLD", "0.35")))
_AI_MODEL_CHECK_EVERY = max(1, int(os.environ.get("AUTOPTU_AI_MODEL_CHECK_EVERY", "25")))
_AI_MODEL_RATING_STORE = model_ratings.default_store(_AI_MODEL_RATINGS_PATH)


def _profile_vector_from_store(store: ai_hybrid.ProfileStore) -> Dict[str, float]:
    vector: Dict[str, float] = {}
    for signature, profile in sorted(store.profiles.items()):
        buckets = {
            "action_type": dict(profile.action_type or {}),
            "target_pref": dict(profile.target_pref or {}),
            "risk_tolerance": dict(profile.risk_tolerance or {}),
            "move_usage": dict(profile.move_usage or {}),
        }
        for bucket_name, values in buckets.items():
            for key, raw in sorted(values.items()):
                try:
                    value = float(raw)
                except Exception:
                    value = 0.0
                if abs(value) < 1e-9:
                    continue
                vector[f"{signature}|{bucket_name}|{key}"] = value
    return vector


def _load_profile_vector_from_path(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    store = ai_hybrid.ProfileStore(path=path)
    try:
        store.load()
    except Exception:
        store.profiles = {}
    return _profile_vector_from_store(store)


def _model_drift_score(baseline: Dict[str, float], current: Dict[str, float]) -> Tuple[float, float, float]:
    keys = set(baseline.keys()) | set(current.keys())
    if not keys:
        return (0.0, 0.0, 0.0)
    l1 = 0.0
    changed = 0
    for key in keys:
        base = float(baseline.get(key, 0.0))
        now = float(current.get(key, 0.0))
        delta = abs(now - base)
        l1 += delta
        if delta > 1e-9:
            changed += 1
    base_mass = sum(abs(v) for v in baseline.values())
    rel_l1 = l1 / max(1.0, base_mass)
    churn = changed / max(1, len(keys))
    composite = (0.8 * rel_l1) + (0.2 * churn)
    return (composite, rel_l1, churn)


def _timestamp_model_id(prefix: str = "model") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rand = f"{random.randint(0, 0xFFFF):04x}"
    return f"{prefix}_{stamp}_{rand}"


def _read_model_registry() -> Dict[str, Any]:
    if not _AI_MODEL_REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(_AI_MODEL_REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_model_registry(data: Dict[str, Any]) -> None:
    _AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    _AI_MODEL_REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _create_registry_entry(model_id: str, path: Path, *, parent_id: Optional[str], auto_created: bool) -> Dict[str, Any]:
    return {
        "id": model_id,
        "path": str(path),
        "parent_id": parent_id or "",
        "auto_created": bool(auto_created),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _bootstrap_model_registry() -> Dict[str, Any]:
    registry = _read_model_registry()
    models = registry.get("models")
    if not isinstance(models, dict):
        models = {}
    current_id = str(registry.get("current_model_id") or "").strip()
    active_path = registry.get("active_path")
    if not active_path:
        active_path = str(_AI_PROFILE_PATH)
    active = Path(active_path)
    active.parent.mkdir(parents=True, exist_ok=True)
    if not current_id:
        current_id = "legacy_default"
    if current_id not in models:
        models[current_id] = _create_registry_entry(current_id, active, parent_id=None, auto_created=False)
    # Auto-discover unmanaged model files.
    if _AI_MODEL_DIR.exists():
        for item in _AI_MODEL_DIR.glob("*.json"):
            if item.name == _AI_MODEL_REGISTRY_PATH.name:
                continue
            if any(str(entry.get("path") or "") == str(item) for entry in models.values()):
                continue
            discovered_id = item.stem
            models[discovered_id] = _create_registry_entry(discovered_id, item, parent_id="", auto_created=True)
    active_entry = models.get(current_id) or {}
    resolved_active_path = Path(str(active_entry.get("path") or active))
    ai_hybrid.set_profile_store_path(resolved_active_path, save_current=False, load=True)
    baseline_vector = registry.get("baseline_vector")
    if not isinstance(baseline_vector, dict):
        baseline_vector = _profile_vector_from_store(_AI_PROFILE_STORE)
    normalized = {
        "models": models,
        "current_model_id": current_id,
        "active_path": str(resolved_active_path),
        "baseline_vector": baseline_vector,
        "updates_since_snapshot": int(registry.get("updates_since_snapshot") or 0),
        "total_updates": int(registry.get("total_updates") or 0),
        "last_drift_score": float(registry.get("last_drift_score") or 0.0),
        "last_rel_l1": float(registry.get("last_rel_l1") or 0.0),
        "last_churn": float(registry.get("last_churn") or 0.0),
        "last_auto_model_id": str(registry.get("last_auto_model_id") or ""),
        "min_updates": _AI_MODEL_MIN_UPDATES,
        "drift_threshold": _AI_MODEL_DRIFT_THRESHOLD,
        "check_every": _AI_MODEL_CHECK_EVERY,
    }
    _write_model_registry(normalized)
    return normalized


_AI_MODEL_REGISTRY: Dict[str, Any] = _bootstrap_model_registry()
_AI_PROFILE_STORE = ai_hybrid.get_profile_store()


def _persist_ai_model_registry() -> None:
    _write_model_registry(_AI_MODEL_REGISTRY)


def _current_model_store() -> ai_hybrid.ProfileStore:
    path = Path(str(_AI_MODEL_REGISTRY.get("active_path") or _AI_PROFILE_PATH))
    return ai_hybrid.set_profile_store_path(path, save_current=False, load=True)


def _checkpoint_ai_model_if_needed() -> Optional[Dict[str, Any]]:
    updates = int(_AI_MODEL_REGISTRY.get("updates_since_snapshot") or 0)
    check_every = max(1, int(_AI_MODEL_REGISTRY.get("check_every") or _AI_MODEL_CHECK_EVERY))
    min_updates = max(1, int(_AI_MODEL_REGISTRY.get("min_updates") or _AI_MODEL_MIN_UPDATES))
    threshold = max(0.01, float(_AI_MODEL_REGISTRY.get("drift_threshold") or _AI_MODEL_DRIFT_THRESHOLD))
    if updates < min_updates:
        return None
    if updates % check_every != 0:
        return None
    baseline = _AI_MODEL_REGISTRY.get("baseline_vector")
    if not isinstance(baseline, dict):
        baseline = {}
    current = _profile_vector_from_store(_AI_PROFILE_STORE)
    composite, rel_l1, churn = _model_drift_score(baseline, current)
    _AI_MODEL_REGISTRY["last_drift_score"] = round(composite, 6)
    _AI_MODEL_REGISTRY["last_rel_l1"] = round(rel_l1, 6)
    _AI_MODEL_REGISTRY["last_churn"] = round(churn, 6)
    if composite < threshold:
        _persist_ai_model_registry()
        return None
    current_id = str(_AI_MODEL_REGISTRY.get("current_model_id") or "legacy_default")
    next_id = _timestamp_model_id()
    next_path = _AI_MODEL_DIR / f"{next_id}.json"
    _AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    _AI_PROFILE_STORE.path = next_path
    _AI_PROFILE_STORE.save()
    models = _AI_MODEL_REGISTRY.get("models")
    if not isinstance(models, dict):
        models = {}
    models[next_id] = _create_registry_entry(next_id, next_path, parent_id=current_id, auto_created=True)
    _AI_MODEL_REGISTRY["models"] = models
    _AI_MODEL_REGISTRY["current_model_id"] = next_id
    _AI_MODEL_REGISTRY["active_path"] = str(next_path)
    _AI_MODEL_REGISTRY["baseline_vector"] = current
    _AI_MODEL_REGISTRY["updates_since_snapshot"] = 0
    _AI_MODEL_REGISTRY["last_auto_model_id"] = next_id
    _persist_ai_model_registry()
    ai_hybrid.set_profile_store_path(next_path, save_current=False, load=True)
    return {
        "created": True,
        "model_id": next_id,
        "parent_id": current_id,
        "drift_score": round(composite, 6),
        "rel_l1": round(rel_l1, 6),
        "churn": round(churn, 6),
    }


def register_ai_profile_update() -> Optional[Dict[str, Any]]:
    _AI_MODEL_REGISTRY["total_updates"] = int(_AI_MODEL_REGISTRY.get("total_updates") or 0) + 1
    _AI_MODEL_REGISTRY["updates_since_snapshot"] = int(_AI_MODEL_REGISTRY.get("updates_since_snapshot") or 0) + 1
    result = _checkpoint_ai_model_if_needed()
    if result is None:
        _persist_ai_model_registry()
    return result


def _summed_bucket_from_vector(vector: Dict[str, float], bucket_name: str) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    marker = f"|{bucket_name}|"
    for key, raw in vector.items():
        if marker not in key:
            continue
        bucket_key = key.split(marker, 1)[1]
        totals[bucket_key] = totals.get(bucket_key, 0.0) + float(raw or 0.0)
    return totals


def _normalized_bucket(values: Dict[str, float]) -> Dict[str, float]:
    total = sum(abs(float(v or 0.0)) for v in values.values())
    if total <= 1e-9:
        return {}
    return {key: float(value) / total for key, value in values.items()}


def _top_bucket_keys(values: Dict[str, float], *, limit: int = 3) -> List[str]:
    ranked = sorted(values.items(), key=lambda item: abs(float(item[1] or 0.0)), reverse=True)
    return [str(key) for key, value in ranked[: max(1, int(limit))] if abs(float(value or 0.0)) > 1e-9]


def _describe_ai_model_style(vector: Dict[str, float]) -> List[str]:
    action = _normalized_bucket(_summed_bucket_from_vector(vector, "action_type"))
    risk = _normalized_bucket(_summed_bucket_from_vector(vector, "risk_tolerance"))
    target = _normalized_bucket(_summed_bucket_from_vector(vector, "target_pref"))
    tags: List[str] = []
    if action.get("attack", 0.0) >= 0.62:
        tags.append("Aggressive")
    if action.get("defend", 0.0) >= 0.48:
        tags.append("Defensive")
    if risk.get("retreats", 0.0) >= 0.55:
        tags.append("Switch-prone")
    if risk.get("stays_in_danger", 0.0) >= 0.55:
        tags.append("Risk-tolerant")
    if target.get("lowest_hp", 0.0) >= 0.55:
        tags.append("Finisher")
    if target.get("nearest", 0.0) >= 0.55:
        tags.append("Position-first")
    return tags or ["Balanced"]


def _compare_bucket(base: Dict[str, float], current: Dict[str, float], key: str) -> float:
    return float(current.get(key, 0.0)) - float(base.get(key, 0.0))


def _summarize_ai_model_diff(
    current_vector: Dict[str, float],
    baseline_vector: Dict[str, float],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    current_action = _normalized_bucket(_summed_bucket_from_vector(current_vector, "action_type"))
    base_action = _normalized_bucket(_summed_bucket_from_vector(baseline_vector, "action_type"))
    current_risk = _normalized_bucket(_summed_bucket_from_vector(current_vector, "risk_tolerance"))
    base_risk = _normalized_bucket(_summed_bucket_from_vector(baseline_vector, "risk_tolerance"))
    current_target = _normalized_bucket(_summed_bucket_from_vector(current_vector, "target_pref"))
    base_target = _normalized_bucket(_summed_bucket_from_vector(baseline_vector, "target_pref"))
    strengths: List[str] = []
    cautions: List[str] = []
    changes: List[Dict[str, Any]] = []

    attack_delta = _compare_bucket(base_action, current_action, "attack")
    defend_delta = _compare_bucket(base_action, current_action, "defend")
    retreat_delta = _compare_bucket(base_risk, current_risk, "retreats")
    danger_delta = _compare_bucket(base_risk, current_risk, "stays_in_danger")
    finish_delta = _compare_bucket(base_target, current_target, "lowest_hp")
    nearest_delta = _compare_bucket(base_target, current_target, "nearest")

    if attack_delta >= 0.08:
        strengths.append("leans harder into proactive attacks")
        changes.append({"label": "More attacks", "delta": round(attack_delta, 3)})
    elif attack_delta <= -0.08:
        cautions.append("attacks less often than the comparison model")
        changes.append({"label": "Fewer attacks", "delta": round(attack_delta, 3)})
    if defend_delta >= 0.08:
        strengths.append("uses more defensive repositioning and recovery")
        changes.append({"label": "More defensive actions", "delta": round(defend_delta, 3)})
    if retreat_delta >= 0.08:
        strengths.append("is more willing to preserve pieces with switches or retreats")
        changes.append({"label": "More retreats", "delta": round(retreat_delta, 3)})
    elif retreat_delta <= -0.08:
        cautions.append("is less willing to disengage when under pressure")
        changes.append({"label": "Fewer retreats", "delta": round(retreat_delta, 3)})
    if danger_delta >= 0.08:
        strengths.append("holds position more often under threat")
        changes.append({"label": "Stays in danger more", "delta": round(danger_delta, 3)})
    if finish_delta >= 0.08:
        strengths.append("focuses low-HP targets more reliably")
        changes.append({"label": "Targets weakened foes more", "delta": round(finish_delta, 3)})
    if nearest_delta >= 0.08:
        changes.append({"label": "Prioritizes nearest targets more", "delta": round(nearest_delta, 3)})

    current_moves = _summed_bucket_from_vector(current_vector, "move_usage")
    base_moves = _summed_bucket_from_vector(baseline_vector, "move_usage")
    move_deltas = []
    for key in set(current_moves) | set(base_moves):
        delta = float(current_moves.get(key, 0.0)) - float(base_moves.get(key, 0.0))
        if abs(delta) > 0.01:
            move_deltas.append((abs(delta), key, delta))
    move_deltas.sort(reverse=True)
    for _, move_name, delta in move_deltas[:3]:
        changes.append(
            {
                "label": f"Move tendency: {move_name}",
                "delta": round(delta, 3),
            }
        )

    return strengths[:4], cautions[:4], changes[:6]


def _analyze_ai_model(model_id: str, *, models: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rows = models if isinstance(models, dict) else (_AI_MODEL_REGISTRY.get("models") if isinstance(_AI_MODEL_REGISTRY.get("models"), dict) else {})
    entry = rows.get(model_id) if isinstance(rows, dict) else None
    if not isinstance(entry, dict):
        return {}
    path = Path(str(entry.get("path") or ""))
    current_vector = _load_profile_vector_from_path(path)
    parent_id = str(entry.get("parent_id") or "").strip()
    baseline_id = parent_id or str(_AI_MODEL_REGISTRY.get("current_model_id") or "").strip()
    if baseline_id == model_id:
        baseline_id = ""
    baseline_vector: Dict[str, float] = {}
    if baseline_id and isinstance(rows, dict):
        baseline_entry = rows.get(baseline_id)
        if isinstance(baseline_entry, dict):
            baseline_vector = _load_profile_vector_from_path(Path(str(baseline_entry.get("path") or "")))
    styles = _describe_ai_model_style(current_vector)
    strengths, cautions, changes = _summarize_ai_model_diff(current_vector, baseline_vector)
    top_moves = _top_bucket_keys(_summed_bucket_from_vector(current_vector, "move_usage"))
    top_targets = _top_bucket_keys(_summed_bucket_from_vector(current_vector, "target_pref"), limit=2)
    summary_parts = [", ".join(styles)]
    if strengths:
        summary_parts.append(f"Best at {strengths[0]}.")
    elif top_moves:
        summary_parts.append(f"Tends to repeat {top_moves[0]}.")
    if cautions:
        summary_parts.append(f"Watch for: {cautions[0]}.")
    return {
        "model_id": model_id,
        "compare_to_id": baseline_id,
        "styles": styles,
        "summary": " ".join(part for part in summary_parts if part).strip(),
        "strengths": strengths,
        "cautions": cautions,
        "top_moves": top_moves,
        "top_targets": top_targets,
        "top_changes": changes,
        "analysis_engine": "heuristic_ai_profile_analysis_v1",
    }


def list_ai_models() -> Dict[str, Any]:
    models = _AI_MODEL_REGISTRY.get("models")
    if not isinstance(models, dict):
        models = {}
    ratings_payload = model_ratings.status(_AI_MODEL_RATING_STORE, models=models)
    ratings_map = {
        str(entry.get("model_id") or ""): entry
        for entry in list(ratings_payload.get("ratings") or [])
        if isinstance(entry, dict)
    }
    rows = []
    current_id = str(_AI_MODEL_REGISTRY.get("current_model_id") or "")
    for model_id, entry in models.items():
        if not isinstance(entry, dict):
            continue
        analysis = _analyze_ai_model(model_id, models=models)
        rows.append(
            {
                "id": model_id,
                "path": str(entry.get("path") or ""),
                "created_at": str(entry.get("created_at") or ""),
                "parent_id": str(entry.get("parent_id") or ""),
                "auto_created": bool(entry.get("auto_created")),
                "selected": model_id == current_id,
                "analysis": analysis,
                "rating": ratings_map.get(model_id, {}),
            }
        )
    rows.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    selected_analysis = None
    for row in rows:
        if row.get("selected"):
            selected_analysis = row.get("analysis")
            break
    return {
        "current_model_id": current_id,
        "active_path": str(_AI_MODEL_REGISTRY.get("active_path") or ""),
        "models": rows,
        "selected_analysis": selected_analysis,
        "ratings": list(ratings_payload.get("ratings") or []),
        "math": {
            "drift_formula": "score = 0.8*relative_L1 + 0.2*key_churn",
            "relative_L1": float(_AI_MODEL_REGISTRY.get("last_rel_l1") or 0.0),
            "key_churn": float(_AI_MODEL_REGISTRY.get("last_churn") or 0.0),
            "score": float(_AI_MODEL_REGISTRY.get("last_drift_score") or 0.0),
            "threshold": float(_AI_MODEL_REGISTRY.get("drift_threshold") or _AI_MODEL_DRIFT_THRESHOLD),
            "min_updates": int(_AI_MODEL_REGISTRY.get("min_updates") or _AI_MODEL_MIN_UPDATES),
            "check_every": int(_AI_MODEL_REGISTRY.get("check_every") or _AI_MODEL_CHECK_EVERY),
            "updates_since_snapshot": int(_AI_MODEL_REGISTRY.get("updates_since_snapshot") or 0),
            "total_updates": int(_AI_MODEL_REGISTRY.get("total_updates") or 0),
        },
    }


def select_ai_model(model_id: str) -> Dict[str, Any]:
    wanted = str(model_id or "").strip()
    if not wanted:
        raise ValueError("model_id is required")
    models = _AI_MODEL_REGISTRY.get("models")
    if not isinstance(models, dict) or wanted not in models:
        raise ValueError(f"Unknown AI model: {wanted}")
    entry = models[wanted]
    path = Path(str(entry.get("path") or ""))
    if not path.exists():
        raise ValueError(f"Model file not found: {path}")
    ai_hybrid.set_profile_store_path(path, save_current=True, load=True)
    global _AI_PROFILE_STORE
    _AI_PROFILE_STORE = ai_hybrid.get_profile_store()
    _AI_MODEL_REGISTRY["current_model_id"] = wanted
    _AI_MODEL_REGISTRY["active_path"] = str(path)
    _AI_MODEL_REGISTRY["baseline_vector"] = _profile_vector_from_store(_AI_PROFILE_STORE)
    _AI_MODEL_REGISTRY["updates_since_snapshot"] = 0
    _persist_ai_model_registry()
    return list_ai_models()


def ai_model_status() -> Dict[str, Any]:
    return list_ai_models()


def ai_record_battle_outcome(
    *,
    winner_is_ai: Optional[bool],
    ai_mode: str = "player",
) -> Dict[str, Any]:
    current_model_id = str(_AI_MODEL_REGISTRY.get("current_model_id") or "").strip()
    if not current_model_id:
        return model_ratings.status(_AI_MODEL_RATING_STORE)
    opponent_id = "player_field" if ai_mode != "ai" else ""
    if ai_mode == "ai":
        return model_ratings.status(_AI_MODEL_RATING_STORE)
    if winner_is_ai is None:
        if opponent_id:
            model_ratings.record_result(
                _AI_MODEL_RATING_STORE,
                winner_model_id=current_model_id,
                loser_model_id=opponent_id,
                draw=True,
            )
        return model_ratings.status(_AI_MODEL_RATING_STORE)
    if winner_is_ai:
        model_ratings.record_result(
            _AI_MODEL_RATING_STORE,
            winner_model_id=current_model_id,
            loser_model_id=opponent_id,
        )
    else:
        model_ratings.record_result(
            _AI_MODEL_RATING_STORE,
            winner_model_id=opponent_id,
            loser_model_id=current_model_id,
        )
    return model_ratings.status(_AI_MODEL_RATING_STORE)


def ai_learning_status(battle: Optional["RulesBattleState"] = None) -> Dict[str, Any]:
    math = ai_model_status().get("math") if isinstance(ai_model_status(), dict) else {}
    payload = {
        "current_model_id": str(_AI_MODEL_REGISTRY.get("current_model_id") or ""),
        "active_path": str(_AI_MODEL_REGISTRY.get("active_path") or ""),
        "last_auto_model_id": str(_AI_MODEL_REGISTRY.get("last_auto_model_id") or ""),
        "total_updates": int(_AI_MODEL_REGISTRY.get("total_updates") or 0),
        "updates_since_snapshot": int(_AI_MODEL_REGISTRY.get("updates_since_snapshot") or 0),
        "drift_score": float(_AI_MODEL_REGISTRY.get("last_drift_score") or 0.0),
        "drift_threshold": float(_AI_MODEL_REGISTRY.get("drift_threshold") or _AI_MODEL_DRIFT_THRESHOLD),
        "relative_l1": float(_AI_MODEL_REGISTRY.get("last_rel_l1") or 0.0),
        "key_churn": float(_AI_MODEL_REGISTRY.get("last_churn") or 0.0),
        "check_every": int(_AI_MODEL_REGISTRY.get("check_every") or _AI_MODEL_CHECK_EVERY),
        "min_updates": int(_AI_MODEL_REGISTRY.get("min_updates") or _AI_MODEL_MIN_UPDATES),
    }
    if isinstance(math, dict):
        payload["math"] = dict(math)
    if battle is not None:
        learning = getattr(battle, "_ai_learning", None)
        if isinstance(learning, dict):
            payload["battle"] = copy.deepcopy(learning)
    return payload


@dataclass
class BattleRecord:
    """Summary of a played duel."""

    matchup: MatchupSpec
    turns: List[str] = field(default_factory=list)
    winner: str = ""


class TextBattleSession:
    """Drive a match plan with manual move selection."""

    def __init__(
        self,
        plan: MatchPlan,
        console: Optional[Console] = None,
        viewer_enabled: bool = False,
        spectator_enabled: bool = False,
    ) -> None:
        self.plan = plan
        self.console = console or Console(force_terminal=True)
        self.engine = MatchEngine(plan)
        self._live: Optional[Live] = None
        self._layout: Optional[Layout] = None
        self._log_renderables = deque(maxlen=200)
        self._live_battle: Optional[RulesBattleState] = None
        self._pending_prompt: Optional[str] = None
        self._last_input: Optional[str] = None
        self._fast_forward: bool = False
        self._spectator_mode: bool = False
        self._spectator_enabled: bool = spectator_enabled
        self._viewer_enabled: bool = viewer_enabled
        self._viewer_conn = None
        self._viewer_listener: Optional[Listener] = None
        self._last_announced_index: int = 0

    def play(self, selector: Optional[MoveSelector] = None) -> List[BattleRecord]:
        """Play every matchup in the plan."""
        if selector is not None:
            return self._play_legacy(selector)
        return self._play_interactive()

    def _play_legacy(self, selector: MoveSelector) -> List[BattleRecord]:
        selector_cb = selector or self._prompt_for_move
        records: List[BattleRecord] = []
        self._print(
            f"[bold]Interactive Mode[/bold]: {len(self.plan.matchups)} duel(s), "
            f"weather={self.plan.weather}"
        )
        for idx, matchup in self.plan.each_matchup():
            record = self._play_duel(idx, matchup, selector_cb)
            records.append(record)
        return records

    def _play_interactive(self) -> List[BattleRecord]:
        records: List[BattleRecord] = []
        self._print(
            f"[bold]Interactive Grid Mode[/bold]: {len(self.plan.matchups)} duel(s), "
            f"weather={self.plan.weather}, grid={self.plan.grid.width}x{self.plan.grid.height}"
        )
        self._print_interactive_help()
        for idx, matchup in self.plan.each_matchup():
            record = self._play_duel_interactive(idx, matchup)
            records.append(record)
        return records

    def _print(self, *args: object, **kwargs: object) -> None:
        if self._live is None:
            self.console.print(*args, **kwargs)
            return
        renderable: object
        if len(args) == 1 and not kwargs:
            renderable = args[0]
        else:
            renderable = Text.from_markup(" ".join(str(arg) for arg in args))
        self._log_renderables.append(renderable)
        if self._live_battle is not None:
            self._refresh_live(self._live_battle)

    def _input(self, prompt: str) -> str:
        if self._live is None:
            return self.console.input(prompt)
        self._pending_prompt = prompt
        self._last_input = None
        if self._live_battle is not None:
            self._refresh_live(self._live_battle)
        self._live.stop()
        value = ""
        try:
            value = self.console.input(prompt)
        finally:
            self._pending_prompt = None
            self._last_input = value
            self._live.start()
            if self._live_battle is not None:
                self._refresh_live(self._live_battle)
        return value

    def _prompt_out_of_turn(self, payload: Dict[str, object]) -> bool:
        battle = self._live_battle
        actor_id = str(payload.get("actor_id") or "")
        label = str(payload.get("label") or "Interrupt")
        trigger = str(payload.get("trigger_move") or payload.get("move") or "")
        actor_label = actor_id
        if battle is not None and actor_id:
            actor_label = self._actor_label(battle, actor_id)
        prompt = f"[bold]Out-of-turn[/bold] {label} available for {actor_label}"
        if trigger:
            prompt += f" (vs {trigger})"
        prompt += ". Trigger? [y/N]: "
        choice = self._input(prompt).strip().lower()
        return choice in {"y", "yes"}

    def _build_live_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split_row(
            Layout(name="left", ratio=3),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(name="status", ratio=2),
            Layout(name="grid", ratio=3),
        )
        layout["right"].split_column(
            Layout(name="log", ratio=4),
            Layout(name="info", ratio=1),
        )
        return layout

    def _refresh_live(self, battle: RulesBattleState) -> None:
        if self._layout is None:
            return
        status = self._build_status_renderable(battle)
        grid = self._build_grid_renderable(battle)
        if self._log_renderables:
            log_group = Group(*list(self._log_renderables)[-80:])
        else:
            log_group = Text("Awaiting actions...", style="dim")
        info = self._build_info_renderable(battle)
        self._layout["status"].update(Panel(status, title="Status"))
        self._layout["grid"].update(Panel(grid, title="Grid"))
        self._layout["log"].update(Panel(log_group, title="Log"))
        self._layout["info"].update(Panel(info, title="Info"))

    def _print_interactive_help(self) -> None:
        context = str(self.plan.battle_context or "").strip().lower()
        active_slots = int(self.plan.active_slots) if self.plan.active_slots else 1
        self._print("[bold]Quick help[/bold]")
        self._print(
            f"Active slots per side: {active_slots}. Others start on the bench."
        )
        self._print(
            "Before round 1, pick which Pokemon start active for free."
        )
        self._print(
            "Trainer turns let you switch or use items to support the team."
        )
        if context == "league":
            self._print(
                "League: trainers declare actions from slow to fast; declarations "
                "resolve before Pokemon act."
            )
        else:
            self._print("Full contact: normal initiative order.")
        self._print(
            "Action economy: Standard + Shift + Swift each turn. Free actions are unlimited."
        )
        self._print(
            "Tips: Delay acts later in the round. Trade converts a Standard into "
            "an extra Shift or Swift."
        )
        self._print(
            "Switch with W to swap an active Pokemon with a benched one."
        )
        self._print(
            "Switching is blocked while Trapped, Grappled, or Immobilized."
        )
        self._print("")

    def _play_duel(
        self,
        index: int,
        matchup: MatchupSpec,
        selector: MoveSelector,
    ) -> BattleRecord:
        you_cb, foe_cb = self.engine.build_pair(matchup)
        terrain = self.engine.build_terrain(self.plan.weather)
        rng = random.Random(self.engine.seed_for_match(index))
        record = BattleRecord(matchup=matchup)
        title = matchup.label or f"Duel {index}"
        self.console.rule(f"{title}")
        self._render_status(you_cb, foe_cb)
        while you_cb.hp > 0 and foe_cb.hp > 0:
            move = selector(you_cb.mon.known_moves, matchup, you_cb, foe_cb)
            event = format_move_event("Player", you_cb, foe_cb, move, terrain, rng)
            record.turns.append(event["text"])
            self._print(event["text"])
            if foe_cb.hp <= 0:
                break
            ai_move = ptu_engine.best_move_by_ev(foe_cb, you_cb)        
            event = format_move_event("AI", foe_cb, you_cb, ai_move, terrain, rng)
            record.turns.append(event["text"])
            self._print(event["text"])
            if you_cb.hp <= 0:
                break
            self._render_status(you_cb, foe_cb)
        record.winner = "Player" if you_cb.hp > 0 else "AI"
        self._print(
            f"[green]{you_cb.mon.name}[/green] stands victorious!"
            if record.winner == "Player"
            else f"[red]{foe_cb.mon.name}[/red] overwhelms your team!"
        )
        self._print("")
        return record

    def _render_status(self, you_cb: ptu_engine.Combatant, foe_cb: ptu_engine.Combatant) -> None:
        table = Table("Side", "Pokemon", "HP", "Types", box=None)
        table.add_row(
            "You",
            you_cb.mon.name,
            f"{you_cb.hp}/{you_cb.mon.max_hp()}",
            ", ".join(you_cb.mon.types),
        )
        table.add_row(
            "Foe",
            foe_cb.mon.name,
            f"{foe_cb.hp}/{foe_cb.mon.max_hp()}",
            ", ".join(foe_cb.mon.types),
        )
        self._print(table)

    def _prompt_for_move(
        self,
        moves: Sequence[ptu_engine.Move],
        matchup: MatchupSpec,
        you_cb: ptu_engine.Combatant,
        foe_cb: ptu_engine.Combatant,
    ) -> ptu_engine.Move:
        del matchup, you_cb, foe_cb  # unused in prompt mode
        table = Table("No.", "Move", "Type", "Category", "Range", "AC", "DB", "Dice", "Freq", "Effects")
        for idx, move in enumerate(moves, start=1):
            table.add_row(
                str(idx),
                move.name,
                move.type,
                move.category,
                self._format_range_label(move),
                str(move.ac if move.ac is not None else "-"),
                str(move.db),
                self._format_dice_label(move.db),
                move.freq,
                self._short_effects(move.effects_text),
            )
        self._print(table)
        while True:
            raw = self._input(f"Choose your move [1-{len(moves)}]: ").strip()
            if not raw:
                continue
            if raw.isdigit():
                choice = int(raw)
                if 1 <= choice <= len(moves):
                    return moves[choice - 1]
            self._print("[yellow]Invalid choice. Enter the move number.[/yellow]")

    # ----- Interactive path -----

    def _play_duel_interactive(self, index: int, matchup: MatchupSpec) -> BattleRecord:
        battle = self._build_battle_state(index, matchup)
        record = BattleRecord(matchup=matchup)
        title = matchup.label or f"Duel {index}"
        self.console.rule(f"{title}")
        if self._viewer_enabled:
            self._start_viewer(battle)
        self._layout = None
        self._spectator_mode = self._spectator_enabled and not self._has_player_controller(battle)
        self._fast_forward = False
        history: List[RulesBattleState] = [self._clone_battle_state(battle)]
        history_index = 0
        if battle.log:
            self._announce_last_event(battle, record)
        self._send_viewer_snapshot(battle)
        while not self._battle_finished(battle):
            self._live_battle = battle
            if self._spectator_mode and not self._fast_forward:
                action = self._spectator_prompt()
                if action == "quit":
                    break
                if action == "toggle":
                    self._fast_forward = True
                    self._print("[cyan]Fast-forward enabled.[/cyan]")
                    continue
                if action == "back":
                    if history_index > 0:
                        history_index -= 1
                        battle = self._clone_battle_state(history[history_index])
                        self._print(f"[cyan]Rewound to round {battle.round}.[/cyan]")
                        self._send_viewer_snapshot(battle)
                    continue
                if action == "replay":
                    history_index = 0
                    battle = self._clone_battle_state(history[0])
                    self._log_renderables.clear()
                    self._print("[cyan]Replaying from the start.[/cyan]")
                    self._send_viewer_snapshot(battle)
                    continue
            entry = battle.advance_turn()
            if entry is None:
                break
            self._announce_last_event(battle, record)
            controller_kind = self._controller_kind_for_actor(battle, entry.actor_id)
            if battle.is_trainer_actor_id(entry.actor_id):
                if controller_kind == "player":
                    self._player_trainer_turn(battle, record, entry.actor_id)
                else:
                    self._ai_trainer_turn(battle, record, entry.actor_id)
            else:
                if controller_kind == "player":
                    self._player_turn(battle, record, entry.actor_id)
                else:
                    try:
                        self._ai_turn(battle, record, entry.actor_id)
                    except ValueError as exc:
                        self._print(f"[red]{exc}[/red]")
                        self._ai_skip_turn(battle, entry.actor_id, record)
            battle.end_turn()
            if self._battle_finished(battle):
                break
            if self._spectator_mode:
                if history_index < len(history) - 1:
                    history = history[: history_index + 1]
                history.append(self._clone_battle_state(battle))
                history_index += 1
            self._send_viewer_snapshot(battle)
        self._send_viewer_snapshot(battle)
        self._stop_viewer()
        self._layout = None
        self._spectator_mode = False
        alive = self._alive_teams(battle)
        if not alive:
            record.winner = "Draw"
            self._print("[yellow]All combatants have fainted.[/yellow]")
        else:
            winning_team = next(iter(alive))
            if self._team_has_player(battle, winning_team):
                record.winner = "Player"
                self._print("[green]You stand victorious![/green]")
            else:
                record.winner = winning_team
                self._print("[red]You were defeated.[/red]")
        self._print("")
        return record

    def _build_battle_state(self, index: int, matchup: MatchupSpec) -> RulesBattleState:
        grid_spec = self.plan.grid
        tiles: Dict[Tuple[int, int], Dict[str, object]] = {}
        for coord, metadata in grid_spec.tiles.items():
            if isinstance(metadata, dict):
                tile_meta = dict(metadata)
            else:
                tile_meta = {"type": str(metadata) if metadata is not None else ""}
            tile_type = tile_meta.get("type")
            if tile_type is not None and not isinstance(tile_type, str):
                tile_meta["type"] = str(tile_type)
            tiles[coord] = tile_meta
        grid_state = RulesGridState(
            width=grid_spec.width,
            height=grid_spec.height,
            blockers=set(grid_spec.blockers),
            tiles=tiles,
        )
        sides = matchup.sides_or_default()
        trainers: Dict[str, RulesTrainerState] = {}
        pokemon_states: Dict[str, RulesPokemonState] = {}
        active_positions: Dict[str, List[Tuple[int, int]]] = {}
        occupied: Set[Tuple[int, int]] = set()
        rng = random.Random((self.plan.seed or 0) + index * 101)
        for side in sides:
            trainer_id = side.identifier or f"trainer-{len(trainers) + 1}"
            trainer = RulesTrainerState(
                identifier=trainer_id,
                name=side.name,
                initiative_modifier=side.initiative_modifier,
                speed=side.speed,
                skills=dict(side.skills),
                save_bonus_base=side.save_bonus,
                evasion_phys=side.evasion_phys,
                evasion_spec=side.evasion_spec,
                evasion_spd=side.evasion_spd,
                controller_kind=side.controller,
                team=side.team or side.controller,
                ai_level=side.ai_level,
                trainer_class=side.trainer_class.to_dict() if side.trainer_class else {},
                features=[feature.to_dict() for feature in side.trainer_features],
                edges=[edge.to_dict() for edge in side.trainer_edges],
                feature_resources=dict(side.feature_resources),
            )
            trainers[trainer_id] = trainer
            base = self._default_origin_for_side(side, grid_state)
            positions = list(side.start_positions)
            active_limit = max(1, int(self.plan.active_slots))
            active_count = min(len(side.pokemon), active_limit)
            needed = active_count
            if grid_state is None:
                auto_positions: List[Tuple[int, int]] = [(0, idx) for idx in range(needed)]
            else:
                auto_positions = self._allocate_positions(grid_state, base, needed, positions, occupied)
            active_positions[trainer_id] = list(auto_positions)
            for idx, spec in enumerate(side.pokemon):
                is_active = idx < active_count
                pos = auto_positions[min(idx, len(auto_positions) - 1)] if is_active else None
                mon_id = f"{trainer_id}-{idx + 1}"
                pokemon_states[mon_id] = RulesPokemonState(
                    spec=spec,
                    controller_id=trainer_id,
                    position=pos,
                    active=is_active,
                )
                if pos is not None:
                    occupied.add(pos)
        self._choose_starting_pokemon(trainers, pokemon_states, active_positions)
        battle = RulesBattleState(
            trainers=trainers,
            pokemon=pokemon_states,
            weather=self.plan.weather,
            grid=grid_state,
            battle_context=self.plan.battle_context,
            active_slots=self.plan.active_slots,
            rng=rng,
        )
        self._live_battle = battle
        battle.out_of_turn_prompt = self._prompt_out_of_turn
        battle.start_round()
        return battle

    def _choose_starting_pokemon(
        self,
        trainers: Dict[str, RulesTrainerState],
        pokemon_states: Dict[str, RulesPokemonState],
        active_positions: Dict[str, List[Tuple[int, int]]],
    ) -> None:
        active_slots = max(1, int(self.plan.active_slots or 1))
        for trainer_id, trainer in trainers.items():
            if trainer.controller_kind != "player":
                continue
            roster = [cid for cid, mon in pokemon_states.items() if mon.controller_id == trainer_id]
            if len(roster) <= active_slots:
                continue
            positions = list(active_positions.get(trainer_id, []))
            label = trainer.name or trainer.identifier
            self._print(f"\nChoose starting Pokemon for {label}:")
            for idx, cid in enumerate(roster, start=1):
                mon = pokemon_states[cid]
                note = " (active)" if mon.active else ""
                self._print(f"{idx}) {mon.spec.name or mon.spec.species}{note}")
            raw = self._input(
                f"Select {active_slots} by number (comma-separated, blank keeps default): "
            ).strip()
            if not raw:
                continue
            tokens = [token for token in raw.replace(",", " ").split() if token]
            selected: List[str] = []
            for token in tokens:
                if not token.isdigit():
                    continue
                choice = int(token)
                if 1 <= choice <= len(roster):
                    cid = roster[choice - 1]
                    if cid not in selected:
                        selected.append(cid)
            if not selected:
                continue
            if len(selected) > active_slots:
                self._print("[yellow]Too many selections; using the first choices.[/yellow]")
                selected = selected[:active_slots]
            if len(selected) < active_slots:
                for cid in roster:
                    if cid not in selected:
                        selected.append(cid)
                    if len(selected) >= active_slots:
                        break
            for cid in roster:
                mon = pokemon_states[cid]
                mon.active = False
                mon.position = None
            for idx, cid in enumerate(selected):
                mon = pokemon_states[cid]
                mon.active = True
                if idx < len(positions):
                    mon.position = positions[idx]

    def _battle_finished(self, battle: RulesBattleState) -> bool:
        return len(self._alive_teams(battle)) <= 1

    def _player_turn(self, battle: RulesBattleState, record: BattleRecord, actor_id: str) -> None:
        if battle.phase == RulesTurnPhase.START:
            battle.advance_phase()  # move into the Command phase
        if self._resolve_pending_setups(battle, record, actor_id):
            return
        moved = False
        while True:
            if battle.current_actor_id is None:
                return
            budget_text = battle.action_budget_summary(actor_id)
            if budget_text:
                self._print(f"[cyan]{budget_text}[/cyan]")
            choice = self._input("[bold]Action[/bold] ([C]heck stats, [M]ove, [A]ttack, [B]attle maneuver, Crea[V]tive action, [R]est, S[W]itch, [I]tems, [G]rid info, [D]elay, [T]rade action, [S]kip): ").strip().lower()
            if choice in {"f", "fast", "fast-forward"}:
                self._print("[yellow]Fast-forward is only available in spectator mode.[/yellow]")
                continue
            if choice in {"g", "grid"}:
                self._render_grid(battle)
                continue
            if choice in {"d", "delay"}:
                if self._handle_delay(battle, actor_id, record):
                    return
                continue
            if choice in {"t", "trade"}:
                if self._handle_trade(battle, actor_id, record):
                    continue
                continue
            if choice in {"m", "move"}:
                if moved:
                    self._print("[yellow]You've already moved this turn.[/yellow]")
                    continue
                if not self._handle_shift(battle, actor_id, record):
                    continue
                moved = True
                continue
            if choice in {"r", "rest", "breather"}:
                self._handle_breather(battle, actor_id, record)
                continue
            if choice in {"w", "switch"}:
                if self._handle_switch(battle, actor_id, record):
                    self._advance_to_end_phase(battle)
                    return
                continue
            if choice in {"s", "skip"}:
                self._handle_skip_turn(battle, actor_id, record)
                return
            if choice in {"c", "check", "stats"}:
                self._render_actor_stats(battle, actor_id)
                continue
            if choice in {"", "a", "attack"}:
                self._handle_attack(battle, actor_id, record)
                continue
            if choice in {"b", "battle", "maneuver"}:
                self._handle_maneuver(battle, actor_id, record)
                continue
            if choice in {"v", "creative", "stunt"}:
                self._handle_creative_action(battle, actor_id, record)
                continue
            if choice in {"i", "item", "items"}:
                self._handle_items(battle, actor_id, record)
                continue
            self._print("[yellow]Unknown action. Choose M, A, B, W, I, G, D, T, or S.[/yellow]")

    def _player_trainer_turn(
        self, battle: RulesBattleState, record: BattleRecord, trainer_id: str
    ) -> None:
        if battle.phase == RulesTurnPhase.START:
            battle.advance_phase()
        while True:
            if battle.current_actor_id is None:
                return
            budget_text = battle.action_budget_summary(trainer_id)
            if budget_text:
                self._print(f"[cyan]{budget_text}[/cyan]")
            choice = self._input(
                "[bold]Trainer Action[/bold] ([S]witch, [C]heck teams, [G]rid, [P]ass): "
            ).strip().lower()
            if choice in {"f", "fast", "fast-forward"}:
                self._print("[yellow]Fast-forward is only available in spectator mode.[/yellow]")
                continue
            if choice in {"g", "grid"}:
                self._render_grid(battle)
                continue
            if choice in {"c", "check", "team", "teams", "status"}:
                self._render_status_interactive(battle)
                continue
            if choice in {"s", "switch"}:
                if self._handle_trainer_switch(battle, trainer_id, record):
                    return
                continue
            if choice in {"p", "pass", "skip", ""}:
                self._handle_skip_turn(battle, trainer_id, record)
                return
            self._print("[yellow]Unknown action. Choose S, C, G, or P.[/yellow]")

    def _ai_turn(self, battle: RulesBattleState, record: BattleRecord, actor_id: str) -> None:
        log_len = len(battle.log)
        ai_level = "standard"
        candidate_snapshot: Optional[Dict[str, Any]] = None
        fallback_reason: Optional[str] = None
        ai_choice_info: Dict[str, Any] = {}
        try:
            if battle.phase == RulesTurnPhase.START:
                battle.advance_phase()
                if battle.current_actor_id is None:
                    self._announce_last_event(battle, record)
                    return
            if self._resolve_pending_setups(battle, record, actor_id):
                return
            actor_state = battle.pokemon.get(actor_id)
            if actor_state and actor_state.fainted:
                bench = [
                    cid
                    for cid, mon in battle.pokemon.items()
                    if mon.controller_id == actor_state.controller_id
                    and not mon.active
                    and mon.hp is not None
                    and mon.hp > 0
                ]
                if bench:
                    action = SwitchAction(actor_id=actor_id, replacement_id=bench[0])
                    try:
                        self._resolve_selected_action(battle, action)
                        self._record_ai_action_learning(battle, actor_id, action)
                        self._publish_ai_turn_diagnostics(
                            battle,
                            actor_id,
                            action=action,
                            reason="forced_switch",
                            source="fainted_auto_switch",
                            ai_level=ai_level,
                            candidate_snapshot=candidate_snapshot,
                            fallback_reason=fallback_reason,
                            info=ai_choice_info,
                        )
                        self._announce_last_event(battle, record)
                        self._advance_to_end_phase(battle)
                    except ValueError:
                        fallback_reason = "Forced switch failed validation."
                        self._ai_skip_turn(battle, actor_id, record)
                    return
            if actor_state and actor_state.equipped_weapon() is None:
                for idx, item in enumerate(actor_state.spec.items):
                    if self._is_weapon_item(item):
                        action = EquipWeaponAction(actor_id=actor_id, item_index=idx)
                        try:
                            self._resolve_selected_action(battle, action)
                        except ValueError:
                            break
                        self._record_ai_action_learning(battle, actor_id, action)
                        self._publish_ai_turn_diagnostics(
                            battle,
                            actor_id,
                            action=action,
                            reason="equip_weapon",
                            source="weapon_auto_equip",
                            ai_level=ai_level,
                            candidate_snapshot=candidate_snapshot,
                            fallback_reason=fallback_reason,
                            info=ai_choice_info,
                        )
                        self._announce_last_event(battle, record)
                        self._advance_to_end_phase(battle)
                        return
            trainer = battle.trainers.get(actor_state.controller_id) if actor_state else None
            ai_level = (trainer.ai_level if trainer else "standard") or "standard"
            item_action = self._ai_choose_item_action(battle, actor_id)
            emergency_shift = royale_policy.choose_emergency_shift(battle, actor_id)
            mcts_action, mcts_info = mcts_policy.choose_action(
                battle,
                actor_id,
                ai_level=ai_level,
                profile_store=_AI_PROFILE_STORE,
            )
            hybrid_action, hybrid_info = ai_hybrid.choose_action(
                battle,
                actor_id,
                ai_level=ai_level,
                profile_store=_AI_PROFILE_STORE,
            )
            grapple_choice = rules_ai.choose_grapple_action(battle, actor_id)
            grapple_action = None
            grapple_info: Dict[str, Any] = {}
            if grapple_choice:
                action_kind, destination = grapple_choice
                status = battle.grapple_status(actor_id)
                target_id = status["other_id"] if status else None
                grapple_action = GrappleAction(
                    actor_id=actor_id,
                    action_kind=action_kind,
                    target_id=target_id,
                    destination=destination,
                )
                grapple_info = {"reason": "grapple"}
            action, info = behavior_tree_policy.choose_action(
                behavior_tree_policy.BTContext(
                    actor_id=actor_id,
                    ai_level=ai_level,
                    item_action=item_action,
                    emergency_shift=emergency_shift,
                    mcts_action=mcts_action,
                    mcts_info=dict(mcts_info or {}),
                    hybrid_action=hybrid_action,
                    hybrid_info=dict(hybrid_info or {}),
                    grapple_action=grapple_action,
                    grapple_info=grapple_info,
                )
            )
            ai_choice_info = dict(info or {})
            if action is not None:
                action = royale_policy.refine_action(battle, actor_id, action)
                try:
                    self._resolve_selected_action(battle, action)
                    self._record_ai_action_learning(battle, actor_id, action)
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=action,
                        reason=str((info or {}).get("reason") or "bt_select"),
                        source=str((info or {}).get("source") or "py_trees"),
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._announce_last_event(battle, record)
                    if isinstance(action, (ShiftAction, DisengageAction)):
                        if self._ai_try_follow_up_attack(
                            battle,
                            actor_id,
                            record,
                            ai_level=ai_level,
                            candidate_snapshot=candidate_snapshot,
                            fallback_reason=fallback_reason,
                            info=ai_choice_info,
                            source="bt_shift_followup",
                            reason="bt_shift_followup",
                        ):
                            return
                    self._advance_to_end_phase(battle)
                    return
                except ValueError as exc:
                    if emergency_shift is action:
                        fallback_reason = "Royale emergency shift failed validation."
                    else:
                        fallback_reason = f"Behavior-tree action rejected by rules: {exc}"
            if grapple_choice:
                action_kind, destination = grapple_choice
                status = battle.grapple_status(actor_id)
                target_id = status["other_id"] if status else None
                action = GrappleAction(
                    actor_id=actor_id,
                    action_kind=action_kind,
                    target_id=target_id,
                    destination=destination,
                )
                self._resolve_selected_action(battle, action)
                self._record_ai_action_learning(battle, actor_id, action)
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=action,
                    reason="grapple",
                    source="rules_ai_grapple",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._announce_last_event(battle, record)
                self._advance_to_end_phase(battle)
                return
            move, target_id, move_score = rules_ai.choose_best_move(
                battle, actor_id, ai_level=ai_level
            )
            switch_id = self._ai_should_switch(
                battle,
                actor_id,
                target_id,
                move_score,
                ai_level,
            )
            if switch_id:
                action = SwitchAction(actor_id=actor_id, replacement_id=switch_id)
                self._resolve_selected_action(battle, action)
                self._record_ai_action_learning(battle, actor_id, action)
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=action,
                    reason="low_hp_switch",
                    source="rules_switch",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._announce_last_event(battle, record)
                return
            if move is not None and self._ai_should_disengage_for_attack(battle, actor_id, move, target_id):
                disengage_action = self._ai_try_disengage_for_attack(
                    battle,
                    actor_id,
                    record,
                    target_id=target_id,
                )
                if disengage_action:
                    if self._ai_try_follow_up_attack(
                        battle,
                        actor_id,
                        record,
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                        source="rules_disengage_followup",
                        reason="disengage_attack_followup",
                    ):
                        return
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=disengage_action,
                        reason="disengage_for_ranged_attack",
                        source="rules_disengage_setup",
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._advance_to_end_phase(battle)
                    return
            if move is not None and self._ai_should_shift_for_attack(battle, actor_id, move, target_id):
                target_id = self._ai_nearest_opponent(battle, actor_id)
                shift_action = self._ai_try_shift_toward_target(
                    battle, actor_id, record, target_range=None, target_id=target_id
                )
                if shift_action:
                    if self._ai_try_follow_up_attack(
                        battle,
                        actor_id,
                        record,
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                        source="rules_shift_followup",
                        reason="shift_toward_target_followup",
                    ):
                        return
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=shift_action,
                        reason="shift_toward_target",
                        source="rules_shift_setup",
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._advance_to_end_phase(battle)
                    return
            if move is None:
                shift_action = self._ai_try_shift_toward_target(
                    battle, actor_id, record, target_range=None, target_id=None
                )
                if shift_action:
                    if self._ai_try_follow_up_attack(
                        battle,
                        actor_id,
                        record,
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                        source="rules_shift_fallback_followup",
                        reason="no_move_shift_followup",
                    ):
                        return
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=shift_action,
                        reason="no_move_shift",
                        source="rules_shift_fallback",
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._advance_to_end_phase(battle)
                    return
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=None,
                    reason="skip_no_move",
                    source="rules_skip",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._ai_skip_turn(battle, actor_id, record)
                return
            if targeting.move_requires_target(move) and target_id is None:
                shift_action = self._ai_try_shift_toward_target(
                    battle, actor_id, record, target_range=None, target_id=None
                )
                if shift_action:
                    if self._ai_try_follow_up_attack(
                        battle,
                        actor_id,
                        record,
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                        source="rules_shift_targeting_followup",
                        reason="target_missing_shift_followup",
                    ):
                        return
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=shift_action,
                        reason="target_missing_shift",
                        source="rules_shift_targeting",
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._advance_to_end_phase(battle)
                    return
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=None,
                    reason="skip_target_missing",
                    source="rules_skip",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._ai_skip_turn(battle, actor_id, record)
                return
            if battle.current_actor_id is None:
                self._announce_last_event(battle, record)
                return
            action = UseMoveAction(
                actor_id=actor_id,
                move_name=move.name,
                target_id=target_id,
                chosen_type=self._ai_move_chosen_type(battle, actor_id, move),
            )
            try:
                self._resolve_selected_action(battle, action)
            except ValueError as exc:
                fallback_reason = f"Move rejected by rules: {exc}"
                if (move.name or "").strip().lower() != "struggle":
                    struggle_action = UseMoveAction(
                        actor_id=actor_id,
                        move_name="Struggle",
                        target_id=target_id,
                    )
                    try:
                        self._resolve_selected_action(battle, struggle_action)
                    except ValueError:
                        pass
                    else:
                        self._record_ai_action_learning(battle, actor_id, struggle_action)
                        self._publish_ai_turn_diagnostics(
                            battle,
                            actor_id,
                            action=struggle_action,
                            reason="fallback_struggle_after_invalid_move",
                            source="rules_ai_fallback",
                            ai_level=ai_level,
                            candidate_snapshot=candidate_snapshot,
                            fallback_reason=fallback_reason,
                            info=ai_choice_info,
                        )
                        self._announce_last_event(battle, record)
                        if battle.phase == RulesTurnPhase.ACTION:
                            battle.advance_phase()
                        return
                shift_action = self._ai_try_shift_toward_target(
                    battle,
                    actor_id,
                    record,
                    target_range=move.target_range,
                    target_id=target_id,
                )
                if shift_action:
                    if self._ai_try_follow_up_attack(
                        battle,
                        actor_id,
                        record,
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                        source="rules_shift_after_reject_followup",
                        reason="shift_after_invalid_move_followup",
                    ):
                        return
                    self._publish_ai_turn_diagnostics(
                        battle,
                        actor_id,
                        action=shift_action,
                        reason="shift_after_invalid_move",
                        source="rules_shift_after_reject",
                        ai_level=ai_level,
                        candidate_snapshot=candidate_snapshot,
                        fallback_reason=fallback_reason,
                        info=ai_choice_info,
                    )
                    self._advance_to_end_phase(battle)
                    return
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=None,
                    reason="skip_after_invalid_move",
                    source="rules_skip_after_reject",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._ai_skip_turn(battle, actor_id, record)
                return
            self._record_ai_action_learning(battle, actor_id, action)
            self._publish_ai_turn_diagnostics(
                battle,
                actor_id,
                action=action,
                reason="rules_best_move",
                source="rules_ai",
                ai_level=ai_level,
                candidate_snapshot=candidate_snapshot,
                fallback_reason=fallback_reason,
                info=ai_choice_info,
            )
            self._announce_last_event(battle, record)
        finally:
            if battle.current_actor_id == actor_id and len(battle.log) == log_len:
                self._publish_ai_turn_diagnostics(
                    battle,
                    actor_id,
                    action=None,
                    reason="guard_skip_no_action",
                    source="turn_guard",
                    ai_level=ai_level,
                    candidate_snapshot=candidate_snapshot,
                    fallback_reason=fallback_reason,
                    info=ai_choice_info,
                )
                self._ai_skip_turn(battle, actor_id, record)

    def _collect_ai_candidates(self, battle: RulesBattleState, actor_id: str, *, limit: int = 8) -> Dict[str, Any]:
        try:
            ranked = ai_hybrid.rank_candidates(battle, actor_id)
        except Exception:
            return {"total": 0, "top": []}
        rows: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for score, action in ranked:
            key = self._ai_action_key(action)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "key": key,
                    "label": self._ai_action_label(action),
                    "score": round(score, 3) if math.isfinite(score) else float("-inf"),
                }
            )
        rows.sort(key=lambda entry: entry.get("score", float("-inf")), reverse=True)
        return {"total": len(rows), "top": rows[: max(1, int(limit))]}

    def _score_ai_action(self, battle: RulesBattleState, actor_id: str, action: object) -> float:
        try:
            score = float(ai_hybrid.score_action(battle, actor_id, action))
        except Exception:
            return float("-inf")
        if not math.isfinite(score):
            return float("-inf")
        return round(score, 3)

    def _ai_action_key(self, action: object) -> str:
        if isinstance(action, UseMoveAction):
            return f"move:{action.move_name}:{action.target_id or ''}"
        if isinstance(action, ShiftAction):
            return f"shift:{action.destination[0]},{action.destination[1]}"
        if isinstance(action, SwitchAction):
            return f"switch:{action.replacement_id}"
        if isinstance(action, GrappleAction):
            dest = action.destination if action.destination else ("", "")
            return f"grapple:{action.action_kind}:{action.target_id or ''}:{dest[0]},{dest[1]}"
        if isinstance(action, TakeBreatherAction):
            return "breather"
        if isinstance(action, DisengageAction):
            return f"disengage:{action.destination[0]},{action.destination[1]}"
        return action.__class__.__name__.lower()

    def _ai_action_label(self, action: Optional[object]) -> str:
        if action is None:
            return "No direct action"
        if isinstance(action, UseMoveAction):
            target = action.target_id or "auto"
            return f"Move: {action.move_name} -> {target}"
        if isinstance(action, ShiftAction):
            return f"Shift to ({action.destination[0]},{action.destination[1]})"
        if isinstance(action, SwitchAction):
            return f"Switch to {action.replacement_id}"
        if isinstance(action, GrappleAction):
            if action.destination:
                return f"Grapple {action.action_kind} -> ({action.destination[0]},{action.destination[1]})"
            return f"Grapple {action.action_kind}"
        if isinstance(action, TakeBreatherAction):
            return "Take a Breather"
        if isinstance(action, DisengageAction):
            return f"Disengage to ({action.destination[0]},{action.destination[1]})"
        return action.__class__.__name__

    def _publish_ai_turn_diagnostics(
        self,
        battle: RulesBattleState,
        actor_id: str,
        *,
        action: Optional[object],
        reason: str,
        source: str,
        ai_level: str,
        candidate_snapshot: Optional[Dict[str, Any]],
        fallback_reason: Optional[str],
        info: Optional[Dict[str, Any]] = None,
    ) -> None:
        snapshot = candidate_snapshot if candidate_snapshot is not None else {"total": 0, "top": []}
        selected_score = self._score_ai_action(battle, actor_id, action) if action is not None else float("-inf")
        payload = {
            "actor_id": actor_id,
            "round": getattr(battle, "round", 0),
            "phase": getattr(getattr(battle, "phase", None), "value", None),
            "ai_level": ai_level,
            "source": source,
            "reason": reason or "unspecified",
            "fallback_reason": fallback_reason or "",
            "fallback_used": bool(fallback_reason),
            "selected_action": self._ai_action_label(action),
            "selected_action_key": self._ai_action_key(action) if action is not None else "",
            "selected_score": None if selected_score == float("-inf") else selected_score,
            "legal_action_count": int(snapshot.get("total") or 0),
            "legal_actions_top": list(snapshot.get("top") or []),
            "info": dict(info or {}),
        }
        setattr(battle, "_ai_diagnostics", payload)

    def _record_ai_action_learning(self, battle: RulesBattleState, actor_id: str, action: object) -> None:
        try:
            global _AI_PROFILE_STORE
            learning = getattr(battle, "_ai_learning", None)
            if not isinstance(learning, dict):
                learning = {
                    "battle_updates": 0,
                    "last_actor_id": "",
                    "last_action_kind": "",
                    "last_action_label": "",
                    "last_model_version": None,
                }
            ai_hybrid.observe_action(battle, actor_id, action, store=_AI_PROFILE_STORE)
            _AI_PROFILE_STORE.save()
            created = register_ai_profile_update()
            action_kind = action.__class__.__name__ if action is not None else "UnknownAction"
            label = action_kind
            move = getattr(action, "move_name", None)
            item = getattr(action, "item_name", None)
            target = getattr(action, "target_id", None)
            if isinstance(move, str) and move.strip():
                label = move.strip()
            elif isinstance(item, str) and item.strip():
                label = item.strip()
            elif isinstance(target, str) and target.strip():
                label = f"{action_kind} -> {target.strip()}"
            learning["battle_updates"] = int(learning.get("battle_updates") or 0) + 1
            learning["last_actor_id"] = actor_id
            learning["last_action_kind"] = action_kind
            learning["last_action_label"] = label
            learning["current_model_id"] = str(_AI_MODEL_REGISTRY.get("current_model_id") or "")
            learning["updates_since_snapshot"] = int(_AI_MODEL_REGISTRY.get("updates_since_snapshot") or 0)
            learning["total_updates"] = int(_AI_MODEL_REGISTRY.get("total_updates") or 0)
            learning["drift_score"] = float(_AI_MODEL_REGISTRY.get("last_drift_score") or 0.0)
            learning["drift_threshold"] = float(_AI_MODEL_REGISTRY.get("drift_threshold") or _AI_MODEL_DRIFT_THRESHOLD)
            if created:
                _AI_PROFILE_STORE = ai_hybrid.get_profile_store()
                learning["last_model_version"] = dict(created)
                battle.log_event(
                    {
                        "type": "ai_model_version",
                        "actor": actor_id,
                        "model_id": created.get("model_id"),
                        "parent_id": created.get("parent_id"),
                        "drift_score": created.get("drift_score"),
                        "detail": "AI model auto-versioned from drift threshold.",
                    }
                )
            setattr(battle, "_ai_learning", learning)
        except Exception:
            # Never let learning persistence break the battle flow.
            pass

    def _ai_should_switch(
        self,
        battle: RulesBattleState,
        actor_id: str,
        target_id: Optional[str],
        move_score: float | None,
        ai_level: str,
    ) -> Optional[str]:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.fainted:
            return None
        current_hp = actor.hp or 0
        max_hp = actor.max_hp() or 1
        hp_ratio = current_hp / max_hp
        thresholds = {"strategic": 0.62, "tactical": 0.48, "standard": 0.36}
        threshold = thresholds.get(ai_level, 0.35)
        actor_team = self._ai_team_id(battle, actor_id)
        danger_now = self._ai_estimate_incoming_danger(
            battle,
            actor,
            actor.position,
            actor_team,
        )
        # Keep stable behavior when healthy and not under pressure.
        if hp_ratio > threshold and danger_now < 0.58:
            return None
        # Keep pressure if a strong attack line is available and danger is manageable.
        if move_score is not None and move_score >= 0.9 and danger_now < 0.8:
            return None
        bench = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == actor.controller_id
            and not mon.active
            and (mon.hp or 0) > 0
            and not mon.fainted
        ]
        if not bench:
            return None
        current_metric = self._ai_switch_metric(
            battle,
            actor_id,
            actor,
            actor.position,
            actor_team,
            pressure=danger_now,
            target_id=target_id,
        )
        best_id: Optional[str] = None
        best_metric = float("-inf")
        for candidate in bench:
            mon = battle.pokemon.get(candidate)
            if mon is None:
                continue
            metric = self._ai_switch_metric(
                battle,
                candidate,
                mon,
                actor.position,
                actor_team,
                pressure=danger_now,
                target_id=target_id,
            )
            # Require a meaningful improvement to avoid switch jitter.
            min_gain = 0.18 if ai_level == "strategic" else 0.24 if ai_level == "tactical" else 0.3
            if metric < current_metric + min_gain:
                continue
            if metric > best_metric:
                best_metric = metric
                best_id = candidate
        return best_id

    def _ai_team_id(self, battle: RulesBattleState, actor_id: str) -> str:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return ""
        trainer = battle.trainers.get(actor.controller_id)
        return (trainer.team or trainer.identifier) if trainer else actor.controller_id

    def _ai_estimate_incoming_danger(
        self,
        battle: RulesBattleState,
        defender: RulesPokemonState,
        defender_pos: Optional[Tuple[int, int]],
        defender_team: str,
    ) -> float:
        if defender is None or defender.fainted:
            return 1.0
        max_hp = max(1, defender.max_hp())
        weather = battle.effective_weather() if hasattr(battle, "effective_weather") else battle.weather
        max_ratio = 0.0
        for pid, foe in battle.pokemon.items():
            if foe.fainted or not foe.active or foe.position is None:
                continue
            if self._ai_team_id(battle, pid) == defender_team:
                continue
            for move in foe.spec.moves:
                if (move.category or "").strip().lower() == "status":
                    continue
                if defender_pos is not None:
                    if not targeting.is_target_in_range(
                        foe.position,
                        defender_pos,
                        move,
                        attacker_size=getattr(foe.spec, "size", ""),
                        target_size=getattr(defender.spec, "size", ""),
                        grid=battle.grid,
                    ):
                        continue
                    if battle.grid and not battle.has_line_of_sight(pid, defender_pos, None):
                        continue
                try:
                    amount = calculations.expected_damage(foe, defender, move, weather=weather)
                except Exception:
                    amount = 0.0
                if amount <= 0:
                    continue
                max_ratio = max(max_ratio, float(amount) / float(max_hp))
        if max_ratio <= 0.0 and defender_pos is not None:
            # Soft proximity pressure even when no immediate ranged hit is found.
            nearest = None
            for pid, foe in battle.pokemon.items():
                if foe.fainted or not foe.active or foe.position is None:
                    continue
                if self._ai_team_id(battle, pid) == defender_team:
                    continue
                dist = targeting.footprint_distance(
                    foe.position,
                    getattr(foe.spec, "size", ""),
                    defender_pos,
                    getattr(defender.spec, "size", ""),
                    battle.grid,
                )
                if nearest is None or dist < nearest:
                    nearest = dist
            if nearest is not None:
                if nearest <= 1:
                    max_ratio = 0.35
                elif nearest <= 3:
                    max_ratio = 0.2
                elif nearest <= 5:
                    max_ratio = 0.1
        return max(0.0, min(1.25, max_ratio))

    def _ai_estimate_entry_hazard_penalty(
        self,
        battle: RulesBattleState,
        actor: RulesPokemonState,
        entry_pos: Optional[Tuple[int, int]],
    ) -> float:
        if entry_pos is None or battle.grid is None:
            return 0.0
        tile = battle.grid.tiles.get(entry_pos) or {}
        if not isinstance(tile, dict):
            return 0.0
        hazards_raw = tile.get("hazards")
        if not isinstance(hazards_raw, dict):
            return 0.0
        hazards = {
            str(key).strip().lower(): int(value)
            for key, value in hazards_raw.items()
            if str(key).strip()
        }
        if not hazards:
            return 0.0
        types = {str(kind).strip().lower() for kind in (actor.spec.types or [])}
        levitate_like = actor.has_ability("Levitate") if hasattr(actor, "has_ability") else False
        grounded = not levitate_like and "flying" not in types
        penalty = 0.0
        spikes = max(0, int(hazards.get("spikes", 0) or 0))
        if spikes > 0 and grounded:
            penalty += min(0.28, 0.08 * spikes)
        if max(0, int(hazards.get("toxic_spikes", 0) or 0)) > 0 and grounded:
            if "poison" in types or "steel" in types:
                penalty -= 0.06
            else:
                penalty += 0.18
        if max(0, int(hazards.get("sticky_web", 0) or 0)) > 0 and grounded:
            penalty += 0.1
        if max(0, int(hazards.get("stealth_rock", 0) or 0)) > 0:
            penalty += 0.12
        if max(0, int(hazards.get("stealth_rock_fairy", 0) or 0)) > 0:
            penalty += 0.12
        return max(-0.08, min(0.65, penalty))

    def _ai_switch_metric(
        self,
        battle: RulesBattleState,
        actor_id: str,
        actor: RulesPokemonState,
        entry_pos: Optional[Tuple[int, int]],
        actor_team: str,
        *,
        pressure: float,
        target_id: Optional[str],
    ) -> float:
        hp_ratio = (actor.hp or 0) / max(1, actor.max_hp())
        danger = self._ai_estimate_incoming_danger(battle, actor, entry_pos, actor_team)
        hazard_penalty = self._ai_estimate_entry_hazard_penalty(battle, actor, entry_pos)
        offense = self._ai_target_offense_potential(
            battle,
            actor_id,
            actor,
            entry_pos,
            actor_team,
            target_id=target_id,
        )
        level_term = min(0.15, max(0.0, float(actor.spec.level or 0) / 300.0))
        # Higher is better: survivability + offense - hazard risk.
        survivability = (0.7 * hp_ratio) + (0.45 * max(0.0, 1.0 - min(1.0, danger)))
        pressure_term = 0.12 * max(0.0, min(1.0, pressure))
        return survivability + offense + level_term + pressure_term - hazard_penalty

    def _ai_target_offense_potential(
        self,
        battle: RulesBattleState,
        actor_id: str,
        actor: RulesPokemonState,
        actor_pos: Optional[Tuple[int, int]],
        actor_team: str,
        *,
        target_id: Optional[str],
    ) -> float:
        weather = battle.effective_weather() if hasattr(battle, "effective_weather") else battle.weather
        targets: List[RulesPokemonState] = []
        if target_id:
            primary = battle.pokemon.get(target_id)
            if primary is not None and not primary.fainted and primary.hp and primary.hp > 0:
                targets.append(primary)
        if not targets:
            for pid, foe in battle.pokemon.items():
                if foe.fainted or not foe.active or foe.hp is None or foe.hp <= 0:
                    continue
                if self._ai_team_id(battle, pid) == actor_team:
                    continue
                targets.append(foe)
        if not targets:
            return 0.0
        best = 0.0
        for foe in targets:
            if actor_pos is None or foe.position is None:
                continue
            for move in actor.spec.moves:
                if (move.category or "").strip().lower() == "status":
                    continue
                if not targeting.is_target_in_range(
                    actor_pos,
                    foe.position,
                    move,
                    attacker_size=getattr(actor.spec, "size", ""),
                    target_size=getattr(foe.spec, "size", ""),
                    grid=battle.grid,
                ):
                    continue
                if battle.grid and not battle.has_line_of_sight(actor_id, foe.position, None):
                    continue
                try:
                    dmg = calculations.expected_damage(actor, foe, move, weather=weather)
                except Exception:
                    dmg = 0.0
                if dmg <= 0:
                    continue
                ratio = float(dmg) / float(max(1, foe.max_hp()))
                best = max(best, ratio)
        return max(0.0, min(0.45, best))

    def _ai_should_shift_for_attack(
        self,
        battle: RulesBattleState,
        actor_id: str,
        move: MoveSpec,
        target_id: Optional[str],
    ) -> bool:
        move_category = (move.category or "").strip().lower()
        if move_category != "status":
            return False
        # If no damaging move can currently reach an opponent, try to close distance.
        return not self._ai_has_attack_in_range(battle, actor_id)

    def _ai_should_disengage_for_attack(
        self,
        battle: RulesBattleState,
        actor_id: str,
        move: MoveSpec,
        target_id: Optional[str],
    ) -> bool:
        actor = battle.pokemon.get(actor_id)
        target = battle.pokemon.get(target_id) if target_id else None
        if actor is None or actor.position is None or target is None or target.position is None:
            return False
        if (move.category or "").strip().lower() == "status":
            return False
        if targeting.normalized_target_kind(move) == "melee":
            return False
        if targeting.move_range_distance(move) <= 1:
            return False
        if targeting.footprint_distance(
            actor.position,
            getattr(actor.spec, "size", ""),
            target.position,
            getattr(target.spec, "size", ""),
            battle.grid,
        ) > 1:
            return False
        return True

    def _ai_has_attack_in_range(self, battle: RulesBattleState, actor_id: str) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.position is None:
            return False
        opponents: List[str] = []
        for pid, target in battle.pokemon.items():
            if target.fainted or not target.active or target.position is None:
                continue
            if target.controller_id == actor.controller_id:
                continue
            opponents.append(pid)
        if not opponents:
            return False
        for move in actor.spec.moves:
            if (move.category or "").strip().lower() == "status":
                continue
            requirements = battle.weapon_requirements_for_move(move)
            if requirements:
                weapon_tags = actor.equipped_weapon_tags()
                if not weapon_tags or not any(req.issubset(weapon_tags) for req in requirements):
                    continue
            for target_id in opponents:
                target = battle.pokemon.get(target_id)
                if target is None or target.position is None:
                    continue
                if not targeting.is_target_in_range(
                    actor.position,
                    target.position,
                    move,
                    attacker_size=getattr(actor.spec, "size", ""),
                    target_size=getattr(target.spec, "size", ""),
                    grid=battle.grid,
                ):
                    continue
                if battle.grid and not battle.has_line_of_sight(actor_id, target.position, target_id):
                    continue
                return True
        return False

    def _ai_nearest_opponent(self, battle: RulesBattleState, actor_id: str) -> Optional[str]:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.position is None:
            return None
        best_id = None
        best_dist = None
        for pid, target in battle.pokemon.items():
            if target.fainted or not target.active or target.position is None:
                continue
            if target.controller_id == actor.controller_id:
                continue
            dist = targeting.footprint_distance(
                actor.position,
                getattr(actor.spec, "size", ""),
                target.position,
                getattr(target.spec, "size", ""),
                battle.grid,
            )
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_id = pid
        return best_id

    def _ai_trainer_turn(
        self, battle: RulesBattleState, record: BattleRecord, trainer_id: str
    ) -> None:
        if battle.phase == RulesTurnPhase.START:
            battle.advance_phase()
        active = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == trainer_id and mon.active
        ]
        bench = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == trainer_id
            and not mon.active
            and mon.hp is not None
            and mon.hp > 0
        ]
        outgoing = next(
            (cid for cid in active if battle.pokemon[cid].fainted), None
        )
        if outgoing and bench:
            action = TrainerSwitchAction(
                actor_id=trainer_id, outgoing_id=outgoing, replacement_id=bench[0]
            )
            try:
                self._resolve_selected_action(battle, action)
            except ValueError:
                outgoing = None
        if outgoing:
            self._announce_last_event(battle, record)
            return
        battle.log_event({"type": "pass", "actor": trainer_id})
        self._announce_last_event(battle, record)
        self._advance_to_end_phase(battle)

    def _handle_shift(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        if battle.grid is None:
            self._print("[yellow]This encounter does not define a grid.[/yellow]")
            return False
        reachable = movement.legal_shift_tiles(battle, actor_id)
        others = {mon.position for pid, mon in battle.pokemon.items() if pid != actor_id}
        current_pos = battle.pokemon[actor_id].position
        if battle.pokemon[actor_id].has_status("Tripped"):
            action = ShiftAction(actor_id=actor_id, destination=current_pos)
            self._resolve_selected_action(battle, action)
            self._announce_last_event(battle, record)
            self._render_grid(battle)
            return True
        filtered = {coord for coord in reachable if coord == current_pos or coord not in others}
        if len(filtered) <= 1:
            self._print("[yellow]No tiles available to move into.[/yellow]")
            return False
        highlights = {coord: "+" for coord in filtered}
        self._render_highlight_grid(battle, highlights, "Reachable tiles marked with +")
        coords_text = ", ".join(f"({x},{y})" for x, y in sorted(filtered))
        self._print(f"Reachable tiles: {coords_text}")
        raw = self._input("Enter destination as x,y (blank to cancel): ").strip()
        if not raw:
            return False
        try:
            x_str, y_str = raw.replace(" ", "").split(",")
            dest = (int(x_str), int(y_str))
        except ValueError:
            self._print("[yellow]Invalid coordinate format.[/yellow]")
            return False
        if dest not in filtered:
            self._print("[yellow]That tile isn't reachable this turn.[/yellow]")
            return False
        action = ShiftAction(actor_id=actor_id, destination=dest)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        self._render_grid(battle)
        return True

    def _handle_switch(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        bench = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == actor.controller_id
            and not mon.active
            and mon.hp is not None
            and mon.hp > 0
        ]
        if not bench:
            self._print("[yellow]No available benched Pokemon to switch in.[/yellow]")
            return False
        rows = []
        for idx, cid in enumerate(bench, start=1):
            mon = battle.pokemon[cid]
            rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
        self._print("Choose a Pokemon to switch in:\n" + "\n".join(rows))
        selection = self._input(f"Select target [1-{len(bench)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(bench):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        replacement_id = bench[choice - 1]
        action = SwitchAction(actor_id=actor_id, replacement_id=replacement_id)
        try:
            self._resolve_selected_action(battle, action)
        except ValueError as exc:
            self._print(f"[yellow]{exc}[/yellow]")
            return False
        self._announce_last_event(battle, record)
        self._render_grid(battle)
        return True

    def _handle_trainer_switch(
        self, battle: RulesBattleState, trainer_id: str, record: BattleRecord
    ) -> bool:
        active = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == trainer_id and mon.active
        ]
        if not active:
            self._print("[yellow]No active Pokemon to recall.[/yellow]")
            return False
        bench = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.controller_id == trainer_id
            and not mon.active
            and mon.hp is not None
            and mon.hp > 0
        ]
        if not bench:
            self._print("[yellow]No available benched Pokemon to switch in.[/yellow]")
            return False
        outgoing_id = active[0]
        if len(active) > 1:
            rows = []
            for idx, cid in enumerate(active, start=1):
                mon = battle.pokemon[cid]
                fainted = " (fainted)" if mon.fainted else ""
                rows.append(f"{idx}) {mon.spec.name or mon.spec.species}{fainted} ({cid})")
            self._print("Choose a Pokemon to switch out:\n" + "\n".join(rows))
            selection = self._input(f"Select target [1-{len(active)}] (blank to cancel): ").strip()
            if not selection:
                return False
            try:
                choice = int(selection)
            except ValueError:
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            if choice < 1 or choice > len(active):
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            outgoing_id = active[choice - 1]
        rows = []
        for idx, cid in enumerate(bench, start=1):
            mon = battle.pokemon[cid]
            rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
        self._print("Choose a Pokemon to switch in:\n" + "\n".join(rows))
        selection = self._input(f"Select target [1-{len(bench)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(bench):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        replacement_id = bench[choice - 1]
        action = TrainerSwitchAction(
            actor_id=trainer_id,
            outgoing_id=outgoing_id,
            replacement_id=replacement_id,
        )
        try:
            self._resolve_selected_action(battle, action)
        except ValueError as exc:
            self._print(f"[yellow]{exc}[/yellow]")
            return False
        self._announce_last_event(battle, record)
        self._render_grid(battle)
        return True

    def _handle_attack(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        return self._handle_attack_with_moves(
            battle,
            actor_id,
            record,
            battle.pokemon[actor_id].spec.moves,
            "move",
        )

    def _handle_maneuver(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        grapple_status = battle.grapple_status(actor_id)
        menu = "[bold]Battle Maneuvers[/bold] ([M]aneuver list, [D]isengage, [S]print, [I]ntercept melee, [R]anged intercept, [W]ake ally, [P]Manipulate, [U]pick up item"
        if grapple_status:
            menu = menu.replace("[M]aneuver list", "[G]rapple actions, [M]aneuver list")
        menu = f"{menu}): "
        choice = self._input(menu).strip().lower()
        if grapple_status and choice in {"g", "grapple"}:
            return self._handle_grapple_actions(battle, actor_id, record)
        if choice in {"d", "disengage"}:
            return self._handle_disengage(battle, actor_id, record)
        if choice in {"s", "sprint"}:
            return self._handle_sprint(battle, actor_id, record)
        if choice in {"i", "intercept melee"}:
            return self._handle_intercept(battle, actor_id, record, "melee")
        if choice in {"r", "intercept ranged"}:
            return self._handle_intercept(battle, actor_id, record, "ranged")
        if choice in {"w", "wake"}:
            return self._handle_wake_ally(battle, actor_id, record)
        if choice in {"p", "manipulate"}:
            return self._handle_manipulate(battle, actor_id, record)
        if choice in {"u", "pickup", "pick up", "item"}:
            return self._handle_pickup_item(battle, actor_id, record)
        maneuvers = self._maneuver_moves()
        if not maneuvers:
            self._print("[red]No battle maneuvers are available.[/red]")
            return False
        return self._handle_attack_with_moves(battle, actor_id, record, maneuvers, "maneuver")

    def _handle_grapple_actions(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        status = battle.grapple_status(actor_id)
        if not status:
            self._print("[yellow]No active grapple to resolve.[/yellow]")
            return False
        other_id = status["other_id"]
        dominant = bool(status.get("dominant"))
        if dominant:
            prompt = "[bold]Grapple Actions[/bold] ([E]nd, [S]ecure, [A]ttack, [M]ove): "
        else:
            prompt = "[bold]Grapple Actions[/bold] ([C]ontest, [E]scape): "
        choice = self._input(prompt).strip().lower()
        if dominant and choice in {"e", "end"}:
            action = GrappleAction(actor_id=actor_id, action_kind="end", target_id=other_id)
        elif dominant and choice in {"s", "secure"}:
            action = GrappleAction(actor_id=actor_id, action_kind="secure", target_id=other_id)
        elif dominant and choice in {"a", "attack"}:
            action = GrappleAction(actor_id=actor_id, action_kind="attack", target_id=other_id)
        elif dominant and choice in {"m", "move"}:
            if battle.grid is None:
                self._print("[yellow]No grid available for grapple movement.[/yellow]")
                return False
            dest = self._prompt_for_destination(battle, actor_id)
            if dest is None:
                return False
            action = GrappleAction(actor_id=actor_id, action_kind="move", target_id=other_id, destination=dest)
        elif (not dominant) and choice in {"c", "contest"}:
            action = GrappleAction(actor_id=actor_id, action_kind="contest", target_id=other_id)
        elif (not dominant) and choice in {"e", "escape"}:
            action = GrappleAction(actor_id=actor_id, action_kind="escape", target_id=other_id)
        else:
            self._print("[yellow]Invalid grapple action choice.[/yellow]")
            return False
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_disengage(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        if battle.grid is None:
            self._print("[yellow]This encounter does not define a grid.[/yellow]")
            return False
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        reachable = movement.legal_shift_tiles(battle, actor_id)
        filtered = {
            coord
            for coord in reachable
            if battle._combatant_distance_to_coord(actor, coord) <= 1
            and (coord == actor.position or battle._position_can_fit(actor_id, coord, exclude_id=actor_id))
        }
        if len(filtered) <= 1:
            self._print("[yellow]No tiles available to disengage into.[/yellow]")
            return False
        highlights = {coord: "+" for coord in filtered}
        self._render_highlight_grid(battle, highlights, "Disengage tiles marked with +")
        coords_text = ", ".join(f"({x},{y})" for x, y in sorted(filtered))
        self._print(f"Reachable tiles: {coords_text}")
        raw = self._input("Enter destination as x,y (blank to cancel): ").strip()
        if not raw:
            return False
        try:
            x_str, y_str = raw.replace(" ", "").split(",")
            dest = (int(x_str), int(y_str))
        except ValueError:
            self._print("[yellow]Invalid coordinate format.[/yellow]")
            return False
        if dest not in filtered:
            self._print("[yellow]That tile isn't reachable for Disengage.[/yellow]")
            return False
        action = DisengageAction(actor_id=actor_id, destination=dest)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        self._render_grid(battle)
        return True

    def _handle_sprint(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        action = SprintAction(actor_id=actor_id)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_intercept(
        self,
        battle: RulesBattleState,
        actor_id: str,
        record: BattleRecord,
        kind: str,
    ) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        actor_trainer = battle.trainers.get(actor.controller_id)
        actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor.controller_id
        allies = [
            cid
            for cid, mon in battle.pokemon.items()
            if cid != actor_id
            and mon.hp is not None
            and mon.hp > 0
            and (battle.trainers.get(mon.controller_id).team if battle.trainers.get(mon.controller_id) else mon.controller_id)
            == actor_team
        ]
        if not allies:
            self._print("[yellow]No allies available to intercept for.[/yellow]")
            return False
        rows = []
        for idx, cid in enumerate(allies, start=1):
            mon = battle.pokemon[cid]
            rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
        self._print("Choose an ally to intercept for:\n" + "\n".join(rows))
        selection = self._input(f"Select ally [1-{len(allies)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(allies):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        ally_id = allies[choice - 1]
        action = InterceptAction(actor_id=actor_id, kind=kind, ally_id=ally_id)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_wake_ally(
        self, battle: RulesBattleState, actor_id: str, record: BattleRecord
    ) -> bool:
        if battle.grid is None:
            self._print("[yellow]This encounter does not define a grid.[/yellow]")
            return False
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.position is None:
            return False
        actor_trainer = battle.trainers.get(actor.controller_id)
        actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor.controller_id
        candidates = []
        for cid, mon in battle.pokemon.items():
            if cid == actor_id or mon.hp is None or mon.hp <= 0:
                continue
            if mon.position is None:
                continue
            target_trainer = battle.trainers.get(mon.controller_id)
            target_team = (target_trainer.team or target_trainer.identifier) if target_trainer else mon.controller_id
            if target_team != actor_team:
                continue
            if not mon.has_status("Sleep") and not mon.has_status("Asleep"):
                continue
            if battle._combatant_distance(actor, mon) != 1:
                continue
            candidates.append(cid)
        if not candidates:
            self._print("[yellow]No adjacent sleeping allies to wake.[/yellow]")
            return False
        rows = []
        for idx, cid in enumerate(candidates, start=1):
            mon = battle.pokemon[cid]
            rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
        self._print("Choose an ally to wake:\n" + "\n".join(rows))
        selection = self._input(f"Select ally [1-{len(candidates)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(candidates):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        target_id = candidates[choice - 1]
        action = WakeAllyAction(actor_id=actor_id, target_id=target_id)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_manipulate(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        tricks = ["Bon Mot", "Flirt", "Terrorize"]
        self._print("Manipulate options:\n" + "\n".join(f"{idx}) {name}" for idx, name in enumerate(tricks, start=1)))
        selection = self._input(f"Select a manipulate option [1-{len(tricks)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(tricks):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        trick = tricks[choice - 1]
        actor_state = battle.pokemon[actor_id]
        actor_trainer = battle.trainers.get(actor_state.controller_id)
        actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor_state.controller_id
        opponents = [
            cid
            for cid, mon in battle.pokemon.items()
            if mon.hp is not None
            and mon.hp > 0
            and (battle.trainers.get(mon.controller_id).team if battle.trainers.get(mon.controller_id) else mon.controller_id)
            != actor_team
        ]
        if not opponents:
            self._print("[yellow]No valid targets available.[/yellow]")
            return False
        rows = []
        for idx, cid in enumerate(opponents, start=1):
            mon = battle.pokemon[cid]
            rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
        self._print("Choose a target:\n" + "\n".join(rows))
        selection = self._input(f"Select target [1-{len(opponents)}] (blank to cancel): ").strip()
        if not selection:
            return False
        try:
            choice = int(selection)
        except ValueError:
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        if choice < 1 or choice > len(opponents):
            self._print("[yellow]Invalid selection.[/yellow]")
            return False
        target_id = opponents[choice - 1]
        action = ManipulateAction(actor_id=actor_id, trick=trick, target_id=target_id)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_pickup_item(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        action = PickupItemAction(actor_id=actor_id)
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _handle_creative_action(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        capability_names = actor.capability_names()
        skill_names = sorted((actor.spec.skills or {}).keys())
        self._print("[bold]Creative Battle Action[/bold]")
        self._print("Use this for improvised stunts, capability use, and custom skill checks.")
        title = self._input("Short title (blank to cancel): ").strip()
        if not title:
            return False
        description = self._input("What are you trying to do? ").strip()
        if capability_names:
            self._print("Capabilities: " + ", ".join(capability_names))
        capability = self._input("Capability to reference (optional): ").strip()
        if not capability:
            capability = ""
        if skill_names:
            self._print("Skills: " + ", ".join(skill_names))
        skill = self._input("Primary skill: ").strip().lower()
        if not skill:
            self._print("[yellow]A primary skill is required.[/yellow]")
            return False
        secondary_skill = self._input("Secondary skill, if the stunt needs two checks (optional): ").strip().lower()
        difficulty = self._input("Difficulty DC, or leave blank if this will be opposed: ").strip()
        dc = None
        if difficulty:
            try:
                dc = int(difficulty)
            except ValueError:
                self._print("[yellow]DC must be numeric.[/yellow]")
                return False
        opponents = [
            cid for cid, mon in battle.pokemon.items()
            if cid != actor_id and mon.active and not mon.fainted
        ]
        target_id = None
        opposed_skill = ""
        if opponents:
            rows = []
            for idx, cid in enumerate(opponents, start=1):
                mon = battle.pokemon[cid]
                rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
            self._print("Targets:\n" + "\n".join(rows))
            target_choice = self._input("Target # for opposed/targeted stunt (blank for none): ").strip()
            if target_choice:
                try:
                    target_index = int(target_choice)
                except ValueError:
                    self._print("[yellow]Invalid target selection.[/yellow]")
                    return False
                if target_index < 1 or target_index > len(opponents):
                    self._print("[yellow]Invalid target selection.[/yellow]")
                    return False
                target_id = opponents[target_index - 1]
                opposed_skill = self._input("Opposed target skill (optional): ").strip().lower()
        note = self._input("GM note or consequence text (optional): ").strip()
        action = CreativeAction(
            actor_id=actor_id,
            title=title,
            description=description,
            skill=skill,
            dc=dc,
            capability=capability or None,
            target_id=target_id,
            opposed_skill=opposed_skill or None,
            secondary_skill=secondary_skill or None,
            note=note,
        )
        self._resolve_selected_action(battle, action)
        self._announce_last_event(battle, record)
        return True

    def _is_weapon_item(self, item: object) -> bool:
        if not isinstance(item, dict):
            return False
        if item.get("weapon") or str(item.get("kind", "")).strip().lower() == "weapon":
            return True
        tags = []
        for key in ("tags", "traits", "qualities", "properties", "types", "type"):
            value = item.get(key)
            if not value:
                continue
            if isinstance(value, str):
                tags.extend([chunk.strip().lower() for chunk in value.replace(",", " ").split()])
            elif isinstance(value, (list, tuple, set)):
                tags.extend([str(chunk).strip().lower() for chunk in value])
        return "weapon" in tags

    def _handle_items(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return False
        if not actor.spec.items:
            self._print("[yellow]No items in inventory.[/yellow]")
            return False
        equipped_index = actor.equipped_weapon_index
        rows = []
        for idx, item in enumerate(actor.spec.items, start=1):
            name = item.get("name") if isinstance(item, dict) else str(item)
            name = name or "Item"
            kind = "weapon" if self._is_weapon_item(item) else "item"
            equipped_mark = " (equipped)" if equipped_index == (idx - 1) else ""
            rows.append(f"{idx}) {name} [{kind}]{equipped_mark}")
        self._print("Inventory:\n" + "\n".join(rows))
        choice = self._input("[bold]Items[/bold] ([E]quip, [U]nequip, [S]use, [B]ack): ").strip().lower()
        if choice in {"b", "back"}:
            return False
        if choice in {"u", "unequip"}:
            action = UnequipWeaponAction(actor_id=actor_id)
            try:
                self._resolve_selected_action(battle, action)
            except ValueError as exc:
                self._print(f"[yellow]{exc}[/yellow]")
                return False
            self._announce_last_event(battle, record)
            return True
        if choice in {"e", "equip"}:
            weapon_indices = [
                (idx, item)
                for idx, item in enumerate(actor.spec.items, start=1)
                if self._is_weapon_item(item)
            ]
            if not weapon_indices:
                self._print("[yellow]No weapons available to equip.[/yellow]")
                return False
            options = []
            for idx, item in weapon_indices:
                name = item.get("name") if isinstance(item, dict) else str(item)
                options.append(f"{idx}) {name or 'Weapon'}")
            self._print("Choose a weapon to equip:\n" + "\n".join(options))
            selection = self._input("Select weapon (blank to cancel): ").strip()
            if not selection:
                return False
            try:
                choice_idx = int(selection)
            except ValueError:
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            action = EquipWeaponAction(actor_id=actor_id, item_index=choice_idx - 1)
            try:
                self._resolve_selected_action(battle, action)
            except ValueError as exc:
                self._print(f"[yellow]{exc}[/yellow]")
                return False
            self._announce_last_event(battle, record)
            return True
        if choice in {"s", "use"}:
            usable_items = [
                (idx, item)
                for idx, item in enumerate(actor.spec.items, start=1)
                if not self._is_weapon_item(item)
            ]
            if not usable_items:
                self._print("[yellow]No usable items available.[/yellow]")
                return False
            options = []
            for idx, item in usable_items:
                name = item.get("name") if isinstance(item, dict) else str(item)
                options.append(f"{idx}) {name or 'Item'}")
            self._print("Choose an item to use:\n" + "\n".join(options))
            selection = self._input("Select item (blank to cancel): ").strip()
            if not selection:
                return False
            try:
                choice_idx = int(selection)
            except ValueError:
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            actor_state = battle.pokemon[actor_id]
            actor_trainer = battle.trainers.get(actor_state.controller_id)
            actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor_state.controller_id
            allies = [
                cid
                for cid, mon in battle.pokemon.items()
                if mon.hp is not None
                and mon.hp > 0
                and (battle.trainers.get(mon.controller_id).team if battle.trainers.get(mon.controller_id) else mon.controller_id)
                == actor_team
            ]
            rows = []
            for idx, cid in enumerate(allies, start=1):
                mon = battle.pokemon[cid]
                rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
            self._print("Choose a target:\n" + "\n".join(rows))
            selection = self._input(f"Select target [1-{len(allies)}] (blank to cancel): ").strip()
            if not selection:
                return False
            try:
                target_choice = int(selection)
            except ValueError:
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            if target_choice < 1 or target_choice > len(allies):
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            target_id = allies[target_choice - 1]
            action = UseItemAction(actor_id=actor_id, item_index=choice_idx - 1, target_id=target_id)
            try:
                self._resolve_selected_action(battle, action)
            except ValueError as exc:
                self._print(f"[yellow]{exc}[/yellow]")
                return False
            self._announce_last_event(battle, record)
            return True
        self._print("[yellow]Invalid items action.[/yellow]")
        return False

    def _handle_attack_with_moves(
        self,
        battle: RulesBattleState,
        actor_id: str,
        record: BattleRecord,
        moves: Sequence[MoveSpec],
        label: str,
    ) -> bool:
        player_moves = list(moves)
        if not player_moves:
            self._print(f"[red]This Pokemon has no {label}s to use.[/red]")
            return False
        move = self._prompt_for_move_interactive(player_moves, battle, actor_id)
        range_move = self._adjust_maneuver_for_telekinetic(battle, actor_id, move)
        requires_target = targeting.move_requires_target(move)
        target_id: Optional[str] = None
        target_pos: Optional[Tuple[int, int]] = None
        move_name = (move.name or "").strip().lower()
        area_kind = targeting.normalized_area_kind(range_move)
        if move_name == "baton pass":
            actor_state = battle.pokemon[actor_id]
            actor_trainer = battle.trainers.get(actor_state.controller_id)
            actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor_state.controller_id
            allies = [
                cid
                for cid, mon in battle.pokemon.items()
                if cid != actor_id
                and mon.hp is not None
                and mon.hp > 0
                and (battle.trainers.get(mon.controller_id).team if battle.trainers.get(mon.controller_id) else mon.controller_id)
                == actor_team
            ]
            if not allies:
                self._print("[yellow]No eligible ally to Baton Pass to.[/yellow]")
                return False
            rows = []
            for idx, cid in enumerate(allies, start=1):
                mon = battle.pokemon[cid]
                rows.append(f"{idx}) {mon.spec.name or mon.spec.species} ({cid})")
            self._print("Choose a Baton Pass recipient:\n" + "\n".join(rows))
            selection = self._input(f"Select ally [1-{len(allies)}] (blank to cancel): ").strip()
            if not selection:
                return False
            try:
                choice = int(selection)
            except ValueError:
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            if choice < 1 or choice > len(allies):
                self._print("[yellow]Invalid selection.[/yellow]")
                return False
            target_id = allies[choice - 1]
        if requires_target:
            actor_state = battle.pokemon[actor_id]
            actor_trainer = battle.trainers.get(actor_state.controller_id)
            actor_team = (actor_trainer.team or actor_trainer.identifier) if actor_trainer else actor_state.controller_id
            candidates: List[str] = []
            ally_ids: Set[str] = set()
            enemy_ids: Set[str] = set()
            for cid, state in battle.pokemon.items():
                if (
                    cid == actor_id
                    or state.hp is None
                    or state.hp <= 0
                    or not state.active
                    or state.position is None
                ):
                    continue
                trainer = battle.trainers.get(state.controller_id)
                team = (trainer.team or trainer.identifier) if trainer else state.controller_id
                candidates.append(cid)
                if team == actor_team:
                    ally_ids.add(cid)
                else:
                    enemy_ids.add(cid)
            if not candidates:
                self._print("[yellow]No other combatants remain to target.[/yellow]")
                return False
            anchors = targeting.target_anchor_tiles(
                battle.grid,
                actor_state.position,
                range_move,
            )
            if anchors:
                highlights: Dict[Tuple[int, int], str] = {}
                enemy_positions = {
                    battle.pokemon[cid].position: cid
                    for cid in enemy_ids
                    if battle.pokemon[cid].position is not None
                }
                ally_positions = {
                    battle.pokemon[cid].position: cid
                    for cid in ally_ids
                    if battle.pokemon[cid].position is not None
                }
                for coord in anchors:
                    if battle.grid and not battle.has_line_of_sight(actor_id, coord):
                        highlights[coord] = "[dim]-[/dim]"
                        continue
                    if coord in enemy_positions:
                        highlights[coord] = "[red]E[/red]"
                    elif coord in ally_positions:
                        highlights[coord] = "[yellow]A[/yellow]"
                    else:
                        highlights[coord] = "[green]x[/green]"
                self._render_highlight_grid(
                    battle,
                    highlights,
                    f"{move.name} targetable tiles (x empty, E enemy, A ally, - blocked)",
                )
            target_overview = self._build_target_overview(
                battle=battle,
                actor_id=actor_id,
                move=range_move,
                candidate_ids=candidates,
                ally_ids=ally_ids,
            )
            self._render_target_status_panel(battle, candidates, target_overview)
            if area_kind and anchors:
                target_id, target_pos = self._prompt_for_target_or_tile(
                    battle,
                    actor_id,
                    candidates,
                    target_overview,
                    anchors,
                )
                if target_id is None and target_pos is None:
                    return False
            else:
                target_id = self._prompt_for_target(battle, candidates, target_overview)
                if target_id is None:
                    return False
        action = UseMoveAction(
            actor_id=actor_id,
            move_name=move.name,
            target_id=target_id,
            target_position=target_pos,
        )
        try:
            self._resolve_selected_action(battle, action)
        except ValueError as exc:
            self._print(f"[yellow]{exc}[/yellow]")
            return False
        self._announce_last_event(battle, record)
        return True

    def _adjust_maneuver_for_telekinetic(
        self,
        battle: RulesBattleState,
        actor_id: str,
        move: MoveSpec,
    ) -> MoveSpec:
        name = (move.name or "").strip().lower()
        if name not in {"disarm", "trip", "push"}:
            return move
        actor = battle.pokemon.get(actor_id)
        if actor is None or not actor.has_capability("Telekinetic"):
            return move
        focus_rank = actor.skill_rank("focus")
        if focus_rank <= 1:
            return move
        adjusted = copy.deepcopy(move)
        adjusted.range_kind = "Ranged"
        adjusted.range_value = focus_rank
        adjusted.target_kind = "Ranged"
        adjusted.target_range = focus_rank
        adjusted.range_text = f"Ranged {focus_rank} (Telekinetic)"
        return adjusted

    def _render_actor_stats(self, battle: RulesBattleState, actor_id: str) -> None:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            self._print("[yellow]Unknown combatant.[/yellow]")
            return
        header = self._actor_label(battle, actor_id)
        self._print(f"[cyan]{header} stats[/cyan]")
        table = Table("Attribute", "Value", box=None)
        table.add_row("HP", f"{actor.hp}/{actor.max_hp()}")
        table.add_row("Max HP", str(actor.max_hp()))
        spec = actor.spec
        table.add_row("Species", spec.species or "-")
        table.add_row("Types", ", ".join(spec.types) if spec.types else "-")
        table.add_row("Attack", str(spec.atk))
        table.add_row("Defense", str(spec.defense))
        table.add_row("Sp. Attack", str(spec.spatk))
        table.add_row("Sp. Defense", str(spec.spdef))
        table.add_row("Speed", str(spec.spd))
        stages = ", ".join(f"{key}:{value:+d}" for key, value in actor.combat_stages.items())
        table.add_row("Combat stages", stages or "-")
        statuses = self._format_status_text(actor) or "-"
        table.add_row("Statuses", statuses)
        abilities = ", ".join(actor.ability_names()) or "-"
        table.add_row("Abilities", abilities)
        table.add_row("Tick value", str(actor.tick_value()))
        movement_modes = ", ".join(
            f"{mode}:{spec.movement.get(mode, 0)}" for mode in sorted(spec.movement.keys())
        )
        table.add_row("Movement", movement_modes or "-")
        self._print(table)

    def _build_target_overview(
        self,
        battle: RulesBattleState,
        actor_id: str,
        move: MoveSpec,
        candidate_ids: Sequence[str],
        ally_ids: Set[str],
    ) -> Dict[str, Dict[str, Any]]:
        overview: Dict[str, Dict[str, Any]] = {}
        actor_state = battle.pokemon.get(actor_id)
        actor_pos = actor_state.position if actor_state else None
        for candidate_id in candidate_ids:
            state = battle.pokemon[candidate_id]
            pos = state.position
            friendly = candidate_id in ally_ids
            alignment_label = "[yellow]Ally[/yellow]" if friendly else "[red]Enemy[/red]"
            note = "[yellow]Friendly fire[/yellow]" if friendly else "-"
            if actor_pos is None or pos is None:
                status_label = "[dim]Unknown position[/dim]"
                reachable = False
                status_key = "unknown"
            else:
                in_range = targeting.is_target_in_range(
                    actor_pos,
                    pos,
                    move,
                    attacker_size=getattr(actor_state.spec, "size", "") if actor_state is not None else "",
                    target_size=getattr(state.spec, "size", ""),
                    grid=battle.grid,
                )
                los = battle.has_line_of_sight(actor_id, pos, candidate_id)
                reachable = in_range and los
                if reachable:
                    status_label = "[bold green]IN RANGE[/bold green]"
                    status_key = "in_range"
                elif not los:
                    status_label = "[yellow]LOS BLOCKED[/yellow]"
                    status_key = "blocked"
                else:
                    status_label = "[red]OUT OF RANGE[/red]"
                    status_key = "out_of_range"
            overview[candidate_id] = {
                "status": status_label,
                "status_key": status_key,
                "reachable": reachable,
                "alignment_label": alignment_label,
                "alignment_key": 1 if friendly else 0,
                "position_label": f"({pos[0]},{pos[1]})" if pos else "?",
                "note": note,
            }
        return overview

    def _render_target_status_panel(
        self,
        battle: RulesBattleState,
        candidate_ids: Sequence[str],
        overview: Dict[str, Dict[str, Any]],
    ) -> None:
        if not overview:
            return
        groups: Dict[str, List[str]] = {"in_range": [], "blocked": [], "out_of_range": [], "unknown": []}
        for candidate_id in candidate_ids:
            entry = overview.get(candidate_id)
            if not entry:
                continue
            label = battle.pokemon[candidate_id].spec.name or battle.pokemon[candidate_id].spec.species
            key = entry.get("status_key", "unknown")
            groups.setdefault(key, []).append(label)
        summary_parts: List[str] = []
        order = [
            ("in_range", "[green]In range[/green]"),
            ("blocked", "[yellow]LOS blocked[/yellow]"),
            ("out_of_range", "[red]Out of range[/red]"),
            ("unknown", "[dim]Unknown[/dim]"),
        ]
        for key, label in order:
            names = groups.get(key)
            if names:
                summary_parts.append(f"{label}: {', '.join(names)}")
        if summary_parts:
            self._print(" | ".join(summary_parts))

    def _handle_skip_turn(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> None:
        self._print("[yellow]You skip the rest of your turn.[/yellow]")
        battle.log_event({"type": "pass", "actor": actor_id})
        self._advance_to_end_phase(battle)
        self._announce_last_event(battle, record)

    def _handle_delay(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        entry = battle.current_initiative_entry()
        if entry is None:
            self._print("[red]No active initiative entry to delay.[/red]")
            return False
        prompt = f"Delay to which initiative value (current {entry.total})? "
        raw = self._input(prompt).strip()
        if not raw:
            return False
        try:
            target_total = int(raw)
        except ValueError:
            self._print("[red]Delay requires a numeric initiative value.[/red]")
            return False
        try:
            battle.queue_action(DelayAction(actor_id=actor_id, target_total=target_total))
            battle.resolve_next_action()
            record.events = list(battle.log)
            return True
        except ValueError as exc:
            self._print(f"[red]{exc}[/red]")
            return False

    def _handle_trade(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        choice = self._input("Trade Standard for [S]hift or s[W]ift? ").strip().lower()
        target = "shift" if choice in {"s", "shift"} else "swift" if choice in {"w", "swift"} else ""
        if not target:
            return False
        try:
            battle.queue_action(TradeStandardForAction(actor_id=actor_id, target_action=target))
            battle.resolve_next_action()
            record.events = list(battle.log)
            return True
        except ValueError as exc:
            self._print(f"[red]{exc}[/red]")
            return False

    def _handle_breather(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> bool:
        action = TakeBreatherAction(actor_id=actor_id)
        try:
            self._resolve_selected_action(battle, action)
            self._announce_last_event(battle, record)
            return True
        except ValueError as exc:
            self._print(f"[yellow]{exc}[/yellow]")
            return False

    def _ai_try_shift_toward_target(
        self,
        battle: RulesBattleState,
        actor_id: str,
        record: BattleRecord,
        *,
        target_range: Optional[int] = None,
        target_id: Optional[str] = None,
    ) -> Optional[ShiftAction]:
        if battle.grid is None:
            return None
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.position is None:
            return None
        if any(actor.has_status(name) for name in ("Trapped", "Grappled", "Stuck", "Immobilized")):
            return None
        target_infos: List[Tuple[Tuple[int, int], int]] = []
        primary_info: Optional[Tuple[Tuple[int, int], int]] = None
        for opponent_id in self._opponent_ids(battle, actor_id):
            opponent = battle.pokemon.get(opponent_id)
            if opponent is None or opponent.position is None:
                continue
            shift_distance = self._estimated_opponent_shift_distance(
                battle, opponent_id
            )
            info = (opponent.position, shift_distance)
            target_infos.append(info)
            if target_id and opponent_id == target_id:
                primary_info = info
        if not target_infos:
            return None
        if primary_info:
            others = [info for info in target_infos if info != primary_info]
            target_infos = [primary_info] + others
        reachable = movement.legal_shift_tiles(battle, actor_id)
        occupied = {
            state.position
            for pid, state in battle.pokemon.items()
            if pid != actor_id and state.position is not None
        }
        filtered = [coord for coord in reachable if coord == actor.position or coord not in occupied]
        if len(filtered) <= 1:
            return None
        last_from = None
        for event in reversed(battle.log or []):
            if event.get("type") != "shift" or event.get("actor") != actor_id:
                continue
            if event.get("to") == actor.position:
                last_from = event.get("from")
            break
        range_needed = target_range if target_range is not None else 1
        best = (float("inf"), float("inf"))
        destination: Optional[Tuple[int, int]] = None
        for coord in filtered:
            if coord == actor.position:
                continue
            if last_from and coord == last_from and len(filtered) > 2:
                continue
            evaluation = self._evaluate_shift_coord(coord, target_infos, range_needed)
            if evaluation < best:
                best = evaluation
                destination = coord
        if destination is None:
            return None
        action = ShiftAction(actor_id=actor_id, destination=destination)
        try:
            self._resolve_selected_action(battle, action)
        except ValueError:
            return None
        self._record_ai_action_learning(battle, actor_id, action)
        self._announce_last_event(battle, record)
        return action

    def _ai_try_disengage_for_attack(
        self,
        battle: RulesBattleState,
        actor_id: str,
        record: BattleRecord,
        *,
        target_id: Optional[str] = None,
    ) -> Optional[DisengageAction]:
        if battle.grid is None:
            return None
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.position is None:
            return None
        if any(actor.has_status(name) for name in ("Trapped", "Grappled", "Stuck", "Immobilized")):
            return None
        reachable = movement.legal_shift_tiles(battle, actor_id)
        occupied = {
            state.position
            for pid, state in battle.pokemon.items()
            if pid != actor_id and state.position is not None
        }
        options = [
            coord
            for coord in reachable
            if coord != actor.position
            and coord not in occupied
            and battle._combatant_distance_to_coord(actor, coord) == 1
        ]
        if not options:
            return None
        target_infos: List[Tuple[Tuple[int, int], int]] = []
        primary_info: Optional[Tuple[Tuple[int, int], int]] = None
        for opponent_id in self._opponent_ids(battle, actor_id):
            opponent = battle.pokemon.get(opponent_id)
            if opponent is None or opponent.position is None:
                continue
            info = (opponent.position, self._estimated_opponent_shift_distance(battle, opponent_id))
            target_infos.append(info)
            if target_id and opponent_id == target_id:
                primary_info = info
        if not target_infos:
            return None
        if primary_info:
            others = [info for info in target_infos if info != primary_info]
            target_infos = [primary_info] + others
        best = (float("inf"), float("inf"))
        destination: Optional[Tuple[int, int]] = None
        for coord in options:
            evaluation = self._evaluate_shift_coord(coord, target_infos, range_needed=2)
            if evaluation < best:
                best = evaluation
                destination = coord
        if destination is None:
            return None
        action = DisengageAction(actor_id=actor_id, destination=destination)
        try:
            self._resolve_selected_action(battle, action)
        except ValueError:
            return None
        self._record_ai_action_learning(battle, actor_id, action)
        self._announce_last_event(battle, record)
        return action

    def _ai_skip_turn(self, battle: RulesBattleState, actor_id: str, record: BattleRecord) -> None:
        if self._ai_try_last_resort_action(battle, actor_id, record):
            return
        battle.log_event({"type": "pass", "actor": actor_id})
        self._announce_last_event(battle, record)
        self._advance_to_end_phase(battle)

    def _ai_try_follow_up_attack(
        self,
        battle: RulesBattleState,
        actor_id: str,
        record: BattleRecord,
        *,
        ai_level: str,
        candidate_snapshot: Optional[Dict[str, Any]],
        fallback_reason: Optional[str],
        info: Optional[Dict[str, Any]] = None,
        source: str = "rules_shift_followup",
        reason: str = "shift_into_attack",
    ) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.fainted:
            return False
        if battle.current_actor_id != actor_id:
            return False
        move, target_id, _move_score = rules_ai.choose_best_move(battle, actor_id, ai_level=ai_level)
        if move is None:
            return False
        if targeting.move_requires_target(move) and target_id is None:
            return False
        action = UseMoveAction(
            actor_id=actor_id,
            move_name=move.name,
            target_id=target_id,
            chosen_type=self._ai_move_chosen_type(battle, actor_id, move),
        )
        try:
            self._resolve_selected_action(battle, action)
        except ValueError:
            return False
        self._record_ai_action_learning(battle, actor_id, action)
        self._publish_ai_turn_diagnostics(
            battle,
            actor_id,
            action=action,
            reason=reason,
            source=source,
            ai_level=ai_level,
            candidate_snapshot=candidate_snapshot,
            fallback_reason=fallback_reason,
            info=info,
        )
        self._announce_last_event(battle, record)
        return True

    def _ai_move_chosen_type(
        self,
        battle: RulesBattleState,
        actor_id: str,
        move: MoveSpec,
    ) -> Optional[str]:
        move_name = (move.name or "").strip().lower()
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return None
        if move_name == "conversion" and hasattr(battle, "_conversion_type_options"):
            options = list(battle._conversion_type_options(actor))
            return str(options[0]) if options else None
        if move_name == "conversion2" and hasattr(battle, "_conversion2_type_options"):
            options = list(battle._conversion2_type_options(actor_id))
            return str(options[0]) if options else None
        return None

    def _ai_try_last_resort_action(
        self, battle: RulesBattleState, actor_id: str, record: BattleRecord
    ) -> bool:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.fainted:
            return False
        if battle.grid is not None and actor.position is not None:
            reachable = movement.legal_shift_tiles(battle, actor_id)
            occupied = {
                state.position
                for pid, state in battle.pokemon.items()
                if pid != actor_id and state.position is not None
            }
            candidates = [
                coord
                for coord in reachable
                if coord != actor.position and coord not in occupied
            ]
            opponent_positions = []
            for opponent_id in self._opponent_ids(battle, actor_id):
                opponent = battle.pokemon.get(opponent_id)
                if opponent and opponent.position is not None:
                    opponent_positions.append(opponent.position)
            if opponent_positions:
                candidates.sort(
                    key=lambda coord: min(
                        targeting.footprint_distance(coord, "Medium", pos, "Medium", battle.grid)
                        for pos in opponent_positions
                    )
                )
            else:
                candidates.sort()
            if candidates:
                action = ShiftAction(actor_id=actor_id, destination=candidates[0])
                try:
                    self._resolve_selected_action(battle, action)
                    self._record_ai_action_learning(battle, actor_id, action)
                    self._announce_last_event(battle, record)
                    self._advance_to_end_phase(battle)
                    return True
                except ValueError:
                    pass
        if actor.hp is not None and actor.hp < actor.max_hp():
            action = TakeBreatherAction(actor_id=actor_id)
            try:
                self._resolve_selected_action(battle, action)
                self._announce_last_event(battle, record)
                self._advance_to_end_phase(battle)
                return True
            except ValueError:
                pass
        action = SprintAction(actor_id=actor_id)
        try:
            self._resolve_selected_action(battle, action)
            self._announce_last_event(battle, record)
            self._advance_to_end_phase(battle)
            return True
        except ValueError:
            return False

    def _ai_choose_item_action(
        self,
        battle: RulesBattleState,
        actor_id: str,
    ) -> Optional[UseItemAction]:
        actor = battle.pokemon.get(actor_id)
        if actor is None or actor.fainted or not actor.spec.items:
            return None
        max_hp = max(1, actor.max_hp())
        current_hp = int(actor.hp or 0)
        hp_ratio = current_hp / max_hp
        has_statuses = bool(actor.statuses)
        for idx, item in enumerate(actor.spec.items):
            if self._is_weapon_item(item):
                continue
            entry = get_item_entry(str(item.get("name") if isinstance(item, dict) else item))
            item_name = str(item.get("name") if isinstance(item, dict) else item).strip().lower()
            effects = parse_item_effects(entry) if entry is not None else {}
            if item_name in {"potion", "super potion", "hyper potion", "fresh water", "super soda pop", "lemonade", "moomoo milk", "enriched water", "medicinal leek"}:
                effects = dict(effects)
                effects["use_heal_hp"] = effects.get("use_heal_hp") or 1
            elif item_name in {"full restore"}:
                effects = dict(effects)
                effects["use_heal_full"] = True
            elif item_name in {"revive", "max revive", "reviver orb"}:
                effects = dict(effects)
                effects["revive_ticks"] = effects.get("revive_ticks", 1)
            if not effects:
                continue
            if current_hp > 0 and (
                effects.get("use_heal_full")
                or effects.get("use_heal_hp")
                or effects.get("use_heal_fraction")
                or effects.get("use_heal_ticks")
            ):
                if hp_ratio <= 0.5:
                    action = UseItemAction(actor_id=actor_id, item_index=idx, target_id=actor_id)
                    try:
                        battle._validate_action(action)
                        return action
                    except ValueError:
                        pass
            if has_statuses and (
                effects.get("cure_major_all")
                or effects.get("cure_minor_all")
                or effects.get("cure_major_count")
                or effects.get("cure_minor_count")
                or effects.get("cure_volatile")
                or effects.get("cure_statuses")
            ):
                action = UseItemAction(actor_id=actor_id, item_index=idx, target_id=actor_id)
                try:
                    battle._validate_action(action)
                    return action
                except ValueError:
                    pass
            if effects.get("revive_ticks") is not None:
                for target_id, mon in battle.pokemon.items():
                    if mon.controller_id != actor.controller_id:
                        continue
                    if mon.hp is not None and mon.hp <= 0:
                        action = UseItemAction(actor_id=actor_id, item_index=idx, target_id=target_id)
                        try:
                            battle._validate_action(action)
                            return action
                        except ValueError:
                            continue
        return None

    def _evaluate_shift_coord(
        self,
        coord: Tuple[int, int],
        target_infos: Sequence[Tuple[Tuple[int, int], int]],
        range_needed: int,
    ) -> Tuple[float, float]:
        """Score candidate shift tiles based on how close they bring the actor to threats."""
        best = (float("inf"), float("inf"))
        for pos, shift_distance in target_infos:
            distance = targeting.footprint_distance(coord, "Medium", pos, "Medium", None)
            predicted_distance = max(0, distance - shift_distance)
            shortfall = max(0, predicted_distance - range_needed)
            candidate = (shortfall, predicted_distance)
            if candidate < best:
                best = candidate
        return best

    def _estimated_opponent_shift_distance(
        self, battle: RulesBattleState, actor_id: str
    ) -> int:
        opponent = battle.pokemon.get(actor_id)
        if opponent is None or opponent.position is None:
            return 0
        tiles = movement.legal_shift_tiles(battle, actor_id)
        if not tiles:
            return 0
        distances = [
            battle._combatant_distance_to_coord(opponent, coord)
            for coord in tiles
            if coord is not None
        ]
        return max(distances) if distances else 0

    def _controller_kind_for_actor(self, battle: RulesBattleState, actor_id: Optional[str]) -> str:
        if not actor_id:
            return "ai"
        trainer = battle.trainers.get(actor_id)
        if trainer and trainer.controller_kind:
            return trainer.controller_kind
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return "ai"
        trainer = battle.trainers.get(actor.controller_id)
        if trainer and trainer.controller_kind:
            return trainer.controller_kind
        fallback = str(actor.controller_id or "").strip().lower()
        return "player" if fallback == "player" else "ai"

    def _resolve_pending_setups(
        self,
        battle: RulesBattleState,
        record: BattleRecord,
        actor_id: str,
    ) -> bool:
        if not battle.has_pending_resolution(actor_id):
            return False
        pending = battle.pokemon[actor_id].pending_resolution or {}
        pending_move = pending.get("move")
        if pending_move and (pending_move.name or "").strip().lower() == "beak blast":
            return False
        if battle.phase == RulesTurnPhase.START:
            battle.advance_phase()
        if battle.phase == RulesTurnPhase.COMMAND:
            battle.advance_phase()
        if not battle.execute_pending_resolution(actor_id):
            return False
        self._announce_last_event(battle, record)
        self._advance_to_end_phase(battle)
        return True

    def _advance_to_end_phase(self, battle: RulesBattleState) -> None:
        while battle.phase != RulesTurnPhase.END:
            battle.advance_phase()

    def _resolve_selected_action(
        self,
        battle: RulesBattleState,
        action: Action,
    ) -> None:
        defer_to_action_phase = False
        if battle.phase == RulesTurnPhase.COMMAND:
            if isinstance(action, TrainerAction):
                defer_to_action_phase = action.action_type != ActionType.FREE
            else:
                defer_to_action_phase = action.action_type == ActionType.STANDARD
        if defer_to_action_phase and not battle.is_league_battle():
            battle.declare_action(action)
            battle.advance_phase()
            battle.resolve_declared_actions()
            return
        battle.queue_action(action)
        battle.resolve_next_action()

    def _alive_teams(self, battle: RulesBattleState) -> Set[str]:
        teams: Set[str] = set()
        for mon in battle.pokemon.values():
            if mon.hp is None or mon.hp <= 0:
                continue
            trainer = battle.trainers.get(mon.controller_id)
            team = (trainer.team or trainer.identifier) if trainer else mon.controller_id
            teams.add(team or mon.controller_id)
        return teams

    def _team_has_player(self, battle: RulesBattleState, team: str) -> bool:
        for trainer in battle.trainers.values():
            team_id = trainer.team or trainer.identifier
            if team_id == team and trainer.controller_kind == "player":
                return True
        return False

    def _has_player_controller(self, battle: RulesBattleState) -> bool:
        return any(trainer.controller_kind == "player" for trainer in battle.trainers.values())

    def _clone_battle_state(self, battle: RulesBattleState) -> RulesBattleState:
        cloned = copy.deepcopy(battle)
        cloned.out_of_turn_prompt = self._prompt_out_of_turn
        return cloned

    def _spectator_prompt(self) -> str:
        choice = self._input(
            "[bold]Spectator[/bold] (Enter=step, [B]ack, [R]eplay, [F]ast-forward, [Q]uit): "
        ).strip().lower()
        if choice in {"q", "quit", "exit"}:
            return "quit"
        if choice in {"f", "fast", "fast-forward"}:
            return "toggle"
        if choice in {"b", "back", "prev", "previous"}:
            return "back"
        if choice in {"r", "replay", "restart"}:
            return "replay"
        return "step"

    def _ordered_combatants(self, battle: RulesBattleState) -> List[str]:
        team_order: Dict[str, int] = {}
        next_order = 0
        for trainer in battle.trainers.values():
            key = trainer.team or trainer.identifier
            if key not in team_order:
                team_order[key] = next_order
                next_order += 1

        def sort_key(item: Tuple[str, RulesPokemonState]) -> Tuple[int, str, str]:
            cid, state = item
            trainer = battle.trainers.get(state.controller_id)
            team = (trainer.team or trainer.identifier) if trainer else state.controller_id
            order = team_order.get(team, 99)
            trainer_name = trainer.name if trainer else state.controller_id
            mon_name = state.spec.name or state.spec.species
            return (order, trainer_name, mon_name, cid)

        return [cid for cid, _state in sorted(battle.pokemon.items(), key=sort_key)]

    def _combatant_markers(self, battle: RulesBattleState) -> Dict[str, str]:
        markers: Dict[str, str] = {}
        ordered = self._ordered_combatants(battle)
        for idx, cid in enumerate(ordered):
            marker = _MARKER_CHARS[idx % len(_MARKER_CHARS)]
            markers[cid] = marker
        return markers

    def _format_status_text(self, state: RulesPokemonState, *, include_duration: bool = False) -> str:
        parts: List[str] = []
        for entry in state.statuses:
            if isinstance(entry, str):
                parts.append(entry.title())
            elif isinstance(entry, dict):
                name = str(entry.get("name", "")).title()
                stacks = entry.get("stacks")
                if stacks:
                    name = f"{name}({stacks})"
                if include_duration:
                    remaining = entry.get("remaining")
                    duration = entry.get("duration")
                    rounds = entry.get("rounds")
                    if remaining is not None:
                        name = f"{name}:{remaining}"
                    elif duration is not None:
                        name = f"{name}:{duration}"
                    elif rounds is not None:
                        name = f"{name}:{rounds}"
                parts.append(name)
        return ", ".join(parts)

    def _positions_summary(self, battle: RulesBattleState) -> str:
        markers = self._combatant_markers(battle)
        segments = []
        for cid in self._ordered_combatants(battle):
            state = battle.pokemon[cid]
            pos = state.position
            if not state.active or pos is None:
                continue
            segments.append(f"{markers[cid]}@({pos[0]},{pos[1]})")
        return ", ".join(segments)

    def _opponent_ids(self, battle: RulesBattleState, actor_id: str) -> List[str]:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return []
        trainer = battle.trainers.get(actor.controller_id)
        actor_team = (trainer.team or trainer.identifier) if trainer else actor.controller_id
        opponents: List[str] = []
        for cid, state in battle.pokemon.items():
            if state.hp is None or state.hp <= 0 or not state.active or state.position is None:
                continue
            opponent_trainer = battle.trainers.get(state.controller_id)
            team = (opponent_trainer.team or opponent_trainer.identifier) if opponent_trainer else state.controller_id
            if team != actor_team:
                opponents.append(cid)
        return opponents

    def _prompt_for_target(
        self,
        battle: RulesBattleState,
        candidate_ids: List[str],
        overview: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Optional[str]:
        overview = overview or {}
        alive = [cid for cid in candidate_ids if battle.pokemon[cid].hp > 0]
        if not alive:
            return None
        alive.sort(
            key=lambda cid: (
                0 if overview.get(cid, {}).get("reachable") else 1,
                overview.get(cid, {}).get("alignment_key", 0),
                cid,
            )
        )
        if len(alive) == 1:
            return alive[0]
        markers = self._combatant_markers(battle)
        table = Table("No.", "Mk", "Pokemon", "Trainer", "Align", "HP", "Pos", "Range/LOS", "Notes", box=None)
        for idx, cid in enumerate(alive, start=1):
            state = battle.pokemon[cid]
            trainer = battle.trainers.get(state.controller_id)
            entry = overview.get(cid, {})
            pos = state.position
            pos_text = entry.get("position_label")
            if not pos_text:
                pos_text = f"({pos[0]},{pos[1]})" if pos else "?"
            table.add_row(
                str(idx),
                markers.get(cid, "?"),
                state.spec.name or state.spec.species,
                trainer.name if trainer else state.controller_id,
                entry.get("alignment_label", "-"),
                f"{state.hp}/{state.max_hp()}",
                pos_text,
                entry.get("status", "-"),
                entry.get("note", "-"),
            )
        self._print(table)
        while True:
            raw = self._input(f"Target [1-{len(alive)}] (blank to cancel): ").strip()
            if not raw:
                return None
            if raw.isdigit():
                choice = int(raw)
                if 1 <= choice <= len(alive):
                    return alive[choice - 1]
            self._print("[yellow]Invalid target selection.[/yellow]")

    def _prompt_for_target_or_tile(
        self,
        battle: RulesBattleState,
        actor_id: str,
        candidate_ids: List[str],
        overview: Optional[Dict[str, Dict[str, Any]]],
        anchor_tiles: Set[Tuple[int, int]],
    ) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
        overview = overview or {}
        alive = [cid for cid in candidate_ids if battle.pokemon[cid].hp > 0]
        alive.sort(
            key=lambda cid: (
                0 if overview.get(cid, {}).get("reachable") else 1,
                overview.get(cid, {}).get("alignment_key", 0),
                cid,
            )
        )
        if alive:
            markers = self._combatant_markers(battle)
            table = Table(
                "No.",
                "Mk",
                "Pokemon",
                "Trainer",
                "Align",
                "HP",
                "Pos",
                "Range/LOS",
                "Notes",
                box=None,
            )
            for idx, cid in enumerate(alive, start=1):
                state = battle.pokemon[cid]
                trainer = battle.trainers.get(state.controller_id)
                entry = overview.get(cid, {})
                pos = state.position
                pos_text = entry.get("position_label")
                if not pos_text:
                    pos_text = f"({pos[0]},{pos[1]})" if pos else "?"
                table.add_row(
                    str(idx),
                    markers.get(cid, "?"),
                    state.spec.name or state.spec.species,
                    trainer.name if trainer else state.controller_id,
                    entry.get("alignment_label", "-"),
                    f"{state.hp}/{state.max_hp()}",
                    pos_text,
                    entry.get("status", "-"),
                    entry.get("note", "-"),
                )
            self._print(table)
        anchor_set = set(anchor_tiles or set())
        prompt = "Target [1-{}] or tile x,y (blank to cancel): ".format(len(alive))
        while True:
            raw = self._input(prompt).strip()
            if not raw:
                return None, None
            if raw.isdigit() and alive:
                choice = int(raw)
                if 1 <= choice <= len(alive):
                    return alive[choice - 1], None
            if "," in raw:
                try:
                    x_str, y_str = raw.replace(" ", "").split(",")
                    coord = (int(x_str), int(y_str))
                except ValueError:
                    self._print("[yellow]Invalid coordinate format.[/yellow]")
                    continue
                if battle.grid and not battle.grid.in_bounds(coord):
                    self._print("[yellow]That tile is out of bounds.[/yellow]")
                    continue
                if anchor_set and coord not in anchor_set:
                    self._print("[yellow]That tile is not a valid anchor.[/yellow]")
                    continue
                if battle.grid and not battle.has_line_of_sight(actor_id, coord):
                    self._print("[yellow]Line of sight is blocked.[/yellow]")
                    continue
                return None, coord
            self._print("[yellow]Invalid target selection.[/yellow]")

    def _default_origin_for_side(self, side: TrainerSideSpec, grid: Optional[RulesGridState]) -> Tuple[int, int]:
        if side.start_positions:
            coord = side.start_positions[0]
            return (int(coord[0]), int(coord[1]))
        base = self.plan.default_you_start if side.controller == "player" or side.team == "players" else self.plan.default_foe_start
        if grid is None:
            return base
        x = max(0, min(grid.width - 1, base[0]))
        y = max(0, min(grid.height - 1, base[1]))
        return (x, y)

    def _allocate_positions(
        self,
        grid: Optional[RulesGridState],
        origin: Tuple[int, int],
        count: int,
        preferred: List[Tuple[int, int]],
        occupied: Set[Tuple[int, int]],
    ) -> List[Tuple[int, int]]:
        if grid is None:
            return [origin for _ in range(count)]
        coords: List[Tuple[int, int]] = []
        for coord in preferred:
            candidate = (int(coord[0]), int(coord[1]))
            if self._tile_available(grid, candidate, occupied):
                coords.append(candidate)
                if len(coords) == count:
                    return coords
        while len(coords) < count:
            candidate = self._next_open_tile(grid, origin, occupied)
            coords.append(candidate)
            occupied.add(candidate)
        return coords

    def _tile_available(
        self,
        grid: RulesGridState,
        coord: Tuple[int, int],
        occupied: Set[Tuple[int, int]],
    ) -> bool:
        if not grid.in_bounds(coord):
            return False
        if coord in occupied:
            return False
        if coord in grid.blockers:
            return False
        return True

    def _next_open_tile(
        self,
        grid: RulesGridState,
        origin: Tuple[int, int],
        occupied: Set[Tuple[int, int]],
    ) -> Tuple[int, int]:
        x = max(0, min(grid.width - 1, origin[0]))
        y = max(0, min(grid.height - 1, origin[1]))
        radius = 0
        while radius < max(grid.width, grid.height):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    candidate = (x + dx, y + dy)
                    if self._tile_available(grid, candidate, occupied):
                        return candidate
            radius += 1
        return origin

    def _render_status_interactive(self, battle: RulesBattleState) -> None:
        self._print(self._build_status_renderable(battle))

    def _build_status_renderable(self, battle: RulesBattleState) -> object:
        markers = self._combatant_markers(battle)
        columns = (
            "Mk",
            "Pokemon",
            "Trainer",
            "Team",
            "HP",
            "TempHP",
            "Inj",
            "InjPen",
            "Status",
            "Position",
            "CS",
            "Abilities",
            "Stats",
            "Caps",
        )
        active_table = Table(*columns, box=None, expand=True)
        bench_table = Table(*columns, box=None, expand=True)
        active_ids = [cid for cid in self._ordered_combatants(battle) if battle.pokemon[cid].active]
        bench_ids = [cid for cid in self._ordered_combatants(battle) if not battle.pokemon[cid].active]
        for combatant_id in active_ids + bench_ids:
            state = battle.pokemon[combatant_id]
            trainer = battle.trainers.get(state.controller_id)
            team = (trainer.team or trainer.identifier) if trainer else state.controller_id
            hp_text = self._format_hp_bar(state.hp, state.max_hp())
            status_text = self._format_status_text(state, include_duration=True) or "-"
            pos = state.position
            cs = state.combat_stages
            cs_text = (
                f"A:{cs.get('atk', 0)} D:{cs.get('def', 0)} "
                f"SA:{cs.get('spatk', 0)} SD:{cs.get('spdef', 0)} "
                f"S:{cs.get('spd', 0)} Acc:{cs.get('accuracy', 0)}"
            )
            abilities = state.ability_names()
            stats_text = self._stats_with_deltas_text(state)
            caps_text = self._capabilities_text(state)
            injury_penalty = self._injury_penalty_preview(battle, combatant_id)
            row = [
                markers.get(combatant_id, "?"),
                state.spec.name or state.spec.species,
                trainer.name if trainer else state.controller_id,
                team,
                hp_text,
                str(state.temp_hp or 0),
                str(state.injuries or 0),
                str(injury_penalty),
                status_text,
                f"({pos[0]},{pos[1]})" if pos else "-",
                cs_text,
                ", ".join(abilities) if abilities else "-",
                stats_text,
                caps_text,
            ]
            if state.active:
                active_table.add_row(*row)
            else:
                bench_table.add_row(*row)
        renderables: List[object] = [active_table]
        current_actor = battle.current_actor_id
        if current_actor:
            summary = battle.action_budget_summary(current_actor)
            if summary:
                renderables.append(Text.from_markup(f"[cyan]{summary}[/cyan]"))
        if bench_ids:
            renderables.append(Text("Party (Bench)", style="dim"))
            renderables.append(bench_table)
        if len(renderables) == 1:
            return renderables[0]
        return Group(*renderables)

    def _stats_with_deltas_text(self, state: RulesPokemonState) -> str:
        atk = calculations.offensive_stat(state, "physical")
        spatk = calculations.offensive_stat(state, "special")
        defense = calculations.defensive_stat(state, "physical")
        spdef = calculations.defensive_stat(state, "special")
        spd = calculations.speed_stat(state)
        return (
            f"Atk {self._stat_with_delta(state.spec.atk, atk)} "
            f"Def {self._stat_with_delta(state.spec.defense, defense)} "
            f"SpA {self._stat_with_delta(state.spec.spatk, spatk)} "
            f"SpD {self._stat_with_delta(state.spec.spdef, spdef)} "
            f"Spd {self._stat_with_delta(state.spec.spd, spd)}"
        )

    def _stat_with_delta(self, base: int, actual: int) -> str:
        try:
            delta = int(actual) - int(base)
        except (TypeError, ValueError):
            return str(actual)
        sign = "+" if delta >= 0 else ""
        return f"{actual} ({sign}{delta})"

    def _capabilities_text(self, state: RulesPokemonState) -> str:
        spec = state.spec
        movement = spec.movement or {}
        move_text = (
            f"O{movement.get('overland', 0)} S{movement.get('swim', 0)} Sk{movement.get('sky', 0)} "
            f"Lv{movement.get('levitate', 0)} B{movement.get('burrow', 0)} "
            f"H{movement.get('h_jump', 0)} L{movement.get('l_jump', 0)} P{movement.get('power', 0)}"
        )
        caps: List[str] = []
        for entry in spec.capabilities or []:
            if isinstance(entry, str):
                caps.append(entry)
            elif isinstance(entry, dict):
                name = str(entry.get("name", "")).strip()
                if name:
                    value = entry.get("value")
                    if value not in (None, ""):
                        caps.append(f"{name} {value}")
                    else:
                        caps.append(name)
        caps_text = ", ".join(caps) if caps else "-"
        return f"Move[{move_text}] Caps[{caps_text}]"

    def _injury_penalty_preview(self, battle: RulesBattleState, actor_id: str) -> int:
        actor = battle.pokemon.get(actor_id)
        if actor is None:
            return 0
        injuries_last = getattr(battle, "_injuries_last_round", {}) or {}
        injuries_prev = getattr(battle, "_injuries_previous_round", {}) or {}
        injuries_start = injuries_last.get(actor_id, 0)
        previous_injuries = injuries_prev.get(actor_id, 0)
        gained_current = max(0, (actor.injuries or 0) - injuries_start)
        gained_previous = max(0, injuries_start - previous_injuries)
        injury_penalty = 2 * (gained_current + gained_previous)
        return -injury_penalty if injury_penalty else 0

    def _format_hp_bar(self, current: int, maximum: int, width: int = 12) -> Text:
        if maximum <= 0:
            return Text("?")
        current = max(0, int(current))
        maximum = max(1, int(maximum))
        pct = max(0.0, min(1.0, current / maximum))
        filled = int(round(pct * width))
        empty = max(0, width - filled)
        color = "green"
        if pct < 0.25:
            color = "red"
        elif pct < 0.5:
            color = "yellow"
        text = Text(f"{current}/{maximum} ", style="bold")
        text.append(f"[{'#' * filled}{'-' * empty}]", style=color)
        return text

    def _build_info_renderable(self, battle: RulesBattleState) -> object:
        lines: List[str] = []
        lines.append(f"Round: {battle.round}")
        if battle.phase:
            lines.append(f"Phase: {battle.phase.name.title()}")
        current_actor = battle.current_actor_id
        if current_actor:
            lines.append(f"Current: {self._actor_label(battle, current_actor)}")
            budget = battle.action_budget_summary(current_actor)
            if budget:
                lines.append(budget)
        last_actor = getattr(battle, "_last_action_actor_id", None)
        if last_actor:
            lines.append(f"Last action: {self._actor_label(battle, last_actor)}")
        if self._pending_prompt:
            lines.append(f"Input: {self._pending_prompt}")
        elif self._last_input:
            lines.append(f"Last input: {self._last_input}")
        lines.append(f"Fast-forward: {'ON' if self._fast_forward else 'OFF'} (toggle with F)")
        if self._spectator_mode:
            lines.append("Spectator: Enter=step, B=back, R=replay, F=auto, Q=quit")
        lines.append("Input appears below. Logs update on the right.")
        return Text("\n".join(lines), style="dim")

    def _start_viewer(self, battle: RulesBattleState) -> None:
        if self._viewer_listener is not None:
            return
        auth = os.urandom(16)
        auth_hex = binascii.hexlify(auth).decode("ascii")
        listener = Listener(("127.0.0.1", 0), authkey=auth)
        port = listener.address[1]
        if getattr(sys, "frozen", False):
            args = [sys.executable, "--viewer", str(port), auth_hex]
        else:
            launcher = Path(__file__).resolve().parents[1] / "auto_ptu_launcher.py"
            args = [sys.executable, str(launcher), "--viewer", str(port), auth_hex]
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_CONSOLE
        subprocess.Popen(args, creationflags=creationflags)
        self._viewer_listener = listener
        try:
            raw_listener = getattr(listener, "_listener", None)
            raw_socket = getattr(raw_listener, "_socket", None)
            if raw_socket is not None:
                raw_socket.settimeout(5.0)
            self._viewer_conn = listener.accept()
        except Exception:
            self._viewer_conn = None
            self._viewer_listener = None
            return
        self._send_viewer_snapshot(battle)

    def _stop_viewer(self) -> None:
        if self._viewer_conn is not None:
            try:
                self._viewer_conn.send({"type": "close"})
            except Exception:
                pass
        if self._viewer_conn is not None:
            try:
                self._viewer_conn.close()
            except Exception:
                pass
        if self._viewer_listener is not None:
            try:
                self._viewer_listener.close()
            except Exception:
                pass
        self._viewer_conn = None
        self._viewer_listener = None

    def _send_viewer_snapshot(self, battle: RulesBattleState) -> None:
        if self._viewer_conn is None:
            return
        snapshot = self._build_viewer_snapshot(battle)
        try:
            self._viewer_conn.send({"type": "snapshot", "data": snapshot})
        except Exception:
            pass

    def _build_viewer_snapshot(self, battle: RulesBattleState) -> dict:
        markers = self._combatant_markers(battle)
        combatants: List[dict] = []
        occupants: Dict[Tuple[int, int], str] = {}
        for cid in self._ordered_combatants(battle):
            state = battle.pokemon[cid]
            trainer = battle.trainers.get(state.controller_id)
            trainer_label = trainer.name if trainer and trainer.name else state.controller_id
            team = (trainer.team or trainer.identifier) if trainer else state.controller_id
            pos = state.position
            if state.active and pos is not None:
                occupants[pos] = markers.get(cid, "?")
            cs = state.combat_stages
            cs_text = (
                f"A:{cs.get('atk', 0)} D:{cs.get('def', 0)} "
                f"SA:{cs.get('spatk', 0)} SD:{cs.get('spdef', 0)} "
                f"S:{cs.get('spd', 0)} Acc:{cs.get('accuracy', 0)}"
            )
            stats_text = self._stats_with_deltas_text(state)
            caps_text = self._capabilities_text(state)
            injury_penalty = self._injury_penalty_preview(battle, cid)
            combatants.append(
                {
                    "marker": markers.get(cid, "?"),
                    "name": f"{trainer_label}: {state.spec.name or state.spec.species}",
                    "team": team,
                    "trainer": trainer_label,
                    "hp": f"{state.hp}/{state.max_hp()}",
                    "temp_hp": str(state.temp_hp or 0),
                    "injuries": str(state.injuries or 0),
                    "injury_penalty": str(injury_penalty),
                    "status": self._format_status_text(state, include_duration=True) or "-",
                    "pos": f"({pos[0]},{pos[1]})" if pos else "-",
                    "cs": cs_text,
                    "abilities": ", ".join(state.ability_names()) if state.ability_names() else "-",
                    "stats": stats_text,
                    "caps": caps_text,
                    "active": bool(state.active),
                }
            )
        grid_payload = None
        if battle.grid is not None:
            tiles = [
                [coord[0], coord[1], str(meta.get("type", "")).lower()]
                for coord, meta in battle.grid.tiles.items()
            ]
            grid_payload = {
                "width": battle.grid.width,
                "height": battle.grid.height,
                "blockers": [list(coord) for coord in battle.grid.blockers],
                "tiles": tiles,
            }
        current = battle.current_actor_id
        current_pos = battle.pokemon[current].position if current and current in battle.pokemon else None
        legend_entries = [
            f"{markers[cid]}={battle.pokemon[cid].spec.name or battle.pokemon[cid].spec.species}"
            for cid in self._ordered_combatants(battle)
        ]
        info = self._build_info_renderable(battle)
        return {
            "combatants": combatants,
            "grid": grid_payload,
            "occupants": {f"{k[0]},{k[1]}": v for k, v in occupants.items()},
            "current_pos": list(current_pos) if current_pos else None,
            "legend": "Legend: " + ", ".join(legend_entries),
            "info": info.plain if hasattr(info, "plain") else str(info),
        }

    def _render_grid(self, battle: RulesBattleState) -> None:
        self._print(self._build_grid_renderable(battle))
        return
    
    def _build_grid_renderable(self, battle: RulesBattleState) -> object:
        if battle.grid is None:
            return Text("No grid.", style="dim")
        grid = battle.grid
        markers = self._combatant_markers(battle)
        occupant_map: Dict[Tuple[int, int], str] = {}
        zone_map, zone_legend = self._zone_overlay(battle)
        for cid, mon in battle.pokemon.items():
            marker = markers.get(cid, "?")
            if mon.position is None or not mon.active:
                continue
            occupant_map[mon.position] = marker
        table = Table(show_header=True, header_style="bold", box=box.ASCII)
        table.add_column("Y/X", justify="right")
        for x in range(grid.width):
            table.add_column(f"{x:02d}", justify="center")
        for y in range(grid.height):
            row_cells: List[str] = [f"{y:02d}"]
            for x in range(grid.width):
                coord = (x, y)
                if coord in occupant_map:
                    marker = occupant_map[coord]
                    current = battle.current_actor_id
                    current_pos = None
                    if current and current in battle.pokemon:
                        current_pos = battle.pokemon[current].position
                    if current_pos == coord:
                        row_cells.append(f"[bold yellow]{marker}[/bold yellow]")
                    else:
                        row_cells.append(f"[cyan]{marker}[/cyan]")
                elif coord in grid.blockers:
                    row_cells.append("[red]#[/red]")
                elif coord in zone_map:
                    row_cells.append(zone_map[coord])
                else:
                    tile_type_value = grid.tiles.get(coord, {}).get("type", "")
                    tile_type = tile_type_value.lower() if isinstance(tile_type_value, str) else ""
                    if tile_type == "water":
                        row_cells.append("[blue]~[/blue]")
                    elif tile_type in {"difficult", "rough"}:
                        row_cells.append("[yellow]*[/yellow]")
                    else:
                        row_cells.append(".")
            table.add_row(*row_cells)
        legend_entries = [
            f"{markers[cid]}={battle.pokemon[cid].spec.name or battle.pokemon[cid].spec.species}"
            for cid in self._ordered_combatants(battle)
        ]
        legend_lines: List[object] = [
            table,
            Text("Legend: " + ", ".join(legend_entries)),
            Text("#=Blocker, ~=Water, *=Difficult"),
        ]
        if zone_legend:
            legend_lines.append(Text("Zones: " + ", ".join(zone_legend)))
        return Group(*legend_lines)

    def _render_highlight_grid(
        self,
        battle: RulesBattleState,
        highlights: Dict[Tuple[int, int], str],
        label: str,
        *,
        use_colors: bool = True,
    ) -> None:
        if battle.grid is None or not highlights:
            return
        grid = battle.grid
        zone_map, _ = self._zone_overlay(battle)
        self._print(f"[cyan]{label}[/cyan]")
        table = Table(show_header=True, header_style="bold", box=box.ASCII)
        table.add_column("Y/X", justify="right")
        for x in range(grid.width):
            table.add_column(f"{x:02d}", justify="center")
        for y in range(grid.height):
            row_cells: List[str] = [f"{y:02d}"]
            for x in range(grid.width):
                coord = (x, y)
                if coord in highlights:
                    value = highlights[coord]
                    row_cells.append(value)
                elif coord in grid.blockers:
                    row_cells.append("[red]#[/red]")
                elif coord in zone_map:
                    row_cells.append(zone_map[coord])
                else:
                    tile_type_value = grid.tiles.get(coord, {}).get("type", "")
                    tile_type = tile_type_value.lower() if isinstance(tile_type_value, str) else ""
                    if tile_type == "water":
                        row_cells.append("[blue]~[/blue]")
                    elif tile_type in {"difficult", "rough"}:
                        row_cells.append("[yellow]*[/yellow]")
                    else:
                        row_cells.append(".")
            table.add_row(*row_cells)
        self._print(table)

    def _zone_overlay(
        self, battle: RulesBattleState
    ) -> Tuple[Dict[Tuple[int, int], str], List[str]]:
        zone_map: Dict[Tuple[int, int], str] = {}
        legend: List[str] = []
        effects = getattr(battle, "zone_effects", []) or []
        if not effects:
            return zone_map, legend
        symbol_map = {
            "ion deluge": ("I", "magenta"),
        }
        for effect in effects:
            name = str(effect.get("name", "")).strip()
            if not name:
                continue
            slug = name.lower()
            symbol, color = symbol_map.get(slug, (name[0].upper(), "magenta"))
            label = f"[{color}]{symbol}[/{color}]"
            for coord in effect.get("tiles", []) or []:
                try:
                    xy = (int(coord[0]), int(coord[1]))
                except (TypeError, ValueError, IndexError):
                    continue
                zone_map.setdefault(xy, label)
            legend.append(f"{symbol}={name}")
        return zone_map, legend

    def _tile_label(self, grid: RulesGridState, coord: Tuple[int, int]) -> str:
        if coord in grid.blockers:
            return "Blocker"
        tile_type_value = grid.tiles.get(coord, {}).get("type", "")
        tile_type = tile_type_value.strip().title() if isinstance(tile_type_value, str) else ""
        return tile_type or "Normal"

    def _announce_last_event(self, battle: RulesBattleState, record: BattleRecord) -> None:
        if not battle.log:
            return
        if self._last_announced_index > len(battle.log):
            self._last_announced_index = 0
        new_events = battle.log[self._last_announced_index :]
        if not new_events:
            return
        for event in new_events:
            self._print_event(battle, record, event)
        self._last_announced_index = len(battle.log)

    def _print_event(self, battle: RulesBattleState, record: BattleRecord, event: dict) -> None:
        event_type = event.get("type")
        if self._fast_forward and event_type not in {"move", "attack_of_opportunity", "faint", "status", "ability", "damage"}:
            return
        if self._live and event_type in {"phase", "turn_end"}:
            return
        actor_id = event.get("actor")
        actor_label = self._actor_label(battle, actor_id)
        if actor_id and battle.is_trainer_actor_id(actor_id):
            actor_label = f"Trainer {actor_label}"
        grid = getattr(battle, "grid", None)

        if event_type == "round_start":
            init_entries = event.get("initiative", [])
            summary_parts = []
            for entry in init_entries:
                label = self._actor_label(battle, entry.get("actor"))
                total = entry.get("total", "?")
                roll = entry.get("roll", "?")
                speed = entry.get("speed", "?")
                mod = entry.get("trainer_modifier", 0)
                summary_parts.append(f"{label}={total} (Speed {speed} + Mod {mod} + d20 {roll})")
            summary = ", ".join(summary_parts) if summary_parts else "No active combatants."
            text = f"--- Round {event.get('round', '?')} begins. Initiative: {summary} ---"
        elif event_type == "turn_start":
            info = event.get("initiative", {})
            total = info.get("total", "?")
            roll = info.get("roll", "?")
            speed = info.get("speed", "?")
            text = (
                f"{self._possessive_label(actor_label)} turn begins "
                f"(Speed {speed} + d20 {roll} = {total})."
            )
        elif event_type == "phase":
            phase = event.get("phase", "").title()
            text = f"{actor_label} enters the {phase} phase."
        elif event_type == "turn_end":
            text = f"{self._possessive_label(actor_label)} turn ends."
        elif event_type == "action_declared":
            detail = event.get("detail") or "an action"
            text = f"{actor_label} declares {detail}."
        elif event_type == "move":
            text = self._describe_move_event(battle, event)
        elif event_type == "action":
            action_type = event.get("action_type", "action").capitalize()
            detail = event.get("detail") or "acted"
            text = f"{actor_label} {detail} ({action_type})."
            if not (event.get("description") or "").strip():
                recent_move = self._find_recent_move_event(
                    battle,
                    event.get("actor"),
                    ignore_event=event,
                )
                if recent_move:
                    move_context = self._describe_move_event(
                        battle,
                        recent_move,
                        include_actor=False,
                    )
                    if move_context:
                        text = f"{move_context} | {text}"
        elif event_type == "maneuver":
            effect = event.get("effect")
            reason = event.get("reason")
            if effect == "intercept_blocked":
                reason_text = reason.replace("_", " ") if reason else "blocked"
                text = f"{actor_label} could not Intercept ({reason_text})."
            elif effect == "intercept":
                target_label = self._actor_label(battle, event.get("target"))
                outcome = "succeeds" if event.get("success") else "fails"
                reason_text = event.get("reason")
                detail = f" ({reason_text})" if reason_text and reason_text != "success" else ""
                text = f"{actor_label} attempts Intercept on {target_label} and {outcome}{detail}."
            else:
                text = f"{actor_label} performs a maneuver."
        elif event_type == "attack_of_opportunity":
            text = self._describe_move_event(battle, event)
        elif event_type == "switch":
            target_label = self._actor_label(battle, event.get("target"))
            text = f"{actor_label} switches to {target_label}."
        elif event_type == "shift":
            origin = event.get("from")
            dest = event.get("to")
            origin_label = (
                self._tile_label(grid, origin) if origin and grid else None
            )
            dest_label = self._tile_label(grid, dest) if dest and grid else None
            origin_text = f" from ({origin[0]},{origin[1]}) [{origin_label}]" if origin else ""
            dest_text = f" to ({dest[0]},{dest[1]}) [{dest_label}]" if dest else ""
            text = f"{actor_label} shifted{origin_text}{dest_text}."
        elif event_type == "pass":
            text = f"{actor_label} skips their turn."
        elif event_type == "status_skip":
            status_name = (event.get("status", "") or "").replace("_", " ").title()
            reason = (event.get("reason") or "status").replace("_", " ").title()
            text = f"{actor_label}'s turn is skipped ({status_name}: {reason})."
        elif event_type == "status":
            text = self._describe_status_event(battle, event)
        elif event_type == "focus_check":
            label = event.get("label", "check")
            dc = event.get("dc", "?")
            roll = event.get("roll", "?")
            skill = event.get("skill", "?")
            total = event.get("total", roll)
            penalty = event.get("penalty", 0)
            outcome = "passes" if event.get("success") else "fails"
            text = (
                f"{actor_label} {outcome} Focus check ({label}) "
                f"DC {dc} (roll {roll} + skill {skill} = {total}), penalty {penalty:+d}."
            )
        elif event_type == "injury_penalty":
            amount = int(event.get("amount", 0) or 0)
            reason = event.get("reason", "injury penalty")
            text = f"{actor_label} suffers {reason} ({amount:+d})."
        elif event_type == "injury_damage":
            amount = int(event.get("amount", 0) or 0)
            injuries = event.get("injuries")
            detail = f" (injuries: {injuries})" if injuries is not None else ""
            text = f"{actor_label} loses {amount} HP from injuries{detail}."
        elif event_type == "injury_stage_loss":
            stat = str(event.get("stat", "")).upper()
            amount = int(event.get("amount", 0) or 0)
            new_stage = event.get("new_stage")
            stage_text = f" new stage {new_stage}" if new_stage is not None else ""
            text = f"{actor_label} suffers injury stage loss: {stat} {amount:+d}{stage_text}."
        elif event_type == "ability":
            ability = event.get("ability", "Ability")
            result = event.get("result", "")
            amount = event.get("amount")
            status_name = (event.get("status", "") or "").replace("_", " ").title()
            if result == "heal" and amount:
                text = f"{actor_label}'s {ability} heals {amount} HP (status: {status_name})."
            elif result == "cure" and status_name:
                text = f"{actor_label}'s {ability} cured {status_name} (roll {event.get('roll', '?')})."
            elif result == "failed":
                text = f"{actor_label}'s {ability} did not trigger (roll {event.get('roll', '?')})."
            else:
                text = f"{actor_label}'s {ability} triggered."
        else:
            text = f"{actor_label} acted."
        description = (event.get("description") or "").strip()
        if description:
            if text and text[-1] not in ".!?":
                text = f"{text}."
            text = f"{text} {description}"
        positions = self._positions_summary(battle)
        summary_parts: List[str] = [text]
        if positions:
            summary_parts.append(f"Positions: {positions}")
        text_with_pos = " | ".join(summary_parts)
        self._print(text_with_pos)
        record.turns.append(text_with_pos)

    def _describe_move_event(
        self,
        battle: RulesBattleState,
        event: dict,
        *,
        include_actor: bool = True,
    ) -> str:
        actor_label = self._actor_label(battle, event.get("actor"))
        event_type = event.get("type")
        result = event.get("result") or {}
        move_name = event.get("move") or result.get("move") or "Move"
        target_actor_id = event.get("target")
        target_label = (
            self._actor_label(battle, target_actor_id) if target_actor_id else None
        )
        verb = "unleashes" if event.get("hit") else "attempts"
        if event_type == "attack_of_opportunity":
            reason = event.get("reason")
            reason_text = f" ({reason})" if reason else ""
            base_sentence = f"{actor_label} seizes an Attack of Opportunity{reason_text} with {move_name}"
        else:
            subject = f"{actor_label} {verb}" if include_actor else verb.title()
            base_sentence = f"{subject} {move_name}"
        if target_label:
            base_sentence += f" on {target_label}"

        dice_label = self._format_dice_from_components(event.get("db_components"))

        def _provided(value: object) -> bool:
            if value is None:
                return False
            if isinstance(value, str):
                if not value.strip():
                    return False
                if value.strip().lower() == "none":
                    return False
            return True

        accuracy_parts: List[str] = []
        roll = event.get("roll")
        needed = event.get("needed")
        roll_provided = _provided(roll)
        needed_provided = _provided(needed)
        if roll_provided and needed_provided:
            accuracy_parts.append(f"Accuracy {roll} vs {needed}")
        elif roll_provided:
            accuracy_parts.append(f"Accuracy {roll}")
        elif needed_provided:
            accuracy_parts.append(f"Target {needed}")
        if dice_label not in {"", "-"}:
            accuracy_parts.append(f"Dice {dice_label}")
        accuracy_section = " | ".join(accuracy_parts)

        narrative_lines: List[str] = [f"{base_sentence}."]
        if accuracy_section:
            narrative_lines.append(f"Accuracy check: {accuracy_section}.")
        accuracy_adjust = event.get("accuracy_adjust")
        if isinstance(accuracy_adjust, int) and accuracy_adjust:
            narrative_lines.append(f"Accuracy modifier: {accuracy_adjust:+d}.")

        weapon_parts: List[str] = []
        if event.get("weapon"):
            weapon_parts.append(f"Weapon {event.get('weapon')}")
            if event.get("weapon_db_bonus"):
                weapon_parts.append(f"DB +{event.get('weapon_db_bonus')}")
            if event.get("weapon_accuracy_bonus"):
                weapon_parts.append(f"Acc +{event.get('weapon_accuracy_bonus')}")
        if weapon_parts:
            narrative_lines.append(f"Weapon bonuses: {', '.join(weapon_parts)}.")

        damage_value = int(event.get("damage", 0) or 0)
        target_hp = event.get("target_hp")
        target_descriptor = target_label or "Target"
        is_status = (event.get("category") or "").strip().lower() == "status"
        if event.get("hit") and not is_status:
            dmg_roll = event.get("damage_roll")
            db = event.get("effective_db")
            type_mult = float(event.get("type_multiplier", 1.0) or 1.0)
            detail_parts: List[str] = []
            if db is not None:
                detail_parts.append(f"DB {db}")
            if dmg_roll is not None:
                detail_parts.append(f"roll {dmg_roll}")
            damage_line = f"{target_descriptor} takes {damage_value} damage"
            if detail_parts:
                damage_line += " (" + " | ".join(detail_parts) + ")"
            if type_mult != 1.0:
                damage_line += f" at {type_mult}x effectiveness"
            damage_line += "."
            if target_hp is not None:
                damage_line += f" HP now {target_hp}."
            narrative_lines.append(damage_line)
            if damage_value > 0:
                narrative_lines.append(f"Damage applied: {damage_value}.")
        elif not event.get("hit"):
            miss_target = target_label or "its mark"
            narrative_lines.append(f"The attack misses {miss_target}.")

        target_pos = event.get("target_position")
        if target_pos:
            try:
                x, y = target_pos
            except Exception:
                pass
            else:
                narrative_lines.append(f"Landing tile: ({x},{y}).")

        area_kind = event.get("area")
        tiles = event.get("area_tiles") or []
        if area_kind:
            area_label = str(area_kind).title()
            if tiles:
                footprint = ", ".join(f"({coord[0]},{coord[1]})" for coord in tiles)
                narrative_lines.append(f"Area {area_label} -> {footprint}.")
            else:
                narrative_lines.append(f"Area {area_label}.")
        return " ".join(narrative_lines).strip()

    def _find_recent_move_event(
        self,
        battle: RulesBattleState,
        actor_id: Optional[str],
        *,
        ignore_event: Optional[dict] = None,
    ) -> Optional[dict]:
        if not actor_id:
            return None
        for candidate in reversed(battle.log or []):
            if candidate is ignore_event:
                continue
            if candidate.get("actor") != actor_id:
                continue
            if candidate.get("type") in {"move", "attack_of_opportunity"}:
                return candidate
        return None

    def _describe_status_event(self, battle: RulesBattleState, event: dict) -> str:
        actor_label = self._actor_label(battle, event.get("actor"))
        status_name = (event.get("status") or "").replace("_", " ").title()
        effect = event.get("effect", "")
        if effect == "damage":
            amount = int(event.get("amount") or 0)
            return f"{actor_label} reels from {status_name}, losing {amount} HP."
        if effect == "sleep":
            remaining = event.get("remaining")
            if remaining is None:
                note = event.get("note")
                note_text = f" ({note})" if note else ""
                return f"{actor_label} is asleep and cannot act{note_text}."
            turns_label = "turn" if remaining == 1 else "turns"
            return f"{actor_label} is asleep and cannot act ({remaining} {turns_label} remaining)."
        if effect == "wake":
            reason = (event.get("reason") or "").replace("_", " ")
            reason_text = f" due to {reason}" if reason else ""
            return f"{actor_label} wakes from {status_name}{reason_text}."
        if effect in {"sleep_save", "freeze_save"}:
            roll = event.get("roll", "?")
            total = event.get("total", roll)
            dc = event.get("dc", "?")
            modifier = event.get("modifier")
            mod_text = ""
            if isinstance(modifier, int) and modifier != 0:
                sign = "+" if modifier > 0 else ""
                mod_text = f"{sign}{modifier}"
            action_text = "wake up" if effect == "sleep_save" else "thaw"
            return f"{actor_label} rolls to {action_text} ({roll}{mod_text} = {total} vs DC {dc})."
        if effect == "skip":
            roll = event.get("roll", "?")
            return f"{actor_label} is paralyzed and cannot act (roll {roll})."
        if effect == "resist":
            roll = event.get("roll", "?")
            return f"{actor_label} resists {status_name} (roll {roll})."
        if effect == "confusion":
            roll = event.get("roll", "?")
            amount = event.get("amount", 0)
            outcome = event.get("outcome")
            if outcome == "hit_self":
                return f"{actor_label} hurts itself in confusion for {amount} damage (roll {roll})."
            if outcome == "acted":
                return f"{actor_label} overcomes confusion (roll {roll})."
            if outcome == "cured":
                return f"{actor_label} snaps out of confusion (roll {roll})."
            return f"{actor_label} struggles with confusion (roll {roll})."
        return f"{actor_label} resolves {status_name}."

    def _actor_label(self, battle: RulesBattleState, actor_id: Optional[str]) -> str:
        if not actor_id:
            return "System"
        trainer = battle.trainers.get(actor_id)
        if trainer:
            return trainer.name or trainer.identifier
        mon = battle.pokemon.get(actor_id)
        if not mon:
            return actor_id
        trainer = battle.trainers.get(mon.controller_id)
        name = mon.spec.name or mon.spec.species
        trainer_name = trainer.name if trainer else mon.controller_id
        return f"{name} ({trainer_name})"

    @staticmethod
    def _possessive_label(label: str) -> str:
        stripped = label.rstrip()
        if not stripped:
            return label
        if stripped.endswith(("s", "S")):
            return f"{label}'"
        return f"{label}'s"

    def _prompt_for_move_interactive(
        self,
        moves: Sequence[MoveSpec],
        battle: Optional[RulesBattleState] = None,
        actor_id: Optional[str] = None,
    ) -> MoveSpec:
        table = Table("No.", "Move", "Type", "Category", "Range", "AC", "DB", "Dice", "Freq", "Effects")
        for idx, move in enumerate(moves, start=1):
            display_move = move
            if battle is not None and actor_id is not None:
                display_move = self._adjust_maneuver_for_telekinetic(battle, actor_id, move)
            db_value = display_move.db or 0
            table.add_row(
                str(idx),
                display_move.name,
                display_move.type,
                display_move.category,
                self._format_range_label(display_move),
                str(display_move.ac if display_move.ac is not None else "-"),
                str(db_value) if db_value > 0 else "-",
                self._format_dice_label(db_value),
                display_move.freq,
                self._short_effects(display_move.effects_text),
            )
        self._print(table)
        while True:
            raw = self._input(f"Choose your move [1-{len(moves)}]: ").strip()
            if not raw:
                continue
            if raw.isdigit():
                choice = int(raw)
                if 1 <= choice <= len(moves):
                    return moves[choice - 1]
            self._print("[yellow]Invalid choice. Enter the move number.[/yellow]")


    def _maneuver_moves(self) -> List[MoveSpec]:
        cache = getattr(self, "_maneuver_cache", None)
        if cache is not None:
            return list(cache)
        maneuvers = ["Grapple", "Disarm", "Trip", "Push", "Dirty Trick", "Hinder", "Blind", "Low Blow"]
        maneuver_rules = {
            "grapple": {
                "ac": 4,
                "effects": "Opposed Combat/Athletics; on win both Grappled and you gain Dominance.",
            },
            "disarm": {
                "ac": 6,
                "effects": "Opposed Combat/Stealth; on win target drops held item.",
            },
            "trip": {
                "ac": 6,
                "effects": "Opposed Combat/Acrobatics; on win target is Tripped.",
            },
            "push": {
                "ac": 4,
                "effects": "Opposed Combat/Athletics; on win push 1m (requires Heavy Lifting).",
            },
            "dirty trick": {
                "ac": 2,
                "effects": "Choose Hinder, Blind, or Low Blow (once/scene/target).",
            },
            "hinder": {
                "ac": 2,
                "effects": "Opposed Athletics; on win target Slowed and -2 skill checks 1 round.",
            },
            "blind": {
                "ac": 2,
                "effects": "Opposed Stealth; on win target Blinded 1 round.",
            },
            "low blow": {
                "ac": 2,
                "effects": "Opposed Acrobatics; on win target Vulnerable and initiative 0 until end of next turn.",
            },
        }
        data_path = Path(__file__).resolve().parents[1] / "data" / "compiled" / "moves.json"
        compiled: Dict[str, dict] = {}
        if data_path.exists():
            try:
                raw = json.loads(data_path.read_text(encoding="utf-8"))
            except Exception:
                raw = []
            for entry in raw or []:
                name = str(entry.get("name") or "").strip()
                if name:
                    compiled[name.lower()] = entry
        built: List[MoveSpec] = []
        for name in maneuvers:
            entry = compiled.get(name.lower(), {})
            rules = maneuver_rules.get(name.lower(), {})
            move = MoveSpec(
                name=name,
                type=entry.get("type", "") or "Normal",
                category=entry.get("category", "Status"),
                db=0,
                ac=rules.get("ac", entry.get("ac") if entry.get("ac") not in (None, "") else 2),
                range_kind="Melee",
                range_value=1,
                target_kind="Melee",
                target_range=1,
                freq="Standard",
                range_text="Melee, 1 Target",
                effects_text=rules.get("effects", entry.get("effects", "")),
            )
            built.append(move)
        self._maneuver_cache = built
        return list(built)


    # ----- Formatting helpers shared by legacy + interactive tables -----

    @staticmethod
    def _format_range_label(move: object) -> str:
        """Return a PTU-style range label such as 'Melee', 'Burst 2', or 'Line 6'."""
        range_text = getattr(move, "range_text", None)
        if isinstance(range_text, str) and range_text.strip():
            return range_text.strip()
        kind = getattr(move, "range_kind", None) or "Melee"
        value = getattr(move, "range_value", None)
        if value in (None, "", 0):
            return str(kind)
        return f"{kind} {value}"

    def _format_dice_label(self, db_value: Optional[int]) -> str:
        """Translate a Damage Base into its dice expression (e.g., DB 8 -> 2d8+10)."""
        if not db_value or db_value <= 0:
            return "-"
        n, s, p = ptu_engine.db_to_dice(int(db_value))
        return self._dice_label_from_parts(n, s, p)

    def _format_dice_from_components(self, components: Optional[Sequence[int]]) -> str:
        """Render dice that were already expanded (n dice, sides, plus flat bonus)."""
        if not components or len(components) != 3:
            return "-"
        try:
            n, s, p = (int(components[0]), int(components[1]), int(components[2]))
        except (TypeError, ValueError):
            return "-"
        if n == 0 and s == 0 and p == 0:
            return "-"
        return self._dice_label_from_parts(n, s, p)

    @staticmethod
    def _dice_label_from_parts(n: int, s: int, p: int) -> str:
        """Convert raw dice parts into `2d8+6` style strings."""
        dice_part = f"{n}d{s}" if n > 0 and s > 0 else ""
        flat_part = ""
        if p:
            sign = "+" if p > 0 else "-"
            flat_part = f"{sign}{abs(p)}"
        if dice_part and flat_part:
            return f"{dice_part}{flat_part}"
        if dice_part:
            return dice_part
        if flat_part:
            return flat_part.lstrip("+")
        return "-"

    @staticmethod
    def _short_effects(effects_text: Optional[str]) -> str:
        """Condense rich effect text into a single readable line for the console."""
        if not effects_text:
            return "-"
        collapsed = " ".join(effects_text.split())
        if len(collapsed) <= 80:
            return collapsed
        return collapsed[:77] + "..."


__all__ = ["BattleRecord", "TextBattleSession", "MoveSelector"]
