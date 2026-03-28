"""AI vs AI batch battle runner (shared by CLI and launcher)."""

from __future__ import annotations

import io
import json
import multiprocessing as mp
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .rich_compat import ensure_rich_unicode

ensure_rich_unicode()

from rich.console import Console

from .gameplay import BattleRecord, TextBattleSession
from .matchmaker import AutoMatchPlanner
from .random_campaign import CsvRandomCampaignBuilder
from .rules import ai_hybrid

_WINDOWS_MP_MAX_WORKERS = 16
_NON_WINDOWS_MP_MAX_WORKERS = 64


def _prepare_parallel_env() -> None:
    # Keep per-process BLAS thread fanout bounded when many workers are spawned.
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")


@dataclass
class BattleJob:
    seed: int
    team_size: int
    min_level: int
    max_level: int
    max_turns: int
    depth: int
    top_k: int
    top_m: int
    rollouts: int
    include_full_log: bool = False


@dataclass
class BattleResult:
    seed: int
    team_size: int
    min_level: int
    max_level: int
    turns: int
    ok: bool
    winner: str = ""
    error: Optional[str] = None
    summary: Dict[str, Dict[str, int]] = field(default_factory=dict)
    roster: Dict[str, List[str]] = field(default_factory=dict)
    log: Optional[List[dict]] = None

    def to_record(self, *, include_log: bool = False) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "seed": self.seed,
            "team_size": self.team_size,
            "min_level": self.min_level,
            "max_level": self.max_level,
            "turns": self.turns,
            "ok": self.ok,
            "winner": self.winner,
            "error": self.error,
            "summary": self.summary,
            "roster": self.roster,
        }
        if include_log:
            payload["log"] = self.log or []
        return payload


def _alive_teams(battle) -> Set[str]:
    teams: Set[str] = set()
    for mon in battle.pokemon.values():
        if mon.hp is None or mon.hp <= 0:
            continue
        trainer = battle.trainers.get(mon.controller_id)
        team = (trainer.team or trainer.identifier) if trainer else mon.controller_id
        teams.add(team or mon.controller_id)
    return teams


def _winner_team(battle) -> str:
    alive = _alive_teams(battle)
    if not alive:
        return "draw"
    if len(alive) > 1:
        return "unfinished"
    return next(iter(alive))


def _summarize_log(log: List[dict]) -> Dict[str, Dict[str, int]]:
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
    return {
        "moves": moves,
        "statuses": statuses,
        "hazards": hazards,
        "abilities": abilities,
    }


def _build_roster(plan) -> Dict[str, List[str]]:
    roster: Dict[str, List[str]] = {}
    matchup = plan.matchups[0]
    for side in matchup.sides_or_default():
        key = side.identifier or side.name
        roster[key] = [mon.name or mon.species for mon in side.pokemon]
    return roster


def _run_single(job: BattleJob) -> BattleResult:
    ai_hybrid._DEFAULT_CONFIG.depth = job.depth
    ai_hybrid._DEFAULT_CONFIG.top_k = job.top_k
    ai_hybrid._DEFAULT_CONFIG.top_m = job.top_m
    ai_hybrid._DEFAULT_CONFIG.rollouts = job.rollouts

    builder = CsvRandomCampaignBuilder(seed=job.seed)
    spec = builder.build(
        team_size=job.team_size, min_level=job.min_level, max_level=job.max_level
    )
    plan = AutoMatchPlanner(spec, seed=job.seed).create_plan(team_size=job.team_size)
    for side in plan.matchups[0].sides:
        side.controller = "ai"

    session = TextBattleSession(
        plan,
        console=Console(file=io.StringIO(), force_terminal=False),
        viewer_enabled=False,
        spectator_enabled=False,
    )
    record = BattleRecord(matchup=plan.matchups[0])
    battle = session._build_battle_state(1, plan.matchups[0])
    turns = 0
    winner = "unfinished"
    error: Optional[str] = None
    ok = True
    try:
        while not session._battle_finished(battle):
            entry = battle.advance_turn()
            if entry is None:
                break
            controller_kind = session._controller_kind_for_actor(battle, entry.actor_id)
            if battle.is_trainer_actor_id(entry.actor_id):
                if controller_kind == "player":
                    ok = False
                    error = "player controller encountered"
                    break
                session._ai_trainer_turn(battle, record, entry.actor_id)
            else:
                if controller_kind == "player":
                    ok = False
                    error = "player controller encountered"
                    break
                session._ai_turn(battle, record, entry.actor_id)
            battle.end_turn()
            turns += 1
            if turns >= job.max_turns:
                ok = False
                error = f"turn limit {job.max_turns} exceeded"
                break
        winner = _winner_team(battle)
    except Exception as exc:
        ok = False
        error = f"{type(exc).__name__}: {exc}"

    summary = _summarize_log(battle.log)
    roster = _build_roster(plan)
    return BattleResult(
        seed=job.seed,
        team_size=job.team_size,
        min_level=job.min_level,
        max_level=job.max_level,
        turns=turns,
        ok=ok,
        winner=winner,
        error=error,
        summary=summary,
        roster=roster,
        log=list(battle.log) if job.include_full_log else None,
    )


def _persist_results(
    results: List[BattleResult],
    *,
    root_dir: Optional[Path] = None,
    include_full_log: bool = False,
    metadata: Optional[Dict[str, object]] = None,
) -> Path:
    base = root_dir or (Path("reports") / "simulations")
    run_id = datetime.now(timezone.utc).strftime("ai_batch_%Y%m%d-%H%M%S")
    run_dir = base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    results_path = run_dir / "results.jsonl"
    ordered = sorted(results, key=lambda entry: entry.seed)
    with results_path.open("w", encoding="utf-8") as handle:
        for result in ordered:
            handle.write(
                json.dumps(result.to_record(include_log=include_full_log), ensure_ascii=False)
            )
            handle.write("\n")

    failures = [entry for entry in results if not entry.ok]
    winners: Dict[str, int] = {}
    for result in results:
        winners[result.winner] = winners.get(result.winner, 0) + 1

    summary_payload: Dict[str, object] = {
        "run_id": run_id,
        "totals": {
            "battles": len(results),
            "passed": len(results) - len(failures),
            "failed": len(failures),
        },
        "winners": winners,
        "average_turns": (
            sum(entry.turns for entry in results) / len(results) if results else 0.0
        ),
        "failed_seeds": [
            {"seed": entry.seed, "error": entry.error, "turns": entry.turns}
            for entry in sorted(failures, key=lambda item: item.seed)
        ],
        "results_file": str(results_path),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "include_full_log": include_full_log,
        "metadata": metadata or {},
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return run_dir


def run_ai_battles(
    *,
    total: int = 10,
    seed: int = 1,
    parallel: int = 4,
    team_size: int = 1,
    min_level: int = 20,
    max_level: int = 40,
    max_turns: int = 1000,
    depth: int = 2,
    top_k: int = 4,
    top_m: int = 2,
    rollouts: int = 2,
    randomize: bool = False,
    store_results: bool = True,
    store_dir: Optional[Path] = None,
    store_full_log: bool = False,
) -> int:
    _prepare_parallel_env()
    rng = random.Random()
    rng.seed(int.from_bytes(os.urandom(8), "big"))
    jobs = []
    for i in range(total):
        if randomize:
            job_seed = rng.randint(1, 1_000_000_000)
            job_team_size = rng.randint(1, 3)
            job_min_level = rng.randint(5, 50)
            job_max_level = min(60, job_min_level + rng.randint(0, 20))
        else:
            job_seed = seed + i
            job_team_size = team_size
            job_min_level = min_level
            job_max_level = max_level
        jobs.append(
            BattleJob(
                seed=job_seed,
                team_size=job_team_size,
                min_level=job_min_level,
                max_level=job_max_level,
                max_turns=max_turns,
                depth=depth,
                top_k=top_k,
                top_m=top_m,
                rollouts=rollouts,
                include_full_log=store_full_log,
            )
        )

    requested_parallel = max(1, int(parallel))
    cpu_cap = max(1, int(os.cpu_count() or 1))
    platform_cap = (
        _WINDOWS_MP_MAX_WORKERS if os.name == "nt" else _NON_WINDOWS_MP_MAX_WORKERS
    )
    effective_parallel = min(requested_parallel, cpu_cap, platform_cap, len(jobs))
    if effective_parallel < requested_parallel:
        print(
            f"[warn] Clamped workers from {requested_parallel} to {effective_parallel} "
            f"(cpu={cpu_cap}, platform_cap={platform_cap}, jobs={len(jobs)})."
        )

    failures = 0
    results: List[BattleResult] = []
    with mp.Pool(processes=effective_parallel) as pool:
        for result in pool.imap_unordered(_run_single, jobs):
            results.append(result)
            if result.ok:
                print(
                    f"seed {result.seed} OK ({result.turns} turns, winner={result.winner})"
                )
            else:
                failures += 1
                print(f"seed {result.seed} ERROR ({result.turns} turns): {result.error}")

    if store_results:
        output_dir = _persist_results(
            results,
            root_dir=store_dir,
            include_full_log=store_full_log,
            metadata={
                "total": total,
                "seed": seed,
                "parallel": parallel,
                "team_size": team_size,
                "min_level": min_level,
                "max_level": max_level,
                "max_turns": max_turns,
                "depth": depth,
                "top_k": top_k,
                "top_m": top_m,
                "rollouts": rollouts,
                "randomize": randomize,
            },
        )
        print(f"Stored simulation batch at {output_dir}")

    print(f"ERRORS={failures}")
    return 1 if failures else 0


__all__ = ["BattleJob", "BattleResult", "run_ai_battles"]
