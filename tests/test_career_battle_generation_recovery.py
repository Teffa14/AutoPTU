from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import BattleSpec, CareerRun
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def failing_battle(_spec: BattleSpec):
    raise RuntimeError("synthetic battle engine failure")


def test_decide_restores_decision_state_when_featured_battle_generation_fails(tmp_path: Path) -> None:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(failing_battle))
    created = service.create_run(
        "battle-failure-user",
        {
            "name": "Iris",
            "region": "kanto",
            "starter": "Rattata",
            "classes": ["Ace Trainer"],
            "seed": 9281,
        },
    )
    before = CareerRun.from_dict(created)
    assert before.season is not None
    assert before.season.status == "decision"
    option_id = before.season.decision.options[0].id
    decision_id = before.season.decision.id

    response = service.decide(
        "battle-failure-user",
        before.id,
        {"expected_revision": before.revision, "option_id": option_id},
        "battle-failure-decision-1",
    )

    restored = CareerRun.from_dict(response["run"])
    assert response["battle_ids"] == []
    assert response["season_resolved"] is False
    assert response["battle_generation_error"] == {
        "code": "featured_battle_generation_failed",
        "retryable": True,
    }
    assert "featured_battle" not in response
    assert restored.revision == before.revision
    assert restored.season is not None
    assert restored.season.status == "decision"
    assert restored.season.decision.id == decision_id

    persisted = CareerRun.from_dict(service.get_run("battle-failure-user", before.id))
    assert persisted.revision == before.revision
    assert persisted.season is not None
    assert persisted.season.status == "decision"
    assert persisted.season.decision.id == decision_id


def test_retryable_battle_failure_does_not_poison_idempotency_key(tmp_path: Path) -> None:
    fallback_engine = CareerEngine()
    attempts = 0

    def fail_once(spec: BattleSpec):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("synthetic transient battle engine failure")
        return fallback_engine.battle_runner(spec)

    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine(fail_once))
    created = CareerRun.from_dict(
        service.create_run(
            "battle-retry-user",
            {
                "name": "Nemona",
                "region": "kanto",
                "starter": "Rattata",
                "classes": ["Ace Trainer"],
                "seed": 9282,
            },
        )
    )
    assert created.season is not None
    option_id = created.season.decision.options[0].id
    payload = {"expected_revision": created.revision, "option_id": option_id}
    key = "battle-retry-decision-1"

    first = service.decide("battle-retry-user", created.id, payload, key)
    assert first["battle_generation_error"]["retryable"] is True

    second = service.decide("battle-retry-user", created.id, payload, key)

    assert attempts == 2
    assert "battle_generation_error" not in second
    assert second["battle_ids"]
    assert "featured_battle" in second
    retried = CareerRun.from_dict(second["run"])
    assert retried.season is not None
    assert retried.season.status == "battle"
