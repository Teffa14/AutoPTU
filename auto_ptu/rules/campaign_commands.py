"""Permissioned, deterministic campaign commands."""

from __future__ import annotations

import hashlib
import random
import re
from typing import Any, Dict, Iterable, List, Tuple

from .campaign_state import CampaignActorState, CampaignState, ParticipantState, SceneState


_GM_COMMANDS = {
    "scene.create",
    "scene.activate",
    "scene.visibility",
    "scene.update",
    "spotlight.set",
    "clock.create",
    "clock.tick",
    "quest.create",
    "quest.objective",
    "faction.adjust",
    "time.set",
    "battle.link",
    "safety.resume",
    "actor.create",
    "actor.assign",
    "actor.level",
    "location.create",
    "location.visibility",
    "exploration.visibility",
    "exploration.point.visibility",
    "exploration.point.update",
    "exploration.token.visibility",
    "recipe.create",
    "shop.create",
    "world.environment",
    "progression.award",
    "npc.reply",
}
_PLAYER_COMMANDS = {
    "chat.post",
    "roll.check",
    "journal.add",
    "safety.pause",
    "participant.control",
    "actor.sheet.update",
    "starter.select",
    "location.travel",
    "exploration.token.move",
    "exploration.point.interact",
    "craft.item",
    "shop.buy",
    "shop.sell",
    "downtime.activity",
    "npc.talk",
    "builder.sync",
}
_DICE_RE = re.compile(r"^\s*(\d{1,2})d(\d{1,4})(?:\s*([+-])\s*(\d{1,4}))?\s*$", re.I)


class CampaignRules:
    """Apply one command and return its event payload."""

    @staticmethod
    def allowed_commands(role: str) -> Iterable[str]:
        if role == "gm":
            return sorted(_GM_COMMANDS | _PLAYER_COMMANDS)
        if role == "player":
            return sorted(_PLAYER_COMMANDS)
        return []

    @classmethod
    def apply(
        cls,
        state: CampaignState,
        actor: ParticipantState,
        command_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        command = str(command_type or "").strip().lower()
        if command not in set(cls.allowed_commands(actor.role)):
            raise PermissionError(f"The {actor.role} role cannot use {command or 'that command'}.")
        handler = getattr(cls, f"_{command.replace('.', '_')}", None)
        if handler is None:
            raise ValueError(f"Unsupported campaign command: {command}")
        detail = handler(state, actor, dict(payload or {}))
        return {
            "type": command,
            "actor_id": actor.id,
            "actor_name": actor.name,
            "detail": detail,
        }

    @staticmethod
    def _identifier(state: CampaignState, prefix: str, existing: Dict[str, Any]) -> str:
        index = max(1, state.revision + 1)
        candidate = f"{prefix}-{index}"
        while candidate in existing:
            index += 1
            candidate = f"{prefix}-{index}"
        return candidate

    @staticmethod
    def _owned_actor(state: CampaignState, participant_id: str, actor_id: str, *, kind: str = "") -> CampaignActorState:
        actor = state.actors.get(str(actor_id or ""))
        if actor is None:
            raise ValueError("Unknown campaign actor.")
        if actor.owner_participant_id != participant_id:
            raise PermissionError("That character belongs to another participant.")
        if kind and actor.kind != kind:
            raise ValueError(f"That character is not a {kind}.")
        return actor

    @staticmethod
    def _trainer_for(state: CampaignState, participant_id: str) -> CampaignActorState:
        trainer = next(
            (
                entry
                for entry in sorted(state.actors.values(), key=lambda item: item.id)
                if entry.owner_participant_id == participant_id and entry.kind == "trainer"
            ),
            None,
        )
        if trainer is None:
            raise ValueError("Select or import a Trainer first.")
        return trainer

    @staticmethod
    def _complete_matching_objectives(state: CampaignState, terms: Iterable[str]) -> List[str]:
        """Complete deterministic story objectives named by scene metadata."""
        normalized = [str(term).strip().lower() for term in terms if str(term).strip()]
        completed: List[str] = []
        if not normalized:
            return completed
        for quest in sorted(state.quests.values(), key=lambda entry: str(entry.get("id") or "")):
            for objective in quest.get("objectives") or []:
                text = str(objective.get("text") or "").strip().lower()
                if objective.get("complete") or not any(term in text for term in normalized):
                    continue
                objective["complete"] = True
                completed.append(str(objective.get("id") or ""))
            if quest.get("objectives") and all(entry.get("complete") for entry in quest["objectives"]):
                quest["status"] = "complete"
        return completed

    @staticmethod
    def _reveal_location(state: CampaignState, location_id: str) -> bool:
        location_id = str(location_id or "")
        if not location_id or location_id not in state.locations:
            return False
        revealed = {str(value) for value in state.world.get("revealed_location_ids") or [] if str(value)}
        before = len(revealed)
        revealed.add(location_id)
        state.world["revealed_location_ids"] = sorted(revealed)
        return len(revealed) != before

    @staticmethod
    def _remember_exploration(state: CampaignState, participant_id: str, location_id: str) -> None:
        participant = state.participants.get(participant_id)
        if participant is None or location_id not in state.exploration_maps:
            return
        remembered = state.exploration_memory.setdefault(participant_id, {}).setdefault(location_id, [])
        remembered[:] = sorted(set(remembered) | state._visible_cell_keys(participant, location_id))

    @classmethod
    def _ensure_exploration_token(
        cls,
        state: CampaignState,
        campaign_actor: CampaignActorState,
        *,
        location_id: str = "",
        reset_position: bool = False,
    ) -> Dict[str, Any] | None:
        location_id = str(location_id or campaign_actor.location_id or state.world.get("current_location_id") or "")
        scene_map = state.exploration_maps.get(location_id)
        if scene_map is None:
            return None
        existing = state.exploration_tokens.get(campaign_actor.id)
        if existing is not None and not reset_position and str(existing.get("location_id") or "") == location_id:
            return existing
        width = max(1, int(scene_map.get("width") or 1))
        height = max(1, int(scene_map.get("height") or 1))
        raw_spawn = scene_map.get("spawn") or [1, height // 2]
        spawn_x = max(0, min(width - 1, int(raw_spawn[0] if len(raw_spawn) > 0 else 1)))
        spawn_y = max(0, min(height - 1, int(raw_spawn[1] if len(raw_spawn) > 1 else height // 2)))
        blocked = {
            state._cell_key(int(value[0]), int(value[1]))
            for value in scene_map.get("blocked") or []
            if isinstance(value, (list, tuple)) and len(value) >= 2
        }
        occupied = {
            state._cell_key(int(token.get("x") or 0), int(token.get("y") or 0))
            for actor_id, token in state.exploration_tokens.items()
            if actor_id != campaign_actor.id and str(token.get("location_id") or "") == location_id
        }
        candidates = sorted(
            (
                (abs(x - spawn_x) + abs(y - spawn_y), y, x)
                for y in range(height)
                for x in range(width)
                if state._cell_key(x, y) not in blocked and state._cell_key(x, y) not in occupied
            ),
            key=lambda value: (value[0], value[1], value[2]),
        )
        if not candidates:
            raise ValueError("The exploration map has no open token space.")
        _, y, x = candidates[0]
        hidden = bool(campaign_actor.sheet.get("hidden_on_map"))
        token = {
            "actor_id": campaign_actor.id,
            "location_id": location_id,
            "x": x,
            "y": y,
            "vision": max(1, int(campaign_actor.sheet.get("vision") or (4 if campaign_actor.kind == "trainer" else 3))),
            "hidden": hidden,
            "revealed": not hidden,
        }
        state.exploration_tokens[campaign_actor.id] = token
        if campaign_actor.owner_participant_id:
            cls._remember_exploration(state, campaign_actor.owner_participant_id, location_id)
        return token

    @classmethod
    def _actor_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor_id = str(payload.get("id") or cls._identifier(state, "actor", state.actors))
        if actor_id in state.actors:
            raise ValueError("That campaign actor already exists.")
        kind = str(payload.get("kind") or "npc").strip().lower()
        if kind not in {"trainer", "pokemon", "npc", "rival", "gym_leader", "league", "champion"}:
            raise ValueError("Unsupported campaign actor kind.")
        owner_id = str(payload.get("owner_participant_id") or "")
        if owner_id and owner_id not in state.participants:
            raise ValueError("Unknown owner participant.")
        entry = CampaignActorState(
            id=actor_id,
            name=str(payload.get("name") or actor_id).strip(),
            kind=kind,
            owner_participant_id=owner_id,
            controller=str(payload.get("controller") or ("ai" if kind not in {"trainer", "pokemon"} else "human")),
            species=str(payload.get("species") or "").strip(),
            level=max(1, int(payload.get("level") or 1)),
            xp=max(0, int(payload.get("xp") or 0)),
            persona=str(payload.get("persona") or "").strip(),
            voice=str(payload.get("voice") or "").strip(),
            goals=[str(value) for value in payload.get("goals") or []],
            knowledge=[str(value) for value in payload.get("knowledge") or []],
            location_id=str(payload.get("location_id") or state.world.get("current_location_id") or ""),
            inventory={str(key): max(0, int(value)) for key, value in dict(payload.get("inventory") or {}).items()},
            currency=max(0, int(payload.get("currency") or 0)),
            sheet=dict(payload.get("sheet") or {}),
        )
        state.actors[actor_id] = entry
        if owner_id:
            participant = state.participants[owner_id]
            if actor_id not in participant.character_ids:
                participant.character_ids.append(actor_id)
        if entry.kind != "pokemon" or entry.owner_participant_id:
            cls._ensure_exploration_token(state, entry)
        return {"actor": actor_id, "name": entry.name, "kind": kind, "owner_participant_id": owner_id}

    @staticmethod
    def _actor_assign(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor_id = str(payload.get("actor_id") or "")
        participant_id = str(payload.get("participant_id") or "")
        entry = state.actors.get(actor_id)
        participant = state.participants.get(participant_id)
        if entry is None or participant is None:
            raise ValueError("Unknown actor or participant.")
        before = entry.owner_participant_id
        if before and before in state.participants:
            state.participants[before].character_ids = [value for value in state.participants[before].character_ids if value != actor_id]
        entry.owner_participant_id = participant_id
        if actor_id not in participant.character_ids:
            participant.character_ids.append(actor_id)
        CampaignRules._ensure_exploration_token(state, entry)
        return {"actor": actor_id, "before": before or None, "after": participant_id}

    @staticmethod
    def _actor_level(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        entry = state.actors.get(str(payload.get("actor_id") or ""))
        if entry is None:
            raise ValueError("Unknown campaign actor.")
        before = int(entry.level)
        if "level" in payload:
            entry.level = max(1, int(payload.get("level") or 1))
        else:
            entry.level = max(1, before + int(payload.get("delta") or 1))
        if "xp" in payload:
            entry.xp = max(0, int(payload.get("xp") or 0))
        return {"actor": entry.id, "before": before, "level": entry.level, "xp": entry.xp}

    @staticmethod
    def _actor_sheet_update(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = state.actors.get(str(payload.get("actor_id") or ""))
        if target is None:
            raise ValueError("Unknown campaign actor.")
        if actor.role != "gm" and target.owner_participant_id != actor.id:
            raise PermissionError("Only the owner or GM can update that character sheet.")
        changes = dict(payload.get("sheet") or {})
        target.sheet.update(changes)
        if "level" in payload:
            target.level = max(1, int(payload.get("level") or 1))
        return {"actor": target.id, "fields": sorted(changes), "level": target.level}

    @staticmethod
    def _normalize_exploration_point(entry: Dict[str, Any], index: int, width: int, height: int) -> Dict[str, Any]:
        label = str(entry.get("label") or "Point of interest").strip()
        check = dict(entry.get("check") or {})
        normalized_check = None
        if check:
            normalized_check = {
                "label": str(check.get("label") or "Check").strip()[:80],
                "expression": str(check.get("expression") or "2d6").strip(),
                "difficulty": max(0, int(check.get("difficulty") or 0)),
            }
        return {
            "id": str(entry.get("id") or f"point-{index + 1}"),
            "label": label,
            "kind": str(entry.get("kind") or "interest").strip().lower(),
            "x": max(0, min(width - 1, int(entry.get("x") or 0))),
            "y": max(0, min(height - 1, int(entry.get("y") or 0))),
            "revealed": bool(entry.get("revealed")),
            "discoverable": bool(entry.get("discoverable")),
            "available": bool(entry.get("available", True)),
            "interaction": str(entry.get("interaction") or "Investigate").strip()[:80],
            "description": str(entry.get("description") or f"{label} is close enough to investigate.").strip()[:1200],
            "result": str(entry.get("result") or f"The party learns something useful from {label}.").strip()[:2000],
            "failure_result": str(entry.get("failure_result") or f"{label} keeps its answer for now.").strip()[:2000],
            "interaction_range": max(0, min(3, int(entry.get("interaction_range") if entry.get("interaction_range") is not None else 1))),
            "once": bool(entry.get("once")),
            "completed_by": sorted({str(value) for value in entry.get("completed_by") or [] if str(value)}),
            "complete_objectives": [str(value) for value in entry.get("complete_objectives") or [] if str(value)],
            **({"check": normalized_check} if normalized_check else {}),
        }

    @staticmethod
    def _exploration_point(state: CampaignState, location_id: str, point_id: str) -> Dict[str, Any]:
        scene_map = state.exploration_maps.get(str(location_id or ""))
        if scene_map is None:
            raise ValueError("Unknown exploration map.")
        point = next(
            (entry for entry in scene_map.get("points") or [] if str(entry.get("id") or "") == str(point_id or "")),
            None,
        )
        if point is None:
            raise ValueError("Unknown point of interest.")
        return point

    @classmethod
    def _builder_sync(cls, state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        sheet = dict(payload.get("sheet") or {})
        profile = dict(sheet.get("profile") or {})
        trainer = next(
            (
                entry
                for entry in state.actors.values()
                if entry.kind == "trainer" and entry.owner_participant_id == actor.id
            ),
            None,
        )
        if trainer is None:
            trainer_id = f"trainer-{re.sub(r'[^a-z0-9]+', '-', actor.id.lower()).strip('-') or state.revision + 1}"
            trainer = CampaignActorState(
                id=trainer_id,
                name=str(profile.get("name") or actor.name).strip(),
                kind="trainer",
                owner_participant_id=actor.id,
                controller=actor.controller,
                level=max(1, int(profile.get("level") or 1)),
                location_id=str(state.world.get("current_location_id") or ""),
                inventory={"Potion": 1, "Poke Ball": 3},
                currency=1500,
            )
            state.actors[trainer.id] = trainer
            actor.character_ids.append(trainer.id)
        trainer.name = str(profile.get("name") or trainer.name).strip()
        trainer.level = max(1, int(profile.get("level") or trainer.level))
        money = profile.get("money")
        if money not in (None, ""):
            try:
                trainer.currency = max(0, int(str(money).replace(",", "")))
            except ValueError:
                pass
        trainer.sheet = {**trainer.sheet, **sheet, "builder_synced": True}
        cls._ensure_exploration_token(state, trainer)

        pokemon_ids: List[str] = []
        for index, build in enumerate(sheet.get("pokemon_builds") or [], start=1):
            if not isinstance(build, dict):
                continue
            species = str(build.get("species") or build.get("name") or "").strip()
            if not species:
                continue
            pokemon_id = f"builder-{re.sub(r'[^a-z0-9]+', '-', actor.id.lower()).strip('-')}-pokemon-{index}"
            entry = state.actors.get(pokemon_id)
            if entry is None:
                entry = CampaignActorState(
                    id=pokemon_id,
                    name=str(build.get("nickname") or build.get("name") or species).strip(),
                    kind="pokemon",
                    owner_participant_id=actor.id,
                    controller=actor.controller,
                    species=species,
                    level=max(1, int(build.get("level") or trainer.level)),
                    location_id=trainer.location_id,
                )
                state.actors[pokemon_id] = entry
            entry.name = str(build.get("nickname") or build.get("name") or entry.name or species).strip()
            entry.species = species
            entry.level = max(1, int(build.get("level") or entry.level))
            entry.owner_participant_id = actor.id
            entry.controller = actor.controller
            entry.location_id = trainer.location_id
            entry.sheet = {**entry.sheet, **dict(build), "builder_slot": index, "builder_synced": True}
            if pokemon_id not in actor.character_ids:
                actor.character_ids.append(pokemon_id)
            cls._ensure_exploration_token(state, entry)
            pokemon_ids.append(pokemon_id)
        return {"trainer": trainer.id, "pokemon": pokemon_ids, "sheet_fields": sorted(sheet)}

    @staticmethod
    def _participant_control(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        participant_id = str(payload.get("participant_id") or actor.id)
        target = state.participants.get(participant_id)
        if target is None:
            raise ValueError("Unknown participant.")
        agent_host_id = str(state.world.get("agent_host_participant_id") or "")
        host_controls_companion = actor.id == agent_host_id and target.role == "player"
        if actor.role != "gm" and actor.id != participant_id and not host_controls_companion:
            raise PermissionError("Only the GM can change another seat's controller.")
        controller = str(payload.get("controller") or "human").strip().lower()
        if controller not in {"human", "ai"}:
            raise ValueError("Controller must be human or ai.")
        before = target.controller or ("ai" if target.is_agent else "human")
        target.controller = controller
        target.is_agent = controller == "ai"
        if payload.get("agent_model") is not None:
            target.agent_model = str(payload.get("agent_model") or "qwen2.5:3b")
        for actor_id in target.character_ids:
            if actor_id in state.actors:
                state.actors[actor_id].controller = controller
        return {"participant_id": participant_id, "before": before, "after": controller, "model": target.agent_model or None}

    @staticmethod
    def _starter_select(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        species = str(payload.get("species") or "").strip()
        if not species:
            raise ValueError("Choose a starter species.")
        trainer = CampaignRules._trainer_for(state, actor.id)
        existing = next(
            (
                entry
                for entry in state.actors.values()
                if entry.owner_participant_id == actor.id and entry.kind == "pokemon" and entry.sheet.get("starter")
            ),
            None,
        )
        if existing is not None:
            raise ValueError("This Trainer already chose a starter.")
        candidates = [
            entry
            for entry in sorted(state.actors.values(), key=lambda item: item.id)
            if entry.kind == "pokemon" and not entry.owner_participant_id and entry.species.lower() == species.lower() and entry.sheet.get("starter_candidate")
        ]
        if not candidates:
            raise ValueError("That starter is not available.")
        starter = candidates[0]
        starter.owner_participant_id = actor.id
        starter.controller = actor.controller or "human"
        starter.sheet["starter"] = True
        starter.sheet.pop("starter_candidate", None)
        if starter.id not in state.participants[actor.id].character_ids:
            state.participants[actor.id].character_ids.append(starter.id)
        trainer.relationships[starter.id] = max(1, int(trainer.relationships.get(starter.id) or 0))
        trainer.sheet["starter_id"] = starter.id
        trainer.sheet["starter_species"] = starter.species
        trainer.sheet["active_party_ids"] = [starter.id]
        state.participants[actor.id].companion = starter.name or starter.species
        CampaignRules._ensure_exploration_token(state, starter)
        badge_quest = state.quests.get("quest-badge-circuit")
        if badge_quest:
            first = next(iter(badge_quest.get("objectives") or []), None)
            if first is not None:
                first["complete"] = True
        return {
            "trainer": trainer.id,
            "starter": starter.id,
            "species": starter.species,
            "name": starter.name,
            "battle_roster": [starter.id],
        }

    @classmethod
    def _location_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("id") or cls._identifier(state, "location", state.locations))
        neighbors = sorted({str(value) for value in payload.get("neighbors") or [] if str(value)})
        state.locations[location_id] = {
            "id": location_id,
            "name": str(payload.get("name") or location_id).strip(),
            "kind": str(payload.get("kind") or "route").strip().lower(),
            "neighbors": neighbors,
            "danger": max(0, min(10, int(payload.get("danger") or 0))),
            "travel_hours": max(0, int(payload.get("travel_hours") or 1)),
            "services": sorted({str(value) for value in payload.get("services") or [] if str(value)}),
            "description": str(payload.get("description") or "").strip(),
            "map_x": max(4, min(96, int(payload.get("map_x") or (10 + (len(state.locations) * 13) % 82)))),
            "map_y": max(8, min(82, int(payload.get("map_y") or (24 + (len(state.locations) * 17) % 50)))),
        }
        raw_map = dict(payload.get("exploration") or {})
        width = max(6, min(20, int(raw_map.get("width") or 10)))
        height = max(5, min(14, int(raw_map.get("height") or 7)))
        blocked = sorted({
            (max(0, min(width - 1, int(value[0]))), max(0, min(height - 1, int(value[1]))))
            for value in raw_map.get("blocked") or []
            if isinstance(value, (list, tuple)) and len(value) >= 2
        }, key=lambda value: (value[1], value[0]))
        terrain = sorted(
            [
                {
                    "x": max(0, min(width - 1, int(entry.get("x") or 0))),
                    "y": max(0, min(height - 1, int(entry.get("y") or 0))),
                    "kind": str(entry.get("kind") or "floor").strip().lower(),
                }
                for entry in raw_map.get("terrain") or []
                if isinstance(entry, dict)
            ],
            key=lambda entry: (entry["y"], entry["x"], entry["kind"]),
        )
        points = sorted(
            [
                cls._normalize_exploration_point(entry, index, width, height)
                for index, entry in enumerate(raw_map.get("points") or [])
                if isinstance(entry, dict)
            ],
            key=lambda entry: entry["id"],
        )
        spawn = raw_map.get("spawn") or [1, height // 2]
        state.exploration_maps[location_id] = {
            "location_id": location_id,
            "name": str(raw_map.get("name") or f"{state.locations[location_id]['name']} scene floor"),
            "theme": str(raw_map.get("theme") or state.locations[location_id]["kind"]),
            "width": width,
            "height": height,
            "spawn": [max(0, min(width - 1, int(spawn[0]))), max(0, min(height - 1, int(spawn[1])))],
            "default_terrain": str(raw_map.get("default_terrain") or "floor").strip().lower(),
            "blocked": [list(value) for value in blocked],
            "terrain": terrain,
            "points": points,
            "revealed_cells": sorted({str(value) for value in raw_map.get("revealed_cells") or [] if str(value)}),
        }
        if not state.world.get("current_location_id"):
            state.world["current_location_id"] = location_id
            cls._reveal_location(state, location_id)
        if bool(payload.get("revealed")):
            cls._reveal_location(state, location_id)
        return dict(state.locations[location_id])

    @staticmethod
    def _location_visibility(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("location_id") or "")
        if location_id not in state.locations:
            raise ValueError("Unknown location.")
        revealed = {str(value) for value in state.world.get("revealed_location_ids") or [] if str(value)}
        current = str(state.world.get("current_location_id") or "")
        make_visible = bool(payload.get("revealed", True))
        if not make_visible and location_id == current:
            raise ValueError("The party's current location cannot be hidden.")
        if make_visible:
            revealed.add(location_id)
        else:
            revealed.discard(location_id)
        state.world["revealed_location_ids"] = sorted(revealed)
        return {"location_id": location_id, "revealed": make_visible}

    @staticmethod
    def _location_travel(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        destination_id = str(payload.get("destination_id") or payload.get("location_id") or "")
        destination = state.locations.get(destination_id)
        if destination is None:
            raise ValueError("Unknown destination.")
        revealed = {str(value) for value in state.world.get("revealed_location_ids") or [] if str(value)}
        if actor.role != "gm" and destination_id not in revealed:
            raise PermissionError("The GM has not revealed that destination.")
        scene = state.active_scene()
        if actor.role != "gm" and scene is not None and scene.spotlight_id and scene.spotlight_id != actor.id:
            raise PermissionError("The spotlighted Trainer currently controls party travel.")
        before = str(state.world.get("current_location_id") or "")
        origin = state.locations.get(before)
        if origin and destination_id not in origin.get("neighbors", []) and before not in destination.get("neighbors", []):
            raise ValueError("That destination is not connected to the current location.")
        hours = max(0, int(destination.get("travel_hours") or 1))
        record = {
            "id": f"travel-{state.revision + 1}",
            "participant_id": actor.id,
            "from": before or None,
            "to": destination_id,
            "hours": hours,
            "danger": int(destination.get("danger") or 0),
        }
        state.world["traveling"] = False
        state.world["current_location_id"] = destination_id
        state.travel_history.append(record)
        state.travel_history = state.travel_history[-100:]
        party_ids = {entry.id for entry in state.participants.values() if entry.role in {"gm", "player"}}
        for entry in state.actors.values():
            if entry.owner_participant_id in party_ids:
                entry.location_id = destination_id
                CampaignRules._ensure_exploration_token(state, entry, location_id=destination_id, reset_position=True)
        return record

    @staticmethod
    def _exploration_token_move(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor_id = str(payload.get("actor_id") or "")
        campaign_actor = state.actors.get(actor_id)
        token = state.exploration_tokens.get(actor_id)
        if campaign_actor is None or token is None:
            raise ValueError("That actor has no exploration token.")
        if actor.role != "gm" and campaign_actor.owner_participant_id != actor.id:
            raise PermissionError("You can only move exploration tokens you own.")
        location_id = str(state.world.get("current_location_id") or "")
        if str(token.get("location_id") or "") != location_id:
            raise ValueError("That token is not on the current scene floor.")
        scene = state.active_scene()
        if actor.role != "gm" and (scene is None or not scene.published or not scene.available):
            raise PermissionError("The GM has not opened this scene for movement.")
        scene_map = state.exploration_maps.get(location_id)
        if scene_map is None:
            raise ValueError("The current location has no exploration map.")
        target_x = int(payload.get("x") if payload.get("x") is not None else token.get("x") or 0)
        target_y = int(payload.get("y") if payload.get("y") is not None else token.get("y") or 0)
        width = int(scene_map.get("width") or 1)
        height = int(scene_map.get("height") or 1)
        if target_x < 0 or target_y < 0 or target_x >= width or target_y >= height:
            raise ValueError("That tile is outside the scene floor.")
        before_x = int(token.get("x") or 0)
        before_y = int(token.get("y") or 0)
        if (target_x, target_y) == (before_x, before_y):
            raise ValueError("Choose a different destination tile.")
        target_key = state._cell_key(target_x, target_y)
        path = state._exploration_paths(actor_id).get(target_key)
        if not path:
            raise ValueError("That destination has no legal path within this token's Speed.")
        if actor.role != "gm" and not state._exploration_route_known(actor, location_id, path):
            raise PermissionError("Explore the fog frontier before routing through unseen terrain.")
        for step in path:
            token["x"] = int(step["x"])
            token["y"] = int(step["y"])
            if campaign_actor.owner_participant_id:
                CampaignRules._remember_exploration(state, campaign_actor.owner_participant_id, location_id)
        discovered_point_ids: List[str] = []
        owner = state.participants.get(str(campaign_actor.owner_participant_id or ""))
        if owner is not None:
            visible_cells = state._visible_cell_keys(owner, location_id)
            for point in sorted(scene_map.get("points") or [], key=lambda entry: str(entry.get("id") or "")):
                point_key = state._cell_key(int(point.get("x") or 0), int(point.get("y") or 0))
                if bool(point.get("discoverable")) and not bool(point.get("revealed")) and point_key in visible_cells:
                    point["revealed"] = True
                    discovered_point_ids.append(str(point.get("id") or ""))
        return {
            "actor_id": actor_id,
            "from": {"x": before_x, "y": before_y},
            "to": {"x": target_x, "y": target_y},
            "location_id": location_id,
            "path": [{"x": before_x, "y": before_y}, *path],
            "steps": len(path),
            "discovered_point_ids": discovered_point_ids,
        }

    @staticmethod
    def _exploration_visibility(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("location_id") or state.world.get("current_location_id") or "")
        scene_map = state.exploration_maps.get(location_id)
        if scene_map is None:
            raise ValueError("Unknown exploration map.")
        width = int(scene_map.get("width") or 1)
        height = int(scene_map.get("height") or 1)
        mode = str(payload.get("mode") or "reveal_all").strip().lower()
        revealed = {str(value) for value in scene_map.get("revealed_cells") or [] if str(value)}
        if mode == "reveal_all":
            revealed = {state._cell_key(x, y) for y in range(height) for x in range(width)}
        elif mode == "restore_fog":
            revealed.clear()
            for participant_id in sorted(state.exploration_memory):
                state.exploration_memory[participant_id].pop(location_id, None)
        elif mode == "cells":
            make_visible = bool(payload.get("revealed", True))
            for value in payload.get("cells") or []:
                key = str(value)
                if key:
                    revealed.add(key) if make_visible else revealed.discard(key)
        else:
            raise ValueError("Visibility mode must be reveal_all, restore_fog, or cells.")
        scene_map["revealed_cells"] = sorted(revealed)
        return {"location_id": location_id, "mode": mode, "revealed_cell_count": len(revealed)}

    @staticmethod
    def _exploration_point_visibility(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("location_id") or state.world.get("current_location_id") or "")
        point_id = str(payload.get("point_id") or "")
        point = CampaignRules._exploration_point(state, location_id, point_id)
        point["revealed"] = bool(payload.get("revealed", True))
        return {"location_id": location_id, "point_id": point_id, "revealed": point["revealed"]}

    @staticmethod
    def _exploration_point_update(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("location_id") or state.world.get("current_location_id") or "")
        point_id = str(payload.get("point_id") or "")
        point = CampaignRules._exploration_point(state, location_id, point_id)
        before = bool(point.get("available", True))
        if "available" in payload:
            point["available"] = bool(payload.get("available"))
        if bool(payload.get("reset_completed")):
            point["completed_by"] = []
        return {
            "location_id": location_id,
            "point_id": point_id,
            "before": before,
            "available": bool(point.get("available", True)),
            "completed_by": list(point.get("completed_by") or []),
        }

    @classmethod
    def _exploration_point_interact(cls, state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        location_id = str(payload.get("location_id") or state.world.get("current_location_id") or "")
        point_id = str(payload.get("point_id") or "")
        point = cls._exploration_point(state, location_id, point_id)
        scene = state.active_scene()
        if actor.role != "gm" and (scene is None or not scene.published or not scene.available):
            raise PermissionError("The GM has not opened this scene for interaction.")
        if actor.role != "gm" and not bool(point.get("revealed")):
            raise PermissionError("The GM has not revealed that point of interest.")
        if not bool(point.get("available", True)):
            raise PermissionError("The GM has locked that interaction for now.")
        completed_by = {str(value) for value in point.get("completed_by") or [] if str(value)}
        if bool(point.get("once")) and completed_by:
            raise ValueError("That interaction is already complete.")

        requested_actor_id = str(payload.get("actor_id") or "")
        candidates = []
        for token in state.exploration_tokens.values():
            token_actor_id = str(token.get("actor_id") or "")
            campaign_actor = state.actors.get(token_actor_id)
            if campaign_actor is None or str(token.get("location_id") or "") != location_id:
                continue
            if requested_actor_id and token_actor_id != requested_actor_id:
                continue
            if actor.role != "gm" and campaign_actor.owner_participant_id != actor.id:
                continue
            distance = max(
                abs(int(token.get("x") or 0) - int(point.get("x") or 0)),
                abs(int(token.get("y") or 0) - int(point.get("y") or 0)),
            )
            candidates.append((distance, token_actor_id, campaign_actor, token))
        if requested_actor_id and not candidates:
            raise PermissionError("You can only interact using an exploration token you control.")
        if not candidates:
            raise ValueError("Place one of your exploration tokens near that point first.")
        distance, campaign_actor_id, campaign_actor, _token = min(candidates, key=lambda value: (value[0], value[1]))
        interaction_range = max(0, min(3, int(point.get("interaction_range") if point.get("interaction_range") is not None else 1)))
        if distance > interaction_range:
            raise ValueError("Move an owned token next to that point before interacting.")

        check_payload = dict(point.get("check") or {})
        check_result = cls._roll_check(state, actor, check_payload) if check_payload else None
        difficulty = int(check_payload.get("difficulty") or 0)
        success = check_result is None or int(check_result.get("total") or 0) >= difficulty
        result = str(point.get("result") if success else point.get("failure_result") or "").strip()
        if not result:
            result = "The interaction changes the party's understanding of the scene."
        completed_objectives = []
        if success:
            completed_by.add(actor.id)
            point["completed_by"] = sorted(completed_by)
            completed_objectives = cls._complete_matching_objectives(state, point.get("complete_objectives") or [])
        return {
            "location_id": location_id,
            "point_id": point_id,
            "label": str(point.get("label") or "Point of interest"),
            "interaction": str(point.get("interaction") or "Investigate"),
            "actor_id": campaign_actor_id,
            "actor_name": campaign_actor.name,
            "result": result,
            "success": success,
            "check": check_result,
            "difficulty": difficulty or None,
            "completed_objectives": completed_objectives,
            "public": bool(point.get("revealed")),
        }

    @staticmethod
    def _exploration_token_visibility(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        actor_id = str(payload.get("actor_id") or "")
        token = state.exploration_tokens.get(actor_id)
        if token is None:
            raise ValueError("Unknown exploration token.")
        token["revealed"] = bool(payload.get("revealed", True))
        return {"actor_id": actor_id, "revealed": token["revealed"]}

    @classmethod
    def _recipe_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        recipe_id = str(payload.get("id") or cls._identifier(state, "recipe", state.recipes))
        state.recipes[recipe_id] = {
            "id": recipe_id,
            "name": str(payload.get("name") or recipe_id).strip(),
            "ingredients": {str(key): max(1, int(value)) for key, value in dict(payload.get("ingredients") or {}).items()},
            "output_item": str(payload.get("output_item") or "Crafted Item").strip(),
            "output_quantity": max(1, int(payload.get("output_quantity") or 1)),
            "hours": max(1, int(payload.get("hours") or 1)),
        }
        return dict(state.recipes[recipe_id])

    @staticmethod
    def _craft_item(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        recipe = state.recipes.get(str(payload.get("recipe_id") or ""))
        if recipe is None:
            raise ValueError("Unknown recipe.")
        trainer = CampaignRules._trainer_for(state, actor.id)
        ingredients = dict(recipe.get("ingredients") or {})
        missing = [key for key in sorted(ingredients) if int(trainer.inventory.get(key) or 0) < int(ingredients[key])]
        if missing:
            raise ValueError(f"Missing ingredients: {', '.join(missing)}")
        for key in sorted(ingredients):
            trainer.inventory[key] = int(trainer.inventory.get(key) or 0) - int(ingredients[key])
            if trainer.inventory[key] <= 0:
                trainer.inventory.pop(key, None)
        output = str(recipe.get("output_item") or "Crafted Item")
        quantity = max(1, int(recipe.get("output_quantity") or 1))
        trainer.inventory[output] = int(trainer.inventory.get(output) or 0) + quantity
        return {"trainer": trainer.id, "recipe": recipe["id"], "item": output, "quantity": quantity, "hours": int(recipe.get("hours") or 1)}

    @classmethod
    def _shop_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        shop_id = str(payload.get("id") or cls._identifier(state, "shop", state.shops))
        stock = {}
        for key, raw in dict(payload.get("stock") or {}).items():
            item = dict(raw) if isinstance(raw, dict) else {"price": raw}
            stock[str(key)] = {"price": max(0, int(item.get("price") or 0)), "quantity": max(0, int(item.get("quantity") or 0))}
        state.shops[shop_id] = {
            "id": shop_id,
            "name": str(payload.get("name") or shop_id).strip(),
            "location_id": str(payload.get("location_id") or state.world.get("current_location_id") or ""),
            "stock": {key: stock[key] for key in sorted(stock)},
        }
        return dict(state.shops[shop_id])

    @staticmethod
    def _shop_buy(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        shop = state.shops.get(str(payload.get("shop_id") or ""))
        if shop is None:
            raise ValueError("Unknown shop.")
        if shop.get("location_id") and shop.get("location_id") != state.world.get("current_location_id"):
            raise ValueError("Travel to that shop before buying.")
        item_name = str(payload.get("item") or "")
        stock = dict(shop.get("stock") or {})
        item = stock.get(item_name)
        quantity = max(1, int(payload.get("quantity") or 1))
        if item is None or int(item.get("quantity") or 0) < quantity:
            raise ValueError("That item is not in stock.")
        trainer = CampaignRules._trainer_for(state, actor.id)
        total = int(item.get("price") or 0) * quantity
        if trainer.currency < total:
            raise ValueError("Not enough money.")
        trainer.currency -= total
        trainer.inventory[item_name] = int(trainer.inventory.get(item_name) or 0) + quantity
        item["quantity"] = int(item.get("quantity") or 0) - quantity
        shop["stock"][item_name] = item
        return {"trainer": trainer.id, "shop": shop["id"], "item": item_name, "quantity": quantity, "cost": total, "currency": trainer.currency}

    @staticmethod
    def _shop_sell(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        shop = state.shops.get(str(payload.get("shop_id") or ""))
        if shop is None:
            raise ValueError("Unknown shop.")
        item_name = str(payload.get("item") or "")
        quantity = max(1, int(payload.get("quantity") or 1))
        trainer = CampaignRules._trainer_for(state, actor.id)
        if int(trainer.inventory.get(item_name) or 0) < quantity:
            raise ValueError("You do not own enough of that item.")
        stock_item = dict((shop.get("stock") or {}).get(item_name) or {"price": int(payload.get("price") or 0), "quantity": 0})
        value = max(0, int(stock_item.get("price") or 0) // 2) * quantity
        trainer.inventory[item_name] -= quantity
        if trainer.inventory[item_name] <= 0:
            trainer.inventory.pop(item_name, None)
        trainer.currency += value
        stock_item["quantity"] = int(stock_item.get("quantity") or 0) + quantity
        shop.setdefault("stock", {})[item_name] = stock_item
        return {"trainer": trainer.id, "shop": shop["id"], "item": item_name, "quantity": quantity, "value": value, "currency": trainer.currency}

    @staticmethod
    def _downtime_activity(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        activity = str(payload.get("activity") or "recover").strip().lower()
        if activity not in {"recover", "train", "bond", "research", "work"}:
            raise ValueError("Unsupported downtime activity.")
        target_id = str(payload.get("actor_id") or "")
        target = CampaignRules._owned_actor(state, actor.id, target_id) if target_id else CampaignRules._trainer_for(state, actor.id)
        detail: Dict[str, Any] = {"id": f"downtime-{state.revision + 1}", "participant_id": actor.id, "actor_id": target.id, "activity": activity, "hours": max(1, int(payload.get("hours") or 2))}
        if activity == "recover":
            target.sheet["current_hp"] = int(target.sheet.get("max_hp") or target.sheet.get("current_hp") or 1)
            target.sheet["conditions"] = []
            detail["recovered"] = True
        elif activity == "train":
            target.xp += 1
            detail["xp"] = target.xp
        elif activity == "bond":
            partner_id = str(payload.get("partner_id") or "")
            partner = CampaignRules._owned_actor(state, actor.id, partner_id)
            target.relationships[partner.id] = min(10, int(target.relationships.get(partner.id) or 0) + 1)
            detail.update({"partner_id": partner.id, "bond": target.relationships[partner.id]})
        elif activity == "research":
            topic = str(payload.get("topic") or "Field observation").strip()
            if topic not in target.knowledge:
                target.knowledge.append(topic)
            detail["topic"] = topic
        elif activity == "work":
            target.currency += max(1, int(payload.get("earnings") or 100))
            detail["currency"] = target.currency
        state.downtime_history.append(detail)
        state.downtime_history = state.downtime_history[-100:]
        return detail

    @staticmethod
    def _world_environment(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        before = {key: state.world.get(key) for key in ("weather", "lighting", "fog")}
        if "weather" in payload:
            state.world["weather"] = str(payload.get("weather") or "Clear").strip()
        if "lighting" in payload:
            state.world["lighting"] = str(payload.get("lighting") or "Daylight").strip()
        if "fog" in payload:
            state.world["fog"] = max(0, min(10, int(payload.get("fog") or 0)))
        after = {key: state.world.get(key) for key in ("weather", "lighting", "fog")}
        return {"before": before, "after": after, "visibility_penalty": max(0, int(after["fog"] or 0) + (2 if after["lighting"] in {"Dark", "Blackout"} else 0))}

    @staticmethod
    def _progression_award(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        award_type = str(payload.get("award_type") or "league_points").strip().lower()
        trainer_id = str(payload.get("trainer_id") or "")
        trainer = state.actors.get(trainer_id) if trainer_id else None
        if trainer is not None and trainer.kind != "trainer":
            raise ValueError("Progression awards belong to Trainers.")
        if award_type == "gym_badge":
            badge = str(payload.get("name") or "Gym Badge").strip()
            badges = state.progression.setdefault("gym_badges", [])
            if badge not in badges:
                badges.append(badge)
            if trainer and badge not in trainer.badges:
                trainer.badges.append(badge)
            return {"award_type": award_type, "name": badge, "badges": list(badges)}
        if award_type == "rival_defeated":
            rival_id = str(payload.get("rival_id") or "rival")
            defeated = state.progression.setdefault("rivals_defeated", [])
            if rival_id not in defeated:
                defeated.append(rival_id)
            return {"award_type": award_type, "rival_id": rival_id, "count": len(defeated)}
        if award_type == "league_rank":
            rank = str(payload.get("rank") or "Qualifier").strip()
            state.progression["league_rank"] = rank
            return {"award_type": award_type, "rank": rank}
        if award_type == "champion":
            state.progression["champion_defeated"] = True
            state.progression["league_rank"] = "Champion"
            return {"award_type": award_type, "champion_defeated": True, "rank": "Champion"}
        points = int(payload.get("points") or 1)
        state.progression["league_points"] = int(state.progression.get("league_points") or 0) + points
        if trainer:
            trainer.league_points += points
        return {"award_type": "league_points", "points": points, "total": state.progression["league_points"]}

    @staticmethod
    def _npc_talk(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        npc = state.actors.get(str(payload.get("npc_id") or ""))
        if npc is None or npc.kind not in {"npc", "rival", "gym_leader", "league", "champion"}:
            raise ValueError("Choose a known NPC.")
        if npc.location_id and npc.location_id != state.world.get("current_location_id"):
            raise ValueError("That character is not at the current location.")
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Say or ask something.")
        dialogue_id = f"dialogue-{state.revision + 1}"
        record = {"id": dialogue_id, "seq": state.revision + 1, "scene_id": state.active_scene_id, "participant_id": actor.id, "participant_name": actor.name, "npc_id": npc.id, "npc_name": npc.name, "text": text[:1200], "response": "", "status": "waiting"}
        state.dialogue.append(record)
        state.dialogue = state.dialogue[-150:]
        return dict(record)

    @staticmethod
    def _npc_reply(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        dialogue_id = str(payload.get("dialogue_id") or "")
        record = next((entry for entry in state.dialogue if entry.get("id") == dialogue_id), None)
        if record is None:
            raise ValueError("Unknown dialogue exchange.")
        npc = state.actors.get(str(record.get("npc_id") or ""))
        if npc is None:
            raise ValueError("Unknown NPC.")
        response = str(payload.get("response") or "").strip()
        if not response:
            raise ValueError("NPC response is required.")
        record["response"] = response[:1600]
        record["status"] = "answered"
        relationship_delta = max(-2, min(2, int(payload.get("relationship_delta") or 0)))
        if relationship_delta:
            npc.relationships[str(record.get("participant_id") or "")] = max(-10, min(10, int(npc.relationships.get(str(record.get("participant_id") or "")) or 0) + relationship_delta))
        scene = state.active_scene()
        objective_terms = []
        if scene is not None:
            trigger_map = dict(scene.metadata.get("complete_objectives_on_npc_reply") or {})
            objective_terms = list(trigger_map.get(npc.id) or [])
        completed = CampaignRules._complete_matching_objectives(state, objective_terms)
        return {"dialogue_id": dialogue_id, "npc_id": npc.id, "npc_name": npc.name, "response": record["response"], "relationship_delta": relationship_delta, "completed_objectives": completed}

    @classmethod
    def _scene_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = str(payload.get("id") or cls._identifier(state, "scene", state.scenes))
        activate = bool(payload.get("activate")) or not state.active_scene_id
        published = bool(payload.get("published", activate))
        scene = SceneState(
            id=scene_id,
            title=str(payload.get("title") or "New Scene").strip(),
            order=max(0, int(payload.get("order") or (len(state.scenes) + 1))),
            kind=str(payload.get("kind") or "roleplay").strip().lower(),
            location=str(payload.get("location") or "").strip(),
            summary=str(payload.get("summary") or "").strip(),
            participant_ids=[str(value) for value in payload.get("participant_ids") or []],
            published=published,
            available=bool(payload.get("available", activate)),
            metadata=dict(payload.get("metadata") or {}),
        )
        if scene.kind not in {"roleplay", "exploration", "combat", "downtime", "travel"}:
            raise ValueError("Scene kind must be roleplay, exploration, combat, downtime, or travel.")
        state.scenes[scene_id] = scene
        if activate:
            state.active_scene_id = scene_id
            scene.published = True
            scene.available = True
            scene.metadata["activated_seq"] = state.revision + 1
            cls._reveal_location(state, str(scene.metadata.get("location_id") or ""))
        return {"scene": scene_id, "title": scene.title, "kind": scene.kind, "published": scene.published, "available": scene.available}

    @staticmethod
    def _scene_activate(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = str(payload.get("scene_id") or "")
        if scene_id not in state.scenes:
            raise ValueError("Unknown scene.")
        current = state.active_scene()
        target = state.scenes[scene_id]
        if current is not None and target.order > current.order:
            current_location = str(current.metadata.get("location_id") or "")
            if current_location and current_location != str(state.world.get("current_location_id") or ""):
                destination = state.locations.get(current_location, {}).get("name") or current.location or current_location
                raise ValueError(f"Travel to {destination} and play the current chapter before continuing.")
            gate = state.scene_gate(current)
            if not gate["ready"]:
                raise ValueError(f"Finish the chapter goal first: {gate['incomplete_labels'][0]}.")
            completed = CampaignRules._complete_matching_objectives(
                state,
                current.metadata.get("complete_objectives_on_exit") or [],
            )
        else:
            completed = []
        state.active_scene_id = scene_id
        target.published = True
        target.available = True
        target.metadata["activated_seq"] = state.revision + 1
        target_location = str(target.metadata.get("location_id") or "")
        CampaignRules._reveal_location(state, target_location)
        present_npcs = {
            str(value)
            for value in [
                *(target.metadata.get("npc_actor_ids") or []),
                target.metadata.get("leader_id"),
                target.metadata.get("rival_id"),
            ]
            if str(value or "")
        }
        for npc_id in sorted(present_npcs):
            if npc_id in state.actors and target_location:
                state.actors[npc_id].location_id = target_location
        return {"scene": scene_id, "published": True, "available": True, "completed_objectives": completed}

    @staticmethod
    def _scene_visibility(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = str(payload.get("scene_id") or "")
        scene = state.scenes.get(scene_id)
        if scene is None:
            raise ValueError("Unknown scene.")
        published = bool(payload.get("published", scene.published))
        available = bool(payload.get("available", scene.available))
        if available:
            published = True
        if scene.id == state.active_scene_id and not published:
            raise ValueError("The active scene cannot be hidden from the table.")
        scene.published = published
        scene.available = available if published else False
        return {"scene": scene.id, "published": scene.published, "available": scene.available}

    @staticmethod
    def _scene_update(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene_id = str(payload.get("scene_id") or state.active_scene_id or "")
        scene = state.scenes.get(scene_id)
        if scene is None:
            raise ValueError("Unknown scene.")
        for key in ("title", "location", "summary", "status"):
            if key in payload:
                setattr(scene, key, str(payload.get(key) or "").strip())
        return {"scene": scene_id, "status": scene.status}

    @staticmethod
    def _spotlight_set(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene = state.active_scene()
        if scene is None:
            raise ValueError("Create or activate a scene first.")
        participant_id = str(payload.get("participant_id") or "") or None
        if participant_id and participant_id not in state.participants:
            raise ValueError("Unknown participant.")
        scene.spotlight_id = participant_id
        return {"scene": scene.id, "participant_id": participant_id}

    @classmethod
    def _clock_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        clock_id = str(payload.get("id") or cls._identifier(state, "clock", state.clocks))
        segments = max(2, min(20, int(payload.get("segments") or 6)))
        state.clocks[clock_id] = {
            "id": clock_id,
            "name": str(payload.get("name") or "Progress Clock").strip(),
            "segments": segments,
            "filled": 0,
            "scene_id": str(payload.get("scene_id") or state.active_scene_id or "") or None,
            "visibility": str(payload.get("visibility") or "table"),
            "reveal_order": max(0, int(payload.get("reveal_order") or 0)),
        }
        return dict(state.clocks[clock_id])

    @staticmethod
    def _clock_tick(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        clock_id = str(payload.get("clock_id") or "")
        clock = state.clocks.get(clock_id)
        if clock is None:
            raise ValueError("Unknown clock.")
        delta = int(payload.get("delta") or 1)
        before = int(clock.get("filled") or 0)
        clock["filled"] = max(0, min(int(clock["segments"]), before + delta))
        return {"clock": clock_id, "before": before, "after": clock["filled"], "complete": clock["filled"] >= clock["segments"]}

    @classmethod
    def _quest_create(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        quest_id = str(payload.get("id") or cls._identifier(state, "quest", state.quests))
        objectives = []
        for index, raw in enumerate(payload.get("objectives") or []):
            text = str(raw.get("text") if isinstance(raw, dict) else raw).strip()
            if text:
                objective = {"id": f"{quest_id}-objective-{index + 1}", "text": text, "complete": False}
                if isinstance(raw, dict):
                    objective["id"] = str(raw.get("id") or objective["id"])
                    objective["visibility"] = str(raw.get("visibility") or "table")
                    objective["reveal_order"] = max(0, int(raw.get("reveal_order") or 0))
                objectives.append(objective)
        state.quests[quest_id] = {
            "id": quest_id,
            "name": str(payload.get("name") or "New Quest").strip(),
            "status": "active",
            "objectives": objectives,
            "reward": str(payload.get("reward") or "").strip(),
            "visibility": str(payload.get("visibility") or "table"),
            "reveal_order": max(0, int(payload.get("reveal_order") or 0)),
        }
        return {"quest": quest_id, "name": state.quests[quest_id]["name"]}

    @staticmethod
    def _quest_objective(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        quest_id = str(payload.get("quest_id") or "")
        objective_id = str(payload.get("objective_id") or "")
        quest = state.quests.get(quest_id)
        if quest is None:
            raise ValueError("Unknown quest.")
        objective = next((entry for entry in quest.get("objectives") or [] if entry.get("id") == objective_id), None)
        if objective is None:
            raise ValueError("Unknown quest objective.")
        objective["complete"] = bool(payload.get("complete", True))
        if quest.get("objectives") and all(entry.get("complete") for entry in quest["objectives"]):
            quest["status"] = "complete"
        elif quest.get("status") == "complete":
            quest["status"] = "active"
        return {"quest": quest_id, "objective": objective_id, "complete": objective["complete"]}

    @classmethod
    def _faction_adjust(cls, state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        faction_id = str(payload.get("faction_id") or "")
        if faction_id not in state.factions:
            faction_id = faction_id or cls._identifier(state, "faction", state.factions)
            state.factions[faction_id] = {
                "id": faction_id,
                "name": str(payload.get("name") or "Faction"),
                "score": 0,
                "visibility": str(payload.get("visibility") or "table"),
                "reveal_order": max(0, int(payload.get("reveal_order") or 0)),
            }
        entry = state.factions[faction_id]
        before = int(entry.get("score") or 0)
        entry["score"] = max(-10, min(10, before + int(payload.get("delta") or 0)))
        return {"faction": faction_id, "before": before, "after": entry["score"]}

    @staticmethod
    def _time_set(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        label = str(payload.get("label") or "").strip()
        if not label:
            raise ValueError("A campaign time label is required.")
        before = state.time_label
        state.time_label = label
        return {"before": before, "after": label}

    @staticmethod
    def _battle_link(state: CampaignState, _actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        scene = state.active_scene()
        if scene is None:
            raise ValueError("Create or activate a scene first.")
        scene.kind = "combat"
        scene.battle_id = str(payload.get("battle_id") or "current")
        return {"scene": scene.id, "battle_id": scene.battle_id}

    @staticmethod
    def _chat_post(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Message text is required.")
        entry = {"id": f"chat-{state.revision + 1}", "actor_id": actor.id, "actor_name": actor.name, "text": text[:2000], "kind": str(payload.get("kind") or "in_character")}
        state.chat.append(entry)
        state.chat = state.chat[-300:]
        return entry

    @classmethod
    def _roll_check(cls, state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        expression = str(payload.get("expression") or "2d6").lower()
        match = _DICE_RE.match(expression)
        if not match:
            raise ValueError("Dice must use NdM, optionally followed by +K or -K.")
        count, sides = int(match.group(1)), int(match.group(2))
        if count > 40 or sides < 2:
            raise ValueError("Dice are limited to 40 dice with at least 2 sides.")
        modifier = int(match.group(4) or 0) * (-1 if match.group(3) == "-" else 1)
        label = str(payload.get("label") or "Check").strip()
        seed_text = f"{state.seed}:{state.revision + 1}:{actor.id}:{count}d{sides}:{modifier}:{label}"
        seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        rolls = [rng.randint(1, sides) for _ in range(count)]
        return {"label": label, "expression": expression, "rolls": rolls, "modifier": modifier, "total": sum(rolls) + modifier}

    @staticmethod
    def _journal_add(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        title = str(payload.get("title") or "Note").strip()
        text = str(payload.get("text") or "").strip()
        if not text:
            raise ValueError("Journal text is required.")
        visibility = str(payload.get("visibility") or "table").strip().lower()
        if visibility not in {"table", "private", "gm"}:
            raise ValueError("Journal visibility must be table, private, or gm.")
        entry = {"id": f"note-{state.revision + 1}", "actor_id": actor.id, "actor_name": actor.name, "title": title, "text": text[:5000], "visibility": visibility}
        state.journal.append(entry)
        state.journal = state.journal[-300:]
        return entry

    @staticmethod
    def _safety_pause(state: CampaignState, actor: ParticipantState, payload: Dict[str, Any]) -> Dict[str, Any]:
        state.safety_paused = True
        state.safety_message = str(payload.get("message") or "The table has paused. Check in before continuing.").strip()
        return {"paused": True, "message": state.safety_message, "requested_by": actor.name}

    @staticmethod
    def _safety_resume(state: CampaignState, _actor: ParticipantState, _payload: Dict[str, Any]) -> Dict[str, Any]:
        state.safety_paused = False
        state.safety_message = ""
        return {"paused": False}
