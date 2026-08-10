from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from auto_ptu.career.catalogs import REGIONS, compiled_decision_count
from auto_ptu.career.class_adapters import compile_class_adapters
from auto_ptu.career.content_compiler import validate_compiled_content
from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, BattleTranscript
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def fake_battle(spec: BattleSpec) -> BattleTranscript:
    winner = "career-home" if spec.seed % 3 else "career-away"
    return BattleTranscript(
        battle_id=spec.id,
        spec=spec,
        winner_team=winner,
        winner_label=spec.home_club if winner == "career-home" else spec.away_club,
        rounds=3,
        events=[{"type": "test", "seed": spec.seed}],
        initial_state={},
        final_state={"winner_team": winner},
        sha256=f"test-{spec.seed}",
    )


def test_catalog_covers_nine_regions_and_more_than_ten_thousand_decisions() -> None:
    assert len(REGIONS) == 9
    assert compiled_decision_count() >= 10_000
    assert all(region.underdogs for region in REGIONS.values())


def test_compiled_decisions_are_authored_and_mechanically_distinct() -> None:
    report = validate_compiled_content()
    assert report["family_count"] >= 200
    assert report["node_count"] >= 10_000
    assert report["mechanically_distinct"] == report["node_count"]


def test_every_ptu_class_and_feature_gets_a_career_adapter() -> None:
    payload = compile_class_adapters()
    assert payload["class_count"] == 69
    assert payload["feature_count"] == 709
    assert payload["unmapped"] == []


def test_career_starts_at_twelve_with_underdog_and_ten_pokeballs() -> None:
    run = CareerEngine(fake_battle).new_run(
        player_id="trainer-1",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=42,
    )
    assert run.age == 12
    assert run.league == "junior"
    assert run.build.pokeballs == 10
    assert run.roster == ["Rattata"]
    assert len(run.season.decision.options) == 3


def test_junior_is_age_gated_then_promotes_to_rookie() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-1",
        name="Ari",
        region="johto",
        starter="Sentret",
        classes=["Mentor"],
        seed=9,
    )
    for _ in range(4):
        run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert run.age == 16
    assert run.league == "rookie"


def test_advanced_mode_requires_three_season_decisions() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-advanced",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        mode="advanced",
        seed=77,
    )
    for expected in (1, 2):
        run, transcripts = engine.advance_season(run, option_id=run.season.decision.options[0].id)
        assert transcripts == []
        assert run.season.decisions_completed == expected
        assert run.season_number == 1
    run, transcripts = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    assert len(transcripts) == 6
    assert run.season_number == 2


def test_career_attributes_change_schedule_preparation_transparently() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-prepared",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=91,
    )
    run.development = 6
    run.scouting = 3
    run.finances = 4
    schedule = engine._schedule(run)
    assert all(spec.home_level_bonus == 3 for spec in schedule)
    assert all(spec.away_level_bonus == -1 for spec in schedule)


def test_active_legacy_run_records_version_migration_before_new_mechanics() -> None:
    engine = CareerEngine(fake_battle)
    run = engine.new_run(
        player_id="trainer-migration",
        name="Ari",
        region="kanto",
        starter="Rattata",
        classes=["Ace Trainer"],
        seed=102,
    )
    run.versions.career = "career-0.1.0"
    run, _ = engine.advance_season(run, option_id=run.season.decision.options[0].id)
    migration = next(entry for entry in run.timeline if entry["type"] == "career.version_migrated")
    assert migration == {
        "type": "career.version_migrated",
        "season": 1,
        "age": 12,
        "from": "career-0.1.0",
        "to": "career-0.2.0",
    }


def test_invalid_underdog_or_class_is_rejected() -> None:
    engine = CareerEngine(fake_battle)
    with pytest.raises(ValueError, match="eligible"):
        engine.new_run(player_id="x", name="X", region="kanto", starter="Mewtwo", classes=["Ace Trainer"])
    with pytest.raises(ValueError, match="Unknown PTU"):
        engine.new_run(player_id="x", name="X", region="kanto", starter="Rattata", classes=["Influencer"])


def test_decision_endpoint_is_revisioned_and_idempotent(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    created = service.create_run(
        "trainer-1",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 5},
    )
    run_id = created["id"]
    option_id = created["season"]["decision"]["options"][0]["id"]
    first = service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": option_id}, "season-1")
    second = service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": option_id}, "season-1")
    assert first == second
    assert first["run"]["revision"] == 1
    with pytest.raises(RuntimeError, match="Revision conflict"):
        service.decide("trainer-1", run_id, {"expected_revision": 0, "option_id": first["run"]["season"]["decision"]["options"][0]["id"]}, "season-2")


def test_ranked_daily_attempts_are_limited_to_three(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    from datetime import date

    day = date(2026, 8, 10)
    challenge = service.daily(day)
    starter = REGIONS[challenge["region"]].underdogs[0]
    payload = {"name": "Ari", "mode": "simple", "starter": starter, "classes": ["Ace Trainer"]}
    for expected in range(1, 4):
        result = service.create_daily_attempt("trainer-1", payload, day)
        assert result["attempt_no"] == expected
    with pytest.raises(PermissionError, match="three"):
        service.create_daily_attempt("trainer-1", payload, day)


def test_sharing_requires_retirement_and_is_explicit(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fake_battle))
    run = service.create_run(
        "trainer-1",
        {"name": "Ari", "region": "kanto", "starter": "Rattata", "classes": ["Ace Trainer"], "seed": 5},
    )
    with pytest.raises(ValueError, match="retired"):
        service.share("trainer-1", run["id"], {"include_replay": False})
    service.retire("trainer-1", run["id"], {"reason": "voluntary"})
    card_only = service.share("trainer-1", run["id"], {"include_replay": False})
    shared = service.share("trainer-1", run["id"], {"include_replay": True})
    assert shared["published"] is True
    assert shared["include_replay"] is True
    assert card_only["share_id"] != shared["share_id"]
    assert service.public_share(card_only["share_id"])["has_replay"] is False
    assert (tmp_path / "meta" / f"{shared['share_id']}.json").exists()
    public = service.public_share(shared["share_id"])
    assert public["summary"]["trainer"] == "Ari"
    assert "timeline" not in public
