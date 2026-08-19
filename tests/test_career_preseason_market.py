from pathlib import Path

import pytest

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


def expire_contract(service: CareerService, run: CareerRun) -> CareerRun:
    assert run.contract is not None
    run.contract.seasons_remaining = 0
    service.store.save_run(run)
    return run


def test_first_season_keeps_real_club_choice(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service)
    snapshot = service.preseason("market-user", run.id)

    assert snapshot["club_completed"] is False
    assert len(snapshot["club_offers"]) == 3


def test_preseason_markets_are_deterministic_and_offer_real_choice(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = expire_contract(service, new_run(service))
    clone = CareerRun.from_dict(run.to_dict())

    assert club_offers(run) == club_offers(clone)
    assert sponsor_offers(run) == sponsor_offers(clone)
    assert capture_board(run) == capture_board(clone)
    assert len(club_offers(run)) == 3
    assert len(sponsor_offers(run)) == 3
    assert len(capture_board(run)) == 6
    assert all(entry["loan_species"] for entry in club_offers(run))
    assert all(entry["gift_species"] for entry in club_offers(run))


def test_same_league_renewal_keeps_club_loans_and_adds_permanent_gift(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = expire_contract(service, new_run(service, "club-user", 4402))
    run.season_number = 2
    if run.season:
        run.season.number = 2
    current_club = run.contract.club_name if run.contract else ""
    service.store.save_run(run)
    offers = service.preseason("club-user", run.id)["club_offers"]
    renewal = next(entry for entry in offers if entry["club_name"] == current_club)

    first = CareerRun.from_dict(service.choose_club("club-user", run.id, {
        "expected_revision": run.revision,
        "offer_id": renewal["id"],
    }))
    assert first.contract is not None
    assert first.contract.club_name == current_club
    assert first.contract.seasons_remaining == 2
    assert permanent_pokemon_count(first) == permanent_pokemon_count(run) + 1
    assert any(entry.ownership == "owned" and entry.caught_species == renewal["gift_species"] for entry in first.pokemon)

    loan_ids = {entry.id for entry in first.pokemon if entry.ownership == "loan"}
    first.contract.seasons_remaining = 0
    first.season_number += 1
    if first.season:
        first.season.number = first.season_number
    service.store.save_run(first)
    second_offers = service.preseason("club-user", first.id)["club_offers"]
    second_renewal = next(entry for entry in second_offers if entry["club_name"] == current_club)
    renewed = CareerRun.from_dict(service.choose_club("club-user", first.id, {
        "expected_revision": first.revision,
        "offer_id": second_renewal["id"],
    }))

    assert loan_ids.issubset({entry.id for entry in renewed.pokemon if entry.ownership == "loan"})


def test_higher_leagues_offer_better_signing_gift_tiers(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = expire_contract(service, new_run(service, "gift-user", 4405))
    run.season_number = 2

    expected = {"junior": "common", "rookie": "rare", "regular": "very_rare", "elite": "epic"}
    for league, rarity in expected.items():
        run.league = league
        if run.contract:
            run.contract.league = league
        offers = club_offers(run)
        assert offers
        assert all(entry["gift_rarity"] == rarity for entry in offers)


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


def test_capture_outing_can_be_skipped_without_spending_balls(tmp_path: Path) -> None:
    service = service_for(tmp_path)
    run = new_run(service, "capture-skip-user", 4406)
    run.build.pokeballs = 0
    service.store.save_run(run)
    pokemon_before = [entry.id for entry in run.pokemon]

    skipped = CareerRun.from_dict(service.capture("capture-skip-user", run.id, {
        "expected_revision": run.revision,
        "candidate_id": "",
    }))

    assert skipped.build.pokeballs == 0
    assert [entry.id for entry in skipped.pokemon] == pokemon_before
    event = next(entry for entry in reversed(skipped.timeline) if entry.get("type") == "capture.board_used")
    assert event["skipped"] is True
    assert service.preseason("capture-skip-user", run.id)["capture_completed"] is True

    with pytest.raises(ValueError, match="already used"):
        service.capture("capture-skip-user", run.id, {
            "expected_revision": skipped.revision,
            "candidate_id": "",
        })
