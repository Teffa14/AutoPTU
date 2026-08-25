from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun
from auto_ptu.career.season_market import settle_sponsor, sign_sponsor, sponsor_offers
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def _run(tmp_path: Path) -> CareerRun:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine())
    return CareerRun.from_dict(service.create_run("renewal-context-user", {
        "name": "Renewal Context Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": 4420,
    }))


def test_completed_sponsor_renewal_exposes_verified_previous_result(tmp_path: Path) -> None:
    run = _run(tmp_path)
    signed = sponsor_offers(run)[0]
    sign_sponsor(run, signed["id"])
    result = settle_sponsor(run, wins=signed["target"] + 1)
    assert result is not None
    assert result["type"] == "sponsor.completed"

    run.season_number = 2
    if run.season:
        run.season.number = 2
    renewal = sponsor_offers(run)[0]

    assert renewal["renewal"] is True
    assert renewal["name"] == signed["name"]
    assert renewal["previous_result"] == {
        "status": "completed",
        "wins": signed["target"] + 1,
        "target": signed["target"],
    }
