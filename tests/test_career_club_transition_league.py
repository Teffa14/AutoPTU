from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def service_for(tmp_path: Path) -> CareerService:
    return CareerService(store=CareerStore(tmp_path), engine=CareerEngine())


def test_club_signing_event_records_authoritative_league(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = CareerRun.from_dict(service.create_run("league-transition-user", {
        "name": "League Step Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": 4512,
    }))
    assert run.contract is not None
    run.contract.seasons_remaining = 0
    run.season_number = 2
    run.league = "regular"
    if run.season:
        run.season.number = 2
        run.season.league = "regular"
    service.store.save_run(run)

    offer = service.preseason("league-transition-user", run.id)["club_offers"][0]
    signed = CareerRun.from_dict(service.choose_club("league-transition-user", run.id, {
        "expected_revision": run.revision,
        "offer_id": offer["id"],
    }))

    event = next(entry for entry in reversed(signed.timeline) if entry.get("type") == "club.offer_signed")
    assert event["league"] == "regular"
