from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..rules import ai_hybrid


@dataclass
class MCTSConfig:
    root_width: int = 4
    iterations: int = 18
    exploration: float = 1.1


def choose_action(
    battle,
    actor_id: str,
    *,
    ai_level: str = "standard",
    profile_store=None,
    config: Optional[MCTSConfig] = None,
) -> Tuple[object | None, Dict[str, object]]:
    if str(ai_level or "").strip().lower() not in {"strategic", "mcts", "strategic-mcts"}:
        return None, {"reason": "mcts_disabled"}
    cfg = config or MCTSConfig()
    candidates = ai_hybrid.generate_candidates(battle, actor_id)
    if not candidates:
        return None, {"reason": "mcts_no_candidates"}
    scored = [(ai_hybrid.score_action(battle, actor_id, action), action) for action in candidates]
    scored.sort(key=lambda item: item[0], reverse=True)
    roots = [action for _, action in scored[: max(1, int(cfg.root_width))]]
    if not roots:
        return None, {"reason": "mcts_no_roots"}
    stats: Dict[str, Dict[str, float]] = {
        ai_hybrid._action_label(action): {"visits": 0.0, "value": 0.0} for action in roots
    }
    action_map = {ai_hybrid._action_label(action): action for action in roots}
    for _ in range(max(1, int(cfg.iterations))):
        total_visits = sum(entry["visits"] for entry in stats.values()) + 1.0
        label = max(
            stats,
            key=lambda key: _uct_score(stats[key]["value"], stats[key]["visits"], total_visits, cfg.exploration),
        )
        action = action_map[label]
        value = _rollout_value(battle, actor_id, action, profile_store=profile_store)
        stats[label]["visits"] += 1.0
        stats[label]["value"] += value
    best_label = max(
        stats,
        key=lambda key: (stats[key]["value"] / max(1.0, stats[key]["visits"]), stats[key]["visits"]),
    )
    best_action = action_map[best_label]
    ranked = []
    for label, entry in sorted(
        stats.items(),
        key=lambda item: (item[1]["value"] / max(1.0, item[1]["visits"]), item[1]["visits"]),
        reverse=True,
    ):
        ranked.append(
            {
                "label": label,
                "mean_value": round(entry["value"] / max(1.0, entry["visits"]), 3),
                "visits": int(entry["visits"]),
            }
        )
    return best_action, {
        "reason": "mcts_search",
        "mcts": {
            "iterations": int(cfg.iterations),
            "root_width": int(cfg.root_width),
            "ranked": ranked[: max(1, int(cfg.root_width))],
        },
    }


def _uct_score(total_value: float, visits: float, total_visits: float, exploration: float) -> float:
    if visits <= 0:
        return float("inf")
    mean = total_value / visits
    return mean + exploration * math.sqrt(math.log(max(1.0, total_visits)) / visits)


def _rollout_value(battle, actor_id: str, action, *, profile_store=None) -> float:
    sim = ai_hybrid._clone_battle(battle)
    ai_hybrid._simulate_action(sim, actor_id, action)
    value = ai_hybrid.score_state(sim, actor_id)
    opponents = ai_hybrid._opponent_ids(sim, actor_id)
    if opponents:
        response = ai_hybrid._opponent_response(
            sim,
            opponents[0],
            ai_hybrid._DEFAULT_CONFIG,
            profile_store or ai_hybrid.get_profile_store(),
        )
        if response:
            ai_hybrid._simulate_action(sim, opponents[0], response)
            value = ai_hybrid.score_state(sim, actor_id)
    return float(value)

