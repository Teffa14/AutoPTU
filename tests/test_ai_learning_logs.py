import json
import os
from pathlib import Path

from auto_ptu.api.engine_facade import EngineFacade
from auto_ptu.gameplay import ai_model_status
from auto_ptu.ai import model_ratings


def test_engine_facade_persists_battle_log_jsonl(tmp_path: Path):
    original = os.environ.get("AUTOPTU_BATTLE_LOG_DIR")
    os.environ["AUTOPTU_BATTLE_LOG_DIR"] = str(tmp_path)
    try:
        facade = EngineFacade()
        state = facade.start_encounter(team_size=1, active_slots=1, seed=41)
        log_path = state.get("battle_log_path")
        assert log_path
        path = Path(str(log_path))
        assert path.exists()
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines
        assert lines[0].get("type") == "battle_start"
        assert any(entry.get("type") == "battle_event" for entry in lines)
    finally:
        if original is None:
            os.environ.pop("AUTOPTU_BATTLE_LOG_DIR", None)
        else:
            os.environ["AUTOPTU_BATTLE_LOG_DIR"] = original


def test_engine_facade_export_battle_log_returns_full_log(tmp_path: Path):
    original = os.environ.get("AUTOPTU_BATTLE_LOG_DIR")
    os.environ["AUTOPTU_BATTLE_LOG_DIR"] = str(tmp_path)
    try:
        facade = EngineFacade()
        facade.start_encounter(team_size=1, active_slots=1, seed=99)
        assert facade.battle is not None
        for idx in range(250):
            facade.battle.log_event({"type": "test", "round": idx // 5, "message": f"entry-{idx}"})
        snapshot = facade.snapshot()
        exported = facade.export_battle_log()
        assert len(snapshot.get("log", [])) == 200
        assert len(exported.get("log", [])) >= 250
        assert exported["log"][-1]["message"] == "entry-249"
    finally:
        if original is None:
            os.environ.pop("AUTOPTU_BATTLE_LOG_DIR", None)
        else:
            os.environ["AUTOPTU_BATTLE_LOG_DIR"] = original


def test_ai_model_status_includes_selected_analysis():
    status = ai_model_status()
    assert "models" in status
    if status.get("models"):
        assert "selected_analysis" in status
        assert "ratings" in status


def test_model_ratings_record_wins_and_losses(tmp_path: Path):
    store = model_ratings.default_store(tmp_path / "ratings.json")
    model_ratings.record_result(store, winner_model_id="model_a", loser_model_id="model_b")
    payload = model_ratings.status(store)
    rows = {entry["model_id"]: entry for entry in payload["ratings"]}
    assert rows["model_a"]["wins"] == 1
    assert rows["model_b"]["losses"] == 1
