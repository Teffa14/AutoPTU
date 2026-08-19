from datetime import date

import pytest
from fastapi import HTTPException

from auto_ptu.api import career_api
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def test_browser_can_restore_owned_unranked_run_after_store_loss(tmp_path, monkeypatch):
    original = CareerService(store=CareerStore(tmp_path / "first"))
    created = original.create_run(
        "browser-user",
        {
            "name": "Ari Vale",
            "region": "kanto",
            "starter": "Bulbasaur",
            "classes": ["Ace Trainer"],
            "mode": "simple",
            "locale": "es",
            "trainer_sprite": "hilda",
            "seed": 41,
        },
    )

    fresh = CareerService(store=CareerStore(tmp_path / "cold-start"))
    monkeypatch.setattr(career_api, "SERVICE", fresh)

    restored = career_api.restore_unranked_run(
        {"run": created},
        authorization="",
        x_career_user="browser-user",
    )

    assert restored["id"] == created["id"]
    assert restored["ranked"] is False
    assert fresh.get_run("browser-user", created["id"])["build"]["name"] == "Ari Vale"
    assert any(
        entry.get("type") == "trainer.appearance_selected" and entry.get("sprite") == "hilda"
        for entry in restored["timeline"]
    )


def test_browser_restore_rejects_ranked_snapshot(tmp_path, monkeypatch):
    service = CareerService(store=CareerStore(tmp_path / "ranked"))
    monkeypatch.setattr(career_api, "SERVICE", service)
    created = service.create_run(
        "browser-user",
        {
            "name": "Ranked Copy",
            "region": "kanto",
            "starter": "Pikachu",
            "classes": ["Ace Trainer"],
            "mode": "simple",
            "locale": "es",
            "seed": 7,
        },
    )
    created["ranked"] = True

    with pytest.raises(HTTPException) as caught:
        career_api.restore_unranked_run(
            {"run": created},
            authorization="",
            x_career_user="browser-user",
        )

    assert caught.value.status_code == 403


def test_development_header_cannot_enter_ranked_daily(tmp_path, monkeypatch):
    monkeypatch.setattr(career_api, "SERVICE", CareerService(store=CareerStore(tmp_path / "daily")))

    with pytest.raises(HTTPException) as caught:
        career_api.create_daily_attempt(
            date(2026, 8, 19),
            {"mode": "simple", "trainer_name": "Local Tester"},
            authorization="",
            x_career_user="browser-user",
        )

    assert caught.value.status_code == 403
    assert "permanent account" in str(caught.value.detail).lower()
