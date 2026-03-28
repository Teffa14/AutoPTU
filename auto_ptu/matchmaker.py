"""Automatic pairing logic for encounter creation."""
from __future__ import annotations

import random
from typing import Any, Iterable, List, Sequence, Tuple

from .data_models import (
    CampaignSpec,
    MatchPlan,
    MatchupSpec,
    PokemonSpec,
    TrainerClassSpec,
    TrainerFeatureSpec,
    TrainerSideSpec,
)


class AutoMatchPlanner:
    """Pick balanced matchups from a campaign without user micromanagement."""

    def __init__(self, campaign: CampaignSpec, seed: int | None = None) -> None:
        self.campaign = campaign
        self.random = random.Random(seed)

    def create_plan(
        self,
        team_size: int = 1,
        prefer_tags: Iterable[str] | None = None,
        weather: str | None = None,
        strategy: str = "level_balance",
    ) -> MatchPlan:
        if team_size <= 0:
            raise ValueError("team_size must be positive")
        prefer_tags = {tag.lower() for tag in (prefer_tags or [])}
        players = self._select_roster(self.campaign.players, team_size, prefer_tags)
        foes = self._select_opponents(players, self.campaign.foes)
        player_sides = self._build_trainer_sides(
            mons=players,
            trainer_meta=self.campaign.metadata.get("player_trainers"),
            default_identifier="player",
            default_name="Allies",
            default_controller="player",
            default_team="players",
        )
        foe_sides = self._build_trainer_sides(
            mons=foes,
            trainer_meta=self.campaign.metadata.get("foe_trainers"),
            default_identifier="foe",
            default_name="Opponents",
            default_controller="ai",
            default_team="foes",
        )
        sides: List[TrainerSideSpec] = player_sides + foe_sides
        label = f"{len(players)}v{len(foes)} Battle"
        matchups: List[MatchupSpec] = [
            MatchupSpec(you=players[0], foe=foes[0], label=label, sides=sides)
        ]
        seed_value = self.random.randint(1, 1_000_000)
        return MatchPlan(
            matchups=matchups,
            weather=weather or self.campaign.default_weather,
            grid=self.campaign.grid,
            battle_context=str(self.campaign.metadata.get("battle_context", "full_contact")),
            active_slots=int(self.campaign.metadata.get("active_slots", 1)),
            description=f"Auto planner ({strategy})",
            seed=seed_value,
        )

    def _select_roster(
        self,
        roster: Sequence[PokemonSpec],
        count: int,
        prefer_tags: Iterable[str],
    ) -> List[PokemonSpec]:
        if not roster:
            raise ValueError("Campaign roster missing entries")
        prefer_tags = list(prefer_tags)
        prioritized: List[PokemonSpec] = []
        others: List[PokemonSpec] = []
        for mon in roster:
            tags_lower = {tag.lower() for tag in mon.tags}
            if prefer_tags and tags_lower.intersection(prefer_tags):
                prioritized.append(mon)
            else:
                others.append(mon)
        ordered = prioritized + sorted(others, key=lambda m: m.level_score(), reverse=True)
        if not ordered:
            ordered = sorted(roster, key=lambda m: m.level_score(), reverse=True)
        picks: List[PokemonSpec] = []
        idx = 0
        while len(picks) < count:
            picks.append(ordered[idx % len(ordered)])
            idx += 1
        return picks

    def _select_opponents(
        self,
        players: Sequence[PokemonSpec],
        foes: Sequence[PokemonSpec],
    ) -> List[PokemonSpec]:
        if not foes:
            raise ValueError("Campaign has no foes to fight")
        available = sorted(foes, key=lambda m: m.level_score())
        picks: List[PokemonSpec] = []
        pool = available.copy()
        for player in players:
            if not pool:
                pool = available.copy()
            best_idx = min(range(len(pool)), key=lambda i: abs(pool[i].level_score() - player.level_score()))
            picks.append(pool.pop(best_idx))
        return picks

    def _build_trainer_sides(
        self,
        mons: Sequence[PokemonSpec],
        trainer_meta: Any,
        default_identifier: str,
        default_name: str,
        default_controller: str,
        default_team: str,
    ) -> List[TrainerSideSpec]:
        if not mons:
            return []
        meta_entries = [entry for entry in (trainer_meta or []) if isinstance(entry, dict)]
        if not meta_entries:
            return [
                TrainerSideSpec(
                    identifier=default_identifier,
                    name=default_name,
                    controller=default_controller,
                    team=default_team,
                    pokemon=list(mons),
                )
            ]
        assignments: List[List[PokemonSpec]] = [[] for _ in meta_entries]
        for idx, mon in enumerate(mons):
            assignments[idx % len(assignments)].append(mon)
        sides: List[TrainerSideSpec] = []
        for idx, (entry, assigned) in enumerate(zip(meta_entries, assignments)):
            if not assigned:
                continue
            identifier = str(entry.get("identifier") or entry.get("id") or f"{default_identifier}-{idx + 1}")
            name = str(entry.get("name") or identifier.title() or default_name)
            controller = str(entry.get("controller") or default_controller)
            team = str(entry.get("team") or default_team or controller)
            initiative = int(entry.get("initiative_modifier", entry.get("initiative", 0)))
            speed_value = entry.get("speed", entry.get("trainer_speed"))
            positions: List[Tuple[int, int]] = []
            for pos in entry.get("start_positions", []):
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    positions.append((int(pos[0]), int(pos[1])))
            class_payload = entry.get("trainer_class") or entry.get("class_spec")
            trainer_class = TrainerClassSpec.from_dict(class_payload) if isinstance(class_payload, dict) else None
            feature_payload = entry.get("trainer_features", entry.get("features", []))
            trainer_features = [
                TrainerFeatureSpec.from_dict(item)
                for item in feature_payload
                if isinstance(item, dict)
            ]
            resources_payload = dict(entry.get("feature_resources", entry.get("resources", {})))
            feature_resources = {
                str(key): int(value)
                for key, value in resources_payload.items()
                if key is not None
            }
            if trainer_class:
                for key, value in trainer_class.resources.items():
                    feature_resources.setdefault(str(key), int(value))
            sides.append(
                TrainerSideSpec(
                    identifier=identifier,
                    name=name,
                    controller=controller,
                    team=team,
                    pokemon=assigned,
                    start_positions=positions,
                    initiative_modifier=initiative,
                    speed=int(speed_value) if speed_value is not None else None,
                    trainer_class=trainer_class,
                    trainer_features=trainer_features,
                    feature_resources=feature_resources,
                )
            )
        return sides


__all__ = ["AutoMatchPlanner"]
