from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def service_for(tmp_path: Path) -> CareerService:
    return CareerService(store=CareerStore(tmp_path), engine=CareerEngine())


def new_run(service: CareerService) -> CareerRun:
    return CareerRun.from_dict(service.create_run("loan-preview-user", {
        "name": "Loan Preview Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": 4421,
    }))


def test_club_switch_previews_exact_loan_returns_and_preserves_return_history(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service)
    first_offer = service.preseason("loan-preview-user", run.id)["club_offers"][0]

    signed = CareerRun.from_dict(service.choose_club("loan-preview-user", run.id, {
        "expected_revision": run.revision,
        "offer_id": first_offer["id"],
    }))
    assert signed.contract is not None
    current_club = signed.contract.club_name
    current_club_id = signed.contract.club_id
    current_loans = [entry for entry in signed.pokemon if entry.ownership == "loan"]
    assert current_loans

    developed_loan = current_loans[0]
    developed_loan.matches = 11
    developed_loan.wins = 7
    developed_loan.stat_training = {"atk": 3, "spd": 2}
    developed_loan.career_health = 92
    developed_loan.training_wear = 8

    signed.contract.seasons_remaining = 0
    signed.season_number = 2
    if signed.season:
        signed.season.number = 2
    service.store.save_run(signed)

    offers = service.preseason("loan-preview-user", signed.id)["club_offers"]
    renewal = next(entry for entry in offers if entry["club_id"] == current_club_id)
    alternative = next(entry for entry in offers if entry["club_id"] != current_club_id)

    assert renewal["returning_loans"] == []
    expected_ids = [entry.id for entry in current_loans]
    assert [entry["id"] for entry in alternative["returning_loans"]] == expected_ids
    assert [entry["species"] for entry in alternative["returning_loans"]] == [entry.species for entry in current_loans]
    assert all(entry["club_id"] == current_club_id for entry in alternative["returning_loans"])
    assert all(entry["club_name"] == current_club for entry in alternative["returning_loans"])

    switched = CareerRun.from_dict(service.choose_club("loan-preview-user", signed.id, {
        "expected_revision": signed.revision,
        "offer_id": alternative["id"],
    }))

    assert not set(expected_ids) & {entry.id for entry in switched.pokemon}
    returned = next(entry for entry in reversed(switched.timeline) if entry.get("type") == "club.loans_returned")
    assert returned["club"] == current_club
    assert returned["club_id"] == current_club_id
    assert returned["pokemon_ids"] == sorted(expected_ids)
    assert [entry["id"] for entry in returned["pokemon"]] == expected_ids
    assert [entry["species"] for entry in returned["pokemon"]] == [entry.species for entry in current_loans]

    returned_developed = next(entry for entry in returned["pokemon"] if entry["id"] == developed_loan.id)
    assert returned_developed["matches"] == 11
    assert returned_developed["wins"] == 7
    assert returned_developed["stat_training"] == {"atk": 3, "spd": 2}
    assert returned_developed["career_health"] == 92
    assert returned_developed["training_wear"] == 8
