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
from .ptu_builds import build_career_pokemon_spec
from .roster import LEVEL_CAPS


_VOLATILE_KEYS = {
    "timestamp", "timestamp_utc", "time", "battle_log_path", "ai_diagnostics",
    "ai_learning", "ai_model",
}


def simulate_battle(spec: BattleSpec, *, max_steps: int = 120) -> BattleTranscript:
    """Resolve one match with a fresh, isolated AutoPTU engine instance."""
    repo = PTUCsvRepository(rng=random.Random(spec.seed))
    builder = CsvRandomCampaignBuilder(repo=repo, seed=spec.seed)
    home_species = list(spec.home_team_species or [spec.home_species])
    away_species = list(spec.away_team_species or [spec.away_species])
    home_levels = list(spec.home_team_levels or [spec.level for _ in home_species])
    away_levels = list(spec.away_team_levels or [spec.level for _ in away_species])
    home_moves = list(spec.home_team_moves or [[] for _ in home_species])
    home_natures = list(spec.home_team_natures or ["" for _ in home_species])
    home_abilities = list(spec.home_team_abilities or [[] for _ in home_species])
    level_cap = LEVEL_CAPS.get(spec.league, 100)
    home_team = [
        _build_species(
            repo, builder, species, min(level_cap, max(1, home_levels[min(index, len(home_levels) - 1)] + spec.home_level_bonus)),
            taught_moves=home_moves[index] if index < len(home_moves) else [],
            nature=home_natures[index] if index < len(home_natures) else "",
            abilities=home_abilities[index] if index < len(home_abilities) else [],
        )
        for index, species in enumerate(home_species)
    ]
    away_team = [
        _build_species(repo, builder, species, min(level_cap, max(1, away_levels[min(index, len(away_levels) - 1)] + spec.away_level_bonus)))
        for index, species in enumerate(away_species)
    ]
    for pokemon, species in zip(home_team, home_species):
        pokemon.name = species
    for pokemon, species in zip(away_team, away_species):
        pokemon.name = species
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
                "ai_level": spec.home_ai_level,
                "pokemon": [pokemon.to_engine_dict() for pokemon in home_team],
                "start_positions": [[2, 4]],
            },
            {
                "id": "career-away",
                "name": spec.away_club,
                "controller": "ai",
                "team": "career-away",
                "ai_level": spec.away_ai_level,
                "pokemon": [pokemon.to_engine_dict() for pokemon in away_team],
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
        team_size=max(len(home_team), len(away_team)),
        active_slots=1,
    )
    snapshot = initial
    steps = 0
    while not snapshot.get("battle_over") and steps < max_steps:
        snapshot = engine.ai_step()
        steps += 1
    timed_out = not snapshot.get("battle_over")
    # Export while the isolated facade still owns the active session. Stopping
    # first clears the in-memory log and produced replays with zero events.
    exported = engine.export_battle_log()
    if timed_out:
        engine.stop_battle()
    canonical_events = [_canonical_value(event) for event in exported.get("log", [])]
    canonical_events = [event for event in canonical_events if isinstance(event, dict)]
    if timed_out:
        snapshot = deepcopy(snapshot)
        winner_team, team_scores = _adjudicate_turn_limit(snapshot)
        snapshot["battle_over"] = True
        snapshot["winner_team"] = winner_team
        snapshot["winner_label"] = spec.home_club if winner_team == "career-home" else spec.away_club if winner_team == "career-away" else None
        canonical_events.append({
            "type": "match_adjudicated",
            "reason": "turn_limit",
            "steps": max_steps,
            "team_scores": team_scores,
            "winner_team": winner_team,
        })
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


def _adjudicate_turn_limit(snapshot: Dict[str, Any]) -> tuple[str | None, Dict[str, int]]:
    """Resolve a rare tactical stalemate from actual PTU state, never RNG."""
    scores: Dict[str, int] = {}
    for entry in snapshot.get("combatants", []) or []:
        team = str(entry.get("team") or "")
        if not team:
            continue
        hp = max(0, int(entry.get("hp") or 0))
        max_hp = max(1, int(entry.get("max_hp") or 1))
        # Alive Pokémon dominate; remaining HP breaks ties. Integer arithmetic
        # keeps adjudication byte-stable across processes.
        scores[team] = scores.get(team, 0) + (100_000 if hp > 0 else 0) + (hp * 10_000 // max_hp)
    home = scores.get("career-home", 0)
    away = scores.get("career-away", 0)
    winner = "career-home" if home > away else "career-away" if away > home else None
    return winner, dict(sorted(scores.items()))


def _build_species(
    repo: PTUCsvRepository,
    builder: CsvRandomCampaignBuilder,
    species: str,
    level: int,
    *,
    taught_moves: Iterable[str] = (),
    nature: str = "",
    abilities: Iterable[str] = (),
):
    mon = build_career_pokemon_spec(
        repo,
        species,
        level,
        nature=nature,
        abilities=list(abilities),
        taught_moves=taught_moves,
    )
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
                "nature": str(entry.get("nature") or ""),
                "hp": entry.get("hp"),
                "max_hp": entry.get("max_hp"),
                "position": deepcopy(entry.get("position")),
                "statuses": deepcopy(entry.get("statuses") or []),
                "active": bool(entry.get("active", True)),
                "sprite_url": entry.get("sprite_url"),
                "size": str(entry.get("size") or "Medium"),
                "footprint_side": int(entry.get("footprint_side") or 1),
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
