import pytest

from auto_ptu.api.career_portable_api import execute_portable_action


def new_run() -> dict:
    return execute_portable_action({
        "action": "new",
        "payload": {
            "name": "Portable Trainer",
            "region": "kanto",
            "starter": "Bulbasaur",
            "classes": ["Ace Trainer"],
            "mode": "simple",
            "locale": "es",
            "trainer_sprite": "hilda",
            "seed": 8819,
        },
    })


def test_casual_career_actions_are_stateless_between_requests() -> None:
    run = new_run()
    assert run["ranked"] is False

    preseason = execute_portable_action({"action": "preseason", "run": run})
    club = preseason["club_offers"][0]
    signed = execute_portable_action({
        "action": "club",
        "run": run,
        "payload": {"expected_revision": run["revision"], "offer_id": club["id"]},
    })
    assert signed["revision"] == run["revision"] + 1
    assert signed["contract"]["club_name"] == club["club_name"]

    refreshed = execute_portable_action({"action": "preseason", "run": signed})
    assert refreshed["club_completed"] is True

    sponsor = execute_portable_action({
        "action": "sponsor",
        "run": signed,
        "payload": {"expected_revision": signed["revision"], "offer_id": ""},
    })
    assert sponsor["revision"] == signed["revision"] + 1

    capture_market = execute_portable_action({"action": "preseason", "run": sponsor})
    candidate = min(capture_market["capture_candidates"], key=lambda entry: entry["ball_cost"])
    captured = execute_portable_action({
        "action": "capture",
        "run": sponsor,
        "payload": {"expected_revision": sponsor["revision"], "candidate_id": candidate["id"]},
    })
    assert captured["revision"] == sponsor["revision"] + 1
    assert any(entry["species"] == candidate["species"] for entry in captured["pokemon"])


def test_portable_endpoint_rejects_ranked_snapshot() -> None:
    run = new_run()
    run["ranked"] = True
    with pytest.raises(PermissionError, match="Ranked careers"):
        execute_portable_action({"action": "preseason", "run": run})
