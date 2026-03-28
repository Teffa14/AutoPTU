"""Battle audit logger for AI vs AI sanity checks."""
from __future__ import annotations

import io
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console

from .session_logger import log_session
from ..gameplay import BattleRecord, TextBattleSession
from ..matchmaker import AutoMatchPlanner
from ..random_campaign import CsvRandomCampaignBuilder
from ..rules import ai_hybrid


@dataclass
class AuditSummary:
    moves: Dict[str, int]
    statuses: Dict[str, int]
    hazards: Dict[str, int]
    abilities: Dict[str, int]


def _summarize_log(log: List[dict]) -> AuditSummary:
    moves: Dict[str, int] = {}
    statuses: Dict[str, int] = {}
    hazards: Dict[str, int] = {}
    abilities: Dict[str, int] = {}
    for entry in log:
        move = entry.get("move")
        if move:
            key = str(move)
            moves[key] = moves.get(key, 0) + 1
        if entry.get("type") == "status":
            status = entry.get("status")
            if status:
                key = str(status)
                statuses[key] = statuses.get(key, 0) + 1
        if entry.get("type") == "hazard":
            hazard = entry.get("hazard")
            if hazard:
                key = str(hazard)
                hazards[key] = hazards.get(key, 0) + 1
        if entry.get("type") == "ability":
            ability = entry.get("ability")
            if ability:
                key = str(ability)
                abilities[key] = abilities.get(key, 0) + 1
    return AuditSummary(moves=moves, statuses=statuses, hazards=hazards, abilities=abilities)


def run_audit_battle(
    *,
    seed: int = 1,
    team_size: int = 1,
    min_level: int = 20,
    max_level: int = 40,
    max_turns: int = 200,
    depth: int = 2,
    top_k: int = 4,
    top_m: int = 2,
    rollouts: int = 2,
    randomize: bool = True,
    output: Optional[Path] = None,
) -> Path:
    ai_hybrid._DEFAULT_CONFIG.depth = depth
    ai_hybrid._DEFAULT_CONFIG.top_k = top_k
    ai_hybrid._DEFAULT_CONFIG.top_m = top_m
    ai_hybrid._DEFAULT_CONFIG.rollouts = rollouts

    if randomize:
        rng = random.Random()
        rng.seed(seed)
        job_seed = rng.randint(1, 1_000_000_000)
        job_team_size = rng.randint(1, 3)
        job_min_level = rng.randint(5, 50)
        job_max_level = min(60, job_min_level + rng.randint(0, 20))
    else:
        job_seed = seed
        job_team_size = team_size
        job_min_level = min_level
        job_max_level = max_level

    builder = CsvRandomCampaignBuilder(seed=job_seed)
    spec = builder.build(team_size=job_team_size, min_level=job_min_level, max_level=job_max_level)
    plan = AutoMatchPlanner(spec, seed=job_seed).create_plan(team_size=job_team_size)
    for side in plan.matchups[0].sides:
        side.controller = "ai"

    log_session(
        mode="audit",
        campaign=spec.name,
        team_size=job_team_size,
        random_csv=True,
        tags=None,
        weather=spec.default_weather,
        seed=job_seed,
    )

    session = TextBattleSession(
        plan,
        console=Console(file=io.StringIO(), force_terminal=False),
        viewer_enabled=False,
        spectator_enabled=False,
    )
    record = BattleRecord(matchup=plan.matchups[0])
    battle = session._build_battle_state(1, plan.matchups[0])
    turns = 0
    while not session._battle_finished(battle):
        entry = battle.advance_turn()
        if entry is None:
            break
        session._ai_turn(battle, record, entry.actor_id) if not battle.is_trainer_actor_id(entry.actor_id) else session._ai_trainer_turn(battle, record, entry.actor_id)
        battle.end_turn()
        turns += 1
        if turns >= max_turns:
            break

    summary = _summarize_log(battle.log)
    payload = {
        "seed": job_seed,
        "team_size": job_team_size,
        "min_level": job_min_level,
        "max_level": job_max_level,
        "turns": turns,
        "summary": {
            "moves": summary.moves,
            "statuses": summary.statuses,
            "hazards": summary.hazards,
            "abilities": summary.abilities,
        },
        "log": battle.log,
    }
    if output is None:
        output = Path("reports") / f"audit_{job_seed}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


__all__ = ["run_audit_battle"]
