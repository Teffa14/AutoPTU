from pathlib import Path

from auto_ptu.career.engine import CareerEngine
from auto_ptu.career.models import CareerRun
from auto_ptu.career.season_market import settle_sponsor, sign_sponsor, sponsor_offers
from auto_ptu.career.service import CareerService
from auto_ptu.career.store import CareerStore


def _new_run(tmp_path: Path, *, user: str = "sponsor-resilience", seed: int = 9917) -> CareerRun:
    service = CareerService(store=CareerStore(tmp_path), engine=CareerEngine())
    return CareerRun.from_dict(service.create_run(user, {
        "name": "Sponsor Resilience",
        "region": "kanto",
        "starter": "Rattata",
        "classes": ["Ace Trainer"],
        "seed": seed,
    }))


def test_settlement_survives_corrupt_persisted_target_bonus_and_season(tmp_path: Path) -> None:
    run = _new_run(tmp_path)
    offer = sponsor_offers(run)[0]
    sign_sponsor(run, offer["id"])
    signed = next(entry for entry in reversed(run.timeline) if entry.get("type") == "sponsor.signed")
    signed["target"] = "NaN"
    signed["bonus"] = float("inf")
    run.timeline.append({
        "type": "sponsor.signed",
        "season": "not-a-season",
        "name": "Corrupt Shadow Sponsor",
        "target": 1,
        "bonus": 999999,
    })
    money_before = run.money
    earnings_before = run.career_earnings
    reputation_before = run.reputation

    result = settle_sponsor(run, wins=999)

    assert result is not None
    assert result["type"] == "sponsor.failed"
    assert result["target"] == 0
    assert result["bonus"] == 0
    assert run.money == money_before
    assert run.career_earnings == earnings_before
    assert run.reputation == reputation_before


def test_sponsor_market_skips_corrupt_previous_outcome_seasons(tmp_path: Path) -> None:
    run = _new_run(tmp_path, user="sponsor-history-resilience", seed=9918)
    renewal_name = sponsor_offers(run)[0]["name"]
    run.season_number = 2
    if run.season:
        run.season.number = 2
    run.timeline.extend([
        {
            "type": "sponsor.completed",
            "season": 1,
            "name": renewal_name,
            "wins": 4,
            "target": 3,
            "bonus": 100,
        },
        {
            "type": "sponsor.completed",
            "season": float("inf"),
            "name": "Corrupt Future Sponsor",
            "wins": 99,
            "target": 1,
            "bonus": 999999,
        },
    ])

    offers = sponsor_offers(run)

    assert offers[0]["name"] == renewal_name
    assert offers[0]["renewal"] is True
    assert all(entry["name"] != "Corrupt Future Sponsor" for entry in offers)
