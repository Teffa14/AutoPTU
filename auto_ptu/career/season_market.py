from __future__ import annotations

import hashlib
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


def preseason_snapshot(run: CareerRun) -> Dict[str, Any]:
    return {
        "season": run.season_number,
        "club_completed": _season_event(run, {"club.offer_signed"}),
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
    alternatives = [club for club in clubs if club != current]
    rng.shuffle(alternatives)
    selected = ([current] if current else []) + alternatives
    selected = selected[:3]
    if len(selected) < 3:
        selected.extend(club for club in clubs if club not in selected)
        selected = selected[:3]
    offers: List[Dict[str, Any]] = []
    for index, club in enumerate(selected):
        offer_rng = random.Random(_stable_seed(run.seed, run.season_number, club, "club-offer"))
        loan_slots = 1 + int(run.league in {"regular", "elite"})
        loan_species = _loan_species(run, offer_rng, loan_slots)
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
            "seasons": 1,
            "loan_slots": loan_slots,
            "loan_species": loan_species,
            "perk": {"stat": perk_stat, "amount": perk_amount, "label": perk_label},
            "renewal": bool(current and club == current),
        })
    return offers


def sign_club(run: CareerRun, offer_id: str) -> Dict[str, Any]:
    _require_preseason(run)
    if _season_event(run, {"club.offer_signed"}):
        raise ValueError("A club has already been selected for this season.")
    offer = next((entry for entry in club_offers(run) if entry["id"] == offer_id), None)
    if offer is None:
        raise ValueError("The selected club offer is no longer available.")
    returned = _return_loans(run)
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
    loans = [_create_loan(run, species, run.contract.club_id) for species in offer["loan_species"]]
    for pokemon in loans:
        run.pokemon.append(pokemon)
        if len(run.active_roster) < 6:
            run.active_roster.append(pokemon.id)
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
        "loan_species": [entry.species for entry in loans],
        "loan_ids": [entry.id for entry in loans],
        "returned_loan_ids": returned,
        "perk": perk,
        "label": f"Signed with {run.contract.club_name}; club loans: {', '.join(entry.species for entry in loans)}.",
    }
    run.timeline.append(event)
    return event


def sponsor_offers(run: CareerRun) -> List[Dict[str, Any]]:
    rng = random.Random(_stable_seed(run.seed, run.season_number, "sponsor-market"))
    candidates = list(_SPONSORS)
    rng.shuffle(candidates)
    matches = LEAGUES[run.league].matches
    base = 35 * LEAGUES[run.league].weight + max(0, run.reputation * 3)
    offers = []
    for index, (name, theme) in enumerate(candidates[:3]):
        target = min(matches, max(2, matches // 2 + (index % 2)))
        upfront = base + rng.randrange(0, 31, 10)
        bonus = upfront + 40 + target * 10
        offers.append({
            "id": f"sponsor:{_slug(name)}:{run.season_number}",
            "name": name,
            "theme": theme,
            "upfront": upfront,
            "bonus": bonus,
            "objective": "wins",
            "target": target,
            "description_es": f"Ganá al menos {target} partidos esta temporada.",
            "description_en": f"Win at least {target} matches this season.",
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
        (entry for entry in reversed(run.timeline) if entry.get("type") == "sponsor.signed" and int(entry.get("season") or 0) == run.season_number),
        None,
    )
    if signed is None or _season_event(run, {"sponsor.completed", "sponsor.failed"}):
        return None
    target = int(signed.get("target") or 0)
    success = wins >= target
    bonus = int(signed.get("bonus") or 0) if success else 0
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


def _loan_species(run: CareerRun, rng: random.Random, count: int) -> List[str]:
    selected: List[str] = []
    unavailable = {entry.species.casefold() for entry in run.pokemon if entry.ownership == "owned"}
    for index in range(count):
        rarity = "rare" if run.league in {"regular", "elite"} or index else "common"
        pool = list(encounter_pool(run.build.region, rarity))
        rng.shuffle(pool)
        species = next(
            (entry for entry in pool if entry.casefold() not in unavailable and entry not in selected),
            pool[0] if pool else run.build.starter,
        )
        selected.append(species)
        unavailable.add(species.casefold())
    return selected


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


def _return_loans(run: CareerRun) -> List[str]:
    loans = [entry for entry in run.pokemon if entry.ownership == "loan"]
    if not loans:
        return []
    loan_ids = {entry.id for entry in loans}
    run.pokemon = [entry for entry in run.pokemon if entry.id not in loan_ids]
    run.active_roster = [entry_id for entry_id in run.active_roster if entry_id not in loan_ids]
    run.roster = [entry.species for entry in run.pokemon]
    run.timeline.append({
        "type": "club.loans_returned",
        "season": run.season_number,
        "age": run.age,
        "pokemon_ids": sorted(loan_ids),
        "label": f"Returned {len(loan_ids)} club loan Pokémon.",
    })
    return sorted(loan_ids)


def _apply_perk(run: CareerRun, stat: str, amount: int) -> None:
    if stat == "health":
        run.health = min(100, run.health + amount)
    elif hasattr(run, stat):
        setattr(run, stat, int(getattr(run, stat)) + amount)


def _season_event(run: CareerRun, types: set[str]) -> bool:
    return any(
        entry.get("type") in types and int(entry.get("season") or 0) == run.season_number
        for entry in run.timeline
    )


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
