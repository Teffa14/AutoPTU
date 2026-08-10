"""Ollama-backed agents that act through AutoPTU's real command boundaries."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .campaign_service import CampaignService


_DICE_RE = re.compile(r"^\d{1,2}d\d{1,4}(?:[+-]\d{1,4})?$")


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


@dataclass
class OllamaClient:
    base_url: str = field(default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    timeout_seconds: float = 120.0

    def _request(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}{path}"
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        if payload is not None:
            request.method = "POST"
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("Ollama returned an invalid response.")
        return decoded

    def models(self) -> List[Dict[str, Any]]:
        payload = self._request("/api/tags")
        return [dict(entry) for entry in payload.get("models") or [] if isinstance(entry, dict)]

    def chat_json(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        schema: Dict[str, Any],
        seed: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        response = self._request(
            "/api/chat",
            {
                "model": model,
                "stream": False,
                "think": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "format": schema,
                "options": {
                    "temperature": 0.15,
                    "seed": int(seed),
                    "num_predict": 240,
                    "top_p": 0.9,
                },
                "keep_alive": "10m",
            },
        )
        content = str((response.get("message") or {}).get("content") or "").strip()
        decision = json.loads(content)
        if not isinstance(decision, dict):
            raise ValueError("Ollama did not return a decision object.")
        usage = {
            "model": str(response.get("model") or model),
            "total_duration": int(response.get("total_duration") or 0),
            "prompt_eval_count": int(response.get("prompt_eval_count") or 0),
            "eval_count": int(response.get("eval_count") or 0),
        }
        return decision, usage


@dataclass
class CampaignAgentRuntime:
    campaign_service: CampaignService
    engine: Any = None
    command_service: Any = None
    ollama: OllamaClient = field(default_factory=OllamaClient)

    def status(self) -> Dict[str, Any]:
        try:
            models = self.ollama.models()
            return {
                "online": True,
                "host": self.ollama.base_url,
                "models": [
                    {
                        "name": str(entry.get("name") or entry.get("model") or ""),
                        "size": int(entry.get("size") or 0),
                        "capabilities": list(entry.get("capabilities") or []),
                    }
                    for entry in models
                ],
                "recommended": {"gm": "qwen2.5:3b", "player": "qwen2.5:3b"},
            }
        except Exception as exc:
            return {
                "online": False,
                "host": self.ollama.base_url,
                "models": [],
                "recommended": {"gm": "qwen2.5:3b", "player": "qwen2.5:3b"},
                "error": str(exc),
            }

    def _authorize_gm(self, campaign_id: str, requester_token: str) -> Any:
        state = self.campaign_service.require_campaign(campaign_id)
        requester = self.campaign_service.require_participant(state, requester_token)
        if requester.role != "gm":
            raise PermissionError("Only a GM seat can direct table agents.")
        return requester

    def _authorize_agent_host(self, campaign_id: str, requester_token: str) -> Any:
        state = self.campaign_service.require_campaign(campaign_id)
        requester = self.campaign_service.require_participant(state, requester_token)
        host_id = str(state.world.get("agent_host_participant_id") or "")
        if requester.role != "gm" and requester.id != host_id:
            raise PermissionError("Only the campaign host can direct table agents.")
        return requester

    @staticmethod
    def _agents(state: Any) -> List[Any]:
        return sorted(
            [entry for entry in state.participants.values() if bool(entry.is_agent) and str(entry.controller) == "ai"],
            key=lambda entry: (entry.role != "gm", entry.id),
        )

    @staticmethod
    def _activity_context(state: Any) -> List[Dict[str, Any]]:
        return [
            {
                "type": str(entry.get("type") or ""),
                "actor": str(entry.get("actor_name") or ""),
                "detail": dict(entry.get("detail") or {}),
            }
            for entry in state.activity[-12:]
        ]

    @staticmethod
    def _campaign_options(state: Any, agent: Any) -> List[Dict[str, Any]]:
        if agent.role == "player":
            options = [
                {"action": "chat.post", "use": "Speak or act in character and move the fiction forward."},
                {"action": "roll.check", "use": "Make a PTU skill check when the outcome is uncertain."},
                {"action": "journal.add", "use": "Record a clue, promise, theory, or character reflection."},
            ]
            location_id = str(state.world.get("current_location_id") or "")
            scene_map = state.exploration_maps.get(location_id)
            scene = state.active_scene()
            if scene_map is not None and scene is not None and scene.published and scene.available:
                owned_tokens = []
                for token in sorted(state.exploration_tokens.values(), key=lambda entry: str(entry.get("actor_id") or "")):
                    actor_id = str(token.get("actor_id") or "")
                    campaign_actor = state.actors.get(actor_id)
                    if campaign_actor is None or campaign_actor.owner_participant_id != agent.id or str(token.get("location_id") or "") != location_id:
                        continue
                    owned_tokens.append((token, campaign_actor))
                    for key, path in state._exploration_paths(actor_id).items():
                        if not state._exploration_route_known(agent, location_id, path):
                            continue
                        x, y = (int(value) for value in key.split(",", 1))
                        options.append(
                            {
                                "action": "exploration.token.move",
                                "option_id": f"move:{actor_id}:{x},{y}",
                                "actor_id": actor_id,
                                "actor_name": campaign_actor.name,
                                "x": x,
                                "y": y,
                                "steps": len(path),
                                "use": f"Move {campaign_actor.name} along a legal {len(path)}-step path while exploring.",
                            }
                        )
                for point in sorted(scene_map.get("points") or [], key=lambda entry: str(entry.get("id") or "")):
                    if not isinstance(point, dict) or not bool(point.get("revealed")) or not bool(point.get("available", True)):
                        continue
                    completed_by = {str(value) for value in point.get("completed_by") or [] if str(value)}
                    if bool(point.get("once")) and completed_by:
                        continue
                    interaction_range = max(0, min(3, int(point.get("interaction_range") if point.get("interaction_range") is not None else 1)))
                    nearby = []
                    for token, campaign_actor in owned_tokens:
                        distance = max(
                            abs(int(token.get("x") or 0) - int(point.get("x") or 0)),
                            abs(int(token.get("y") or 0) - int(point.get("y") or 0)),
                        )
                        if distance <= interaction_range:
                            nearby.append((distance, campaign_actor.id, campaign_actor))
                    if nearby:
                        _distance, actor_id, campaign_actor = min(nearby, key=lambda value: (value[0], value[1]))
                        options.append(
                            {
                                "action": "exploration.point.interact",
                                "option_id": f"interact:{point.get('id')}:{actor_id}",
                                "point_id": str(point.get("id") or ""),
                                "point_name": str(point.get("label") or "Point of interest"),
                                "actor_id": actor_id,
                                "actor_name": campaign_actor.name,
                                "use": f"{point.get('interaction') or 'Investigate'} at {point.get('label') or 'this point'} using {campaign_actor.name}.",
                            }
                        )
            return options
        options: List[Dict[str, Any]] = [
            {"action": "chat.post", "use": "Frame a vivid consequence, reveal, NPC response, or new choice."}
        ]
        # Open every chapter with authored fiction. After the local GM has
        # narrated in this scene, later turns can manipulate campaign systems.
        last_activation = max(
            (index for index, entry in enumerate(state.activity) if entry.get("type") == "scene.activate"),
            default=-1,
        )
        narrated_here = any(
            entry.get("actor_id") == agent.id and entry.get("type") == "chat.post"
            for entry in state.activity[last_activation + 1 :]
        )
        if not narrated_here:
            return options
        # Chapter transitions remain an explicit table decision.  The GM agent
        # directs the active scene, while the game shell's Continue control owns
        # ordered progression so a model cannot jump over unfinished chapters.
        for participant in sorted(state.participants.values(), key=lambda entry: entry.id):
            if participant.role == "player":
                options.append({"action": "spotlight.set", "participant_id": participant.id, "name": participant.name})
        for clock_id in sorted(state.clocks):
            clock = state.clocks[clock_id]
            if int(clock.get("filled") or 0) < int(clock.get("segments") or 0):
                options.append({"action": "clock.tick", "clock_id": clock_id, "name": clock.get("name"), "delta": 1})
        for quest_id in sorted(state.quests):
            quest = state.quests[quest_id]
            for objective in quest.get("objectives") or []:
                if not objective.get("complete"):
                    options.append(
                        {
                            "action": "quest.objective",
                            "quest_id": quest_id,
                            "objective_id": objective.get("id"),
                            "objective": objective.get("text"),
                        }
                    )
        scene = state.active_scene()
        if scene is not None and scene.kind == "combat" and not scene.battle_id:
            options.append({"action": "battle.link", "battle_id": "current", "scene_id": scene.id})
        return options

    @staticmethod
    def _decision_schema(options: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        actions = sorted({str(option.get("action") or "chat.post") for option in options})
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": actions},
                "intent": {"type": "string"},
                "text": {"type": "string"},
                "label": {"type": "string"},
                "expression": {"type": "string"},
                "scene_id": {"type": "string"},
                "participant_id": {"type": "string"},
                "clock_id": {"type": "string"},
                "quest_id": {"type": "string"},
                "objective_id": {"type": "string"},
                "battle_id": {"type": "string"},
                "option_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "point_id": {"type": "string"},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["action", "intent"],
        }

    def _fallback_campaign_decision(self, state: Any, agent: Any, options: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        if agent.role == "player":
            if state.revision % 3 == 0:
                return {
                    "action": "roll.check",
                    "intent": "Test the most important uncertainty in the scene.",
                    "label": "Perception",
                    "expression": "2d6+1",
                }
            return {
                "action": "chat.post",
                "intent": "Respond to the active danger and invite another character into the moment.",
                "text": f"{agent.name} steps into the scene, checks on {agent.companion or 'their partner'}, and acts on the strongest clue in front of the group.",
            }
        preferred = next((option for option in options if option.get("action") == "chat.post"), options[0])
        return {
            **preferred,
            "intent": "Keep the scene moving and give the party a clear consequential choice.",
            "text": "The situation changes visibly, demanding a choice from the Trainers before the danger can grow.",
        }

    @staticmethod
    def _matching_option(decision: Dict[str, Any], options: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        action = str(decision.get("action") or "")
        candidates = [option for option in options if option.get("action") == action]
        selectors = {
            key: str(decision.get(key))
            for key in ("option_id", "scene_id", "participant_id", "clock_id", "objective_id", "battle_id", "actor_id", "point_id", "x", "y")
            if decision.get(key) is not None and str(decision.get(key)) != ""
        }
        if selectors:
            exact = next(
                (
                    option
                    for option in candidates
                    if all(str(option.get(key)) == requested for key, requested in selectors.items())
                ),
                None,
            )
            if exact is not None:
                return exact
        return candidates[0] if candidates else None

    def _campaign_command(
        self,
        state: Any,
        agent: Any,
        decision: Dict[str, Any],
        options: Sequence[Dict[str, Any]],
    ) -> Tuple[str, Dict[str, Any]]:
        selected = self._matching_option(decision, options)
        if selected is None:
            decision = self._fallback_campaign_decision(state, agent, options)
            selected = self._matching_option(decision, options) or dict(options[0])
        action = str(selected.get("action") or decision.get("action") or "chat.post")
        if action == "chat.post":
            text = str(decision.get("text") or "").strip()
            if not text:
                text = str(self._fallback_campaign_decision(state, agent, options).get("text") or "The scene moves forward.")
            return action, {"kind": "narration" if agent.role == "gm" else "in_character", "text": text[:1200]}
        if action == "roll.check":
            expression = str(decision.get("expression") or "2d6+1").replace(" ", "")
            if not _DICE_RE.match(expression):
                expression = "2d6+1"
            return action, {"label": str(decision.get("label") or "Skill Check")[:80], "expression": expression}
        if action == "journal.add":
            text = str(decision.get("text") or decision.get("intent") or "A clue worth remembering.").strip()
            return action, {"title": "Field Note", "text": text[:1200], "visibility": "table"}
        if action == "exploration.token.move":
            return action, {
                "actor_id": selected["actor_id"],
                "x": int(selected["x"]),
                "y": int(selected["y"]),
            }
        if action == "exploration.point.interact":
            return action, {
                "point_id": selected["point_id"],
                "actor_id": selected["actor_id"],
            }
        if action == "scene.activate":
            return action, {"scene_id": selected["scene_id"]}
        if action == "spotlight.set":
            return action, {"participant_id": selected["participant_id"]}
        if action == "clock.tick":
            return action, {"clock_id": selected["clock_id"], "delta": 1}
        if action == "quest.objective":
            return action, {
                "quest_id": selected["quest_id"],
                "objective_id": selected["objective_id"],
                "complete": True,
            }
        if action == "battle.link":
            return action, {"battle_id": "current"}
        return "chat.post", {"kind": "narration", "text": "The world answers with a new complication."}

    def step(
        self,
        campaign_id: str,
        requester_token: str,
        *,
        agent_id: str,
        model_override: str = "",
    ) -> Dict[str, Any]:
        requester = self._authorize_agent_host(campaign_id, requester_token)
        state = self.campaign_service.require_campaign(campaign_id)
        agent = state.participants.get(str(agent_id or ""))
        if agent is None or not agent.is_agent:
            raise ValueError("Unknown campaign agent.")
        if agent.controller != "ai":
            raise ValueError("That seat is currently human-controlled.")
        options = self._campaign_options(state, agent)
        if not options:
            raise ValueError("The agent has no legal campaign action.")
        scene = state.active_scene()
        system = (
            "You are playing Pokemon Tabletop United inside AutoPTU. "
            "You must choose exactly one option supplied by the engine. Never invent ids or rules fields. "
            "Write concise, specific fiction that responds to the latest table event. "
            f"Your seat is {agent.name}. Role: {agent.role}. Persona: {agent.agent_persona}"
        )
        prompt = json.dumps(
            {
                "campaign": state.name,
                "time": state.time_label,
                "active_scene": {
                    "id": scene.id if scene else None,
                    "title": scene.title if scene else None,
                    "kind": scene.kind if scene else None,
                    "location": scene.location if scene else None,
                    "summary": scene.summary if scene else None,
                },
                "latest_events": self._activity_context(state),
                "legal_options": options,
                "instruction": "Choose one legal option. Explain intent briefly. Supply vivid text for chat.post or journal.add. Use a valid NdM+K expression for roll.check.",
            },
            ensure_ascii=False,
        )
        model = str(model_override or agent.agent_model or ("gpt-oss:20b" if agent.role == "gm" else "qwen2.5:3b"))
        source = "ollama"
        error = ""
        usage: Dict[str, Any] = {"model": model}
        try:
            decision, usage = self.ollama.chat_json(
                model=model,
                system=system,
                prompt=prompt,
                schema=self._decision_schema(options),
                seed=_stable_seed(state.seed, state.revision + 1, agent.id),
            )
        except Exception as exc:
            source = "deterministic-fallback"
            error = str(exc)
            decision = self._fallback_campaign_decision(state, agent, options)
        action, payload = self._campaign_command(state, agent, decision, options)
        result = self.campaign_service.command(
            campaign_id,
            agent.token,
            {"type": action, "payload": payload},
        )
        return {
            "agent": agent.public_dict(),
            "source": source,
            "decision": {**decision, "action": action},
            "usage": usage,
            "error": error or None,
            "event": result["event"],
            "campaign": self.campaign_service.public_state(state, requester),
        }

    def npc_reply(
        self,
        campaign_id: str,
        requester_token: str,
        *,
        dialogue_id: str,
        model_override: str = "",
    ) -> Dict[str, Any]:
        """Portray one persistent NPC using only that character's recorded truth."""
        state = self.campaign_service.require_campaign(campaign_id)
        requester = self.campaign_service.require_participant(state, requester_token)
        record = next((entry for entry in state.dialogue if entry.get("id") == dialogue_id), None)
        if record is None:
            raise ValueError("Unknown dialogue exchange.")
        if requester.role != "gm" and str(record.get("participant_id") or "") != requester.id:
            raise PermissionError("That conversation belongs to another participant.")
        npc = state.actors.get(str(record.get("npc_id") or ""))
        if npc is None or npc.controller != "ai":
            raise ValueError("That NPC is not AI-controlled.")
        gm_agent = next(
            (entry for entry in state.participants.values() if entry.role == "gm" and entry.is_agent),
            None,
        )
        command_token = requester.token if requester.role == "gm" else (gm_agent.token if gm_agent else "")
        if not command_token:
            raise PermissionError("An AI GM seat is required to portray this NPC.")
        schema = {
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "relationship_delta": {"type": "integer", "minimum": -2, "maximum": 2},
                "known_fact_used": {"type": "string"},
            },
            "required": ["response", "relationship_delta", "known_fact_used"],
        }
        system = (
            f"You are {npc.name}, a persistent Pokemon Tabletop United character. "
            f"Persona: {npc.persona} Voice: {npc.voice} Goals: {', '.join(npc.goals) or 'unspecified'}. "
            f"You know only these campaign facts: {', '.join(npc.knowledge) or 'none recorded'}. "
            "Stay in character. Never invent secret knowledge, completed events, relationships, or rules outcomes. "
            "When asked beyond your knowledge, say that you do not know or state what you reasonably suspect as uncertainty. "
            "Answer in 1-4 vivid sentences and make the relationship change follow the actual tone of the exchange."
        )
        prompt = json.dumps(
            {
                "campaign": state.name,
                "time": state.time_label,
                "location_id": state.world.get("current_location_id"),
                "speaker": record.get("participant_name"),
                "question_or_action": record.get("text"),
                "relationship": npc.relationships.get(str(record.get("participant_id") or ""), 0),
                "recent_dialogue": state.dialogue[-6:],
            },
            ensure_ascii=False,
        )
        model = str(model_override or (gm_agent.agent_model if gm_agent else "") or "qwen2.5:3b")
        source = "ollama"
        error = ""
        usage: Dict[str, Any] = {"model": model}
        try:
            decision, usage = self.ollama.chat_json(
                model=model,
                system=system,
                prompt=prompt,
                schema=schema,
                seed=_stable_seed(state.seed, state.revision + 1, npc.id, dialogue_id),
            )
        except Exception as exc:
            source = "deterministic-fallback"
            error = str(exc)
            known = npc.knowledge[0] if npc.knowledge else "what I have seen here"
            decision = {
                "response": f"{npc.name} considers the question. \"I can speak truthfully about {known}, but I won't pretend certainty beyond that.\"",
                "relationship_delta": 0,
                "known_fact_used": known,
            }
        response = str(decision.get("response") or "").strip()
        if not response:
            raise ValueError("The NPC produced no response.")
        result = self.campaign_service.command(
            campaign_id,
            command_token,
            {
                "type": "npc.reply",
                "payload": {
                    "dialogue_id": dialogue_id,
                    "response": response,
                    "relationship_delta": int(decision.get("relationship_delta") or 0),
                },
            },
        )
        return {
            "npc": npc.public_dict(),
            "source": source,
            "usage": usage,
            "error": error or None,
            "decision": decision,
            "event": result["event"],
            "campaign": self.campaign_service.public_state(state, requester),
        }

    def round(
        self,
        campaign_id: str,
        requester_token: str,
        *,
        gm_model: str = "",
        player_model: str = "",
        include_gm: bool = True,
    ) -> Dict[str, Any]:
        requester = self._authorize_agent_host(campaign_id, requester_token)
        state = self.campaign_service.require_campaign(campaign_id)
        agents = self._agents(state)
        if not include_gm:
            agents = [entry for entry in agents if entry.role == "player"]
        turns = []
        for agent in agents:
            turns.append(
                self.step(
                    campaign_id,
                    requester_token,
                    agent_id=agent.id,
                    model_override=gm_model if agent.role == "gm" else player_model,
                )
            )
        return {
            "turns": [
                {
                    "agent": entry["agent"],
                    "source": entry["source"],
                    "decision": entry["decision"],
                    "usage": entry["usage"],
                    "error": entry["error"],
                    "event": entry["event"],
                }
                for entry in turns
            ],
            "campaign": self.campaign_service.public_state(state, requester),
        }

    def advance(
        self,
        campaign_id: str,
        requester_token: str,
        *,
        model_override: str = "",
    ) -> Dict[str, Any]:
        """Let the hosted AI GM open exactly the next completed chapter."""
        requester = self._authorize_agent_host(campaign_id, requester_token)
        state = self.campaign_service.require_campaign(campaign_id)
        ordered = sorted(state.scenes.values(), key=lambda entry: (entry.order or 10_000, entry.id))
        current_index = next((index for index, entry in enumerate(ordered) if entry.id == state.active_scene_id), -1)
        if current_index < 0 or current_index + 1 >= len(ordered):
            raise ValueError("There is no next chapter to open.")
        gm_agent = state.participants.get(state.gm_id)
        if gm_agent is None or gm_agent.role != "gm" or not gm_agent.is_agent or gm_agent.controller != "ai":
            raise PermissionError("This campaign does not have an authoritative AI GM.")
        target = ordered[current_index + 1]
        activation = self.campaign_service.command(
            campaign_id,
            gm_agent.token,
            {"type": "scene.activate", "payload": {"scene_id": target.id}},
        )
        narration = self.step(
            campaign_id,
            requester_token,
            agent_id=gm_agent.id,
            model_override=model_override,
        )
        return {
            "scene": {"id": target.id, "title": target.title, "order": target.order, "kind": target.kind, "location": target.location},
            "event": activation["event"],
            "narration": {
                "source": narration["source"],
                "decision": narration["decision"],
                "usage": narration["usage"],
                "error": narration["error"],
                "event": narration["event"],
            },
            "campaign": self.campaign_service.public_state(state, requester),
        }

    @staticmethod
    def _battle_schema(move_names: Sequence[str]) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["move", "shift", "end_turn"]},
                "intent": {"type": "string"},
                "move": {"type": "string", "enum": list(move_names) or ["none"]},
                "target_id": {"type": "string"},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["action", "intent"],
        }

    def battle_step(
        self,
        campaign_id: str,
        requester_token: str,
        *,
        model_override: str = "",
    ) -> Dict[str, Any]:
        self._authorize_agent_host(campaign_id, requester_token)
        if self.engine is None:
            raise ValueError("Battle agent runtime is unavailable.")
        snapshot = self.engine.snapshot()
        if snapshot.get("status") != "ok":
            raise ValueError("Start a battle before asking an agent to act.")
        state = self.campaign_service.require_campaign(campaign_id)
        actor_id = str(snapshot.get("current_actor_id") or "")
        agents = self._agents(state)
        players = [entry for entry in agents if entry.role == "player"]
        owning_seat = next(
            (entry for entry in state.participants.values() if actor_id == entry.id or actor_id.startswith(f"{entry.id}-")),
            None,
        )
        if owning_seat is not None and owning_seat.controller != "ai":
            raise ValueError("The active combatant is human-controlled.")
        agent = next((entry for entry in players if actor_id == entry.id or actor_id.startswith(f"{entry.id}-")), None)
        if agent is None:
            agent = next((entry for entry in agents if entry.role == "gm"), None)
        if agent is None:
            raise ValueError("The active combatant has no AI campaign controller.")
        if snapshot.get("trainer_turn"):
            battle = self.engine.commit_action({"type": "end_turn", "actor_id": actor_id})
            if self.command_service is not None:
                battle = self.command_service.after_resolution(battle)
            return {
                "agent": agent.public_dict(),
                "source": "engine",
                "decision": {"action": "end_turn", "intent": "Finish the Trainer declaration and pass spotlight to the Pokemon."},
                "battle": battle,
            }
        actor = next((entry for entry in snapshot.get("combatants") or [] if str(entry.get("id")) == actor_id), None)
        if actor is None:
            raise ValueError("The current battle actor is unavailable.")
        move_targets = snapshot.get("move_targets") or {}
        legal_move_records = [
            move
            for move in actor.get("moves") or []
            if move_targets.get(str(move.get("name") or "")) or []
        ]
        move_names = [
            str(move.get("name") or "")
            for move in sorted(
                legal_move_records,
                key=lambda move: (-int(move.get("damage_base") or 0), str(move.get("name") or "")),
            )
        ]
        actor_team = str(actor.get("team") or "")
        enemy_positions = [
            list(entry.get("position") or [])
            for entry in snapshot.get("combatants") or []
            if str(entry.get("team") or "") != actor_team
            and int(entry.get("hp") or 0) > 0
            and len(list(entry.get("position") or [])) >= 2
        ]

        def shift_priority(coord: List[int]) -> tuple[int, int, int]:
            distance = min(
                (abs(int(coord[0]) - int(target[0])) + abs(int(coord[1]) - int(target[1])) for target in enemy_positions),
                default=0,
            )
            return (distance, int(coord[1]), int(coord[0]))

        shifts = sorted(
            [list(coord) for coord in snapshot.get("legal_shifts") or [] if list(coord) != list(snapshot.get("current_pos") or [])],
            key=shift_priority,
        )
        model = str(model_override or agent.agent_model or "qwen2.5:3b")
        source = "ollama"
        error = ""
        usage: Dict[str, Any] = {"model": model}
        prompt = json.dumps(
            {
                "actor": {"id": actor_id, "name": actor.get("name"), "hp": actor.get("hp"), "max_hp": actor.get("max_hp")},
                "legal_moves": {name: list(move_targets.get(name) or []) for name in move_names},
                "legal_shifts": shifts[:24],
                "battle_round": snapshot.get("round"),
                "instruction": "Choose one legal action. Prefer a useful move with an exact listed target. Shift only for positioning; end only when no useful action remains.",
            },
            ensure_ascii=False,
        )
        try:
            decision, usage = self.ollama.chat_json(
                model=model,
                system=f"You are {agent.name}, {agent.agent_persona} You are controlling the active Pokemon in a PTU battle. Use only supplied legal actions.",
                prompt=prompt,
                schema=self._battle_schema(move_names),
                seed=_stable_seed(state.seed, snapshot.get("round"), actor_id, len(snapshot.get("log") or [])),
            )
        except Exception as exc:
            source = "deterministic-fallback"
            error = str(exc)
            decision = {"action": "move" if move_names else "shift" if shifts else "end_turn", "intent": "Use the first deterministic legal battle option."}
        action = str(decision.get("action") or "")
        if move_names and action != "move":
            # A legal attack is actionable now; do not let a generative model
            # burn the turn on indecisive shifts. Positioning remains available
            # whenever the engine exposes no targetable move.
            action = "move"
            decision = {
                **decision,
                "action": "move",
                "move": move_names[0],
                "target_id": list(move_targets.get(move_names[0]) or [None])[0],
                "intent": str(decision.get("intent") or "") or "Commit to the strongest legal attack.",
            }
            source = f"{source}-tactical-policy"
        if action == "move" and move_names:
            move_name = str(decision.get("move") or "")
            if move_name not in move_names:
                move_name = move_names[0]
            targets = list(move_targets.get(move_name) or [])
            target_id = decision.get("target_id")
            if target_id not in targets:
                target_id = targets[0]
            payload = {"type": "move", "actor_id": actor_id, "move": move_name, "target_id": target_id}
        elif action == "shift" and shifts:
            requested = [decision.get("x"), decision.get("y")]
            coord = requested if requested in shifts else shifts[0]
            payload = {"type": "shift", "actor_id": actor_id, "x": int(coord[0]), "y": int(coord[1])}
            decision["x"], decision["y"] = coord
        else:
            action = "end_turn"
            payload = {"type": "end_turn", "actor_id": actor_id}
        try:
            battle = self.engine.commit_action(payload)
        except ValueError as exc:
            # The authoritative engine remains the final legality boundary.
            # If a future content-specific rule is narrower than the public
            # legal snapshot, keep the AI turn playable with a deterministic
            # legal alternative instead of returning a repeatable HTTP 400.
            original_error = str(exc)
            fallback_payloads = []
            for fallback_move in move_names:
                for fallback_target in list(move_targets.get(fallback_move) or []):
                    candidate = {
                        "type": "move",
                        "actor_id": actor_id,
                        "move": fallback_move,
                        "target_id": fallback_target,
                    }
                    if candidate != payload:
                        fallback_payloads.append(candidate)
            fallback_payloads.extend(
                {"type": "shift", "actor_id": actor_id, "x": int(coord[0]), "y": int(coord[1])}
                for coord in shifts
            )
            fallback_payloads.append({"type": "end_turn", "actor_id": actor_id})
            last_error: Exception = exc
            for candidate in fallback_payloads:
                try:
                    battle = self.engine.commit_action(candidate)
                    payload = candidate
                    action = str(candidate["type"])
                    decision = {"action": action, "intent": "Use the first engine-accepted legal fallback after a content-specific rejection."}
                    if candidate.get("move"):
                        decision["move"] = candidate["move"]
                        decision["target_id"] = candidate.get("target_id")
                    if action == "shift":
                        decision["x"], decision["y"] = candidate["x"], candidate["y"]
                    source = f"{source}-guarded-fallback"
                    error = "; ".join(value for value in [error, original_error] if value)
                    break
                except ValueError as fallback_error:
                    last_error = fallback_error
            else:
                raise last_error
        if self.command_service is not None:
            battle = self.command_service.after_resolution(battle)
        return {
            "agent": agent.public_dict(),
            "source": source,
            "decision": {**decision, "action": action},
            "usage": usage,
            "error": error or None,
            "battle": battle,
        }
