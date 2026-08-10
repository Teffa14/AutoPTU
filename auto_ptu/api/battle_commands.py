"""Player-facing command planning and GM reaction windows.

This layer never resolves PTU math itself.  It stages payloads already understood
by :class:`EngineFacade`, dry-runs them through a cloned battle, and hands legal
commands back to the authoritative action resolver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .engine_facade import EngineFacade


@dataclass
class PlannedCommand:
    id: str
    payload: Dict[str, Any]
    actor_id: str
    label: str
    action_type: str
    status: str = "ready"
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "payload": dict(self.payload),
            "actor_id": self.actor_id,
            "label": self.label,
            "action_type": self.action_type,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class ReactionRegistration:
    id: str
    name: str
    source_kind: str
    actor_ids: List[str]
    trigger_types: List[str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    once_per_round: bool = True
    last_triggered_round: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_kind": self.source_kind,
            "actor_ids": list(self.actor_ids),
            "trigger_types": list(self.trigger_types),
            "conditions": dict(self.conditions),
            "once_per_round": self.once_per_round,
            "last_triggered_round": self.last_triggered_round,
        }


@dataclass
class BattleCommandService:
    facade: EngineFacade
    queue: List[PlannedCommand] = field(default_factory=list)
    paused: bool = False
    interrupt_window: Optional[Dict[str, Any]] = None
    _battle_identity: Optional[int] = None
    _counter: int = 0
    reactions: List[ReactionRegistration] = field(default_factory=list)
    _reaction_counter: int = 0
    _log_cursor: int = 0

    def _sync_battle(self) -> None:
        identity = id(self.facade.battle) if self.facade.battle is not None else None
        if identity == self._battle_identity:
            return
        self._battle_identity = identity
        self.queue = []
        self.interrupt_window = None
        self.paused = False
        self._counter = 0
        self.reactions = self._discover_reactions()
        self._reaction_counter = len(self.reactions)
        self._log_cursor = len(getattr(self.facade.battle, "log", []) or []) if self.facade.battle is not None else 0

    def _discover_reactions(self) -> List[ReactionRegistration]:
        battle = self.facade.battle
        if battle is None:
            return []
        discovered: List[ReactionRegistration] = []
        sources: List[tuple[str, str, Any]] = []
        for actor_id, pokemon in sorted(battle.pokemon.items()):
            for kind, entries in (("ability", pokemon.spec.abilities), ("item", pokemon.spec.items), ("feature", pokemon.spec.trainer_features)):
                for entry in entries or []:
                    if isinstance(entry, dict):
                        sources.append((actor_id, kind, entry))
        for trainer_id, trainer in sorted(battle.trainers.items()):
            for entry in trainer.features or []:
                if isinstance(entry, dict):
                    sources.append((trainer_id, "feature", entry))
        for index, (actor_id, kind, entry) in enumerate(sources, start=1):
            raw_triggers = entry.get("reaction_trigger") or entry.get("trigger_types") or []
            if isinstance(raw_triggers, str):
                raw_triggers = [raw_triggers]
            trigger_types = sorted({str(value).strip().lower() for value in raw_triggers if str(value).strip()})
            if not trigger_types:
                continue
            discovered.append(
                ReactionRegistration(
                    id=f"reaction-auto-{index}",
                    name=str(entry.get("name") or f"{kind.title()} reaction"),
                    source_kind=kind,
                    actor_ids=[actor_id],
                    trigger_types=trigger_types,
                    conditions=dict(entry.get("reaction_conditions") or {}),
                    once_per_round=bool(entry.get("once_per_round", True)),
                )
            )
        return discovered

    @staticmethod
    def _require_role(role: str, *, gm: bool = False) -> str:
        normalized = str(role or "player").strip().lower()
        if normalized not in {"gm", "player", "spectator"}:
            raise ValueError("Battle role must be gm, player, or spectator.")
        if normalized == "spectator":
            raise PermissionError("Spectators cannot change battle state.")
        if gm and normalized != "gm":
            raise PermissionError("Only the GM can use that battle control.")
        return normalized

    def state(self) -> Dict[str, Any]:
        self._sync_battle()
        return {
            "paused": self.paused,
            "queue": [entry.to_dict() for entry in self.queue],
            "interrupt_window": dict(self.interrupt_window) if self.interrupt_window else None,
            "reaction_registry": [entry.to_dict() for entry in self.reactions],
            "can_resolve": bool(self.queue and not self.paused and not self.interrupt_window),
        }

    def decorate(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(snapshot)
        payload["command_center"] = self.state()
        return payload

    def register_reaction(self, payload: Dict[str, Any], *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        battle = self.facade.battle
        if battle is None:
            raise ValueError("No active battle.")
        actor_ids = sorted({str(value) for value in payload.get("actor_ids") or [] if str(value)})
        if not actor_ids:
            raise ValueError("At least one reaction actor is required.")
        known_ids = set(battle.pokemon) | set(battle.trainers)
        unknown = [actor_id for actor_id in actor_ids if actor_id not in known_ids]
        if unknown:
            raise ValueError(f"Unknown reaction actor: {unknown[0]}")
        raw_triggers = payload.get("trigger_types") or payload.get("trigger_type") or []
        if isinstance(raw_triggers, str):
            raw_triggers = [raw_triggers]
        trigger_types = sorted({str(value).strip().lower() for value in raw_triggers if str(value).strip()})
        if not trigger_types:
            raise ValueError("At least one battle event trigger type is required.")
        source_kind = str(payload.get("source_kind") or "custom").strip().lower()
        if source_kind not in {"ability", "feature", "item", "move", "custom"}:
            raise ValueError("Reaction source must be an ability, feature, item, move, or custom rule.")
        self._reaction_counter += 1
        registration = ReactionRegistration(
            id=str(payload.get("id") or f"reaction-{self._reaction_counter}"),
            name=str(payload.get("name") or "Registered reaction").strip(),
            source_kind=source_kind,
            actor_ids=actor_ids,
            trigger_types=trigger_types,
            conditions=dict(payload.get("conditions") or {}),
            once_per_round=bool(payload.get("once_per_round", True)),
        )
        if any(entry.id == registration.id for entry in self.reactions):
            raise ValueError("That reaction id is already registered.")
        self.reactions.append(registration)
        self.reactions.sort(key=lambda entry: entry.id)
        return self.state()

    def remove_reaction(self, reaction_id: str, *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        before = len(self.reactions)
        self.reactions = [entry for entry in self.reactions if entry.id != reaction_id]
        if len(self.reactions) == before:
            raise KeyError("Registered reaction not found.")
        return self.state()

    @staticmethod
    def _event_matches(registration: ReactionRegistration, event: Dict[str, Any]) -> bool:
        if str(event.get("type") or "").strip().lower() not in registration.trigger_types:
            return False
        return all(event.get(key) == value for key, value in registration.conditions.items())

    def after_resolution(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Scan newly emitted battle events and open the first deterministic reaction window."""
        self._sync_battle()
        battle = self.facade.battle
        if battle is None:
            return self.decorate(snapshot)
        log = list(battle.log or [])
        new_events = log[self._log_cursor :]
        self._log_cursor = len(log)
        if not self.interrupt_window:
            for event in new_events:
                round_number = int(event.get("round") or battle.round or 0)
                for registration in sorted(self.reactions, key=lambda entry: entry.id):
                    if registration.once_per_round and registration.last_triggered_round == round_number:
                        continue
                    if not self._event_matches(registration, event):
                        continue
                    eligible = [
                        actor_id
                        for actor_id in registration.actor_ids
                        if actor_id in battle.pokemon and battle._out_of_turn_move_options(actor_id)
                    ]
                    if not eligible:
                        continue
                    self.open_interrupt(
                        {
                            "trigger": f"{registration.name}: {event.get('type')}",
                            "source_actor_id": event.get("actor"),
                            "actor_ids": eligible,
                        },
                        role="gm",
                    )
                    if self.interrupt_window is not None:
                        self.interrupt_window["automatic"] = True
                        self.interrupt_window["reaction_id"] = registration.id
                        self.interrupt_window["trigger_event"] = dict(event)
                    registration.last_triggered_round = round_number
                    return self.decorate(snapshot)
        return self.decorate(snapshot)

    def stage(self, payload: Dict[str, Any], *, role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        battle = self.facade.battle
        if battle is None:
            raise ValueError("No active battle.")
        command_payload = dict(payload or {})
        action_type = str(command_payload.get("type") or "").strip().lower()
        if not action_type:
            raise ValueError("Action type is required.")
        if any(entry.payload.get("type") in {"end_turn", "delay"} for entry in self.queue):
            raise ValueError("No action can be queued after Delay or End Turn.")
        actor_id = str(command_payload.get("actor_id") or battle.current_actor_id or "")
        command_payload["actor_id"] = actor_id
        self._counter += 1
        command = PlannedCommand(
            id=f"command-{self._counter}",
            payload=command_payload,
            actor_id=actor_id,
            label=action_type.replace("_", " ").title(),
            action_type="free" if action_type in {"end_turn", "delay"} else "unknown",
        )
        candidate = [*self.queue, command]
        metadata = self._validate_sequence(candidate)
        for entry, detail in zip(candidate, metadata):
            entry.label = str(detail.get("label") or entry.label)
            entry.action_type = str(detail.get("action_type") or entry.action_type)
            entry.status = "ready"
            entry.error = ""
        self.queue = candidate
        return self.state()

    def remove(self, command_id: str, *, role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        before = len(self.queue)
        self.queue = [entry for entry in self.queue if entry.id != command_id]
        if len(self.queue) == before:
            raise KeyError("Queued command not found.")
        if self.queue:
            self._validate_sequence(self.queue)
        return self.state()

    def reorder(self, command_id: str, index: int, *, role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        current = next((entry for entry in self.queue if entry.id == command_id), None)
        if current is None:
            raise KeyError("Queued command not found.")
        reordered = [entry for entry in self.queue if entry.id != command_id]
        reordered.insert(max(0, min(int(index), len(reordered))), current)
        self._validate_sequence(reordered)
        self.queue = reordered
        return self.state()

    def clear(self, *, role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        self.queue = []
        return self.state()

    def pause(self, paused: bool, *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        self.paused = bool(paused)
        return self.state()

    def resolve(self, *, mode: str = "next", role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        if self.paused:
            raise ValueError("The GM has paused battle resolution.")
        if self.interrupt_window:
            raise ValueError("Resolve or close the interrupt window first.")
        if not self.queue:
            return self.decorate(self.facade.snapshot())
        resolve_all = str(mode or "next").strip().lower() == "all"
        resolved: List[str] = []
        while self.queue:
            command = self.queue[0]
            try:
                snapshot = self.facade.commit_action(dict(command.payload))
            except Exception as exc:
                command.status = "rejected"
                command.error = str(exc)
                raise
            self.queue.pop(0)
            resolved.append(command.id)
            self.after_resolution(snapshot)
            if snapshot.get("pending_prompts") or self.interrupt_window or not resolve_all:
                break
        result = self.after_resolution(self.facade.snapshot())
        result["resolved_commands"] = resolved
        return result

    def _validate_sequence(self, commands: List[PlannedCommand]) -> List[Dict[str, str]]:
        battle = self.facade.battle
        if battle is None:
            raise ValueError("No active battle.")
        clone = self.facade._clone_battle_for_history(battle)
        clone.out_of_turn_prompt = lambda _payload: True
        metadata: List[Dict[str, str]] = []
        terminal = False
        for entry in commands:
            if terminal:
                raise ValueError("No action can be queued after Delay or End Turn.")
            kind = str(entry.payload.get("type") or "").strip().lower()
            if kind == "end_turn":
                metadata.append({"label": "End Turn", "action_type": "free"})
                terminal = True
                continue
            action = self.facade._build_action(clone, dict(entry.payload))
            clone.queue_action(action)
            resolved = clone.resolve_next_action()
            if resolved is None:
                raise ValueError("Queued action did not resolve during validation.")
            metadata.append(
                {
                    "label": resolved.describe_action(),
                    "action_type": getattr(getattr(resolved, "action_type", None), "value", str(getattr(resolved, "action_type", "unknown"))),
                }
            )
            if kind == "delay":
                terminal = True
        return metadata

    def open_interrupt(self, payload: Dict[str, Any], *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        battle = self.facade.battle
        if battle is None:
            raise ValueError("No active battle.")
        if self.interrupt_window:
            raise ValueError("An interrupt window is already open.")
        allowed = [str(value) for value in payload.get("actor_ids") or []]
        if not allowed:
            allowed = sorted(
                actor_id
                for actor_id, actor in battle.pokemon.items()
                if actor.active and not actor.fainted and battle.is_player_controlled(actor_id)
            )
        options: Dict[str, List[Dict[str, Any]]] = {}
        for actor_id in allowed:
            if actor_id not in battle.pokemon:
                raise ValueError(f"Unknown interrupt actor: {actor_id}")
            options[actor_id] = list(battle._out_of_turn_move_options(actor_id))
        self._counter += 1
        self.interrupt_window = {
            "id": f"interrupt-{self._counter}",
            "trigger": str(payload.get("trigger") or "GM reaction window").strip(),
            "source_actor_id": payload.get("source_actor_id"),
            "allowed_actor_ids": allowed,
            "pending_actor_ids": list(allowed),
            "options": options,
            "responses": [],
            "status": "collecting",
        }
        return self.state()

    def respond_interrupt(self, payload: Dict[str, Any], *, role: str = "player") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role)
        window = self.interrupt_window
        if not window:
            raise ValueError("No interrupt window is open.")
        actor_id = str(payload.get("actor_id") or "")
        if actor_id not in window["pending_actor_ids"]:
            raise PermissionError("That actor cannot respond to this interrupt window.")
        passed = bool(payload.get("pass"))
        response: Dict[str, Any] = {"id": f"response-{len(window['responses']) + 1}", "actor_id": actor_id, "passed": passed, "status": "passed" if passed else "stacked"}
        if not passed:
            move_name = str(payload.get("move") or payload.get("move_name") or "")
            target_id = str(payload.get("target_id") or "") or None
            option = next(
                (
                    entry
                    for entry in window["options"].get(actor_id, [])
                    if str(entry.get("move") or "") == move_name and (str(entry.get("target_id") or "") or None) == target_id
                ),
                None,
            )
            if option is None:
                raise ValueError("That reaction move and target are not legal in this window.")
            response.update({"move": move_name, "target_id": target_id, "label": option.get("label") or move_name})
        window["responses"].append(response)
        window["pending_actor_ids"] = [value for value in window["pending_actor_ids"] if value != actor_id]
        if not window["pending_actor_ids"]:
            window["status"] = "ready"
        return self.state()

    def resolve_interrupt(self, *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        window = self.interrupt_window
        battle = self.facade.battle
        if not window or battle is None:
            raise ValueError("No interrupt window is open.")
        stacked = next((entry for entry in reversed(window["responses"]) if entry.get("status") == "stacked"), None)
        if stacked is None:
            self.interrupt_window = None
            return self.decorate(self.facade.snapshot())
        self.facade._push_history()
        resolved = battle._resolve_out_of_turn_move(
            stacked["actor_id"],
            move_name=stacked["move"],
            target_id=stacked.get("target_id"),
        )
        if not resolved:
            stacked["status"] = "rejected"
            raise ValueError("The reaction was no longer legal when the stack resolved.")
        stacked["status"] = "resolved"
        battle.log_event(
            {
                "type": "interrupt",
                "actor": stacked["actor_id"],
                "move": stacked["move"],
                "target": stacked.get("target_id"),
                "effect": "manual_reaction_window",
                "description": f"{stacked.get('label') or stacked['move']} resolved from the reaction stack.",
            }
        )
        if not any(entry.get("status") == "stacked" for entry in window["responses"]) and not window["pending_actor_ids"]:
            self.interrupt_window = None
        return self.decorate(self.facade.snapshot())

    def close_interrupt(self, *, role: str = "gm") -> Dict[str, Any]:
        self._sync_battle()
        self._require_role(role, gm=True)
        self.interrupt_window = None
        return self.state()
