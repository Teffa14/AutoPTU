from __future__ import annotations

from auto_ptu.csv_repository import PTUCsvRepository
from auto_ptu.rules.hooks import move_specials


def test_toxic_thread_alias_resolution() -> None:
    repo = PTUCsvRepository()
    record = repo.get_move("Toxic Thread")
    spec = move_specials._lookup_move_spec("Toxic Thread")
    print("Toxic Thread alias ->", {
        "csv_move": record.name if record else None,
        "spec_move": spec.name if spec else None,
    })
    assert record is not None
    assert spec is not None
    assert record.name == "Toxic Thread"
    assert spec.name == "Toxic Thread"
