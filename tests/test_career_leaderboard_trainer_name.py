from datetime import date

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def test_ranked_leaderboard_preserves_the_winning_career_trainer_name(tmp_path) -> None:
    store = CareerStore(tmp_path / "career")
    engine = CareerEngine()
    challenge = engine.daily_challenge(date(2026, 8, 27))
    run = engine.new_run(
        player_id="player-123456789",
        name="Nemona Prime",
        region=challenge.region,
        starter="Bulbasaur" if challenge.region == "kanto" else next(iter(__import__("auto_ptu.career.catalogs", fromlist=["REGIONS"]).REGIONS[challenge.region].partner_choices)),
        classes=["Ace Trainer"],
        mode="simple",
        locale="es",
        seed=challenge.seed,
        ranked=True,
        daily_challenge_id=challenge.id,
        attempt_no=1,
    )
    run.score = 321
    engine.retire(run, "completed")
    store.save_run(run)

    entries = store.leaderboard(challenge.id, "simple")
    assert len(entries) == 1
    assert entries[0].trainer_name == "Nemona Prime"

    payload = CareerService(store=store, engine=engine).leaderboard(date(2026, 8, 27), "simple")
    assert payload["entries"][0]["trainer_name"] == "Nemona Prime"
    assert payload["entries"][0]["handle"].startswith("Trainer-")
