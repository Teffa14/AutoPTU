from pathlib import Path
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auto_ptu.api.campaign_service import CampaignService
from auto_ptu.api.campaign_agents import CampaignAgentRuntime
from auto_ptu.api.campaign_agent_api import build_campaign_agent_router
from auto_ptu.api.campaign_battle_access import CampaignBattleAccess
from auto_ptu.api.campaign_realtime import CampaignRealtimeHub
from auto_ptu.rules.campaign_state import CampaignState


def _service(path: Path) -> CampaignService:
    return CampaignService(path / "campaign.sqlite3")


def _create(service: CampaignService) -> dict:
    return service.create(
        {
            "id": "opal-region",
            "name": "Opal Region",
            "gm_id": "gm",
            "gm_name": "Morgan",
            "gm_token": "gm-token",
            "invite_code": "OPAL01",
            "seed": 915,
        }
    )


def test_campaign_roles_enforce_gm_player_and_spectator_permissions(tmp_path: Path):
    service = _service(tmp_path)
    _create(service)
    player = service.join(
        "opal-region",
        {"name": "Ari", "role": "player", "invite_code": "OPAL01", "token": "player-token"},
    )
    spectator = service.join(
        "opal-region",
        {"name": "Sam", "role": "spectator", "invite_code": "OPAL01", "token": "spectator-token"},
    )

    with pytest.raises(PermissionError):
        service.command("opal-region", "player-token", {"type": "scene.create", "payload": {"title": "Route 1"}})
    with pytest.raises(PermissionError):
        service.command("opal-region", "spectator-token", {"type": "chat.post", "payload": {"text": "hello"}})

    assert "roll.check" in player["campaign"]["permissions"]
    assert spectator["campaign"]["permissions"] == []


def test_campaign_dice_event_is_deterministic_and_ordered(tmp_path: Path):
    transcripts = []
    for name in ("first", "second"):
        service = _service(tmp_path / name)
        _create(service)
        service.join(
            "opal-region",
            {
                "participant_id": "ari",
                "name": "Ari",
                "role": "player",
                "invite_code": "OPAL01",
                "token": "player-token",
            },
        )
        service.command(
            "opal-region",
            "gm-token",
            {"type": "scene.create", "payload": {"id": "scene-route", "title": "Route 1", "activate": True}},
        )
        result = service.command(
            "opal-region",
            "player-token",
            {"type": "roll.check", "payload": {"label": "Perception", "expression": "3d6+2"}},
        )
        event = result["event"]
        assert event["type"] == "roll.check"
        assert event["seq"] == 4
        assert event["detail"]["total"] == sum(event["detail"]["rolls"]) + 2
        assert list(event["detail"]) == ["label", "expression", "rolls", "modifier", "total"]
        transcripts.append(result["campaign"]["activity"])

    assert transcripts[0] == transcripts[1]


def test_starter_campaign_is_populated_and_deterministic(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        result = service.create_starter(
            {
                "id": "prism-trail-fixture",
                "gm_name": "Morgan",
                "gm_token": "starter-token",
                "invite_code": "PRISM1",
                "seed": 731245,
            }
        )
        campaign = result["campaign"]

        assert result["token"] == "starter-token"
        assert campaign["starter"] is True
        assert campaign["revision"] == 78
        assert len(campaign["participants"]) == 5
        assert [entry["name"] for entry in campaign["participants"] if entry["is_agent"]] == [
            "The Prism Keeper",
            "Milo Reed",
            "Nova Vale",
            "Sera Moss",
        ]
        assert {entry["agent_model"] for entry in campaign["participants"] if entry["is_agent"]} == {"qwen2.5:3b"}
        assert campaign["active_scene"]["id"] == "scene-starter-day"
        assert [scene["kind"] for scene in campaign["scenes"]] == [
            "roleplay",
            "combat",
            "exploration",
            "combat",
            "downtime",
            "travel",
            "combat",
            "roleplay",
            "combat",
            "roleplay",
            "combat",
            "combat",
            "combat",
            "downtime",
        ]
        assert [clock["id"] for clock in campaign["clocks"]] == ["clock-cinder-plan", "clock-league-scrutiny"]
        assert [quest["id"] for quest in campaign["quests"]] == ["quest-badge-circuit", "quest-cinder-truth", "quest-prism-league"]
        assert [faction["score"] for faction in campaign["factions"]] == [-1, 0, 1]
        assert len(campaign["actors"]) == 33
        assert len(campaign["locations"]) == 9
        assert len(campaign["chat"]) == 1
        assert campaign["journal"][0]["title"] == "Journey Record"
        assert campaign["time_label"] == "Day 1, Starter Morning"
        assert campaign["world"] == {
            "current_location_id": "lumenfall-lab",
            "revealed_location_ids": ["lumenfall-lab"],
            "weather": "Clear",
            "lighting": "Morning",
            "fog": 0,
            "traveling": False,
        }
        transcripts.append(campaign)

    assert transcripts[0] == transcripts[1]


def test_legacy_campaign_snapshot_gains_deterministic_exploration_compatibility(tmp_path: Path):
    service = _service(tmp_path)
    service.create_starter({"id": "legacy-floor", "gm_token": "gm-token", "seed": 731245})
    payload = service.require_campaign("legacy-floor").snapshot_dict()
    payload.pop("exploration_maps")
    payload.pop("exploration_tokens")
    payload.pop("exploration_memory")
    restored = CampaignState.from_dict(payload)

    service._ensure_exploration_compatibility(restored)

    assert sorted(restored.exploration_maps) == sorted(restored.locations)
    assert restored.exploration_maps["lumenfall-lab"]["theme"] == "laboratory"
    assert "trainer-nova" in restored.exploration_tokens
    assert "pokemon-growlithe" in restored.exploration_tokens
    assert "starter-bulbasaur" not in restored.exploration_tokens


def test_player_snapshot_hides_future_scenes_secret_actors_and_unrevealed_map(tmp_path: Path):
    service = _service(tmp_path)
    service.create_starter(
        {"id": "private-prism-trail", "gm_token": "gm-token", "invite_code": "SECRET", "seed": 731245}
    )
    joined = service.join(
        "private-prism-trail",
        {
            "participant_id": "human-player",
            "name": "Ari",
            "role": "player",
            "invite_code": "SECRET",
            "token": "player-token",
        },
    )
    player_state = joined["campaign"]

    trainer = next(actor for actor in player_state["actors"] if actor["kind"] == "trainer")
    assert trainer["owner_participant_id"] == "human-player"
    assert trainer["currency"] == 1500
    selected = service.command(
        "private-prism-trail",
        "player-token",
        {"type": "starter.select", "payload": {"species": "Squirtle"}},
    )["campaign"]
    assert selected["viewer"]["companion"] == "Squirtle"
    assert next(actor for actor in selected["actors"] if actor["id"] == "trainer-human-player")["sheet"]["active_party_ids"] == ["starter-squirtle"]

    assert [scene["id"] for scene in player_state["scenes"]] == ["scene-starter-day"]
    assert [location["id"] for location in player_state["locations"]] == ["lumenfall-lab"]
    assert "npc-alder" in {actor["id"] for actor in player_state["actors"]}
    assert "npc-cassian" not in {actor["id"] for actor in player_state["actors"]}
    assert "pokemon-riolu" not in {actor["id"] for actor in player_state["actors"]}
    alder = next(actor for actor in player_state["actors"] if actor["id"] == "npc-alder")
    assert "knowledge" not in alder
    assert "goals" not in alder
    assert "sheet" not in alder
    serialized = json.dumps(player_state, sort_keys=True)
    assert "The Champion's Prism" not in serialized
    assert "pokemon-absol" not in serialized
    assert "Complete prism covenant" not in serialized

    preview = service.command(
        "private-prism-trail",
        "gm-token",
        {
            "type": "scene.visibility",
            "payload": {"scene_id": "scene-first-rival", "published": True, "available": False},
        },
    )
    player_state = service.get("private-prism-trail", "player-token")
    assert preview["event"]["detail"]["available"] is False
    assert [scene["id"] for scene in player_state["scenes"]] == ["scene-starter-day", "scene-first-rival"]
    assert player_state["scenes"][1]["available"] is False
    assert [location["id"] for location in player_state["locations"]] == ["lumenfall-lab"]
    with pytest.raises(PermissionError):
        service.command(
            "private-prism-trail",
            "player-token",
            {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}},
        )
    with pytest.raises(PermissionError, match="has not revealed"):
        service.command(
            "private-prism-trail",
            "player-token",
            {"type": "location.travel", "payload": {"location_id": "sunpath-route"}},
        )

    service.command(
        "private-prism-trail",
        "gm-token",
        {"type": "starter.select", "payload": {"species": "Bulbasaur"}},
    )
    service.command(
        "private-prism-trail",
        "gm-token",
        {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}},
    )
    player_state = service.get("private-prism-trail", "player-token")
    assert "sunpath-route" in {location["id"] for location in player_state["locations"]}
    service.command(
        "private-prism-trail",
        "player-token",
        {"type": "location.travel", "payload": {"location_id": "sunpath-route"}},
    )
    arrived = service.get("private-prism-trail", "player-token")
    assert arrived["world"]["current_location_id"] == "sunpath-route"
    assert "npc-cassian" in {actor["id"] for actor in arrived["actors"]}
    assert "pokemon-riolu" not in {actor["id"] for actor in arrived["actors"]}
    visible_events = json.dumps(service.events("private-prism-trail", "player-token"), sort_keys=True)
    assert "The Champion's Prism" not in visible_events
    assert "pokemon-absol" not in visible_events


def test_exploration_token_movement_and_fog_memory_are_deterministic(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        service.create_starter(
            {"id": "exploration-trail", "gm_token": "gm-token", "invite_code": "EXPLORE", "seed": 731245}
        )
        service.join(
            "exploration-trail",
            {"participant_id": "human-player", "name": "Ari", "role": "player", "invite_code": "EXPLORE", "token": "player-token"},
        )
        before = service.get("exploration-trail", "player-token")["exploration"]
        trainer = next(token for token in before["tokens"] if token["actor_id"] == "trainer-human-player")
        assert before["viewer_token_ids"] == ["trainer-human-player"]
        assert (trainer["x"], trainer["y"]) == (3, 3)

        result = service.command(
            "exploration-trail",
            "player-token",
            {"type": "exploration.token.move", "payload": {"actor_id": trainer["actor_id"], "x": 7, "y": 3}},
        )
        event = result["event"]
        assert list(event["detail"]) == ["actor_id", "from", "to", "location_id", "path", "steps", "discovered_point_ids"]
        assert event["detail"]["discovered_point_ids"] == []
        assert event["detail"]["from"] == {"x": 3, "y": 3}
        assert event["detail"]["to"] == {"x": 7, "y": 3}
        assert event["detail"]["steps"] == 4
        assert event["detail"]["path"] == [
            {"x": 3, "y": 3},
            {"x": 4, "y": 3},
            {"x": 5, "y": 3},
            {"x": 6, "y": 3},
            {"x": 7, "y": 3},
        ]
        after = result["campaign"]["exploration"]
        moved = next(token for token in after["tokens"] if token["actor_id"] == trainer["actor_id"])
        assert (moved["x"], moved["y"]) == (7, 3)
        assert any(cell["state"] == "explored" for cell in after["cells"])
        assert [cell["key"] for cell in after["cells"]] == [f"{x},{y}" for y in range(7) for x in range(10)]
        transcripts.append(after)

    assert transcripts[0] == transcripts[1]


def test_exploration_movement_enforces_actor_ownership_and_server_legality(tmp_path: Path):
    service = _service(tmp_path)
    service.create_starter(
        {"id": "owned-exploration", "gm_token": "gm-token", "invite_code": "OWNED1", "seed": 731245}
    )
    service.join(
        "owned-exploration",
        {"participant_id": "human-player", "name": "Ari", "role": "player", "invite_code": "OWNED1", "token": "player-token"},
    )
    state = service.get("owned-exploration", "player-token")
    own = next(token for token in state["exploration"]["tokens"] if token["actor_id"] == "trainer-human-player")
    other = next(token for token in state["exploration"]["tokens"] if token["owner_participant_id"] == "agent-nova")
    with pytest.raises(PermissionError, match="only move"):
        service.command(
            "owned-exploration",
            "player-token",
            {"type": "exploration.token.move", "payload": {"actor_id": other["actor_id"], "x": other["x"] + 1, "y": other["y"]}},
        )
    moved = service.command(
        "owned-exploration",
        "player-token",
        {"type": "exploration.token.move", "payload": {"actor_id": own["actor_id"], "x": own["x"] + 2, "y": own["y"]}},
    )
    assert moved["event"]["detail"]["steps"] == 2
    with pytest.raises(PermissionError, match="fog frontier"):
        service.command(
            "owned-exploration",
            "player-token",
            {"type": "exploration.token.move", "payload": {"actor_id": own["actor_id"], "x": 9, "y": 6}},
        )
    with pytest.raises(ValueError, match="within this token's Speed"):
        service.command(
            "owned-exploration",
            "player-token",
            {"type": "exploration.token.move", "payload": {"actor_id": own["actor_id"], "x": 0, "y": 6}},
        )
    with pytest.raises(ValueError, match="outside"):
        service.command(
            "owned-exploration",
            "gm-token",
            {"type": "exploration.token.move", "payload": {"actor_id": own["actor_id"], "x": -1, "y": own["y"]}},
        )


def test_gm_controls_exploration_fog_points_and_hidden_tokens_without_leaks(tmp_path: Path):
    service = _service(tmp_path)
    service.create_starter(
        {"id": "secret-exploration", "gm_token": "gm-token", "invite_code": "HIDDEN", "seed": 731245}
    )
    service.join(
        "secret-exploration",
        {"participant_id": "human-player", "name": "Ari", "role": "player", "invite_code": "HIDDEN", "token": "player-token"},
    )
    player_state = service.get("secret-exploration", "player-token")
    assert "lab-sealed-drawer" not in {point["id"] for point in player_state["exploration"]["points"]}
    assert any(cell["state"] == "hidden" for cell in player_state["exploration"]["cells"])

    service.command("secret-exploration", "gm-token", {"type": "exploration.visibility", "payload": {"mode": "reveal_all"}})
    revealed_floor = service.get("secret-exploration", "player-token")["exploration"]
    assert all(cell["state"] == "visible" for cell in revealed_floor["cells"])
    assert "lab-sealed-drawer" not in {point["id"] for point in revealed_floor["points"]}

    service.command(
        "secret-exploration",
        "gm-token",
        {"type": "exploration.point.visibility", "payload": {"point_id": "lab-sealed-drawer", "revealed": True}},
    )
    published = service.get("secret-exploration", "player-token")
    assert "lab-sealed-drawer" in {point["id"] for point in published["exploration"]["points"]}
    sealed = next(point for point in published["exploration"]["points"] if point["id"] == "lab-sealed-drawer")
    assert sealed["available"] is False
    assert sealed["can_interact"] is False
    assert sealed["result"] == ""
    assert "Inside is a copied covenant clause" not in json.dumps(published)

    service.command(
        "secret-exploration",
        "gm-token",
        {"type": "exploration.token.visibility", "payload": {"actor_id": "npc-alder", "revealed": False}},
    )
    hidden_npc = service.get("secret-exploration", "player-token")
    assert "npc-alder" not in {token["actor_id"] for token in hidden_npc["exploration"]["tokens"]}
    assert "npc-alder" not in {actor["id"] for actor in hidden_npc["actors"]}

    service.command("secret-exploration", "gm-token", {"type": "exploration.visibility", "payload": {"mode": "restore_fog"}})
    fogged_again = service.get("secret-exploration", "player-token")["exploration"]
    assert any(cell["state"] == "hidden" for cell in fogged_again["cells"])
    assert "lab-sealed-drawer" not in {point["id"] for point in fogged_again["points"]}


def test_exploration_points_require_proximity_and_gm_unlock_then_publish_deterministic_results(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        service.create_starter(
            {"id": "point-play", "gm_token": "gm-token", "invite_code": "POINT1", "seed": 731245}
        )
        service.join(
            "point-play",
            {"participant_id": "human-player", "name": "Ari", "role": "player", "invite_code": "POINT1", "token": "player-token"},
        )
        player = service.get("point-play", "player-token")
        trainer = next(token for token in player["exploration"]["tokens"] if token["actor_id"] == "trainer-human-player")
        pods = next(point for point in player["exploration"]["points"] if point["id"] == "lab-starter-pods")
        assert pods["can_interact"] is True
        discovery = service.command(
            "point-play",
            "player-token",
            {"type": "exploration.point.interact", "payload": {"point_id": pods["id"], "actor_id": trainer["actor_id"]}},
        )
        assert discovery["event"]["detail"]["success"] is True
        assert "starter candidates answer" in discovery["event"]["detail"]["result"]
        assert discovery["event"]["type"] == "exploration.point.interact"

        service.command("point-play", "gm-token", {"type": "exploration.visibility", "payload": {"mode": "reveal_all"}})
        service.command(
            "point-play",
            "gm-token",
            {"type": "exploration.point.visibility", "payload": {"point_id": "lab-sealed-drawer", "revealed": True}},
        )
        with pytest.raises(PermissionError, match="locked"):
            service.command(
                "point-play",
                "player-token",
                {"type": "exploration.point.interact", "payload": {"point_id": "lab-sealed-drawer", "actor_id": trainer["actor_id"]}},
            )
        service.command(
            "point-play",
            "gm-token",
            {"type": "exploration.point.update", "payload": {"point_id": "lab-sealed-drawer", "available": True}},
        )
        with pytest.raises(ValueError, match="next to"):
            service.command(
                "point-play",
                "player-token",
                {"type": "exploration.point.interact", "payload": {"point_id": "lab-sealed-drawer", "actor_id": trainer["actor_id"]}},
            )
        moved = service.command(
            "point-play",
            "player-token",
            {"type": "exploration.token.move", "payload": {"actor_id": trainer["actor_id"], "x": 7, "y": 1}},
        )
        assert moved["event"]["detail"]["steps"] == 4
        opened = service.command(
            "point-play",
            "player-token",
            {"type": "exploration.point.interact", "payload": {"point_id": "lab-sealed-drawer", "actor_id": trainer["actor_id"]}},
        )
        detail = opened["event"]["detail"]
        assert detail["check"]["expression"] == "3d6+1"
        assert detail["success"] == (detail["check"]["total"] >= 12)
        assert any(entry["type"] == "exploration.point.interact" for entry in opened["campaign"]["activity"])
        point = next(entry for entry in opened["campaign"]["exploration"]["points"] if entry["id"] == "lab-sealed-drawer")
        assert point["result"] == detail["result"] if detail["success"] else point["result"] == ""
        transcripts.append(detail)

    assert transcripts[0] == transcripts[1]


class _FakeOllama:
    base_url = "fake://ollama"

    def models(self):
        return [{"name": "test-model", "size": 1, "capabilities": ["completion", "tools"]}]

    def chat_json(self, *, model, system, prompt, schema, seed):
        context = __import__("json").loads(prompt)
        options = context.get("legal_options") or []
        actions = [entry.get("action") for entry in options]
        if "roll.check" in actions and "Role: player" in system:
            decision = {"action": "roll.check", "intent": "Read the clue", "label": "Perception", "expression": "2d6+1"}
        else:
            decision = {"action": "chat.post", "intent": "Reveal a consequence", "text": "The compass needle flashes toward the Glasswood trail."}
        return decision, {"model": model, "seed": seed, "eval_count": 12}


def test_solo_starter_makes_the_human_a_trainer_and_ai_gm_authoritative(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter(
        {
            "id": "solo-prism-trail",
            "play_mode": "solo",
            "player_name": "Avery",
            "player_token": "player-token",
            "agent_gm_token": "agent-gm-token",
            "invite_code": "SOLO01",
            "seed": 731245,
        }
    )
    campaign = created["campaign"]
    state = service.require_campaign("solo-prism-trail")

    assert created["token"] == "player-token"
    assert campaign["viewer"]["id"] == "player"
    assert campaign["viewer"]["role"] == "player"
    assert state.gm_id == "agent-gm"
    assert state.participants["agent-gm"].controller == "ai"
    assert state.participants["agent-gm"].is_agent is True
    assert state.world["agent_host_participant_id"] == "player"
    assert state.actors["trainer-player"].owner_participant_id == "player"
    assert campaign["scene_gate"]["incomplete_labels"] == ["Choose a starter partner"]
    assert [scene["id"] for scene in campaign["scenes"]] == ["scene-starter-day"]
    control = service.command(
        "solo-prism-trail",
        "player-token",
        {"type": "participant.control", "payload": {"participant_id": "agent-nova", "controller": "human"}},
    )
    assert control["event"]["detail"]["after"] == "human"
    assert state.participants["agent-nova"].is_agent is False
    service.command(
        "solo-prism-trail",
        "player-token",
        {"type": "participant.control", "payload": {"participant_id": "agent-nova", "controller": "ai"}},
    )
    with pytest.raises(PermissionError):
        service.command(
            "solo-prism-trail",
            "player-token",
            {"type": "participant.control", "payload": {"participant_id": "agent-gm", "controller": "human"}},
        )

    with pytest.raises(PermissionError, match="player role"):
        service.command(
            "solo-prism-trail",
            "player-token",
            {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}},
        )

    runtime = CampaignAgentRuntime(campaign_service=service, ollama=_FakeOllama())
    with pytest.raises(ValueError, match="Choose a starter partner"):
        runtime.advance("solo-prism-trail", "player-token")

    selected = service.command(
        "solo-prism-trail",
        "player-token",
        {"type": "starter.select", "payload": {"species": "Bulbasaur"}},
    )["campaign"]
    assert selected["scene_gate"]["ready"] is True
    starter = next(entry for entry in state.actors.values() if entry.species == "Bulbasaur" and entry.sheet.get("starter"))
    assert starter.owner_participant_id == "player"
    assert starter.id in state.participants["player"].character_ids

    advanced = runtime.advance("solo-prism-trail", "player-token")
    assert advanced["campaign"]["active_scene_id"] == "scene-first-rival"
    assert [scene["id"] for scene in advanced["campaign"]["scenes"]] == ["scene-starter-day", "scene-first-rival"]
    assert advanced["narration"]["event"]["actor_id"] == "agent-gm"
    assert advanced["campaign"]["scene_gate"]["ready"] is False

    with pytest.raises(ValueError, match="Travel to Sunpath Route"):
        service.battle_setup("solo-prism-trail", "player-token")
    service.command(
        "solo-prism-trail",
        "player-token",
        {"type": "location.travel", "payload": {"location_id": "sunpath-route"}},
    )
    setup = service.battle_setup("solo-prism-trail", "player-token")
    assert setup["scene_id"] == "scene-first-rival"
    assert setup["trainer_owners"]["player"] == "player"
    access = CampaignBattleAccess(service)
    access.bind(setup)
    identity = access.identity("player-token")
    assert identity["owned_trainer_ids"] == ["player"]
    assert identity["owned_actor_ids"] == ["player-1"]
    completed = service.complete_battle("solo-prism-trail", "player-token", winner_team="players")
    assert completed["event"]["actor_id"] == "player"
    assert completed["campaign"]["scene_gate"]["ready"] is True
    assert state.progression["rivals_defeated"] == ["npc-cassian"]


def test_exploration_movement_discovers_authored_hidden_clues_deterministically(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        service.create_starter({"id": "discover-prism", "gm_token": "gm-token", "seed": 731245})
        service.command("discover-prism", "gm-token", {"type": "starter.select", "payload": {"species": "Bulbasaur"}})
        service.command("discover-prism", "gm-token", {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}})
        service.command("discover-prism", "gm-token", {"type": "location.travel", "payload": {"location_id": "sunpath-route"}})
        state = service.require_campaign("discover-prism")
        state.scenes["scene-first-rival"].metadata["battle_completed"] = True
        service.command("discover-prism", "gm-token", {"type": "scene.activate", "payload": {"scene_id": "scene-glasswood-voices"}})
        service.command("discover-prism", "gm-token", {"type": "location.travel", "payload": {"location_id": "glasswood-crossing"}})

        point = next(entry for entry in state.exploration_maps["glasswood-crossing"]["points"] if entry["id"] == "glasswood-echo")
        assert point["discoverable"] is True
        assert point["revealed"] is False
        discoveries = []
        paths = []
        for _step in range(3):
            legal = state._exploration_paths("trainer-player")
            target_key = min(
                legal,
                key=lambda key: (
                    max(abs(int(key.split(",")[0]) - int(point["x"])), abs(int(key.split(",")[1]) - int(point["y"]))),
                    len(legal[key]),
                    key,
                ),
            )
            x, y = (int(value) for value in target_key.split(","))
            moved = service.command(
                "discover-prism",
                "gm-token",
                {"type": "exploration.token.move", "payload": {"actor_id": "trainer-player", "x": x, "y": y}},
            )["event"]["detail"]
            paths.append(moved["path"])
            discoveries.extend(moved["discovered_point_ids"])
            if point["revealed"]:
                break
        assert discoveries == ["glasswood-echo"]
        assert point["revealed"] is True
        transcripts.append({"paths": paths, "discoveries": discoveries})

    assert transcripts[0] == transcripts[1]


def test_ollama_campaign_agent_uses_real_command_boundary_deterministically(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        created = service.create_starter(
            {
                "id": "agent-prism-trail",
                "gm_token": "gm-token",
                "invite_code": "AGENT1",
                "seed": 731245,
            }
        )
        runtime = CampaignAgentRuntime(campaign_service=service, ollama=_FakeOllama())
        result = runtime.step("agent-prism-trail", created["token"], agent_id="agent-nova")

        assert result["source"] == "ollama"
        assert result["event"]["type"] == "roll.check"
        assert result["event"]["actor_id"] == "agent-nova"
        assert result["event"]["seq"] == 79
        assert result["event"]["detail"]["expression"] == "2d6+1"
        transcripts.append(result["campaign"]["activity"])

    assert transcripts[0] == transcripts[1]


class _FakeExplorationOllama(_FakeOllama):
    def chat_json(self, *, model, system, prompt, schema, seed):
        context = json.loads(prompt)
        option = next(entry for entry in context["legal_options"] if entry.get("action") == "exploration.token.move")
        return {
            "action": option["action"],
            "option_id": option["option_id"],
            "actor_id": option["actor_id"],
            "x": option["x"],
            "y": option["y"],
            "intent": "Scout one legal tile with my partner.",
        }, {"model": model, "seed": seed}


class _FakePointOllama(_FakeOllama):
    def chat_json(self, *, model, system, prompt, schema, seed):
        context = json.loads(prompt)
        option = next(entry for entry in context["legal_options"] if entry.get("action") == "exploration.point.interact")
        return {
            "action": option["action"],
            "option_id": option["option_id"],
            "point_id": option["point_id"],
            "actor_id": option["actor_id"],
            "intent": "Meet the starter candidates in the scene.",
        }, {"model": model, "seed": seed}


def test_ollama_player_can_move_an_owned_exploration_token_through_real_rules(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        created = service.create_starter(
            {"id": "agent-exploration", "gm_token": "gm-token", "invite_code": "AGENT2", "seed": 731245}
        )
        state = service.require_campaign("agent-exploration")
        before = {
            actor_id: (int(token["x"]), int(token["y"]))
            for actor_id, token in state.exploration_tokens.items()
            if state.actors[actor_id].owner_participant_id == "agent-nova"
        }
        runtime = CampaignAgentRuntime(campaign_service=service, ollama=_FakeExplorationOllama())
        result = runtime.step("agent-exploration", created["token"], agent_id="agent-nova")

        assert result["source"] == "ollama"
        assert result["event"]["type"] == "exploration.token.move"
        assert result["event"]["actor_id"] == "agent-nova"
        moved_actor = result["event"]["detail"]["actor_id"]
        assert state.actors[moved_actor].owner_participant_id == "agent-nova"
        assert tuple(result["event"]["detail"]["from"].values()) == before[moved_actor]
        assert tuple(result["event"]["detail"]["to"].values()) != before[moved_actor]
        transcripts.append(result["event"]["detail"])

    assert transcripts[0] == transcripts[1]


def test_ollama_player_can_use_a_nearby_scene_interaction_through_real_rules(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter(
        {"id": "agent-point", "gm_token": "gm-token", "invite_code": "AGENT3", "seed": 731245}
    )
    service.command(
        "agent-point",
        "gm-token",
        {"type": "exploration.token.move", "payload": {"actor_id": "trainer-nova", "x": 3, "y": 2}},
    )
    runtime = CampaignAgentRuntime(campaign_service=service, ollama=_FakePointOllama())
    result = runtime.step("agent-point", created["token"], agent_id="agent-nova")

    assert result["source"] == "ollama"
    assert result["event"]["type"] == "exploration.point.interact"
    assert result["event"]["detail"]["point_id"] == "lab-starter-pods"
    assert result["event"]["detail"]["actor_id"] == "trainer-nova"
    assert "starter candidates answer" in result["event"]["detail"]["result"]


def test_ollama_gm_opens_each_chapter_with_narration(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter({"id": "narrated-prism-trail", "gm_token": "gm-token", "seed": 731245})
    runtime = CampaignAgentRuntime(campaign_service=service, ollama=_FakeOllama())

    opening = runtime.step("narrated-prism-trail", created["token"], agent_id="agent-gm")
    assert opening["event"]["type"] == "chat.post"
    assert opening["event"]["detail"]["kind"] == "narration"

    service.command(
        "narrated-prism-trail",
        created["token"],
        {"type": "starter.select", "payload": {"species": "Bulbasaur"}},
    )
    service.command(
        "narrated-prism-trail",
        created["token"],
        {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}},
    )
    next_chapter = runtime.step("narrated-prism-trail", created["token"], agent_id="agent-gm")
    assert next_chapter["event"]["type"] == "chat.post"
    assert next_chapter["campaign"]["active_scene_id"] == "scene-first-rival"


class _FakeBattleEngine:
    def __init__(self):
        self.actions = []

    def snapshot(self):
        return {
            "status": "ok",
            "round": 1,
            "current_actor_id": "player-1",
            "current_actor_is_player": True,
            "trainer_turn": None,
            "current_pos": [1, 1],
            "legal_shifts": [[1, 1], [1, 2]],
            "move_targets": {"Tackle": ["foe-1"]},
            "combatants": [
                {"id": "player-1", "name": "Growlithe", "hp": 30, "max_hp": 30, "moves": [{"name": "Tackle"}]},
                {"id": "foe-1", "name": "Rattata", "hp": 20, "max_hp": 20, "moves": []},
            ],
            "log": [],
        }

    def commit_action(self, payload):
        self.actions.append(dict(payload))
        return {**self.snapshot(), "last_agent_action": dict(payload)}


class _FakeBattleOllama(_FakeOllama):
    def chat_json(self, *, model, system, prompt, schema, seed):
        return {"action": "move", "intent": "Pressure the foe", "move": "Tackle", "target_id": "foe-1"}, {"model": model}


class _ShiftHappyBattleOllama(_FakeOllama):
    def chat_json(self, *, model, system, prompt, schema, seed):
        return {"action": "shift", "intent": "Keep repositioning", "x": 1, "y": 2}, {"model": model}


def test_ollama_player_agent_submits_legal_battle_action(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter({"id": "battle-agents", "gm_token": "gm-token", "seed": 731245})
    engine = _FakeBattleEngine()
    runtime = CampaignAgentRuntime(campaign_service=service, engine=engine, ollama=_FakeBattleOllama())

    result = runtime.battle_step("battle-agents", created["token"])

    assert result["source"] == "ollama"
    assert engine.actions == [{"type": "move", "actor_id": "player-1", "move": "Tackle", "target_id": "foe-1"}]
    assert result["battle"]["last_agent_action"] == engine.actions[0]


def test_battle_agent_attacks_instead_of_repeatedly_shifting_when_a_target_is_legal(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter({"id": "decisive-battle-agents", "gm_token": "gm-token", "seed": 731245})
    engine = _FakeBattleEngine()
    runtime = CampaignAgentRuntime(campaign_service=service, engine=engine, ollama=_ShiftHappyBattleOllama())

    result = runtime.battle_step("decisive-battle-agents", created["token"])

    assert result["source"] == "ollama-tactical-policy"
    assert result["decision"]["action"] == "move"
    assert engine.actions == [{"type": "move", "actor_id": "player-1", "move": "Tackle", "target_id": "foe-1"}]


def test_campaign_battle_agent_response_preserves_authenticated_identity(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter({"id": "identity-agents", "gm_token": "gm-token", "seed": 731245})
    engine = _FakeBattleEngine()
    runtime = CampaignAgentRuntime(campaign_service=service, engine=engine, ollama=_FakeBattleOllama())
    access = CampaignBattleAccess(service)
    access.bind({"campaign_id": "identity-agents", "scene_id": "scene-first-rival"})
    app = FastAPI()
    app.include_router(build_campaign_agent_router(runtime, access))

    response = TestClient(app).post(
        "/api/campaigns/identity-agents/agents/battle/step",
        headers={"Authorization": f"Bearer {created['token']}"},
        json={},
    )

    assert response.status_code == 200
    identity = response.json()["battle"]["battle_identity"]
    assert identity["bound"] is True
    assert identity["role"] == "gm"
    assert identity["campaign_id"] == "identity-agents"


def test_campaign_snapshot_restores_scene_clock_quest_and_authentication(tmp_path: Path):
    service = _service(tmp_path)
    _create(service)
    service.command(
        "opal-region",
        "gm-token",
        {"type": "scene.create", "payload": {"id": "scene-lab", "title": "Professor's Lab", "activate": True}},
    )
    service.command(
        "opal-region",
        "gm-token",
        {"type": "clock.create", "payload": {"id": "clock-storm", "name": "Storm Arrives", "segments": 4}},
    )
    service.command(
        "opal-region",
        "gm-token",
        {"type": "clock.tick", "payload": {"clock_id": "clock-storm", "delta": 2}},
    )
    service.command(
        "opal-region",
        "gm-token",
        {"type": "quest.create", "payload": {"id": "quest-dex", "name": "Field Research", "objectives": ["Scan three Pokemon"]}},
    )

    restored = _service(tmp_path)
    campaign = restored.get("opal-region", "gm-token")

    assert campaign["active_scene"]["id"] == "scene-lab"
    assert campaign["clocks"] == [
        {
            "id": "clock-storm",
            "name": "Storm Arrives",
            "segments": 4,
            "filled": 2,
            "scene_id": "scene-lab",
            "visibility": "table",
            "reveal_order": 0,
        }
    ]
    assert campaign["quests"][0]["objectives"][0]["complete"] is False


def test_player_can_pause_table_but_only_gm_can_resume(tmp_path: Path):
    service = _service(tmp_path)
    _create(service)
    service.join(
        "opal-region",
        {"name": "Ari", "role": "player", "invite_code": "OPAL01", "token": "player-token"},
    )
    paused = service.command(
        "opal-region",
        "player-token",
        {"type": "safety.pause", "payload": {"message": "Please pause the scene."}},
    )
    assert paused["campaign"]["safety_paused"] is True
    with pytest.raises(PermissionError):
        service.command("opal-region", "player-token", {"type": "safety.resume", "payload": {}})
    resumed = service.command("opal-region", "gm-token", {"type": "safety.resume", "payload": {}})
    assert resumed["campaign"]["safety_paused"] is False


def test_persistent_identity_world_actions_and_battle_setup_are_deterministic(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        created = service.create_starter({"id": "full-journey", "gm_token": "gm-token", "invite_code": "FIXED1", "seed": 731245})
        service.command("full-journey", "gm-token", {"type": "starter.select", "payload": {"species": "Eevee"}})
        service.command("full-journey", "gm-token", {"type": "participant.control", "payload": {"participant_id": "agent-nova", "controller": "human"}})
        service.command(
            "full-journey",
            "gm-token",
            {
                "type": "builder.sync",
                "payload": {"sheet": {"profile": {"name": "Morgan", "level": 3, "money": 2800}, "skills": {"Command": 3}, "pokemon_builds": []}},
            },
        )
        service.command("full-journey", "gm-token", {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}})
        service.command("full-journey", "gm-token", {"type": "location.travel", "payload": {"location_id": "sunpath-route"}})
        setup = service.battle_setup("full-journey", "gm-token")
        state = service.get("full-journey", "gm-token")

        assert setup["scene_id"] == "scene-first-rival"
        assert [side["identifier"] for side in setup["battle"]["sides"]] == ["gm", "agent-milo", "agent-nova", "agent-sera", "npc-cassian"]
        assert {side["controller"] for side in setup["battle"]["sides"]} == {"player"}
        assert setup["actor_owners"]["gm-1"] == "gm"
        assert setup["actor_owners"]["agent-nova-1"] == "agent-nova"
        assert setup["battle"]["sides"][0]["pokemon"][0]["species"] == "Eevee"
        assert state["world"]["current_location_id"] == "sunpath-route"
        assert next(entry for entry in state["participants"] if entry["id"] == "agent-nova")["controller"] == "human"
        assert next(entry for entry in state["participants"] if entry["id"] == "gm")["companion"] == "Eevee"
        trainer = next(entry for entry in state["actors"] if entry["id"] == "trainer-player")
        assert trainer["sheet"]["builder_synced"] is True
        assert trainer["sheet"]["starter_species"] == "Eevee"
        assert trainer["sheet"]["active_party_ids"] == ["starter-eevee"]
        transcripts.append({"setup": setup, "state": state})

    assert transcripts[0] == transcripts[1]


def test_campaign_battle_access_ignores_client_role_and_enforces_owner(tmp_path: Path):
    service = _service(tmp_path)
    service.create_starter({"id": "owned-battle", "gm_token": "gm-token", "seed": 731245})
    service.command("owned-battle", "gm-token", {"type": "starter.select", "payload": {"species": "Bulbasaur"}})
    service.command("owned-battle", "gm-token", {"type": "scene.activate", "payload": {"scene_id": "scene-first-rival"}})
    service.command("owned-battle", "gm-token", {"type": "location.travel", "payload": {"location_id": "sunpath-route"}})
    setup = service.battle_setup("owned-battle", "gm-token")
    access = CampaignBattleAccess(service)
    access.bind(setup)
    state = service.require_campaign("owned-battle")
    nova_token = state.participants["agent-nova"].token

    assert access.authorize(nova_token, actor_id="agent-nova-1", legacy_role="gm") == "player"
    with pytest.raises(PermissionError):
        access.authorize(nova_token, actor_id="gm-1", legacy_role="gm")
    with pytest.raises(PermissionError):
        access.authorize(nova_token, gm=True, legacy_role="gm")
    assert access.authorize("gm-token", actor_id="agent-nova-1", gm=True) == "gm"


class _NpcOllama(_FakeOllama):
    def chat_json(self, *, model, system, prompt, schema, seed):
        assert "You know only these campaign facts" in system
        return {
            "response": "Choose the partner who chooses your patience as much as your ambition.",
            "relationship_delta": 1,
            "known_fact_used": "Starter temperaments",
        }, {"model": model, "seed": seed}


def test_persistent_npc_answers_from_recorded_persona_and_knowledge(tmp_path: Path):
    service = _service(tmp_path)
    created = service.create_starter({"id": "npc-truth", "gm_token": "gm-token", "seed": 731245})
    exchange = service.command(
        "npc-truth",
        "gm-token",
        {"type": "npc.talk", "payload": {"npc_id": "npc-alder", "text": "How should I choose?"}},
    )["event"]
    runtime = CampaignAgentRuntime(campaign_service=service, ollama=_NpcOllama())
    result = runtime.npc_reply("npc-truth", created["token"], dialogue_id=exchange["detail"]["id"])

    assert result["source"] == "ollama"
    assert result["event"]["type"] == "npc.reply"
    assert result["npc"]["name"] == "Professor Alder"
    assert result["campaign"]["dialogue"][-1]["status"] == "answered"
    assert result["campaign"]["dialogue"][-1]["response"].startswith("Choose the partner")


def test_moonmere_npc_reply_completes_truth_objective_deterministically(tmp_path: Path):
    transcripts = []
    for directory in ("first", "second"):
        service = _service(tmp_path / directory)
        created = service.create_starter({"id": "moonmere-truth", "gm_token": "gm-token", "seed": 731245})
        service.command("moonmere-truth", "gm-token", {"type": "starter.select", "payload": {"species": "Bulbasaur"}})
        service.command("moonmere-truth", "gm-token", {"type": "scene.activate", "payload": {"scene_id": "scene-moonmere-truth"}})
        for location_id in ("sunpath-route", "brookfall-city", "embermarket", "copperline-route", "voltspire-city", "moonmere"):
            service.command("moonmere-truth", "gm-token", {"type": "location.travel", "payload": {"location_id": location_id}})
        exchange = service.command(
            "moonmere-truth",
            "gm-token",
            {"type": "npc.talk", "payload": {"npc_id": "npc-ilyra", "text": "Tell me the covenant truth."}},
        )["event"]
        runtime = CampaignAgentRuntime(campaign_service=service, ollama=_NpcOllama())
        result = runtime.npc_reply("moonmere-truth", created["token"], dialogue_id=exchange["detail"]["id"])
        truth_quest = next(entry for entry in result["campaign"]["quests"] if entry["id"] == "quest-cinder-truth")

        assert result["event"]["detail"]["completed_objectives"] == ["quest-cinder-truth-objective-2"]
        assert truth_quest["objectives"][1]["complete"] is True
        transcripts.append(result["campaign"]["quests"])

    assert transcripts[0] == transcripts[1]


def test_campaign_websocket_pushes_events_without_polling(tmp_path: Path, monkeypatch):
    import auto_ptu.api.campaign_api as campaign_api
    from auto_ptu.api.server import app

    service = _service(tmp_path)
    hub = CampaignRealtimeHub()
    service.add_event_listener(hub.publish)
    monkeypatch.setattr(campaign_api, "SERVICE", service)
    monkeypatch.setattr(campaign_api, "REALTIME", hub)
    client = TestClient(app)
    created = client.post(
        "/api/campaigns",
        json={"id": "websocket-table", "gm_token": "ws-token", "invite_code": "LIVE01", "seed": 44},
    ).json()
    assert created["campaign"]["id"] == "websocket-table"

    with client.websocket_connect("/api/campaigns/websocket-table/ws?token=ws-token") as socket:
        initial = socket.receive_json()
        assert initial["type"] == "campaign.snapshot"
        response = client.post(
            "/api/campaigns/websocket-table/command",
            headers={"Authorization": "Bearer ws-token"},
            json={"type": "chat.post", "payload": {"text": "A live table event."}},
        )
        assert response.status_code == 200
        pushed = socket.receive_json()
        assert pushed["type"] == "campaign.event"
        assert pushed["event"] == {"seq": 2, "type": "campaign.updated"}
