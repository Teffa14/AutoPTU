"""Serializable state for a long-running PTU campaign.

The battle engine deliberately owns encounter resolution.  These models own the
state around encounters: table roles, scenes, clocks, quests, journals, and the
shared narrative feed.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


CAMPAIGN_ROLES = ("gm", "player", "spectator")


@dataclass
class ParticipantState:
    id: str
    name: str
    role: str
    token: str = ""
    character_ids: List[str] = field(default_factory=list)
    is_agent: bool = False
    agent_model: str = ""
    agent_persona: str = ""
    companion: str = ""
    color: str = ""
    controller: str = "human"

    def public_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload.pop("token", None)
        payload["controller"] = self.controller or ("ai" if self.is_agent else "human")
        return payload


@dataclass
class CampaignActorState:
    """One persistent Trainer, Pokemon, NPC, rival, or League character."""

    id: str
    name: str
    kind: str
    owner_participant_id: str = ""
    controller: str = "human"
    species: str = ""
    level: int = 1
    xp: int = 0
    persona: str = ""
    voice: str = ""
    goals: List[str] = field(default_factory=list)
    knowledge: List[str] = field(default_factory=list)
    location_id: str = ""
    inventory: Dict[str, int] = field(default_factory=dict)
    currency: int = 0
    badges: List[str] = field(default_factory=list)
    league_points: int = 0
    relationships: Dict[str, int] = field(default_factory=dict)
    sheet: Dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["goals"] = list(self.goals)
        payload["knowledge"] = list(self.knowledge)
        payload["inventory"] = {key: int(self.inventory[key]) for key in sorted(self.inventory)}
        payload["badges"] = list(self.badges)
        payload["relationships"] = {key: int(self.relationships[key]) for key in sorted(self.relationships)}
        payload["sheet"] = dict(self.sheet)
        return payload


@dataclass
class SceneState:
    id: str
    title: str
    order: int = 0
    kind: str = "roleplay"
    location: str = ""
    summary: str = ""
    status: str = "open"
    participant_ids: List[str] = field(default_factory=list)
    spotlight_id: Optional[str] = None
    battle_id: Optional[str] = None
    published: bool = False
    available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignState:
    """Persistent state shared by every role at the table."""

    id: str
    name: str
    seed: int
    gm_id: str
    invite_code: str
    system: str = "Pokemon Tabletop United 1.05"
    revision: int = 0
    time_label: str = "Day 1, Morning"
    active_scene_id: Optional[str] = None
    safety_paused: bool = False
    safety_message: str = ""
    participants: Dict[str, ParticipantState] = field(default_factory=dict)
    actors: Dict[str, CampaignActorState] = field(default_factory=dict)
    scenes: Dict[str, SceneState] = field(default_factory=dict)
    clocks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    factions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    chat: List[Dict[str, Any]] = field(default_factory=list)
    journal: List[Dict[str, Any]] = field(default_factory=list)
    dialogue: List[Dict[str, Any]] = field(default_factory=list)
    locations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recipes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    shops: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exploration_maps: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exploration_tokens: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exploration_memory: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    world: Dict[str, Any] = field(default_factory=lambda: {
        "current_location_id": "",
        "revealed_location_ids": [],
        "weather": "Clear",
        "lighting": "Daylight",
        "fog": 0,
        "traveling": False,
    })
    progression: Dict[str, Any] = field(default_factory=lambda: {
        "gym_badges": [],
        "league_rank": "Unranked",
        "league_points": 0,
        "rivals_defeated": [],
        "champion_defeated": False,
    })
    travel_history: List[Dict[str, Any]] = field(default_factory=list)
    downtime_history: List[Dict[str, Any]] = field(default_factory=list)
    activity: List[Dict[str, Any]] = field(default_factory=list)

    def participant_for_token(self, token: str) -> Optional[ParticipantState]:
        clean = str(token or "").strip()
        if not clean:
            return None
        return next((entry for entry in self.participants.values() if entry.token == clean), None)

    def active_scene(self) -> Optional[SceneState]:
        return self.scenes.get(self.active_scene_id or "")

    def scene_gate(self, scene: Optional[SceneState] = None) -> Dict[str, Any]:
        """Return deterministic, player-safe chapter completion state."""
        scene = scene or self.active_scene()
        if scene is None:
            return {"ready": False, "requirements": [], "incomplete_labels": ["Open a chapter"]}
        activation_seq = max(0, int(scene.metadata.get("activated_seq") or 0))
        requirements = []
        for index, raw in enumerate(scene.metadata.get("completion_gate") or []):
            if not isinstance(raw, dict):
                continue
            requirement = dict(raw)
            kind = str(requirement.get("kind") or "activity").strip().lower()
            label = str(requirement.get("label") or "Complete the chapter goal").strip()
            complete = False
            if kind == "starter":
                complete = any(
                    actor.kind == "pokemon"
                    and bool(actor.sheet.get("starter"))
                    and bool(actor.owner_participant_id)
                    for actor in self.actors.values()
                )
            elif kind == "battle":
                complete = bool(scene.metadata.get("battle_completed"))
            elif kind == "point":
                point_id = str(requirement.get("point_id") or "")
                location_id = str(scene.metadata.get("location_id") or self.world.get("current_location_id") or "")
                point = next(
                    (
                        entry
                        for entry in self.exploration_maps.get(location_id, {}).get("points") or []
                        if str(entry.get("id") or "") == point_id
                    ),
                    None,
                )
                complete = bool(point and point.get("completed_by"))
            elif kind == "npc":
                npc_id = str(requirement.get("npc_id") or "")
                complete = any(
                    str(entry.get("npc_id") or "") == npc_id
                    and str(entry.get("status") or "") == "answered"
                    and int(entry.get("seq") or 0) > activation_seq
                    for entry in self.dialogue
                )
            elif kind == "activity":
                event_type = str(requirement.get("event_type") or "")
                complete = any(
                    int(entry.get("seq") or 0) > activation_seq
                    and (not event_type or str(entry.get("type") or "") == event_type)
                    for entry in self.activity
                )
            requirements.append({
                "id": str(requirement.get("id") or f"gate-{index + 1}"),
                "kind": kind,
                "label": label,
                "complete": complete,
            })
        incomplete = [entry["label"] for entry in requirements if not entry["complete"]]
        return {"ready": not incomplete, "requirements": requirements, "incomplete_labels": incomplete}

    def record_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.revision += 1
        normalized = dict(event)
        normalized["seq"] = self.revision
        self.activity.append(normalized)
        self.activity = self.activity[-300:]
        return normalized

    @staticmethod
    def _player_scene_dict(scene: SceneState) -> Dict[str, Any]:
        """Return only fiction and play-state the GM intentionally published."""
        safe_metadata = {
            key: value
            for key, value in scene.metadata.items()
            if key in {"location_id", "chapter", "battle_completed"}
        }
        return {
            "id": scene.id,
            "title": scene.title,
            "order": scene.order,
            "kind": scene.kind,
            "location": scene.location,
            "summary": scene.summary,
            "status": scene.status,
            "participant_ids": list(scene.participant_ids),
            "spotlight_id": scene.spotlight_id,
            "battle_id": scene.battle_id,
            "published": True,
            "available": bool(scene.available),
            "metadata": safe_metadata,
        }

    @staticmethod
    def _participant_dict(entry: ParticipantState, viewer: Optional[ParticipantState], *, is_gm: bool) -> Dict[str, Any]:
        if is_gm or (viewer is not None and entry.id == viewer.id):
            return entry.public_dict()
        return {
            "id": entry.id,
            "name": entry.name,
            "role": entry.role,
            "is_agent": bool(entry.is_agent),
            "companion": entry.companion,
            "color": entry.color,
            "controller": entry.controller or ("ai" if entry.is_agent else "human"),
        }

    def _revealed_location_ids(self) -> set[str]:
        revealed = {str(value) for value in self.world.get("revealed_location_ids") or [] if str(value)}
        current = str(self.world.get("current_location_id") or "")
        if current:
            revealed.add(current)
        return revealed

    @staticmethod
    def _cell_key(x: int, y: int) -> str:
        return f"{int(x)},{int(y)}"

    def _visible_cell_keys(self, viewer: Optional[ParticipantState], location_id: str) -> set[str]:
        scene_map = self.exploration_maps.get(location_id)
        if scene_map is None:
            return set()
        width = max(1, int(scene_map.get("width") or 1))
        height = max(1, int(scene_map.get("height") or 1))
        if viewer is not None and viewer.role == "gm":
            return {self._cell_key(x, y) for y in range(height) for x in range(width)}

        visible = {
            str(value)
            for value in scene_map.get("revealed_cells") or []
            if str(value)
        }
        blocked = {
            self._cell_key(int(value[0]), int(value[1]))
            for value in scene_map.get("blocked") or []
            if isinstance(value, (list, tuple)) and len(value) >= 2
        }
        viewer_id = str(viewer.id if viewer else "")
        spectator = bool(viewer and viewer.role == "spectator")
        owned_ids = set()
        for actor in self.actors.values():
            owner = self.participants.get(actor.owner_participant_id)
            if actor.owner_participant_id == viewer_id or (spectator and owner is not None and owner.role == "player"):
                owned_ids.add(actor.id)
        fog_penalty = max(0, int(self.world.get("fog") or 0))
        dark_penalty = 2 if str(self.world.get("lighting") or "") in {"Dark", "Blackout"} else 0
        directions = ((0, -1), (-1, 0), (1, 0), (0, 1))
        for token in sorted(self.exploration_tokens.values(), key=lambda entry: str(entry.get("actor_id") or "")):
            if str(token.get("location_id") or "") != location_id or str(token.get("actor_id") or "") not in owned_ids:
                continue
            start_x = int(token.get("x") or 0)
            start_y = int(token.get("y") or 0)
            radius = max(1, int(token.get("vision") or 3) - fog_penalty - dark_penalty)
            frontier = [(start_x, start_y, 0)]
            visited = set()
            while frontier:
                x, y, distance = frontier.pop(0)
                key = self._cell_key(x, y)
                if key in visited or x < 0 or y < 0 or x >= width or y >= height:
                    continue
                visited.add(key)
                visible.add(key)
                if distance >= radius or (key in blocked and distance > 0):
                    continue
                for dx, dy in directions:
                    frontier.append((x + dx, y + dy, distance + 1))
        return visible

    def _exploration_speed(self, actor_id: str) -> int:
        """Return a bounded scene-floor speed for one persistent actor."""
        token = self.exploration_tokens.get(str(actor_id or ""), {})
        actor = self.actors.get(str(actor_id or ""))
        default = 5 if actor is not None and actor.kind == "pokemon" else 4
        raw_speed = token.get("speed")
        if raw_speed in (None, "") and actor is not None:
            raw_speed = actor.sheet.get("overland") or actor.sheet.get("speed")
        try:
            return max(1, min(12, int(raw_speed or default)))
        except (TypeError, ValueError):
            return default

    def _exploration_paths(self, actor_id: str, *, max_steps: Optional[int] = None) -> Dict[str, List[Dict[str, int]]]:
        """Build deterministic shortest legal paths from an exploration token."""
        actor_id = str(actor_id or "")
        token = self.exploration_tokens.get(actor_id)
        if token is None:
            return {}
        location_id = str(token.get("location_id") or "")
        scene_map = self.exploration_maps.get(location_id)
        if scene_map is None:
            return {}
        width = max(1, int(scene_map.get("width") or 1))
        height = max(1, int(scene_map.get("height") or 1))
        limit = self._exploration_speed(actor_id) if max_steps is None else max(0, int(max_steps))
        start = (int(token.get("x") or 0), int(token.get("y") or 0))
        blocked = {
            (int(value[0]), int(value[1]))
            for value in scene_map.get("blocked") or []
            if isinstance(value, (list, tuple)) and len(value) >= 2
        }
        occupied = {
            (int(other.get("x") or 0), int(other.get("y") or 0))
            for other in self.exploration_tokens.values()
            if str(other.get("actor_id") or "") != actor_id
            and str(other.get("location_id") or "") == location_id
        }
        directions = ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1))
        frontier = deque([start])
        distance = {start: 0}
        previous: Dict[tuple[int, int], tuple[int, int]] = {}
        while frontier:
            x, y = frontier.popleft()
            if distance[(x, y)] >= limit:
                continue
            for dx, dy in directions:
                target = (x + dx, y + dy)
                target_x, target_y = target
                if target in distance or target_x < 0 or target_y < 0 or target_x >= width or target_y >= height:
                    continue
                if target in blocked or target in occupied:
                    continue
                # A diagonal cannot squeeze through the corner of a wall.
                if dx and dy and ((x + dx, y) in blocked or (x, y + dy) in blocked):
                    continue
                distance[target] = distance[(x, y)] + 1
                previous[target] = (x, y)
                frontier.append(target)

        paths: Dict[str, List[Dict[str, int]]] = {}
        for target in sorted((value for value in distance if value != start), key=lambda value: (distance[value], value[1], value[0])):
            route = []
            current = target
            while current != start:
                route.append(current)
                current = previous[current]
            route.reverse()
            paths[self._cell_key(*target)] = [{"x": x, "y": y} for x, y in route]
        return paths

    def _exploration_route_known(
        self,
        viewer: Optional[ParticipantState],
        location_id: str,
        path: List[Dict[str, int]],
    ) -> bool:
        """Allow one fog-frontier destination without exposing routes through darkness."""
        if viewer is not None and viewer.role == "gm":
            return True
        scene_map = self.exploration_maps.get(location_id, {})
        viewer_id = str(viewer.id if viewer else "")
        known = self._visible_cell_keys(viewer, location_id)
        known.update(str(value) for value in scene_map.get("revealed_cells") or [] if str(value))
        known.update(
            str(value)
            for value in self.exploration_memory.get(viewer_id, {}).get(location_id, [])
            if str(value)
        )
        return all(self._cell_key(int(step["x"]), int(step["y"])) in known for step in path[:-1])

    def _exploration_dict(self, viewer: Optional[ParticipantState], *, is_gm: bool) -> Optional[Dict[str, Any]]:
        location_id = str(self.world.get("current_location_id") or "")
        scene_map = self.exploration_maps.get(location_id)
        if scene_map is None:
            return None
        width = max(1, int(scene_map.get("width") or 1))
        height = max(1, int(scene_map.get("height") or 1))
        visible = self._visible_cell_keys(viewer, location_id)
        viewer_id = str(viewer.id if viewer else "")
        remembered = {
            str(value)
            for value in self.exploration_memory.get(viewer_id, {}).get(location_id, [])
            if str(value)
        }
        globally_revealed = {str(value) for value in scene_map.get("revealed_cells") or [] if str(value)}
        remembered.update(globally_revealed)
        terrain_by_key = {
            self._cell_key(int(entry.get("x") or 0), int(entry.get("y") or 0)): str(entry.get("kind") or "floor")
            for entry in scene_map.get("terrain") or []
            if isinstance(entry, dict)
        }
        blocked = {
            self._cell_key(int(value[0]), int(value[1]))
            for value in scene_map.get("blocked") or []
            if isinstance(value, (list, tuple)) and len(value) >= 2
        }
        cells: List[Dict[str, Any]] = []
        for y in range(height):
            for x in range(width):
                key = self._cell_key(x, y)
                state = "visible" if is_gm or key in visible else "explored" if key in remembered else "hidden"
                cells.append({
                    "key": key,
                    "x": x,
                    "y": y,
                    "state": state,
                    "terrain": terrain_by_key.get(key, str(scene_map.get("default_terrain") or "floor")) if state != "hidden" else "unknown",
                    "blocked": key in blocked if state != "hidden" else False,
                })

        tokens: List[Dict[str, Any]] = []
        active_scene = self.active_scene()
        player_movement_open = bool(active_scene and active_scene.published and active_scene.available)
        for token in sorted(self.exploration_tokens.values(), key=lambda entry: str(entry.get("actor_id") or "")):
            if str(token.get("location_id") or "") != location_id:
                continue
            actor_id = str(token.get("actor_id") or "")
            actor = self.actors.get(actor_id)
            if actor is None:
                continue
            key = self._cell_key(int(token.get("x") or 0), int(token.get("y") or 0))
            owned = bool(viewer_id and actor.owner_participant_id == viewer_id)
            revealed = bool(token.get("revealed", not token.get("hidden", False)))
            if not is_gm and not owned and (key not in visible or not revealed):
                continue
            reachable_cells = []
            if is_gm or (owned and player_movement_open):
                for target_key, path in self._exploration_paths(actor_id).items():
                    if not is_gm and not self._exploration_route_known(viewer, location_id, path):
                        continue
                    target_x, target_y = (int(value) for value in target_key.split(",", 1))
                    reachable_cells.append({"key": target_key, "x": target_x, "y": target_y, "steps": len(path)})
            tokens.append({
                "actor_id": actor.id,
                "name": actor.name,
                "kind": actor.kind,
                "species": actor.species,
                "owner_participant_id": actor.owner_participant_id,
                "x": int(token.get("x") or 0),
                "y": int(token.get("y") or 0),
                "vision": int(token.get("vision") or 3),
                "speed": self._exploration_speed(actor_id),
                "reachable_cells": reachable_cells,
                "owned": owned,
                "hidden": bool(token.get("hidden")) if is_gm else False,
                "revealed": revealed,
            })

        points: List[Dict[str, Any]] = []
        for point in sorted(scene_map.get("points") or [], key=lambda entry: str(entry.get("id") or "")):
            if not isinstance(point, dict):
                continue
            key = self._cell_key(int(point.get("x") or 0), int(point.get("y") or 0))
            if not is_gm and (not bool(point.get("revealed")) or key not in visible | remembered):
                continue
            interaction_range = max(0, min(3, int(point.get("interaction_range") if point.get("interaction_range") is not None else 1)))
            nearby_actor_ids = []
            for token in tokens:
                if not (is_gm or token["owned"]):
                    continue
                if max(abs(int(token["x"]) - int(point.get("x") or 0)), abs(int(token["y"]) - int(point.get("y") or 0))) <= interaction_range:
                    nearby_actor_ids.append(str(token["actor_id"]))
            completed_by = sorted({str(value) for value in point.get("completed_by") or [] if str(value)})
            available = bool(point.get("available", True))
            once_complete = bool(point.get("once")) and bool(completed_by)
            can_interact = bool(
                nearby_actor_ids
                and available
                and not once_complete
                and (is_gm or (player_movement_open and bool(point.get("revealed"))))
            )
            check = dict(point.get("check") or {})
            points.append({
                "id": str(point.get("id") or key),
                "label": str(point.get("label") or "Point of interest"),
                "kind": str(point.get("kind") or "interest"),
                "x": int(point.get("x") or 0),
                "y": int(point.get("y") or 0),
                "revealed": bool(point.get("revealed")),
                "available": available,
                "interaction": str(point.get("interaction") or "Investigate"),
                "description": str(point.get("description") or "There is something here worth investigating."),
                "interaction_range": interaction_range,
                "check": {
                    "label": str(check.get("label") or "Check"),
                    "expression": str(check.get("expression") or "2d6"),
                    "difficulty": int(check.get("difficulty") or 0),
                } if check else None,
                "once": bool(point.get("once")),
                "completed": bool(completed_by),
                "completed_by": completed_by if is_gm else [],
                "result": str(point.get("result") or "") if is_gm or completed_by else "",
                "nearby_actor_ids": nearby_actor_ids,
                "can_interact": can_interact,
            })
        return {
            "location_id": location_id,
            "name": str(scene_map.get("name") or self.locations.get(location_id, {}).get("name") or "Scene floor"),
            "theme": str(scene_map.get("theme") or self.locations.get(location_id, {}).get("kind") or "route"),
            "width": width,
            "height": height,
            "cells": cells,
            "tokens": tokens,
            "points": points,
            "viewer_token_ids": sorted(token["actor_id"] for token in tokens if token["owned"]),
            "fully_revealed": len(globally_revealed) >= width * height,
        }

    def _actor_dicts(self, viewer: Optional[ParticipantState], *, is_gm: bool) -> List[Dict[str, Any]]:
        if is_gm:
            return [self.actors[key].public_dict() for key in sorted(self.actors)]
        viewer_id = str(viewer.id if viewer else "")
        current_location = str(self.world.get("current_location_id") or "")
        npc_kinds = {"npc", "rival", "gym_leader", "league", "champion"}
        visible: List[Dict[str, Any]] = []
        for actor in sorted(self.actors.values(), key=lambda entry: entry.id):
            owned = bool(viewer_id and actor.owner_participant_id == viewer_id)
            party_member = bool(actor.owner_participant_id)
            nearby_npc = actor.kind in npc_kinds and actor.location_id == current_location
            token = self.exploration_tokens.get(actor.id)
            if nearby_npc and current_location in self.exploration_maps and token is not None:
                cell = self._cell_key(int(token.get("x") or 0), int(token.get("y") or 0))
                nearby_npc = cell in self._visible_cell_keys(viewer, current_location) and bool(
                    token.get("revealed", not token.get("hidden", False))
                )
            starter_candidate = bool(
                actor.kind == "pokemon"
                and not actor.owner_participant_id
                and actor.location_id == current_location
                and actor.sheet.get("starter_candidate")
            )
            if not (owned or party_member or nearby_npc or starter_candidate):
                continue
            if owned:
                visible.append(actor.public_dict())
                continue
            public = {
                "id": actor.id,
                "name": actor.name,
                "kind": actor.kind,
                "owner_participant_id": actor.owner_participant_id,
                "controller": actor.controller,
                "species": actor.species,
                "level": actor.level,
                "location_id": actor.location_id,
            }
            if nearby_npc:
                public.update({"persona": actor.persona, "voice": actor.voice})
            if starter_candidate:
                public["sheet"] = {"starter_candidate": True}
            visible.append(public)
        return visible

    @staticmethod
    def _record_is_visible(entry: Dict[str, Any], *, published_order: int) -> bool:
        if str(entry.get("visibility") or "table") == "gm":
            return False
        reveal_order = int(entry.get("reveal_order") or 0)
        return reveal_order <= published_order

    def visible_activity(self, viewer: Optional[ParticipantState]) -> List[Dict[str, Any]]:
        if viewer is not None and viewer.role == "gm":
            return [dict(entry) for entry in self.activity]
        safe_types = {
            "chat.post",
            "roll.check",
            "safety.pause",
            "safety.resume",
            "scene.activate",
            "scene.visibility",
            "spotlight.set",
            "clock.tick",
            "quest.objective",
            "battle.link",
            "starter.select",
            "location.travel",
            "exploration.point.interact",
            "craft.item",
            "shop.buy",
            "shop.sell",
            "downtime.activity",
            "npc.talk",
            "npc.reply",
            "participant.control",
            "battle.complete",
            "progression.award",
        }
        viewer_id = str(viewer.id if viewer else "")
        visible: List[Dict[str, Any]] = []
        dialogue_by_id = {str(entry.get("id") or ""): entry for entry in self.dialogue}
        for entry in self.activity:
            event_type = str(entry.get("type") or "")
            if event_type not in safe_types:
                continue
            if event_type == "exploration.point.interact" and not bool(dict(entry.get("detail") or {}).get("public")):
                continue
            if event_type in {"npc.talk", "npc.reply"}:
                detail = dict(entry.get("detail") or {})
                dialogue = dialogue_by_id.get(str(detail.get("id") or detail.get("dialogue_id") or ""), {})
                if str(dialogue.get("participant_id") or entry.get("actor_id") or "") != viewer_id:
                    continue
            visible.append(dict(entry))
        return visible

    def to_dict(self, *, viewer: Optional[ParticipantState] = None) -> Dict[str, Any]:
        is_gm = bool(viewer and viewer.role == "gm")
        ordered_scenes = sorted(self.scenes.values(), key=lambda item: (item.order or 10_000, item.id))
        visible_scenes = ordered_scenes if is_gm else [entry for entry in ordered_scenes if entry.published]
        scene_payloads = [asdict(entry) if is_gm else self._player_scene_dict(entry) for entry in visible_scenes]
        active_scene = self.active_scene()
        has_next_scene = bool(
            active_scene
            and any((entry.order, entry.id) > (active_scene.order, active_scene.id) for entry in ordered_scenes)
        )
        active_scene_payload = None
        if active_scene is not None and (is_gm or active_scene.published):
            active_scene_payload = asdict(active_scene) if is_gm else self._player_scene_dict(active_scene)
        published_scene_ids = {entry.id for entry in self.scenes.values() if entry.published}
        published_order = max((entry.order for entry in self.scenes.values() if entry.published), default=0)
        revealed_location_ids = self._revealed_location_ids()
        journal = []
        for entry in self.journal:
            visibility = str(entry.get("visibility") or "table")
            owner_id = str(entry.get("actor_id") or "")
            if visibility == "gm" and not is_gm:
                continue
            if visibility == "private" and not is_gm and (viewer is None or viewer.id != owner_id):
                continue
            journal.append(dict(entry))
        clocks = []
        for key in sorted(self.clocks):
            entry = dict(self.clocks[key])
            scene_id = str(entry.get("scene_id") or "")
            if is_gm or (
                self._record_is_visible(entry, published_order=published_order)
                and (not scene_id or scene_id in published_scene_ids)
            ):
                clocks.append(entry)
        quests = []
        for key in sorted(self.quests):
            entry = dict(self.quests[key])
            if not is_gm and not self._record_is_visible(entry, published_order=published_order):
                continue
            if not is_gm:
                entry["objectives"] = [
                    dict(objective)
                    for objective in entry.get("objectives") or []
                    if objective.get("complete") or self._record_is_visible(objective, published_order=published_order)
                ]
            quests.append(entry)
        factions = [
            dict(self.factions[key])
            for key in sorted(self.factions)
            if is_gm or self._record_is_visible(self.factions[key], published_order=published_order)
        ]
        if is_gm:
            locations = [dict(self.locations[key]) for key in sorted(self.locations)]
        else:
            locations = []
            for key in sorted(revealed_location_ids):
                if key not in self.locations:
                    continue
                entry = dict(self.locations[key])
                entry["neighbors"] = [value for value in entry.get("neighbors") or [] if value in revealed_location_ids]
                locations.append(entry)
        current_location_id = str(self.world.get("current_location_id") or "")
        current_services = set(self.locations.get(current_location_id, {}).get("services") or [])
        recipes = [dict(self.recipes[key]) for key in sorted(self.recipes)] if is_gm or current_services.intersection({"crafting", "camp"}) else []
        shops = [
            dict(self.shops[key])
            for key in sorted(self.shops)
            if is_gm or str(self.shops[key].get("location_id") or "") == current_location_id
        ]
        dialogue = [
            dict(entry)
            for entry in self.dialogue
            if is_gm or str(entry.get("participant_id") or "") == str(viewer.id if viewer else "")
        ]
        world = dict(self.world)
        world["revealed_location_ids"] = sorted(revealed_location_ids)
        activity = self.visible_activity(viewer)
        return {
            "id": self.id,
            "name": self.name,
            "system": self.system,
            "seed": self.seed if is_gm else None,
            "revision": self.revision,
            "time_label": self.time_label,
            "active_scene_id": self.active_scene_id,
            "safety_paused": self.safety_paused,
            "safety_message": self.safety_message,
            "invite_code": self.invite_code if is_gm else None,
            "participants": [
                self._participant_dict(entry, viewer, is_gm=is_gm)
                for entry in sorted(self.participants.values(), key=lambda item: (item.role != "gm", item.name.lower(), item.id))
            ],
            "actors": self._actor_dicts(viewer, is_gm=is_gm),
            "scenes": scene_payloads,
            "active_scene": active_scene_payload,
            "has_next_scene": has_next_scene,
            "scene_gate": self.scene_gate(active_scene),
            "clocks": clocks,
            "quests": quests,
            "factions": factions,
            "chat": list(self.chat[-150:]),
            "journal": journal[-150:],
            "dialogue": dialogue[-150:],
            "locations": locations,
            "recipes": recipes,
            "shops": shops,
            "exploration": self._exploration_dict(viewer, is_gm=is_gm),
            "world": world,
            "progression": dict(self.progression),
            "travel_history": list(self.travel_history[-100:]),
            "downtime_history": list(self.downtime_history[-100:]) if is_gm else [dict(entry) for entry in self.downtime_history if str(entry.get("participant_id") or "") == str(viewer.id if viewer else "")][-100:],
            "activity": activity[-150:],
            "viewer": viewer.public_dict() if viewer else None,
        }

    def snapshot_dict(self) -> Dict[str, Any]:
        payload = self.to_dict(viewer=self.participants.get(self.gm_id))
        payload["gm_id"] = self.gm_id
        payload["invite_code"] = self.invite_code
        payload["participants"] = [asdict(self.participants[key]) for key in sorted(self.participants)]
        payload["actors"] = [self.actors[key].public_dict() for key in sorted(self.actors)]
        payload["exploration_maps"] = {key: dict(self.exploration_maps[key]) for key in sorted(self.exploration_maps)}
        payload["exploration_tokens"] = {key: dict(self.exploration_tokens[key]) for key in sorted(self.exploration_tokens)}
        payload["exploration_memory"] = {
            participant_id: {
                location_id: sorted(str(value) for value in locations[location_id])
                for location_id in sorted(locations)
            }
            for participant_id, locations in sorted(self.exploration_memory.items())
        }
        payload.pop("exploration", None)
        payload.pop("viewer", None)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CampaignState":
        participants: Dict[str, ParticipantState] = {}
        for raw in payload.get("participants") or []:
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            entry = ParticipantState(
                id=str(raw["id"]),
                name=str(raw.get("name") or raw["id"]),
                role=str(raw.get("role") or "player"),
                token=str(raw.get("token") or ""),
                character_ids=[str(value) for value in raw.get("character_ids") or []],
                is_agent=bool(raw.get("is_agent")),
                agent_model=str(raw.get("agent_model") or ""),
                agent_persona=str(raw.get("agent_persona") or ""),
                companion=str(raw.get("companion") or ""),
                color=str(raw.get("color") or ""),
                controller=str(raw.get("controller") or ("ai" if raw.get("is_agent") else "human")),
            )
            participants[entry.id] = entry
        actors: Dict[str, CampaignActorState] = {}
        for raw in payload.get("actors") or []:
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            actor = CampaignActorState(
                id=str(raw["id"]),
                name=str(raw.get("name") or raw["id"]),
                kind=str(raw.get("kind") or "npc"),
                owner_participant_id=str(raw.get("owner_participant_id") or ""),
                controller=str(raw.get("controller") or "human"),
                species=str(raw.get("species") or ""),
                level=max(1, int(raw.get("level") or 1)),
                xp=max(0, int(raw.get("xp") or 0)),
                persona=str(raw.get("persona") or ""),
                voice=str(raw.get("voice") or ""),
                goals=[str(value) for value in raw.get("goals") or []],
                knowledge=[str(value) for value in raw.get("knowledge") or []],
                location_id=str(raw.get("location_id") or ""),
                inventory={str(key): int(value) for key, value in dict(raw.get("inventory") or {}).items()},
                currency=max(0, int(raw.get("currency") or 0)),
                badges=[str(value) for value in raw.get("badges") or []],
                league_points=int(raw.get("league_points") or 0),
                relationships={str(key): int(value) for key, value in dict(raw.get("relationships") or {}).items()},
                sheet=dict(raw.get("sheet") or {}),
            )
            actors[actor.id] = actor
        scenes: Dict[str, SceneState] = {}
        raw_scenes = [entry for entry in payload.get("scenes") or [] if isinstance(entry, dict) and entry.get("id")]
        active_scene_id = str(payload.get("active_scene_id") or "")
        active_order = next((int(entry.get("order") or 0) for entry in raw_scenes if str(entry.get("id") or "") == active_scene_id), 0)
        for raw in raw_scenes:
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            entry = SceneState(
                id=str(raw["id"]),
                title=str(raw.get("title") or "Scene"),
                order=int(raw.get("order") or 0),
                kind=str(raw.get("kind") or "roleplay"),
                location=str(raw.get("location") or ""),
                summary=str(raw.get("summary") or ""),
                status=str(raw.get("status") or "open"),
                participant_ids=[str(value) for value in raw.get("participant_ids") or []],
                spotlight_id=raw.get("spotlight_id"),
                battle_id=raw.get("battle_id"),
                published=bool(raw.get("published", int(raw.get("order") or 0) <= active_order)),
                available=bool(raw.get("available", str(raw.get("id") or "") == active_scene_id)),
                metadata=dict(raw.get("metadata") or {}),
            )
            scenes[entry.id] = entry
        state = cls(
            id=str(payload.get("id") or "campaign"),
            name=str(payload.get("name") or "PTU Campaign"),
            seed=int(payload.get("seed") or 1),
            gm_id=str(payload.get("gm_id") or next((item.id for item in participants.values() if item.role == "gm"), "")),
            invite_code=str(payload.get("invite_code") or ""),
            system=str(payload.get("system") or "Pokemon Tabletop United 1.05"),
            revision=int(payload.get("revision") or 0),
            time_label=str(payload.get("time_label") or "Day 1, Morning"),
            active_scene_id=payload.get("active_scene_id"),
            safety_paused=bool(payload.get("safety_paused")),
            safety_message=str(payload.get("safety_message") or ""),
            participants=participants,
            actors=actors,
            scenes=scenes,
            clocks={str(entry["id"]): dict(entry) for entry in payload.get("clocks") or [] if isinstance(entry, dict) and entry.get("id")},
            quests={str(entry["id"]): dict(entry) for entry in payload.get("quests") or [] if isinstance(entry, dict) and entry.get("id")},
            factions={str(entry["id"]): dict(entry) for entry in payload.get("factions") or [] if isinstance(entry, dict) and entry.get("id")},
            chat=[dict(entry) for entry in payload.get("chat") or [] if isinstance(entry, dict)],
            journal=[dict(entry) for entry in payload.get("journal") or [] if isinstance(entry, dict)],
            dialogue=[dict(entry) for entry in payload.get("dialogue") or [] if isinstance(entry, dict)],
            locations={str(entry["id"]): dict(entry) for entry in payload.get("locations") or [] if isinstance(entry, dict) and entry.get("id")},
            recipes={str(entry["id"]): dict(entry) for entry in payload.get("recipes") or [] if isinstance(entry, dict) and entry.get("id")},
            shops={str(entry["id"]): dict(entry) for entry in payload.get("shops") or [] if isinstance(entry, dict) and entry.get("id")},
            exploration_maps={str(key): dict(value) for key, value in dict(payload.get("exploration_maps") or {}).items() if isinstance(value, dict)},
            exploration_tokens={str(key): dict(value) for key, value in dict(payload.get("exploration_tokens") or {}).items() if isinstance(value, dict)},
            exploration_memory={
                str(participant_id): {
                    str(location_id): sorted({str(cell) for cell in cells if str(cell)})
                    for location_id, cells in dict(locations).items()
                    if isinstance(cells, list)
                }
                for participant_id, locations in dict(payload.get("exploration_memory") or {}).items()
                if isinstance(locations, dict)
            },
            world=dict(payload.get("world") or {}),
            progression=dict(payload.get("progression") or {}),
            travel_history=[dict(entry) for entry in payload.get("travel_history") or [] if isinstance(entry, dict)],
            downtime_history=[dict(entry) for entry in payload.get("downtime_history") or [] if isinstance(entry, dict)],
            activity=[dict(entry) for entry in payload.get("activity") or [] if isinstance(entry, dict)],
        )
        state.world = {
            "current_location_id": "",
            "revealed_location_ids": [],
            "weather": "Clear",
            "lighting": "Daylight",
            "fog": 0,
            "traveling": False,
            **state.world,
        }
        revealed = {str(value) for value in state.world.get("revealed_location_ids") or [] if str(value)}
        current_location_id = str(state.world.get("current_location_id") or "")
        if current_location_id:
            revealed.add(current_location_id)
        for record in state.travel_history:
            revealed.update(str(record.get(key) or "") for key in ("from", "to") if str(record.get(key) or ""))
        restored_active = state.active_scene()
        restored_active_order = restored_active.order if restored_active else 0
        for scene in state.scenes.values():
            if scene.published and scene.order <= restored_active_order and str(scene.metadata.get("location_id") or ""):
                revealed.add(str(scene.metadata["location_id"]))
        state.world["revealed_location_ids"] = sorted(revealed)
        state.progression = {
            "gym_badges": [],
            "league_rank": "Unranked",
            "league_points": 0,
            "rivals_defeated": [],
            "champion_defeated": False,
            **state.progression,
        }
        return state
