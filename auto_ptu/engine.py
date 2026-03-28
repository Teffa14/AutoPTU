"""Thin wrapper around the PTU engine to run whole encounter plans."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from . import ptu_engine
from .data_models import MatchPlan, MatchupSpec, PokemonSpec


@dataclass
class MatchResult:
    matchup: MatchupSpec
    mode: str
    payload: Dict[str, Any]

    @property
    def discord_post(self) -> str | None:
        return self.payload.get("discord_post")


class MatchEngine:
    def __init__(self, plan: MatchPlan) -> None:
        self.plan = plan

    def run(self, mode: str = "expectimax", depth: int = 6, sims: int = 600) -> List[MatchResult]:
        results: List[MatchResult] = []
        for idx, matchup in self.plan.each_matchup():
            you_cb, foe_cb = self.build_pair(matchup)
            terrain = self.build_terrain(self.plan.weather)
            grid = self.plan.grid.to_engine_grid()
            if mode == "monte-carlo":
                payload = ptu_engine.monte_carlo_first_move(
                    you_cb,
                    foe_cb,
                    terrain,
                    sims=sims,
                    seed=self.seed_for_match(idx),
                )
            else:
                payload = ptu_engine.expectimax_battle(
                    you_cb,
                    foe_cb,
                    terrain,
                    grid=grid,
                    depth=depth,
                    seed=self.seed_for_match(idx),
                )
            results.append(MatchResult(matchup=matchup, mode=mode, payload=payload))
        return results

    def build_pair(self, matchup: MatchupSpec):
        you_pos = matchup.you_start or self.plan.default_you_start
        foe_pos = matchup.foe_start or self.plan.default_foe_start
        you_cb = self.build_combatant(matchup.you, controller="Player", pos=you_pos)
        foe_cb = self.build_combatant(matchup.foe, controller="AI", pos=foe_pos)
        return you_cb, foe_cb

    @staticmethod
    def build_combatant(
        spec: PokemonSpec,
        controller: str,
        pos: Tuple[int, int],
        identifier: Optional[str] = None,
    ):
        mon = ptu_engine.build_mon_from_dict(spec.to_engine_dict())
        combatant_id = identifier or controller.lower()
        return ptu_engine.build_combatant(mon, id=combatant_id, controller=controller, pos=pos)

    def build_terrain(self, weather: str | None = None) -> ptu_engine.Terrain:
        weather_lower = (weather or self.plan.weather or "").lower()
        if weather_lower in {"rain", "storm", "downpour"}:
            terr = ptu_engine.Terrain.rain()
        else:
            terr = ptu_engine.Terrain(name=weather or self.plan.weather or "Standard")
        terr.tiles = dict(getattr(self.plan.grid, "tiles", {}))  # type: ignore[attr-defined]
        return terr

    def seed_for_match(self, index: int) -> int:
        base = self.plan.seed or 1337
        return base + index * 101


__all__ = ["MatchEngine", "MatchResult"]
