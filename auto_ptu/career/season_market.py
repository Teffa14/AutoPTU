from __future__ import annotations

import hashlib
import math
import random
from typing import Any, Dict, List

from .catalogs import LEAGUES, REGIONS, choose_encounter_rarity, encounter_pool
from .models import CareerPokemon, CareerRun, ClubContract
from .ptu_builds import identity_seed, persistent_identity
from .roster import active_pokemon, capture_species, career_level_cap


_SPONSORS = (
    ("Rotom Broadcast", "media"),
    ("Porygon Systems", "analysis"),
    ("Helios Performance", "training"),
    ("Mistral Outfitters", "travel"),
    ("Evergreen Care", "health"),
    ("Victory Circuit", "competition"),
    ("Northstar Labs", "research"),
    ("Premier Ball Co.", "equipment"),
)

_CLUB_PERKS = (
    ("development", 1, "Academy support"),
    ("scouting", 1, "Regional scouting network"),
    ("reputation", 1, "Media department"),
    ("health", 3, "Medical staff"),
)

_LEAGUE_GIFT_RARITY = {
    "junior": "common",
    "rookie": "rare",
    "regular": "very_rare",
    "elite": "epic",
}

_RARITY_FALLBACKS = {
    "epic": ("epic", "very_rare", "rare", "common"),
    "very_rare": ("very_rare", "rare", "common"),
    "rare": ("rare", "common"),
    "common": ("common",),
}


def preseason_snapshot(run: CareerRun) -> Dict[str, Any]:
    club_completed = _season_event(run, {"club.offer_signed"}) or _contract_covers_current_season(run)
    return {
        "season": run.season_number,
        "club_completed": club_completed,
        "sponsor_completed": _season_event(run, {"sponsor.signed", "sponsor.declined"}),
        "capture_completed": _season_event(run, {"capture.board_used"}),
        "club_offers": club_offers(run),
        "sponsor_offers": sponsor_offers(run),
        "capture_candidates": capture_board(run),
    }


def club_offers(run: CareerRun) -> List[Dict[str, Any]]:
    region = REGIONS[run.build.region]
    clubs = list(region.clubs)
    rng = random.Random(_stable_seed(run.seed, run.season_number, "club-market"))
    current = run.contract.club_name if run.contract else ""
    renewal_allowed = bool(current and run.season_number > 1 and _same_league_as_last_season(run))
    alternatives = [club for club in clubs if club != current]
    rng.shuffle(alternatives)
    selected = ([current] if renewal_allowed else []) + alternatives
    selected = selected[:3]
    if len(selected) < 3:
        selected.extend(club for club in clubs if club not in selected and (renewal_allowed or club != current))
        selected = selected[:3]
    offers: List[Dict[str, Any]] = []
    for club in selected:
        offer_rng = random.Random(_stable_seed(run.seed, run.season_number, club, "club-offer"))
        renewal = bool(renewal_allowed and club == current)
        loan_slots = 1 + int(run.league in {"regular", "elite"})
        existing_loans = [
            entry.species
            for entry in run.pokemon
            if entry.ownership == "loan" and entry.loan_club_id == _slug(club)
        ] if renewal else []
        retained_loans = existing_loans[:loan_slots]
        loan_species = retained_loans + _loan_species(
            run,
            offer_rng,
            max(0, loan_slots - len(retained_loans)),
            excluded={entry.casefold() for entry in retained_loans},
        )
        gift_target_rarity = _LEAGUE_GIFT_RARITY.get(run.league, "common")
        gift_species, gift_rarity = _gift_species(
            run,
            offer_rng,
            gift_target_rarity,
            excluded={entry.casefold() for entry in loan_species},
        )
        perk_stat, perk_amount, perk_label = _CLUB_PERKS[_stable_seed(club, run.season_number) % len(_CLUB_PERKS)]
        salary_base = 120 * LEAGUES[run.league].weight + max(0, run.reputation * 5)
        salary = max(60, salary_base + offer_rng.choice((-20, 0, 20, 40)))
        offers.append({
            "id": f"club:{_slug(club)}:{run.season_number}",
            "club_id": _slug(club),
            "club_name": club,
            "region": run.build.region,
            "league": run.league,
            "salary": salary,
            "seasons": 2 if renewal else 1,
            "loan_slots": loan_slots,
            "loan_species": loan_species,
            "returning_loans": [] if renewal else _loan_return_preview(run),
            "gift_species": gift_species,
            "gift_rarity": gift_rarity,
            "gift_target_rarity": gift_target_rarity,
            "perk": {"stat": perk_stat, "amount": perk_amount, "label": perk_label},
            "renewal": renewal,
            "retains_current_team": renewal,
        })
    return offers


def sign_club(run: CareerRun, offer_id: str) -> Dict[str, Any]:
    _require_preseason(run)
    if _season_event(run, {"club.offer_signed"}) or _contract_covers_current_season(run):
        raise ValueError("A club has already been selected for this season.")
    offer = next((entry for entry in club_offers(run) if entry["id"] == offer_id), None)
    if offer is None:
        raise ValueError("The selected club offer is no longer available.")

    renewal = bool(offer.get("renewal")) and run.contract is not None and run.contract.club_id == str(offer["club_id"])
    returned = [] if renewal else _return_loans(run)
    existing_loan_species = {
        entry.species.casefold()
        for entry in run.pokemon
        if entry.ownership == "loan" and entry.loan_club_id == str(offer["club_id"])
    }
    if renewal:
        for pokemon in run.pokemon:
            if pokemon.ownership == "loan" and pokemon.loan_club_id == str(offer["club_id"]):
                pokemon.loan_expires_season = run.season_number + int(offer["seasons"]) - 1

    run.contract = ClubContract(
        club_id=str(offer["club_id"]),
        club_name=str(offer["club_name"]),
        region=run.build.region,
        league=run.league,
        salary=int(offer["salary"]),
        seasons_remaining=int(offer["seasons"]),
        loan_slots=int(offer["loan_slots"]),
    )
    perk = dict(offer["perk"])
    _apply_perk(run, str(perk["stat"]), int(perk["amount"]))

    loans = [
        _create_loan(run, species, run.contract.club_id)
        for species in offer["loan_species"]
        if species.casefold() not in existing_loan_species
    ]
    for pokemon in loans:
        pokemon.loan_expires_season = run.season_number + run.contract.seasons_remaining - 1
        run.pokemon.append(pokemon)
        if len(run.active_roster) < 6:
            run.active_roster.append(pokemon.id)

    gift_species = str(offer.get("gift_species") or "")
    gift = capture_species(run, gift_species, source="club_signing_gift", spend_ball=False) if gift_species else None
    run.roster = [entry.species for entry in run.pokemon]
    if run.season:
        run.season.club_name = run.contract.club_name
    event = {
        "type": "club.offer_signed",
        "season": run.season_number,
        "age": run.age,
        "club": run.contract.club_name,
        "club_id": run.contract.club_id,
        "salary": run.contract.salary,
        "seasons": run.contract.seasons_remaining,
        "renewal": renewal,
        "retained_team": renewal,
        "loan_species": [entry.species for entry in run.pokemon if entry.ownership == "loan" and entry.loan_club_id == run.contract.club_id],
        "loan_ids": [entry.id for entry in run.pokemon if entry.ownership == "loan" and entry.loan_club_id == run.contract.club_id],
        "returned_loan_ids": returned,
        "gift_species": gift.species if gift else "",
        "gift_pokemon_id": gift.id if gift else "",
        "gift_rarity": offer.get("gift_rarity"),
        "gift_target_rarity": offer.get("gift_target_rarity"),
        "perk": perk,
        "label": (
            f"Extended with {run.contract.club_name} for {run.contract.seasons_remaining} seasons; current club squad retained."
            if renewal
            else f"Signed with {run.contract.club_name} for {run.contract.seasons_remaining} season; club loans registered."
        ) + (f" Signing gift: {gift.species}." if gift else ""),
    }
    run.timeline.append(event)
    return event


def sponsor_offers(run: CareerRun) -> List[Dict[str, Any]]:
    rng = random.Random(_stable_seed(run.seed, run.season_number, "sponsor-market"))
    candidates = list(_SPONSORS)
    rng.shuffle(candidates)
    previous_outcome = _previous_sponsor_outcome(run)
    renewal_name = ""
    blocked_name = ""
    if previous_outcome is not None:
        previous_name = str(previous_outcome.get("name") or "").strip()
        if previous_outcome.get("type") == "sponsor.completed":
            renewal_name = previous_name
        elif previous_outcome.get("type") == "sponsor.failed":
            blocked_name = previous_name
    if blocked_name:
        candidates = [entry for entry in candidates if entry[0] != blocked_name]
    if renewal_name:
        renewal = next((entry for entry in _SPONSORS if entry[0] == renewal_name), None)
        if renewal is not None:
            candidates = [renewal] + [entry for entry in candidates if entry[0] != renewal_name]

    matches = LEAGUES[run.league].matches
    base = 35 * LEAGUES[run.league].weight + max(0, run.reputation * 3)
    offers = []
    for index, (name, theme) in enumerate(candidates[:3]):
        target = min(matches, max(2, matches // 2 + (index % 2)))
        upfront = base + rng.randrange(0, 31, 10)
        bonus = upfront + 40 + target * 10
        is_renewal = bool(renewal_name and name == renewal_name)
        description_es = f"Ganá al menos {target} partidos esta temporada."
        description_en = f"Win at least {target} matches this season."
        if is_renewal:
            description_es = f"Renovación tras cumplir el objetivo anterior. {description_es}"
            description_en = f"Renewal after completing the previous objective. {description_en}"
        offers.append({
            "id": f"sponsor:{_slug(name)}:{run.season_number}",
            "name": name,
            "theme": theme,
            "upfront": upfront,
            "bonus": bonus,
            "objective": "wins",
            "target": target,
            "renewal": is_renewal,
            "description_es": description_es,
            "description_en": description_en,
        })
    return offers


def sign_sponsor(run: CareerRun, offer_id: str) -> Dict[str, Any]:
    _require_preseason(run)
    if _season_event(run, {"sponsor.signed", "sponsor.declined"}):
        raise ValueError("The sponsor decision is already closed for this season.")
    if not offer_id:
        event = {
            "type": "sponsor.declined", "season": run.season_number, "age": run.age,
            "label": "The trainer chose to continue the season without a sponsor.",
        }
        run.timeline.append(event)
        return event
    offer = next((entry for entry in sponsor_offers(run) if entry["id"] == offer_id), None)
    if offer is None:
        raise ValueError("The selected sponsor offer is no longer available.")
    upfront = int(offer["upfront"])
    run.money += upfront
    run.career_earnings += upfront
    event = {
        "type": "sponsor.signed",
        "season": run.season_number,
        "age": run.age,
        **offer,
        "label": f"Signed a one-season sponsorship with {offer['name']} for ₽ {upfront} up front.",
    }
    run.timeline.append(event)
    return event


def settle_sponsor(run: CareerRun, *, wins: int) -> Dict[str, Any] | None:
    signed = next(
        (
            entry
            for entry in reversed(run.timeline)
            if entry.get("type") == "sponsor.signed" and _event_season(entry) == run.season_number
        ),
        None,
    )
    if signed is None or _season_event(run, {"sponsor.completed", "sponsor.failed"}):
        return None
    target_value = _safe_nonnegative_int(signed.get("target"))
    target = target_value if target_value is not None else 0
    success = bool(target_value and wins >= target_value)
    bonus_value = _safe_nonnegative_int(signed.get("bonus"))
    bonus = bonus_value if success and bonus_value is not None else 0
    if bonus:
        run.money += bonus
        run.career_earnings += bonus
        run.reputation += 1
    event = {
        "type": "sponsor.completed" if success else "sponsor.failed",
        "season": run.season_number,
        "age": run.age,
        "name": signed.get("name"),
        "wins": wins,
        "target": target,
        "bonus": bonus,
        "label": f"Sponsor objective {'completed' if success else 'missed'}: {wins}/{target} wins.",
    }
    run.timeline.append(event)
    return event


def capture_board(run: CareerRun) -> List[Dict[str, Any]]:
    rng = random.Random(_stable_seed(run.seed, run.season_number, "capture-board"))
    owned = {entry.caught_species.casefold() for entry in run.pokemon if entry.ownership == "owned"}
    recent = {
        str(species).casefold()
        for event in run.timeline[-50:]
        if event.get("type") == "pokemon.captured"
        for species in event.get("species", [])
    }
    selected: List[Dict[str, Any]] = []
    used: set[str] = set()
    minimums = ("common", "common", "rare", "rare", "very_rare", "very_rare")
    scouting_boost = max(0, run.scouting) + max(0, run.pokedex_level)
    for index, minimum in enumerate(minimums):
        rarity = choose_encounter_rarity(
            run.build.region,
            run.league,
            rng,
            minimum=minimum if index < 4 or scouting_boost >= 2 else "rare",
            pokedex_level=max(0, run.pokedex_level + max(0, run.scouting) // 3),
        )
        pool = list(encounter_pool(run.build.region, rarity))
        rng.shuffle(pool)
        candidate = next(
            (species for species in pool if species.casefold() not in owned | recent | used),
            next((species for species in pool if species.casefold() not in used), pool[0] if pool else ""),
        )
        if not candidate:
            continue
        used.add(candidate.casefold())
        selected.append({
            "id": f"capture:{run.season_number}:{index}:{_slug(candidate)}",
            "species": candidate,
            "rarity": rarity,
            "ball_cost": 1,
        })
    return selected


def capture_candidate(run: CareerRun, candidate_id: str) -> Dict[str, Any]:
    _require_preseason(run)
    if _season_event(run, {"capture.board_used"}):
        raise ValueError("The scouting capture opportunity was already used this season.")
    if not str(candidate_id).strip():
        event = {
            "type": "capture.board_used",
            "season": run.season_number,
            "age": run.age,
            "skipped": True,
            "pokemon_id": "",
            "species": "",
            "rarity": "",
            "sent_to_pc": False,
            "label": "The trainer kept their Poké Balls and skipped this season's scouting capture.",
        }
        run.timeline.append(event)
        return event
    candidate = next((entry for entry in capture_board(run) if entry["id"] == candidate_id), None)
    if candidate is None:
        raise ValueError("The selected Pokémon is no longer in this season's scouting board.")
    if run.build.pokeballs < int(candidate["ball_cost"]):
        raise ValueError("There are not enough Poké Balls for this capture.")
    pokemon = capture_species(run, str(candidate["species"]), source="season_capture_board", spend_ball=True)
    if pokemon is None:
        raise ValueError("The selected Pokémon could not be captured.")
    event = {
        "type": "capture.board_used",
        "season": run.season_number,
        "age": run.age,
        "skipped": False,
        "pokemon_id": pokemon.id,
        "species": pokemon.species,
        "rarity": candidate["rarity"],
        "sent_to_pc": pokemon.id not in run.active_roster,
        "label": f"Scouting opportunity used to capture {pokemon.species}.",
    }
    run.timeline.append(event)
    return event


def permanent_pokemon_count(run: CareerRun) -> int:
    return sum(1 for entry in run.pokemon if entry.ownership == "owned")


def _loan_species(run: CareerRun, rng: random.Random, count: int, *, excluded: set[str] | None = None) -> List[str]:
    selected: List[str] = []
    unavailable = {entry.species.casefold() for entry in run.pokemon if entry.ownership == "owned"}
    unavailable.update(excluded or set())
    for index in range(count):
        rarity = "rare" if run.league in {"regular", "elite"} or index else "common"
        pool = list(encounter_pool(run.build.region, rarity))
        rng.shuffle(pool)
        species = next(
            (entry for entry in pool if entry.casefold() not in unavailable and entry.casefold() not in {value.casefold() for value in selected}),
            pool[0] if pool else run.build.starter,
        )
        selected.append(species)
        unavailable.add(species.casefold())
    return selected


def _gift_species(
    run: CareerRun,
    rng: random.Random,
    rarity: str,
    *,
    excluded: set[str] | None = None,
) -> tuple[str, str]:
    unavailable = {entry.caught_species.casefold() for entry in run.pokemon if entry.ownership == "owned"}
    unavailable.update(excluded or set())
    for candidate_rarity in _RARITY_FALLBACKS.get(rarity, (rarity, "common")):
        pool = list(encounter_pool(run.build.region, candidate_rarity))
        rng.shuffle(pool)
        species = next((entry for entry in pool if entry.casefold() not in unavailable), "")
        if species:
            return species, candidate_rarity
    return "", ""


def _create_loan(run: CareerRun, species: str, club_id: str) -> CareerPokemon:
    loan_id = f"{run.id}-loan-s{run.season_number}-{club_id}-{_slug(species)}"
    lineup = active_pokemon(run)
    level = min(career_level_cap(run), max((entry.level for entry in lineup), default=LEAGUES[run.league].min_level))
    nature, abilities = persistent_identity(species, level, identity_seed(run.seed, loan_id))
    return CareerPokemon(
        id=loan_id,
        species=species,
        caught_species=species,
        level=level,
        acquired_season=run.season_number,
        acquired_age=run.age,
        capture_region=run.build.region,
        status="pc",
        nature=nature,
        abilities=abilities,
        ownership="loan",
        loan_club_id=club_id,
        loan_expires_season=run.season_number,
    )


def _loan_return_preview(run: CareerRun) -> List[Dict[str, Any]]:
    active = set(run.active_roster)
    current_club_id = run.contract.club_id if run.contract else ""
    current_club_name = run.contract.club_name if run.contract else ""
    return [
        {
            "id": entry.id,
            "species": entry.species,
            "club_id": entry.loan_club_id,
            "club_name": current_club_name if entry.loan_club_id == current_club_id else entry.loan_club_id,
            "active": entry.id in active,
        }
        for entry in run.pokemon
        if entry.ownership == "loan"
    ]


def _return_loans(run: CareerRun) -> List[str]:
    loans = [entry for entry in run.pokemon if entry.ownership == "loan"]
    if not loans:
        return []
    returned_pokemon = _loan_return_preview(run)
    loan_ids = {entry.id for entry in loans}
    run.pokemon = [entry for entry in run.pokemon if entry.id not in loan_ids]
    run.active_roster = [entry_id for entry_id in run.active_roster if entry_id not in loan_ids]
    run.roster = [entry.species for entry in run.pokemon]
    run.timeline.append({
        "type": "club.loans_returned",
        "season": run.season_number,
        "age": run.age,
        "club": run.contract.club_name if run.contract else "",
        "club_id": run.contract.club_id if run.contract else "",
        "pokemon_ids": sorted(loan_ids),
        "pokemon": returned_pokemon,
        "label": f"Returned {len(loan_ids)} club loan Pokémon.",
    })
    return sorted(loan_ids)


def _apply_perk(run: CareerRun, stat: str, amount: int) -> None:
    if stat == "health":
        run.health = min(100, run.health + amount)
    elif hasattr(run, stat):
        setattr(run, stat, int(getattr(run, stat)) + amount)


def _contract_covers_current_season(run: CareerRun) -> bool:
    # The default club on a brand-new career is only a placeholder until the
    # player makes the first club choice. From season two onward, a genuinely
    # multi-season signed deal carries forward without forcing another market.
    return bool(
        run.season_number > 1
        and run.contract
        and run.contract.seasons_remaining > 0
        and _same_league_as_last_season(run)
    )


def _same_league_as_last_season(run: CareerRun) -> bool:
    previous = next(
        (entry for entry in reversed(run.timeline) if entry.get("type") == "season.completed"),
        None,
    )
    if previous is None:
        return True
    return str(previous.get("league") or run.league) == run.league


def _previous_sponsor_outcome(run: CareerRun) -> Dict[str, Any] | None:
    return next(
        (
            entry
            for entry in reversed(run.timeline)
            if entry.get("type") in {"sponsor.completed", "sponsor.failed"}
            and (_event_season(entry) is not None and _event_season(entry) < run.season_number)
        ),
        None,
    )


def _season_event(run: CareerRun, types: set[str]) -> bool:
    return any(
        entry.get("type") in types and _event_season(entry) == run.season_number
        for entry in run.timeline
    )


def _safe_nonnegative_int(value: Any) -> int | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return int(parsed)


def _event_season(entry: Dict[str, Any]) -> int | None:
    return _safe_nonnegative_int(entry.get("season"))


def _require_preseason(run: CareerRun) -> None:
    if run.status != "active" or run.season is None or run.season.status != "decision":
        raise ValueError("Preseason choices are only available before the schedule is locked.")
    if run.season.decisions_completed > 0:
        raise ValueError("Preseason choices close after the first career decision is committed.")


def _stable_seed(*parts: object) -> int:
    payload = ":".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _slug(value: str) -> str:
    return "-".join(part for part in "".join(char.lower() if char.isalnum() else " " for char in value).split() if part)