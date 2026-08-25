import json

import pytest

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.store import CareerStore


def test_local_store_skips_corrupt_run_records_for_aggregate_consumers(tmp_path) -> None:
    store = CareerStore(tmp_path / "career")
    run = CareerEngine().new_run(
        player_id="registry-survivor",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=2401,
        daily_challenge_id="daily-corrupt-registry",
    )
    run.status = "retired"
    run.score = 87
    run.attempt_no = 1
    store.save_run(run)

    (store.runs_dir / "000-truncated.json").write_text('{"id": "broken"', encoding="utf-8")
    (store.runs_dir / "001-wrong-shape.json").write_text('["not", "a", "run"]', encoding="utf-8")
    (store.runs_dir / "002-incomplete.json").write_text('{"id": "missing-build"}', encoding="utf-8")

    restored = store.list_runs()
    leaderboard = store.leaderboard("daily-corrupt-registry", "simple")

    assert [entry.id for entry in restored] == [run.id]
    assert store.attempt_count("daily-corrupt-registry", run.player_id, "simple") == 1
    assert len(leaderboard) == 1
    assert leaderboard[0].run_id == run.id
    assert leaderboard[0].score == 87


def test_explicit_load_still_surfaces_requested_corrupt_run(tmp_path) -> None:
    store = CareerStore(tmp_path / "career")
    (store.runs_dir / "broken.json").write_text('{"id": "broken"', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        store.load_run("broken")
