import copy

import pytest

from auto_ptu.api.battle_commands import BattleCommandService
from auto_ptu.api.engine_facade import EngineFacade


def _pokemon_turn(seed: int = 42) -> tuple[EngineFacade, dict]:
    facade = EngineFacade()
    facade.start_encounter(team_size=1, active_slots=1, seed=seed)
    snapshot = facade.commit_action({"type": "end_turn"})
    assert snapshot["current_actor_id"] == "player-1"
    return facade, snapshot


def _run_planned_turn() -> tuple[list[dict], tuple[int, int], str]:
    facade, _snapshot = _pokemon_turn()
    service = BattleCommandService(facade)
    before = copy.deepcopy(facade.battle.log)

    service.stage({"type": "shift", "actor_id": "player-1", "destination": [1, 0]})
    service.stage({"type": "move", "actor_id": "player-1", "move": "Rain Dance"})

    assert facade.battle.log == before
    result = service.resolve(mode="all")
    assert result["resolved_commands"] == ["command-1", "command-2"]
    assert result["command_center"]["queue"] == []
    return copy.deepcopy(facade.battle.log), facade.battle.pokemon["player-1"].position, facade.battle.weather


def test_planned_action_sequence_is_deterministic_and_applies_in_order():
    first = _run_planned_turn()
    second = _run_planned_turn()

    assert first == second
    log, position, weather = first
    shift_index = next(index for index, entry in enumerate(log) if entry.get("type") == "shift" and entry.get("actor") == "player-1")
    rain_index = next(index for index, entry in enumerate(log) if entry.get("move") == "Rain Dance")
    assert shift_index < rain_index
    assert position == (1, 0)
    assert weather == "Rain"


def test_snapshot_hides_actions_after_their_action_economy_is_spent():
    facade, snapshot = _pokemon_turn()
    destination = next(coord for coord in snapshot["legal_shifts"] if coord != snapshot["current_pos"])

    after_shift = facade.commit_action(
        {"type": "shift", "actor_id": "player-1", "x": destination[0], "y": destination[1]}
    )
    assert after_shift["legal_shifts"] == []

    after_move = facade.commit_action(
        {"type": "move", "actor_id": "player-1", "move": "Rain Dance", "target_id": None}
    )
    assert all(not targets for targets in after_move["move_targets"].values())


def test_snapshot_hides_scene_move_after_frequency_quota_is_spent():
    facade, snapshot = _pokemon_turn()
    assert snapshot["move_targets"]["Rain Dance"]
    facade.battle.frequency_usage.setdefault("player-1", {})["Rain Dance"] = 1

    exhausted = facade.snapshot()

    assert exhausted["move_targets"]["Rain Dance"] == []


def test_reaction_window_collects_then_resolves_lifo_without_changing_turn():
    facade = EngineFacade()
    facade.start_encounter(team_size=1, active_slots=1, seed=42)
    service = BattleCommandService(facade)
    active_actor = facade.battle.current_actor_id
    log_before = copy.deepcopy(facade.battle.log)

    opened = service.open_interrupt(
        {"trigger": "Weather response", "actor_ids": ["player-1"]},
        role="gm",
    )
    options = opened["interrupt_window"]["options"]["player-1"]
    rain = next(entry for entry in options if entry["move"] == "Rain Dance")
    stacked = service.respond_interrupt(
        {"actor_id": "player-1", "move": rain["move"], "target_id": rain.get("target_id")},
        role="player",
    )

    assert stacked["interrupt_window"]["responses"][0]["status"] == "stacked"
    assert facade.battle.log == log_before
    service.resolve_interrupt(role="gm")

    assert facade.battle.current_actor_id == active_actor
    assert facade.battle.log[-1]["type"] == "interrupt"
    assert facade.battle.log[-1]["effect"] == "manual_reaction_window"


def test_spectators_cannot_stage_actions_and_only_gm_can_open_interrupts():
    facade, _snapshot = _pokemon_turn()
    service = BattleCommandService(facade)

    with pytest.raises(PermissionError):
        service.stage({"type": "move", "actor_id": "player-1", "move": "Rain Dance"}, role="spectator")
    with pytest.raises(PermissionError):
        service.open_interrupt({"trigger": "Test"}, role="player")


def _automatic_reaction_transcript() -> tuple[dict, list[dict]]:
    facade = EngineFacade()
    facade.start_encounter(team_size=1, active_slots=1, seed=42)
    service = BattleCommandService(facade)
    service.state()
    service.register_reaction(
        {
            "id": "reaction-weather-watch",
            "name": "Weather Watch",
            "source_kind": "ability",
            "actor_ids": ["player-1"],
            "trigger_types": ["weather_changed"],
            "conditions": {"weather": "Rain"},
        },
        role="gm",
    )
    facade.battle.log_event({"type": "weather_changed", "weather": "Rain", "actor": "foe-1", "round": 1})
    decorated = service.after_resolution(facade.snapshot())
    return decorated["command_center"]["interrupt_window"], decorated["command_center"]["reaction_registry"]


def test_registered_ability_trigger_opens_the_same_deterministic_reaction_stack():
    first = _automatic_reaction_transcript()
    second = _automatic_reaction_transcript()

    assert first == second
    window, registry = first
    assert window["automatic"] is True
    assert window["reaction_id"] == "reaction-weather-watch"
    assert window["allowed_actor_ids"] == ["player-1"]
    assert window["trigger_event"]["weather"] == "Rain"
    assert registry[-1]["source_kind"] == "ability"
