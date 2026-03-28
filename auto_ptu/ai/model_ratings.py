from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import trueskill


DEFAULT_MU = 25.0
DEFAULT_SIGMA = DEFAULT_MU / 3.0


@dataclass
class RatingStore:
    path: Path
    env: trueskill.TrueSkill

    def load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return raw if isinstance(raw, dict) else {}

    def save(self, payload: Dict[str, Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def default_store(path: Path) -> RatingStore:
    return RatingStore(path=path, env=trueskill.TrueSkill(draw_probability=0.05))


def ensure_entry(payload: Dict[str, Dict[str, Any]], model_id: str) -> Dict[str, Any]:
    entry = payload.get(model_id)
    if isinstance(entry, dict):
        entry.setdefault("mu", DEFAULT_MU)
        entry.setdefault("sigma", DEFAULT_SIGMA)
        entry.setdefault("wins", 0)
        entry.setdefault("losses", 0)
        entry.setdefault("draws", 0)
        entry.setdefault("matches", 0)
        return entry
    payload[model_id] = {
        "mu": DEFAULT_MU,
        "sigma": DEFAULT_SIGMA,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "matches": 0,
    }
    return payload[model_id]


def conservative_score(entry: Dict[str, Any]) -> float:
    return float(entry.get("mu") or DEFAULT_MU) - (3.0 * float(entry.get("sigma") or DEFAULT_SIGMA))


def record_result(
    store: RatingStore,
    *,
    winner_model_id: str | None,
    loser_model_id: str | None,
    draw: bool = False,
) -> Dict[str, Dict[str, Any]]:
    payload = store.load()
    if draw:
        if not winner_model_id or not loser_model_id:
            return payload
        first = ensure_entry(payload, winner_model_id)
        second = ensure_entry(payload, loser_model_id)
        rated_a, rated_b = store.env.rate_1vs1(
            trueskill.Rating(mu=float(first["mu"]), sigma=float(first["sigma"])),
            trueskill.Rating(mu=float(second["mu"]), sigma=float(second["sigma"])),
            drawn=True,
        )
        _write_rating(first, rated_a, draw=True)
        _write_rating(second, rated_b, draw=True)
        store.save(payload)
        return payload
    if not winner_model_id or not loser_model_id:
        return payload
    winner = ensure_entry(payload, winner_model_id)
    loser = ensure_entry(payload, loser_model_id)
    rated_winner, rated_loser = store.env.rate_1vs1(
        trueskill.Rating(mu=float(winner["mu"]), sigma=float(winner["sigma"])),
        trueskill.Rating(mu=float(loser["mu"]), sigma=float(loser["sigma"])),
    )
    _write_rating(winner, rated_winner, win=True)
    _write_rating(loser, rated_loser, loss=True)
    store.save(payload)
    return payload


def status(store: RatingStore, *, models: Optional[Dict[str, dict]] = None) -> Dict[str, Any]:
    payload = store.load()
    rows = []
    known = set(payload.keys()) | set(models.keys() if isinstance(models, dict) else [])
    for model_id in sorted(known):
        entry = ensure_entry(payload, model_id)
        rows.append(
            {
                "model_id": model_id,
                "mu": round(float(entry["mu"]), 3),
                "sigma": round(float(entry["sigma"]), 3),
                "conservative": round(conservative_score(entry), 3),
                "wins": int(entry.get("wins") or 0),
                "losses": int(entry.get("losses") or 0),
                "draws": int(entry.get("draws") or 0),
                "matches": int(entry.get("matches") or 0),
            }
        )
    rows.sort(key=lambda row: (row["conservative"], row["mu"]), reverse=True)
    return {"ratings": rows}


def _write_rating(entry: Dict[str, Any], rating: trueskill.Rating, *, win: bool = False, loss: bool = False, draw: bool = False) -> None:
    entry["mu"] = float(rating.mu)
    entry["sigma"] = float(rating.sigma)
    entry["matches"] = int(entry.get("matches") or 0) + 1
    if win:
        entry["wins"] = int(entry.get("wins") or 0) + 1
    if loss:
        entry["losses"] = int(entry.get("losses") or 0) + 1
    if draw:
        entry["draws"] = int(entry.get("draws") or 0) + 1

