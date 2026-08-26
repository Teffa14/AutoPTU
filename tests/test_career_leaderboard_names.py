from __future__ import annotations

from types import SimpleNamespace

from auto_ptu.career.leaderboard_names import _local_leaderboard, trainer_display_name


def _run(*, player_id: str, name: object, score: int = 100):
    return SimpleNamespace(
        daily_challenge_id="daily-2026-08-25",
        mode="daily",
        status="retired",
        player_id=player_id,
        score=score,
        attempt_no=1,
        id=f"run-{player_id}",
        build=SimpleNamespace(name=name),
        achievements=[],
        updated_at="2026-08-25T00:00:00+00:00",
    )


def test_trainer_display_name_rejects_invisible_and_corrupt_values() -> None:
    assert trainer_display_name("   Mayra   Sol  ") == "Mayra Sol"
    assert trainer_display_name(None) == "Trainer"
    assert trainer_display_name("  null  ") == "Trainer"
    assert trainer_display_name("NaN", "Visible Handle") == "Visible Handle"


class _BrokenString:
    def __str__(self) -> str:
        raise RuntimeError("corrupt persisted display value")


def test_trainer_display_name_survives_broken_string_conversion() -> None:
    assert trainer_display_name(_BrokenString(), "Public Handle") == "Public Handle"


def test_trainer_display_name_strips_format_controls_and_bounds_layout_length() -> None:
    # Directional/zero-width format controls are invisible UI state and can make a
    # public leaderboard label render misleadingly. Extremely long persisted names
    # can also expand the leaderboard row far beyond its intended mobile layout.
    assert trainer_display_name("Red\u202e\u200b Campo") == "Red Campo"
    assert trainer_display_name("A" * 200) == "A" * 48


def test_local_leaderboard_always_exposes_a_visible_trainer_name() -> None:
    store = SimpleNamespace(
        list_runs=lambda: [
            _run(player_id="blank", name="   ", score=300),
            _run(player_id="none", name=None, score=200),
            _run(player_id="named", name="  Red   Campo  ", score=100),
        ]
    )

    entries = _local_leaderboard(store, "daily-2026-08-25", "daily")

    assert [entry.handle for entry in entries] == ["Trainer", "Trainer", "Red Campo"]
    assert all(entry.handle.strip() for entry in entries)
