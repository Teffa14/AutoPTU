from __future__ import annotations

import sys
from types import SimpleNamespace

from auto_ptu.career.postgres_store import PostgresCareerStore, _libpq_compatible_url


class _FakePsycopg:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def connect(self, database_url: str, **kwargs):
        self.calls.append((database_url, kwargs))
        return object()


def test_serverless_connection_disables_prepared_statements() -> None:
    store = PostgresCareerStore.__new__(PostgresCareerStore)
    store.database_url = "postgresql://pooler.example.invalid/db"
    store.psycopg = _FakePsycopg()

    store._connect(autocommit=False)

    assert store.psycopg.calls == [
        ("postgresql://pooler.example.invalid/db", {"prepare_threshold": None, "autocommit": False})
    ]


def test_pooled_url_precedes_non_pooling_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_URL", "postgresql://pooler.example.invalid/db")
    monkeypatch.setenv("POSTGRES_URL_NON_POOLING", "postgresql://direct.example.invalid/db")
    monkeypatch.setitem(sys.modules, "psycopg", _FakePsycopg())

    store = PostgresCareerStore()

    assert store.database_url == "postgresql://pooler.example.invalid/db"


def test_integration_hints_are_removed_but_libpq_options_remain() -> None:
    source = "postgresql://user:pass@pooler.example.invalid:6543/db?sslmode=require&supa=base-pooler.x&pgbouncer=true"

    assert _libpq_compatible_url(source) == (
        "postgresql://user:pass@pooler.example.invalid:6543/db?sslmode=require"
    )


def test_idempotency_record_references_featured_transcript_without_duplicating_it() -> None:
    captured = {}

    class Connection:
        def execute(self, _query, parameters):
            captured["parameters"] = parameters

    store = PostgresCareerStore.__new__(PostgresCareerStore)
    store.psycopg = SimpleNamespace(types=SimpleNamespace(json=SimpleNamespace(Jsonb=lambda value: value)))
    run_id = "12345678-1234-5678-1234-567812345678"
    response = {
        "run": {"revision": 2}, "battle_ids": [f"{run_id}-s1-m6"],
        "featured_battle": {"battle_id": f"{run_id}-s1-m6", "events": [{"large": "payload"}]},
    }

    store._execute_record_idempotency(Connection(), run_id, "season-1", response)

    stored = captured["parameters"][-1]
    assert "featured_battle" not in stored
    assert stored["featured_battle_id"] == f"{run_id}-s1-m6"
    assert response["featured_battle"]["events"]
