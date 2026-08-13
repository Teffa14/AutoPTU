from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Sequence

from .catalogs import LEAGUES, REGIONS
from .evolutions import next_evolution
from .models import BattleSpec, BattleTranscript, CareerPokemon, CareerRun
from .ptu_builds import identity_seed, is_legal_taught_move, persistent_identity

LEVEL_CAPS = {"junior": 20, "rookie": 35, "regular": 55, "elite": 100}


def initialize_roster(run: CareerRun, stable_seed: int) -> bool:
    """Upgrade legacy saves without granting unchosen Pokemon."""
    changed = False
    if not run.pokemon:
        existing = run.roster or [run.build.starter]
        for index, species in enumerate(existing):
            run.pokemon.append(_pokemon(run, str(species), index == 0, _base_level(run)))
        changed = True
    if not any(entry.is_partner for entry in run.pokemon):
        run.pokemon[0].is_partner = True
        changed = True

    cap = career_level_cap(run)
    for pokemon in run.pokemon:
        if pokemon.level > cap:
            pokemon.level = cap
            changed = True
        if _evolve_ready(run, pokemon):
            changed = True
        if _refresh_identity(run, pokemon):
            changed = True

    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner is not None and run.build.starter != partner.species:
        run.build.starter = partner.species
        changed = True

    valid_ids = {entry.id for entry in run.pokemon}
    active = [entry_id for entry_id in run.active_roster if entry_id in valid_ids]
    if not active:
        partner = next((entry.id for entry in run.pokemon if entry.is_partner), run.pokemon[0].id)
        active = [partner]
    if len(active) < min(6, len(run.pokemon)):
        active.extend(entry.id for entry in run.pokemon if entry.id not in active)
    active = active[:6]
    if active != run.active_roster:
        run.active_roster = active
        changed = True
    changed = _sync(run) or changed
    return changed


def capture_species(run: CareerRun, species: str, *, source: str, spend_ball: bool = True) -> CareerPokemon | None:
    canonical = next((entry for entry in REGIONS[run.build.region].underdogs if entry.lower() == species.lower()), None)
    if canonical is None:
        return None
    if spend_ball and run.build.pokeballs <= 0:
        return None
    pokemon = _pokemon(run, canonical, False, _base_level(run))
    run.pokemon.append(pokemon)
    if spend_ball:
        run.build.pokeballs -= 1
    if len(run.active_roster) < 6:
        run.active_roster.append(pokemon.id)
    _capture_event(run, [pokemon], source)
    _sync(run)
    return pokemon


def grant_partner_levels(run: CareerRun, levels: int, *, source: str) -> List[dict]:
    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner is None:
        return []
    previous_level = partner.level
    partner.level = min(career_level_cap(run), partner.level + max(0, int(levels)))
    gained = partner.level - previous_level
    if gained <= 0:
        return []
    _refresh_identity(run, partner)
    run.timeline.append({
        "type": "pokemon.trained",
        "season": run.season_number,
        "age": run.age,
        "pokemon_id": partner.id,
        "species": partner.species,
        "levels": gained,
        "source": source,
        "label": f"{partner.species} gained {gained} levels.",
    })
    evolutions = _evolve_ready(run, partner)
    _sync(run)
    return evolutions


def teach_partner_move(run: CareerRun, move: str, *, source: str) -> bool:
    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    canonical = str(move).strip()
    if (
        partner is None
        or not canonical
        or canonical in partner.taught_moves
        or not is_legal_taught_move(partner.species, canonical)
    ):
        return False
    partner.taught_moves.append(canonical)
    run.timeline.append({
        "type": "pokemon.move_learned",
        "season": run.season_number,
        "age": run.age,
        "pokemon_id": partner.id,
        "species": partner.species,
        "move": canonical,
        "source": source,
        "label": f"{partner.species} learned {canonical}.",
    })
    return True


def set_active_roster(run: CareerRun, pokemon_ids: Sequence[str]) -> None:
    requested = [str(value) for value in pokemon_ids]
    required = min(6, len(run.pokemon))
    if len(requested) != required:
        raise ValueError(f"The active team must contain exactly {required} Pokémon.")
    if len(set(requested)) != len(requested):
        raise ValueError("The active team cannot contain the same Pokémon twice.")
    owned = {entry.id for entry in run.pokemon}
    if any(entry_id not in owned for entry_id in requested):
        raise ValueError("The active team contains a Pokémon that is not in this career.")
    run.active_roster = requested
    _sync(run)


def active_pokemon(run: CareerRun) -> List[CareerPokemon]:
    by_id = {entry.id: entry for entry in run.pokemon}
    selected = [by_id[entry_id] for entry_id in run.active_roster if entry_id in by_id]
    return selected or run.pokemon[:1]


def progress_after_season(
    run: CareerRun,
    specs: Iterable[BattleSpec],
    transcripts: Iterable[BattleTranscript],
) -> dict:
    appearances = Counter(
        pokemon_id
        for spec in specs
        for pokemon_id in (spec.home_pokemon_ids or ([spec.home_pokemon_id] if spec.home_pokemon_id else []))
    )
    wins = Counter(
        pokemon_id
        for transcript in transcripts
        if transcript.winner_team == "career-home" and transcript.spec.home_pokemon_id
        for pokemon_id in (transcript.spec.home_pokemon_ids or [transcript.spec.home_pokemon_id])
    )
    used: List[str] = []
    evolutions: List[dict] = []
    active_ids = set(run.active_roster)
    for pokemon in run.pokemon:
        played = appearances[pokemon.id]
        pokemon.matches += played
        pokemon.wins += wins[pokemon.id]
        if played:
            # A full team now participates in every fixture. Progress is capped
            # per season so a six-match calendar develops a partner without
            # jumping dozens of levels at once.
            pokemon.level += 6 + min(2, played // 3)
            used.append(pokemon.species)
        elif pokemon.id in active_ids:
            pokemon.level += 3
        else:
            pokemon.level += 1
        pokemon.level = min(career_level_cap(run), pokemon.level)
        evolutions.extend(_evolve_ready(run, pokemon))
        _refresh_identity(run, pokemon)
    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner:
        run.build.starter = partner.species
    _sync(run)
    return {"pokemon_used": used, "evolutions": evolutions}


def _pokemon(run: CareerRun, species: str, partner: bool, level: int) -> CareerPokemon:
    pokemon_id = f"{run.id}-p{len(run.pokemon) + 1:03d}"
    nature, abilities = persistent_identity(species, level, identity_seed(run.seed, pokemon_id))
    return CareerPokemon(
        id=pokemon_id,
        species=species,
        caught_species=species,
        level=level,
        acquired_season=run.season_number,
        acquired_age=run.age,
        capture_region=run.build.region,
        is_partner=partner,
        status="active" if len(run.pokemon) < 6 else "pc",
        nature=nature,
        abilities=abilities,
    )


def _base_level(run: CareerRun) -> int:
    return min(career_level_cap(run), LEAGUES[run.league].min_level + min(15, max(0, run.season_number - 1)))


def career_level_cap(run: CareerRun) -> int:
    return LEVEL_CAPS.get(run.league, 100)


def _capture_event(run: CareerRun, captured: Sequence[CareerPokemon], source: str) -> None:
    if not captured:
        return
    names = [entry.species for entry in captured]
    run.timeline.append({
        "type": "pokemon.captured",
        "season": run.season_number,
        "age": run.age,
        "source": source,
        "species": names,
        "pokemon_ids": [entry.id for entry in captured],
        "label": f"Captured {', '.join(names)}. {run.build.pokeballs} Poké Balls remain.",
    })


def _evolve_ready(run: CareerRun, pokemon: CareerPokemon) -> List[dict]:
    evolutions: List[dict] = []
    while True:
        target = next_evolution(
            pokemon.species,
            seed=identity_seed(run.seed, pokemon.id),
            region=run.build.region,
            level=pokemon.level,
        )
        if target is None:
            break
        previous = pokemon.species
        evolved, threshold = target
        pokemon.species = evolved
        _refresh_identity(run, pokemon, replace_abilities=True)
        event = {
            "from": previous,
            "to": evolved,
            "level": pokemon.level,
            "threshold": threshold,
            "season": run.season_number,
            "age": run.age,
            "pokemon_id": pokemon.id,
        }
        pokemon.evolution_history.append(event)
        evolutions.append(event)
        run.timeline.append({
            "type": "pokemon.evolved",
            "label": f"{previous} evolved into {evolved} at level {pokemon.level}.",
            **event,
        })
    return evolutions


def _refresh_identity(run: CareerRun, pokemon: CareerPokemon, *, replace_abilities: bool = False) -> bool:
    previous = (pokemon.nature, tuple(pokemon.abilities))
    nature, abilities = persistent_identity(
        pokemon.species,
        pokemon.level,
        identity_seed(run.seed, pokemon.id),
        nature=pokemon.nature,
        existing_abilities=() if replace_abilities else pokemon.abilities,
    )
    pokemon.nature = nature
    pokemon.abilities = abilities
    return previous != (pokemon.nature, tuple(pokemon.abilities))


def _sync(run: CareerRun) -> bool:
    changed = False
    active = set(run.active_roster)
    for pokemon in run.pokemon:
        status = "active" if pokemon.id in active else "pc"
        if pokemon.status != status:
            pokemon.status = status
            changed = True
    roster = [entry.species for entry in run.pokemon]
    if roster != run.roster:
        run.roster = roster
        changed = True
    return changed
