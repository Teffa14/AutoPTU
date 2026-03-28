"""Roleplay API endpoints (draft)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ..config import REPORTS_DIR
from ..rules.roleplay.quests import QuestObjective, QuestState
from ..rules.roleplay.factions import ReputationTrack
from ..rules.roleplay.dialogue import DialogueNode, DialogueChoice
from ..persistence.event_store import EventStore

router = APIRouter(prefix="/api/roleplay", tags=["roleplay"])

# Persistent event log
STORE = EventStore(REPORTS_DIR / "roleplay_events.sqlite3")

# In-memory storage for draft scaffolding
QUESTS: Dict[str, QuestState] = {}
FACTIONS: Dict[str, ReputationTrack] = {}
DIALOGUES: Dict[str, DialogueNode] = {}


@router.post("/check")
def roleplay_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    character_id = payload.get("character_id")
    skill = payload.get("skill")
    dc = payload.get("dc")
    roll = payload.get("roll")
    if not character_id or not skill or dc is None:
        raise HTTPException(status_code=400, detail="character_id, skill, dc required")
    if roll is None:
        event = {
            "id": str(uuid4()),
            "type": "skill_check",
            "actor_id": character_id,
            "payload": {"skill": skill, "dc": dc, "needs_roll": True},
        }
        STORE.append(event)
        return {"event": event}
    success = int(roll) >= int(dc)
    event = {
        "id": str(uuid4()),
        "type": "skill_check",
        "actor_id": character_id,
        "payload": {"skill": skill, "dc": dc, "roll": roll, "success": success},
    }
    STORE.append(event)
    return {"event": event}


@router.post("/quest")
def quest_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    quest_id = payload.get("quest_id") or str(uuid4())
    name = payload.get("name") or "Quest"
    action = payload.get("action") or "update"
    objective_id = payload.get("objective_id")
    status = payload.get("status")

    quest = QUESTS.get(quest_id)
    if not quest:
        objectives_payload = payload.get("objectives") or []
        objectives = []
        for entry in objectives_payload:
            if not isinstance(entry, dict):
                continue
            obj_id = entry.get("id") or str(uuid4())
            objectives.append(
                QuestObjective(id=obj_id, description=str(entry.get("description") or "Objective"))
            )
        quest = QuestState(id=quest_id, name=str(name), objectives=objectives)
        QUESTS[quest_id] = quest

    event = None
    if action == "complete_objective" and objective_id:
        event = quest.complete_objective(str(objective_id))
    if status:
        event = quest.set_status(str(status))

    evt = {"id": str(uuid4()), "type": "quest_updated", "payload": {"detail": event}}
    STORE.append(evt)
    return {"quest": asdict(quest), "event": evt}


@router.post("/faction")
def faction_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    faction_id = payload.get("faction_id") or str(uuid4())
    name = payload.get("name") or "Faction"
    delta = int(payload.get("delta", 0))
    faction = FACTIONS.get(faction_id)
    if not faction:
        faction = ReputationTrack(id=faction_id, name=str(name))
        FACTIONS[faction_id] = faction
    event = faction.adjust(delta)
    evt = {"id": str(uuid4()), "type": "reputation_changed", "payload": {"detail": event}}
    STORE.append(evt)
    return {"faction": asdict(faction), "event": evt}


@router.post("/dialogue")
def dialogue_choice(payload: Dict[str, Any]) -> Dict[str, Any]:
    dialogue_id = payload.get("dialogue_id") or str(uuid4())
    choice_id = payload.get("choice_id")
    node = DIALOGUES.get(dialogue_id)
    if not node:
        text = payload.get("text") or "..."
        choices_payload = payload.get("choices") or []
        choices = []
        for entry in choices_payload:
            if not isinstance(entry, dict):
                continue
            cid = entry.get("id") or str(uuid4())
            choices.append(
                DialogueChoice(
                    id=cid,
                    text=str(entry.get("text") or "Choice"),
                    next_node=entry.get("next_node"),
                    effects=entry.get("effects") or {},
                )
            )
        node = DialogueNode(id=dialogue_id, text=str(text), choices=choices)
        DIALOGUES[dialogue_id] = node

    resolved = node.resolve_choice(str(choice_id)) if choice_id else None
    if choice_id and not resolved:
        raise HTTPException(status_code=400, detail="choice not found")

    evt = {
        "id": str(uuid4()),
        "type": "dialogue_choice",
        "payload": {"choice_id": choice_id, "next_node": resolved.next_node if resolved else None},
    }
    STORE.append(evt)
    return {"dialogue": asdict(node), "choice": asdict(resolved) if resolved else None, "event": evt}


@router.get("/events")
def roleplay_events(since: Optional[str] = None) -> Dict[str, Any]:
    events = [asdict(evt) for evt in STORE.events(since=since)]
    return {"events": events}
