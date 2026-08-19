from pathlib import Path

from auto_ptu.career.catalogs import all_region_encounters
from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun
from auto_ptu.career.roster import capture_species
from auto_ptu.career.season_market import (
    capture_board,
    club_offers,
    permanent_pokemon_count,
    settle_sponsor,
    sponsor_offers,
)
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def service_for(tmp_path: Path) -> CareerService:
    return CareerService(store=CareerStore(tmp_path), engine=CareerEngine())


def new_run(service: CareerService, user: str = "market-user", seed: int = 4401) -> CareerRun:
    return CareerRun.from_dict(service.create_run(user, {
        "name": "Market Trainer",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": seed,
    }))


def test_preseason_markets_are_deterministic_and_offer_real_choice(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service)
    clone = CareerRun.from_dict(run.to_dict())

    assert club_offers(run) == club_offers(clone)
    assert sponsor_offers(run) == sponsor_offers(clone)
    assert capture_board(run) == capture_board(clone)
    assert len(club_offers(run)) == 3
    assert len(sponsor_offers(run)) == 3
    assert len(capture_board(run)) == 6
    assert all(entry["loan_species"] for entry in club_offers(run))


def test_signing_club_replaces_loans_without_adding_permanent_captures(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service, "club-user", 4402)
    permanent_before = permanent_pokemon_count(run)
    offers = service.preseason("club-user", run.id)["club_offers"]

    signed = CareerRun.from_dict(service.choose_club("club-user", run.id, {
        "expected_revision": run.revision,
        "offer_id": offers[1]["id"],
    }))
    loans = [entry for entry in signed.pokemon if entry.ownership == "loan"]

    assert signed.contract is not None
    assert signed.contract.club_name == offers[1]["club_name"]
    assert len(loans) == offers[1]["loan_slots"]
    assert permanent_pokemon_count(signed) == permanent_before
    assert all(entry.loan_club_id == signed.contract.club_id for entry in loans)


def test_sponsor_pays_upfront_and_bonus_only_when_objective_is_met(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service, "sponsor-user", 4403)
    offer = sponsor_offers(run)[0]
    money_before = run.money

    from auto_ptu.career.season_market import sign_sponsor
    sign_sponsor(run, offer["id"])
    assert run.money == money_before + offer["upfront"]

    result = settle_sponsor(run, wins=offer["target"])
    assert result is not None
    assert result["bonus"] == offer["bonus"]
    assert run.money == money_before + offer["upfront"] + offer["bonus"]
    assert settle_sponsor(run, wins=offer["target"] + 1) is None


def test_capture_board_still_works_with_six_owned_pokemon_and_overflows_to_pc(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service, "capture-user", 4404)
    run.build.pokeballs = 30
    species = [entry for entry in all_region_encounters(run.build.region) if entry.casefold() != run.build.starter.casefold()]
    for entry in species[:5]:
        capture_species(run, entry, source="test-fill")
    service.store.save_run(run)

    assert permanent_pokemon_count(run) >= 6
    assert len(run.active_roster) == 6
    before = permanent_pokemon_count(run)
    snapshot = service.preseason("capture-user", run.id)
    assert len(snapshot["capture_candidates"]) == 6

    captured = CareerRun.from_dict(service.capture("capture-user", run.id, {
        "expected_revision": run.revision,
        "candidate_id": snapshot["capture_candidates"][0]["id"],
    }))

    assert permanent_pokemon_count(captured) == before + 1
    newest = captured.pokemon[-1]
    assert newest.ownership == "owned"
    assert newest.id not in captured.active_roster
    assert newest.status == "pc"
