from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from typing import Any, Dict, Iterable

from ..api.engine_facade import EngineFacade
from ..csv_repository import PTUCsvRepository
from ..random_campaign import CsvRandomCampaignBuilder
from .catalogs import REGIONS
from .models import BattleSpec, BattleTranscript
from .paldea import build_paldea_spec


_VOLATILE_KEYS = {
    "timestamp", "timestamp_utc", "time", "battle_log_path", "ai_diagnostics",
    "ai_learning", "ai_model",
}


def simulate_battle(spec: BattleSpec, *, max_steps: int = 600) -> BattleTranscript:
    """Resolve one match with a fresh, isolated AutoPTU engine instance."""
    repo = PTUCsvRepository(rng=random.Random(spec.seed))
    builder = CsvRandomCampaignBuilder(repo=repo, seed=spec.seed)
    home_level = max(1, spec.level + spec.home_level_bonus)
    away_level = max(1, spec.level + spec.away_level_bonus)
    home = _build_species(repo, builder, spec.home_species, home_level)
    away = _build_species(repo, builder, spec.away_species, away_level)
    home.name = spec.home_species
    away.name = spec.away_species
    payload = {
        "name": f"{spec.home_club} vs {spec.away_club}",
        "description": f"{REGIONS[spec.region].label} {spec.league.title()} League",
        "active_slots": 1,
        "sides": [
            {
                "id": "career-home",
                "name": spec.home_club,
                "controller": "ai",
                "team": "career-home",
                "ai_level": "standard",
                "pokemon": [home.to_engine_dict()],
                "start_positions": [[2, 4]],
            },
            {
                "id": "career-away",
                "name": spec.away_club,
                "controller": "ai",
                "team": "career-away",
                "ai_level": "standard",
                "pokemon": [away.to_engine_dict()],
                "start_positions": [[12, 4]],
            },
        ],
        "grid": {"width": 15, "height": 9, "blockers": [], "tiles": {}},
    }
    engine = EngineFacade()
    initial = engine.start_encounter(
        battle_payload=payload,
        seed=spec.seed,
        ai_mode="ai",
        step_ai=True,
        team_size=1,
        active_slots=1,
    )
    snapshot = initial
    steps = 0
    while not snapshot.get("battle_over") and steps < max_steps:
        snapshot = engine.ai_step()
        steps += 1
    if not snapshot.get("battle_over"):
        engine.stop_battle()
    exported = engine.export_battle_log()
    canonical_events = [_canonical_value(event) for event in exported.get("log", [])]
    canonical_events = [event for event in canonical_events if isinstance(event, dict)]
    initial_state = _compact_state(initial)
    final_state = _compact_state(snapshot)
    digest_payload = {
        "spec": _canonical_value({key: value for key, value in spec.__dict__.items() if key != "id"}),
        "winner_team": snapshot.get("winner_team"),
        "rounds": int(snapshot.get("round") or 0),
        "events": canonical_events,
        "initial_state": initial_state,
        "final_state": final_state,
    }
    digest = hashlib.sha256(
        json.dumps(digest_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team=snapshot.get("winner_team"),
        winner_label=snapshot.get("winner_label"),
        rounds=int(snapshot.get("round") or 0),
        events=canonical_events,
        initial_state=initial_state,
        final_state=final_state,
        sha256=digest,
    )


def _build_species(repo: PTUCsvRepository, builder: CsvRandomCampaignBuilder, species: str, level: int):
    if repo.get_species(species) is not None:
        mon = repo.build_pokemon_spec(species, level=level, assign_abilities=True, assign_nature=True)
    else:
        mon = build_paldea_spec(species, level, repo)
    builder._apply_level_up_stats(mon)
    return mon


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
            if str(key) not in _VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, set):
        return [_canonical_value(item) for item in sorted(value, key=lambda item: str(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _compact_state(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    combatants = []
    for entry in snapshot.get("combatants", []) or []:
        combatants.append(
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "species": entry.get("species"),
                "team": entry.get("team"),
                "level": int(entry.get("level") or 1),
                "hp": entry.get("hp"),
                "max_hp": entry.get("max_hp"),
                "position": deepcopy(entry.get("position")),
                "statuses": deepcopy(entry.get("statuses") or []),
                "sprite_url": entry.get("sprite_url"),
                "stats": _canonical_value(entry.get("stats") or {}),
                "effective_stats": _canonical_value(entry.get("effective_stats") or {}),
                "abilities": sorted(str(value) for value in (entry.get("abilities") or [])),
                "moves": sorted(
                    (
                        {
                            "name": str(move.get("name") or ""),
                            "type": str(move.get("type") or ""),
                            "category": str(move.get("category") or ""),
                            "db": move.get("db"),
                            "ac": move.get("ac"),
                            "range": str(move.get("range") or ""),
                        }
                        for move in (entry.get("moves") or [])
                        if isinstance(move, dict) and str(move.get("name") or "").strip()
                    ),
                    key=lambda move: (move["name"].lower(), move["type"].lower()),
                ),
            }
        )
    combatants.sort(key=lambda entry: str(entry.get("id") or ""))
    return {
        "round": int(snapshot.get("round") or 0),
        "battle_over": bool(snapshot.get("battle_over")),
        "winner_team": snapshot.get("winner_team"),
        "grid": _canonical_value(snapshot.get("grid")),
        "combatants": combatants,
    }
