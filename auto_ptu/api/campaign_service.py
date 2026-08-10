"""Persistence and authentication boundary for campaign play."""

from __future__ import annotations

import re
import secrets
import hashlib
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..persistence.event_store import EventStore
from ..csv_repository import PTUCsvRepository
from ..rules.campaign_commands import CampaignRules
from ..rules.campaign_state import CAMPAIGN_ROLES, CampaignState, ParticipantState
from .campaign_starter import build_starter_blueprint


def _slug(value: object, fallback: str = "campaign") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return cleaned[:48] or fallback


@dataclass
class CampaignService:
    store_path: Path
    store: EventStore = field(init=False)
    campaigns: Dict[str, CampaignState] = field(default_factory=dict)
    event_listeners: List[Callable[[str, Dict[str, Any]], None]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.store = EventStore(self.store_path)
        index = self.store.load_snapshot("campaign:index") or {}
        for campaign_id in sorted(index.get("campaign_ids") or []):
            payload = self.store.load_snapshot(f"campaign:{campaign_id}")
            if isinstance(payload, dict):
                state = CampaignState.from_dict(payload)
                self._ensure_exploration_compatibility(state)
                self.campaigns[str(campaign_id)] = state

    @staticmethod
    def _ensure_exploration_compatibility(state: CampaignState) -> None:
        """Give legacy saves scene floors and tokens without adding fake events."""
        gm = state.participants.get(state.gm_id)
        if gm is None:
            return
        blueprint = build_starter_blueprint(gm.name)
        starter_maps = {
            str(location["id"]): dict(location.get("exploration") or {})
            for location in blueprint.get("locations") or []
            if isinstance(location, dict) and location.get("id")
        }
        starter_scenes = {
            str(scene["id"]): dict(scene.get("metadata") or {})
            for scene in blueprint.get("scenes") or []
            if isinstance(scene, dict) and scene.get("id")
        }
        for scene_id, scene in sorted(state.scenes.items()):
            authored_gate = starter_scenes.get(scene_id, {}).get("completion_gate")
            if authored_gate and not scene.metadata.get("completion_gate"):
                scene.metadata["completion_gate"] = [dict(entry) for entry in authored_gate]
        for location_id in sorted(state.locations):
            if location_id in state.exploration_maps:
                scene_map = state.exploration_maps[location_id]
                authored_points = {
                    str(point.get("id") or ""): dict(point)
                    for point in starter_maps.get(location_id, {}).get("points") or []
                    if isinstance(point, dict) and point.get("id")
                }
                width = max(1, int(scene_map.get("width") or 10))
                height = max(1, int(scene_map.get("height") or 7))
                scene_map["points"] = sorted(
                    [
                        CampaignRules._normalize_exploration_point(
                            {**authored_points.get(str(point.get("id") or ""), {}), **dict(point)},
                            index,
                            width,
                            height,
                        )
                        for index, point in enumerate(scene_map.get("points") or [])
                        if isinstance(point, dict)
                    ],
                    key=lambda point: point["id"],
                )
            else:
                location = dict(state.locations[location_id])
                location["exploration"] = starter_maps.get(location_id, {"width": 10, "height": 7, "theme": location.get("kind") or "route"})
                CampaignRules._location_create(state, gm, location)
        for actor in sorted(state.actors.values(), key=lambda entry: entry.id):
            if actor.kind != "pokemon" or actor.owner_participant_id:
                CampaignRules._ensure_exploration_token(state, actor)

    def _persist(self, state: CampaignState, event: Dict[str, Any]) -> None:
        self.store.save_snapshot(f"campaign:{state.id}", state.snapshot_dict())
        self.store.save_snapshot("campaign:index", {"campaign_ids": sorted(self.campaigns)})
        self.store.append(
            {
                "id": f"{state.id}:{int(event['seq']):08d}",
                "type": str(event.get("type") or "campaign.updated"),
                "actor_id": event.get("actor_id"),
                "payload": {"campaign_id": state.id, **event},
            }
        )
        for listener in list(self.event_listeners):
            try:
                listener(state.id, dict(event))
            except Exception:
                continue

    def add_event_listener(self, listener: Callable[[str, Dict[str, Any]], None]) -> None:
        if listener not in self.event_listeners:
            self.event_listeners.append(listener)

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = str(payload.get("name") or "New PTU Campaign").strip()
        base_id = _slug(payload.get("id") or name)
        campaign_id = base_id
        suffix = 2
        while campaign_id in self.campaigns:
            campaign_id = f"{base_id}-{suffix}"
            suffix += 1
        token = str(payload.get("gm_token") or secrets.token_urlsafe(24))
        gm_id = str(payload.get("gm_id") or "gm")
        gm = ParticipantState(
            id=gm_id,
            name=str(payload.get("gm_name") or "Game Master").strip(),
            role="gm",
            token=token,
            controller="human",
        )
        state = CampaignState(
            id=campaign_id,
            name=name,
            seed=int(payload.get("seed") or secrets.randbelow(2_000_000_000) + 1),
            gm_id=gm_id,
            invite_code=str(payload.get("invite_code") or secrets.token_hex(3).upper()),
            participants={gm.id: gm},
        )
        self.campaigns[state.id] = state
        event = state.record_event(
            {
                "type": "campaign.created",
                "actor_id": gm.id,
                "actor_name": gm.name,
                "detail": {"name": state.name, "system": state.system},
            }
        )
        self._persist(state, event)
        return {"campaign": self.public_state(state, gm), "token": token}

    def create_starter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create an evented regional journey with persistent people and Pokémon."""
        play_mode = str(payload.get("play_mode") or "director").strip().lower()
        if play_mode not in {"solo", "director"}:
            raise ValueError("Play mode must be solo or director.")
        solo = play_mode == "solo"
        human_name = str(
            payload.get("player_name")
            or payload.get("gm_name")
            or ("Trainer" if solo else "Game Master")
        ).strip()
        authority_id = "agent-gm" if solo else str(payload.get("gm_id") or "gm")
        authority_name = "The Prism Keeper" if solo else human_name
        created = self.create(
            {
                "id": payload.get("id") or "prism-league-journey",
                "name": payload.get("name") or "Prism League: A Trainer's Journey",
                "gm_id": authority_id,
                "gm_name": authority_name,
                "gm_token": payload.get("agent_gm_token") if solo else payload.get("gm_token"),
                "invite_code": payload.get("invite_code"),
                "seed": payload.get("seed") or 731245,
            }
        )
        campaign_id = str(created["campaign"]["id"])
        authority_token = str(created["token"])
        state = self.require_campaign(campaign_id)
        gm_agent = {"participant_id": "agent-gm", "name": "The Prism Keeper", "role": "gm", "agent_model": str(payload.get("gm_model") or "qwen2.5:3b"), "agent_persona": "A fair, character-driven PTU Game Master who portrays every NPC from their recorded goals and knowledge, never skips consequences, and opens choices instead of dictating outcomes.", "companion": "The living world", "color": "#f6c453"}
        if solo:
            authority = state.participants[authority_id]
            authority.is_agent = True
            authority.controller = "ai"
            authority.agent_model = str(gm_agent["agent_model"])
            authority.agent_persona = str(gm_agent["agent_persona"])
            authority.companion = str(gm_agent["companion"])
            authority.color = str(gm_agent["color"])
            player_token = str(payload.get("player_token") or secrets.token_urlsafe(24))
            player = ParticipantState(
                id="player",
                name=human_name,
                role="player",
                token=player_token,
                character_ids=["trainer-player"],
                color="#79aef2",
                controller="human",
            )
            state.participants[player.id] = player
            state.world["play_mode"] = "solo"
            state.world["agent_host_participant_id"] = player.id
            joined_event = state.record_event(
                {
                    "type": "participant.joined",
                    "actor_id": player.id,
                    "actor_name": player.name,
                    "detail": {"role": "player", "play_mode": "solo"},
                }
            )
            self._persist(state, joined_event)
            public_token = player_token
        else:
            public_token = authority_token
            self.add_agent(campaign_id, authority_token, gm_agent)

        starter_agents = (
            {"participant_id": "agent-nova", "name": "Nova Vale", "role": "player", "agent_model": str(payload.get("player_model") or "qwen2.5:3b"), "agent_persona": "A bold Ace Trainer who protects others first, loves tactical risks, and speaks with energetic confidence.", "companion": "Growlithe", "color": "#fb7185", "character_ids": ["trainer-nova", "pokemon-growlithe"]},
            {"participant_id": "agent-milo", "name": "Milo Reed", "role": "player", "agent_model": str(payload.get("player_model") or "qwen2.5:3b"), "agent_persona": "A careful Researcher who follows evidence, respects wild habitats, and changes theories when the facts demand it.", "companion": "Shinx", "color": "#67e8f9", "character_ids": ["trainer-milo", "pokemon-shinx"]},
            {"participant_id": "agent-sera", "name": "Sera Moss", "role": "player", "agent_model": str(payload.get("player_model") or "qwen2.5:3b"), "agent_persona": "An empathetic Ranger who de-escalates danger, listens for unspoken needs, and never abandons a trail.", "companion": "Chikorita", "color": "#a7f3d0", "character_ids": ["trainer-sera", "pokemon-chikorita"]},
        )
        for agent in starter_agents:
            digest = hashlib.sha256(f"{campaign_id}:{agent['participant_id']}:{created['campaign']['seed']}".encode("utf-8")).hexdigest()[:32]
            self.add_agent(campaign_id, authority_token, {**agent, "token": f"agent-{digest}"})

        blueprint = build_starter_blueprint(human_name, player_owner_id="player" if solo else authority_id)
        for location in blueprint["locations"]:
            self.command(campaign_id, authority_token, {"type": "location.create", "payload": location})
        for actor_payload in blueprint["actors"]:
            self.command(campaign_id, authority_token, {"type": "actor.create", "payload": actor_payload})
        for recipe in blueprint["recipes"]:
            self.command(campaign_id, authority_token, {"type": "recipe.create", "payload": recipe})
        for shop in blueprint["shops"]:
            self.command(campaign_id, authority_token, {"type": "shop.create", "payload": shop})
        for scene in blueprint["scenes"]:
            self.command(campaign_id, authority_token, {"type": "scene.create", "payload": scene})
        for quest in blueprint["quests"]:
            self.command(campaign_id, authority_token, {"type": "quest.create", "payload": quest})

        self.command(campaign_id, authority_token, {"type": "clock.create", "payload": {"id": "clock-cinder-plan", "name": "Team Cinder Controls the Prism", "segments": 8, "scene_id": "scene-glasswood-voices"}})
        self.command(campaign_id, authority_token, {"type": "clock.create", "payload": {"id": "clock-league-scrutiny", "name": "League Scrutiny", "segments": 6, "scene_id": "scene-badge-gate"}})
        self.command(campaign_id, authority_token, {"type": "faction.adjust", "payload": {"faction_id": "faction-rangers", "name": "Prism Rangers", "delta": 1, "reveal_order": 1}})
        self.command(campaign_id, authority_token, {"type": "faction.adjust", "payload": {"faction_id": "faction-cinder", "name": "Team Cinder", "delta": -1, "reveal_order": 3}})
        self.command(campaign_id, authority_token, {"type": "faction.adjust", "payload": {"faction_id": "faction-league", "name": "Prism League", "delta": 0, "reveal_order": 2}})
        self.command(campaign_id, authority_token, {"type": "time.set", "payload": {"label": "Day 1, Starter Morning"}})
        self.command(campaign_id, authority_token, {"type": "world.environment", "payload": {"weather": "Clear", "lighting": "Morning", "fog": 0}})
        starter_species = str(payload.get("starter_species") or "").strip()
        if starter_species:
            self.command(campaign_id, public_token, {"type": "starter.select", "payload": {"species": starter_species}})
        self.command(campaign_id, authority_token, {"type": "chat.post", "payload": {"kind": "narration", "text": f"Morning light moves through Professor Alder's glass lab. Five starter Pokémon watch {human_name} with five very different kinds of curiosity. Professor Alder waits for the choice to belong to both Trainer and partner."}})
        self.command(campaign_id, authority_token, {"type": "journal.add", "payload": {"title": "Journey Record", "visibility": "table", "text": "The team begins at Professor Alder's Lab. Badges, rival relationships, public choices, crafted supplies, and League results persist in this campaign."}})
        result = self.get(campaign_id, public_token)
        result["starter"] = True
        return {"campaign": result, "token": public_token}

    def add_agent(self, campaign_id: str, requester_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self.require_campaign(campaign_id)
        requester = self.require_participant(state, requester_token)
        if requester.role != "gm":
            raise PermissionError("Only the GM can add an agent seat.")
        participant_id = str(payload.get("participant_id") or "").strip()
        if not participant_id:
            raise ValueError("Agent participant id is required.")
        if participant_id in state.participants:
            return {"campaign": self.public_state(state, requester), "agent": state.participants[participant_id].public_dict()}
        role = str(payload.get("role") or "player").strip().lower()
        if role not in {"gm", "player"}:
            raise ValueError("Agent role must be gm or player.")
        participant = ParticipantState(
            id=participant_id,
            name=str(payload.get("name") or participant_id).strip(),
            role=role,
            token=str(payload.get("token") or secrets.token_urlsafe(24)),
            character_ids=[str(value) for value in payload.get("character_ids") or []],
            is_agent=True,
            agent_model=str(payload.get("agent_model") or "qwen2.5:3b"),
            agent_persona=str(payload.get("agent_persona") or "A collaborative Pokemon Tabletop United player."),
            companion=str(payload.get("companion") or ""),
            color=str(payload.get("color") or "#79aef2"),
            controller="ai",
        )
        state.participants[participant.id] = participant
        event = state.record_event(
            {
                "type": "participant.joined",
                "actor_id": participant.id,
                "actor_name": participant.name,
                "detail": {"role": role, "is_agent": True, "model": participant.agent_model},
            }
        )
        self._persist(state, event)
        return {"campaign": self.public_state(state, requester), "agent": participant.public_dict()}

    def list_campaigns(self) -> List[Dict[str, Any]]:
        records = []
        for state in sorted(self.campaigns.values(), key=lambda item: (item.name.lower(), item.id)):
            scene = state.active_scene()
            records.append(
                {
                    "id": state.id,
                    "name": state.name,
                    "system": state.system,
                    "revision": state.revision,
                    "participants": len(state.participants),
                    "active_scene": scene.title if scene else None,
                }
            )
        return records

    def join(self, campaign_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self.require_campaign(campaign_id)
        if str(payload.get("invite_code") or "").strip().upper() != state.invite_code.upper():
            raise PermissionError("Invite code is invalid.")
        role = str(payload.get("role") or "player").strip().lower()
        if role not in CAMPAIGN_ROLES or role == "gm":
            raise ValueError("Join role must be player or spectator.")
        participant_id = str(payload.get("participant_id") or f"participant-{state.revision + 1}")
        if participant_id in state.participants:
            raise ValueError("That participant id is already in use.")
        token = str(payload.get("token") or secrets.token_urlsafe(24))
        participant = ParticipantState(
            id=participant_id,
            name=str(payload.get("name") or "Player").strip(),
            role=role,
            token=token,
            character_ids=[str(value) for value in payload.get("character_ids") or []],
            is_agent=bool(payload.get("is_agent")),
            agent_model=str(payload.get("agent_model") or ""),
            agent_persona=str(payload.get("agent_persona") or ""),
            companion=str(payload.get("companion") or ""),
            color=str(payload.get("color") or ""),
            controller=str(payload.get("controller") or ("ai" if payload.get("is_agent") else "human")),
        )
        state.participants[participant.id] = participant
        event = state.record_event(
            {
                "type": "participant.joined",
                "actor_id": participant.id,
                "actor_name": participant.name,
                "detail": {"role": role},
            }
        )
        self._persist(state, event)
        if role == "player" and "scene-starter-day" in state.scenes:
            # A joined human is immediately a playable persistent Trainer, not
            # an empty observer who must discover the builder before acting.
            joined = self.command(
                campaign_id,
                token,
                {
                    "type": "builder.sync",
                    "payload": {
                        "sheet": {
                            "profile": {"name": participant.name, "level": 1, "money": 1500},
                            "trainer_classes": [],
                            "pokemon_builds": [],
                        }
                    },
                },
            )
            return {"campaign": joined["campaign"], "token": token}
        return {"campaign": self.public_state(state, participant), "token": token}

    def command(self, campaign_id: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        state = self.require_campaign(campaign_id)
        requester = self.require_participant(state, token)
        actor = requester
        acting_id = str(payload.get("as_participant_id") or "")
        if acting_id:
            if requester.role != "gm":
                raise PermissionError("Only a GM can submit a command for another seat.")
            actor = state.participants.get(acting_id)  # type: ignore[assignment]
            if actor is None:
                raise ValueError("Unknown acting participant.")
        event = CampaignRules.apply(
            state,
            actor,
            str(payload.get("type") or ""),
            dict(payload.get("payload") or {}),
        )
        event = state.record_event(event)
        self._persist(state, event)
        return {"campaign": self.public_state(state, requester), "event": event}

    def get(self, campaign_id: str, token: str) -> Dict[str, Any]:
        state = self.require_campaign(campaign_id)
        actor = self.require_participant(state, token)
        return self.public_state(state, actor)

    def events(self, campaign_id: str, token: str, since_seq: int = 0) -> List[Dict[str, Any]]:
        state = self.require_campaign(campaign_id)
        participant = self.require_participant(state, token)
        return [
            dict(entry)
            for entry in state.visible_activity(participant)
            if int(entry.get("seq") or 0) > int(since_seq)
        ]

    def battle_setup(self, campaign_id: str, token: str) -> Dict[str, Any]:
        """Build an exact battle from the persistent actors in the active scene."""
        state = self.require_campaign(campaign_id)
        requester = self.require_participant(state, token)
        agent_host_id = str(state.world.get("agent_host_participant_id") or "")
        if requester.role != "gm" and requester.id != agent_host_id:
            raise PermissionError("Only the campaign GM can open the shared tactical encounter.")
        scene = state.active_scene()
        if scene is None or scene.kind != "combat":
            raise ValueError("Activate a combat scene before opening the tactical board.")
        required_location = str(scene.metadata.get("location_id") or "")
        if required_location and required_location != str(state.world.get("current_location_id") or ""):
            destination = state.locations.get(required_location, {}).get("name") or required_location
            raise ValueError(f"Travel to {destination} before starting this encounter.")
        opponent_ids = [str(value) for value in scene.metadata.get("opponent_actor_ids") or []]
        opponents = [state.actors[value] for value in opponent_ids if value in state.actors]
        if len(opponents) != len(opponent_ids) or not opponents:
            raise ValueError("This combat scene has no complete persistent opponent roster.")

        repo = PTUCsvRepository(rng=random.Random(state.seed + scene.order * 1009))

        def pokemon_payload(entry, *, items: Optional[List[str]] = None) -> Dict[str, Any]:
            spec = repo.build_pokemon_spec(
                entry.species or entry.name,
                level=max(1, int(entry.level)),
                move_names=[str(value) for value in entry.sheet.get("moves") or []] or None,
                nickname=entry.name,
                assign_abilities=True,
                assign_nature=True,
                nature=str(entry.sheet.get("nature") or "") or None,
            )
            payload = spec.to_engine_dict()
            if items:
                payload["items"] = list(items)
            return payload

        sides: List[Dict[str, Any]] = []
        actor_owners: Dict[str, str] = {}
        trainer_owners: Dict[str, str] = {}
        for participant in sorted(
            (entry for entry in state.participants.values() if entry.role in {"gm", "player"}),
            key=lambda entry: (entry.role != "gm", entry.id),
        ):
            owned = [
                state.actors[actor_id]
                for actor_id in participant.character_ids
                if actor_id in state.actors and state.actors[actor_id].kind == "pokemon"
            ]
            if not owned:
                continue
            trainer = next(
                (
                    state.actors[actor_id]
                    for actor_id in participant.character_ids
                    if actor_id in state.actors and state.actors[actor_id].kind == "trainer"
                ),
                None,
            )
            item_list: List[str] = []
            if trainer is not None:
                for item_name in sorted(trainer.inventory):
                    item_list.extend([item_name] * max(0, int(trainer.inventory[item_name])))
            trainer_id = participant.id
            sides.append(
                {
                    "identifier": trainer_id,
                    "name": trainer.name if trainer is not None else participant.name,
                    # Campaign seats own turn dispatch.  Keeping every tactical
                    # side interactive prevents the legacy battle session from
                    # silently auto-resolving AI seats before the campaign's
                    # Ollama agent endpoint can make and record their decision.
                    "controller": "player",
                    "team": "players",
                    "pokemon": [
                        pokemon_payload(entry, items=item_list if index == 0 else None)
                        for index, entry in enumerate(owned)
                    ],
                    "skills": dict((trainer.sheet if trainer else {}).get("skills") or {}),
                    "trainer_features": list((trainer.sheet if trainer else {}).get("trainer_features") or []),
                }
            )
            trainer_owners[trainer_id] = participant.id
            for index, entry in enumerate(owned, start=1):
                actor_owners[f"{trainer_id}-{index}"] = participant.id

        if not sides:
            raise ValueError("The party has no selected persistent Pokemon.")
        opponent_trainer_id = str(scene.metadata.get("leader_id") or scene.metadata.get("rival_id") or f"opponent-{scene.id}")
        opponent_actor = state.actors.get(opponent_trainer_id)
        sides.append(
            {
                "identifier": opponent_trainer_id,
                "name": opponent_actor.name if opponent_actor else str(scene.title),
                # Opponents are portrayed by the persistent AI GM seat through
                # CampaignAgentRuntime.battle_step, not the legacy auto-player.
                "controller": "player",
                "team": "foes",
                "pokemon": [pokemon_payload(entry) for entry in opponents],
            }
        )
        trainer_owners[opponent_trainer_id] = state.gm_id
        for index in range(1, len(opponents) + 1):
            actor_owners[f"{opponent_trainer_id}-{index}"] = state.gm_id

        fog = max(0, int(state.world.get("fog") or 0))
        battle_payload = {
            "name": scene.title,
            "description": scene.summary,
            "weather": str(state.world.get("weather") or "Clear"),
            "battle_context": "full_contact" if "league" in scene.id or "gym" in scene.id else "friendly",
            "active_slots": max(1, len(opponents)),
            "grid": {
                "width": 16,
                "height": 10,
                "tiles": {
                    f"{x},{y}": {"type": "fog", "visibility_penalty": fog}
                    for x in range(16)
                    for y in range(10)
                    if fog > 0
                },
                "map": {
                    "campaign_id": state.id,
                    "scene_id": scene.id,
                    "location_id": scene.metadata.get("location_id"),
                    "lighting": state.world.get("lighting"),
                    "fog": fog,
                },
            },
            "sides": sides,
        }
        return {
            "campaign_id": state.id,
            "scene_id": scene.id,
            "seed": state.seed + scene.order * 1009,
            "battle": battle_payload,
            "actor_owners": dict(sorted(actor_owners.items())),
            "trainer_owners": dict(sorted(trainer_owners.items())),
        }

    def complete_battle(self, campaign_id: str, token: str, *, winner_team: str) -> Dict[str, Any]:
        """Apply one campaign battle's persistent progression exactly once."""
        state = self.require_campaign(campaign_id)
        requester = self.require_participant(state, token)
        agent_host_id = str(state.world.get("agent_host_participant_id") or "")
        if requester.role != "gm" and requester.id != agent_host_id:
            raise PermissionError("Only the campaign GM can finalize a tactical encounter.")
        authority = state.participants.get(state.gm_id)
        if authority is None:
            raise PermissionError("The campaign has no authoritative GM seat.")
        authority_token = authority.token
        scene = state.active_scene()
        if scene is None or scene.kind != "combat":
            raise ValueError("No active campaign combat can be finalized.")
        if scene.metadata.get("battle_completed"):
            return {"campaign": self.public_state(state, requester), "already_completed": True}
        if str(winner_team or "").lower() not in {"players", "player", "allies"}:
            raise ValueError("The party has not won this encounter.")

        scene.metadata["battle_completed"] = True
        scene.status = "complete"
        awards: List[Dict[str, Any]] = []
        trainer_owner_id = requester.id if requester.role == "player" else state.gm_id
        trainer_id = next(
            (actor.id for actor in state.actors.values() if actor.kind == "trainer" and actor.owner_participant_id == trainer_owner_id),
            "",
        )
        if scene.metadata.get("badge"):
            awards.append(self.command(campaign_id, authority_token, {"type": "progression.award", "payload": {"award_type": "gym_badge", "name": scene.metadata["badge"], "trainer_id": trainer_id}})["event"])
        if scene.metadata.get("rival_id"):
            awards.append(self.command(campaign_id, authority_token, {"type": "progression.award", "payload": {"award_type": "rival_defeated", "rival_id": scene.metadata["rival_id"], "trainer_id": trainer_id}})["event"])
        league_rank = str(scene.metadata.get("league_rank") or "")
        if league_rank:
            award_type = "champion" if league_rank.lower() == "champion" else "league_rank"
            awards.append(self.command(campaign_id, authority_token, {"type": "progression.award", "payload": {"award_type": award_type, "rank": league_rank, "trainer_id": trainer_id}})["event"])

        objective_terms: List[str] = []
        if scene.metadata.get("badge"):
            objective_terms.append(str(scene.metadata["badge"]))
        if scene.id == "scene-league-qualifier":
            objective_terms.append("qualifier")
        elif scene.id == "scene-league-rival":
            objective_terms.append("Cassian")
        elif scene.id == "scene-champion":
            objective_terms.append("Champion Ilyra")
        for quest in sorted(state.quests.values(), key=lambda entry: str(entry.get("id") or "")):
            for objective in quest.get("objectives") or []:
                text = str(objective.get("text") or "")
                if not objective.get("complete") and any(term.lower() in text.lower() for term in objective_terms):
                    awards.append(self.command(campaign_id, authority_token, {"type": "quest.objective", "payload": {"quest_id": quest["id"], "objective_id": objective["id"], "complete": True}})["event"])

        opponent_levels = [
            state.actors[actor_id].level
            for actor_id in scene.metadata.get("opponent_actor_ids") or []
            if actor_id in state.actors
        ]
        next_level = max(opponent_levels or [1]) + 2
        for actor in sorted(state.actors.values(), key=lambda entry: entry.id):
            if actor.kind == "pokemon" and actor.owner_participant_id and actor.level < next_level:
                awards.append(self.command(campaign_id, authority_token, {"type": "actor.level", "payload": {"actor_id": actor.id, "level": next_level, "xp": 0}})["event"])
        event = state.record_event({"type": "battle.complete", "actor_id": requester.id, "actor_name": requester.name, "detail": {"scene_id": scene.id, "winner_team": "players", "awards": len(awards)}})
        self._persist(state, event)
        return {"campaign": self.public_state(state, requester), "event": event, "awards": awards}

    @staticmethod
    def public_state(state: CampaignState, actor: ParticipantState) -> Dict[str, Any]:
        payload = state.to_dict(viewer=actor)
        payload["permissions"] = list(CampaignRules.allowed_commands(actor.role))
        return payload

    def require_campaign(self, campaign_id: str) -> CampaignState:
        state = self.campaigns.get(str(campaign_id or ""))
        if state is None:
            raise KeyError("Campaign not found.")
        return state

    @staticmethod
    def require_participant(state: CampaignState, token: str) -> ParticipantState:
        participant = state.participant_for_token(token)
        if participant is None:
            raise PermissionError("A valid campaign participant token is required.")
        return participant
