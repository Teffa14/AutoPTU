from __future__ import annotations

from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore
from auto_ptu.career.trainer_sprites import trainer_sprite_for_run


def _service(tmp_path):
    return CareerService(store=CareerStore(tmp_path / "career"))


def test_character_creation_persists_trainer_sprite_and_allows_first_club_choice(tmp_path) -> None:
    service = _service(tmp_path)

    catalog = service.catalog("es")
    sprite_ids = {entry["id"] for entry in catalog["trainer_sprites"]}
    assert "hilda" in sprite_ids

    created = service.create_run(
        "qa-player",
        {
            "name": "QA Trainer",
            "region": "kanto",
            "starter": "Bulbasaur",
            "classes": ["Ace Trainer"],
            "mode": "simple",
            "locale": "es",
            "trainer_sprite": "hilda",
            "seed": 1337,
        },
    )

    run = service.store.load_run(created["id"])
    assert run.build.name == "QA Trainer"
    assert run.build.starter == "Bulbasaur"
    assert run.build.classes == ["Ace Trainer"]
    assert trainer_sprite_for_run(run) == "hilda"
    assert any(
        event.get("type") == "trainer.appearance_selected" and event.get("trainer_sprite") == "hilda"
        for event in run.timeline
    )

    reloaded = service.get_run("qa-player", created["id"])
    appearance = next(event for event in reversed(reloaded["timeline"]) if event.get("type") == "trainer.appearance_selected")
    assert appearance["trainer_sprite"] == "hilda"

    preseason = service.preseason("qa-player", created["id"])
    signed = service.choose_club(
        "qa-player",
        created["id"],
        {
            "expected_revision": reloaded["revision"],
            "offer_id": preseason["club_offers"][0]["id"],
        },
    )
    assert signed["revision"] == reloaded["revision"] + 1
    assert any(event.get("type") == "club.offer_signed" for event in signed["timeline"])
    assert any(event.get("type") == "trainer.appearance_selected" and event.get("trainer_sprite") == "hilda" for event in signed["timeline"])


def test_invalid_trainer_sprite_falls_back_to_default(tmp_path) -> None:
    service = _service(tmp_path)
    created = service.create_run(
        "qa-player",
        {
            "name": "Fallback Trainer",
            "region": "kanto",
            "starter": "Bulbasaur",
            "classes": ["Ace Trainer"],
            "mode": "simple",
            "trainer_sprite": "not-a-real-sprite",
            "seed": 2026,
        },
    )

    run = service.store.load_run(created["id"])
    assert trainer_sprite_for_run(run) == "red"
