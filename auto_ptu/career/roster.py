from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Sequence

from .catalogs import LEAGUES, REGIONS, all_region_encounters
from .evolutions import next_evolution
from .models import BattleSpec, BattleTranscript, CareerPokemon, CareerRun
from .ptu_builds import identity_seed, is_legal_taught_move, persistent_identity

LEVEL_CAPS = {"junior": 20, "rookie": 35, "regular": 55, "elite": 100}
TRAINING_KIT_WEAR = 12
BASE_ACTIVE_SEASON_WEAR = 2
VETERAN_WEAR_START_SEASON = 9
PC_AGING_START_SEASON = 12


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
        if pokemon.status == "retired" or pokemon.career_health <= 0:
            if pokemon.status != "retired":
                pokemon.status = "retired"
                changed = True
            pokemon.career_health = 0
            continue
        if _evolve_ready(run, pokemon):
            changed = True
        if _refresh_identity(run, pokemon):
            changed = True

    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner is not None and run.build.starter != partner.species:
        run.build.starter = partner.species
        changed = True

    eligible_ids = {entry.id for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0}
    active = [entry_id for entry_id in run.active_roster if entry_id in eligible_ids]
    if not active and eligible_ids:
        partner_id = next(
            (entry.id for entry in run.pokemon if entry.is_partner and entry.id in eligible_ids),
            next(iter(eligible_ids)),
        )
        active = [partner_id]
    target_size = min(6, len(eligible_ids))
    if len(active) < target_size:
        active.extend(entry.id for entry in run.pokemon if entry.id in eligible_ids and entry.id not in active)
    active = active[:6]
    if active != run.active_roster:
        run.active_roster = active
        changed = True
    changed = _sync(run) or changed
    return changed


def capture_species(run: CareerRun, species: str, *, source: str, spend_ball: bool = True) -> CareerPokemon | None:
    canonical = next((entry for entry in all_region_encounters(run.build.region) if entry.lower() == species.lower()), None)
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
    partner = next((entry for entry in run.pokemon if entry.is_partner and entry.status != "retired"), None)
    if partner is None:
        return []
    return grant_pokemon_levels(run, partner.id, levels, source=source)


def grant_pokemon_levels(run: CareerRun, pokemon_id: str, levels: int, *, source: str) -> List[dict]:
    pokemon = next((entry for entry in run.pokemon if entry.id == pokemon_id and entry.status != "retired"), None)
    if pokemon is None:
        return []
    previous_level = pokemon.level
    pokemon.level = min(career_level_cap(run), pokemon.level + max(0, int(levels)))
    gained = pokemon.level - previous_level
    if gained <= 0:
        return []
    _refresh_identity(run, pokemon)
    run.timeline.append({
        "type": "pokemon.trained",
        "season": run.season_number,
        "age": run.age,
        "pokemon_id": pokemon.id,
        "species": pokemon.species,
        "levels": gained,
        "source": source,
        "label": f"{pokemon.species} gained {gained} levels.",
    })
    evolutions = _evolve_ready(run, pokemon)
    _sync(run)
    return evolutions


def teach_partner_move(run: CareerRun, move: str, *, source: str) -> bool:
    partner = next((entry for entry in run.pokemon if entry.is_partner and entry.status != "retired"), None)
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


def grant_stat_training(
    run: CareerRun,
    pokemon_id: str,
    stat: str,
    amount: int,
    *,
    source: str,
) -> dict | None:
    """Persist deterministic training that changes the generated battle build.

    Regular seasonal training is sustainable. A Training Kit is intensive work:
    every successful use consumes Pokemon career health and can eventually force
    that individual Pokemon to retire from competitive play.
    """
    aliases = {"attack": "atk", "defense": "def", "special_attack": "spatk", "special_defense": "spdef", "speed": "spd"}
    key = aliases.get(str(stat).lower(), str(stat).lower())
    if key not in {"hp", "atk", "def", "spatk", "spdef", "spd"}:
        return None
    pokemon = next((entry for entry in run.pokemon if entry.id == pokemon_id), None)
    if pokemon is None or pokemon.status == "retired" or pokemon.career_health <= 0:
        return None
    previous = int(pokemon.stat_training.get(key, 0))
    gained = min(max(0, 12 - previous), max(0, int(amount)))
    if gained <= 0:
        return None
    pokemon.stat_training[key] = previous + gained

    wear = 0
    retired = False
    if source == "item:training_kit":
        wear = TRAINING_KIT_WEAR
        pokemon.training_wear += wear
        pokemon.career_health = max(0, pokemon.career_health - wear)
        if pokemon.career_health <= 0:
            retired = _retire_pokemon(run, pokemon, reason="training_wear")

    event = {
        "type": "pokemon.stat_trained",
        "season": run.season_number,
        "age": run.age,
        "pokemon_id": pokemon.id,
        "species": pokemon.species,
        "stat": key,
        "amount": gained,
        "total": pokemon.stat_training[key],
        "source": source,
        "career_health": pokemon.career_health,
        "training_wear": wear,
        "retired": retired,
        "label": (
            f"{pokemon.species} gained {gained} permanent {key} training; intensive training reduced career health to {pokemon.career_health}."
            if wear
            else f"{pokemon.species} gained {gained} permanent {key} training."
        ),
    }
    run.timeline.append(event)
    _sync(run)
    return event


def set_active_roster(run: CareerRun, pokemon_ids: Sequence[str]) -> None:
    requested = [str(value) for value in pokemon_ids]
    eligible = {entry.id for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0}
    required = min(6, len(eligible))
    if len(requested) != required:
        raise ValueError(f"The active team must contain exactly {required} available Pokémon.")
    if len(set(requested)) != len(requested):
        raise ValueError("The active team cannot contain the same Pokémon twice.")
    if any(entry_id not in eligible for entry_id in requested):
        raise ValueError("The active team contains a retired or unavailable Pokémon.")
    run.active_roster = requested
    _sync(run)


def active_pokemon(run: CareerRun) -> List[CareerPokemon]:
    by_id = {entry.id: entry for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0}
    selected = [by_id[entry_id] for entry_id in run.active_roster if entry_id in by_id]
    if selected:
        return selected
    return [entry for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0][:1]


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
    longevity: List[dict] = []
    active_ids = set(run.active_roster)
    for pokemon in run.pokemon:
        if pokemon.status == "retired" or pokemon.career_health <= 0:
            continue
        played = appearances[pokemon.id]
        pokemon.matches += played
        pokemon.wins += wins[pokemon.id]
        if played:
            pokemon.level += 6 + min(2, played // 3)
            used.append(pokemon.species)
        elif pokemon.id in active_ids:
            pokemon.level += 3
        else:
            pokemon.level += 1
        pokemon.level = min(career_level_cap(run), pokemon.level)
        evolutions.extend(_evolve_ready(run, pokemon))
        _refresh_identity(run, pokemon)

        wear = _season_career_wear(run, pokemon, played=played, active=pokemon.id in active_ids)
        if wear:
            before = pokemon.career_health
            pokemon.career_health = max(0, pokemon.career_health - wear)
            retired = pokemon.career_health <= 0 and _retire_pokemon(run, pokemon, reason="career_wear")
            longevity.append({
                "pokemon_id": pokemon.id,
                "species": pokemon.species,
                "wear": before - pokemon.career_health,
                "career_health": pokemon.career_health,
                "played": played,
                "retired": bool(retired),
            })

    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner:
        run.build.starter = partner.species
    if longevity:
        run.timeline.append({
            "type": "pokemon.longevity_updated",
            "season": run.season_number,
            "age": run.age,
            "updates": longevity,
            "label": "Season workload reduced competitive career health for the roster.",
        })
    _sync(run)
    return {"pokemon_used": used, "evolutions": evolutions, "pokemon_longevity": longevity}


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


def _season_career_wear(run: CareerRun, pokemon: CareerPokemon, *, played: int, active: bool) -> int:
    """Return deterministic irreversible wear for one completed season.

    Match workload is the main source. Long-tenured Pokemon accumulate an extra
    veteran load. Pokemon outside the active team age much more slowly. Training
    Kit wear is applied separately and remains deliberately much larger.
    """
    career_seasons = max(1, run.season_number - pokemon.acquired_season + 1)
    veteran_wear = min(3, max(0, career_seasons - VETERAN_WEAR_START_SEASON) // 4)
    if played > 0:
        workload_wear = min(2, max(0, played - 1) // 3)
        return BASE_ACTIVE_SEASON_WEAR + workload_wear + veteran_wear
    if active:
        return 1 + veteran_wear
    return 1 if career_seasons >= PC_AGING_START_SEASON else 0


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


def _retire_pokemon(run: CareerRun, pokemon: CareerPokemon, *, reason: str) -> bool:
    if pokemon.status == "retired":
        return False
    pokemon.status = "retired"
    pokemon.career_health = 0
    pokemon.retired_season = run.season_number
    pokemon.retired_reason = reason
    run.active_roster = [entry_id for entry_id in run.active_roster if entry_id != pokemon.id]
    replacements = [
        entry.id
        for entry in run.pokemon
        if entry.id not in run.active_roster and entry.id != pokemon.id and entry.status != "retired" and entry.career_health > 0
    ]
    while len(run.active_roster) < min(6, sum(1 for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0)) and replacements:
        run.active_roster.append(replacements.pop(0))
    if reason == "training_wear":
        label = f"{pokemon.species} retired from competitive play after intensive Training Kit wear."
    elif reason == "career_wear":
        label = f"{pokemon.species} retired from competitive play after accumulated seasonal workload."
    else:
        label = f"{pokemon.species} retired from competitive play."
    run.timeline.append({
        "type": "pokemon.retired",
        "season": run.season_number,
        "age": run.age,
        "pokemon_id": pokemon.id,
        "species": pokemon.species,
        "reason": reason,
        "label": label,
    })
    return True


def _sync(run: CareerRun) -> bool:
    changed = False
    eligible_ids = {entry.id for entry in run.pokemon if entry.status != "retired" and entry.career_health > 0}
    sanitized = [entry_id for entry_id in run.active_roster if entry_id in eligible_ids][:6]
    if sanitized != run.active_roster:
        run.active_roster = sanitized
        changed = True
    active = set(run.active_roster)
    for pokemon in run.pokemon:
        if pokemon.career_health <= 0 or pokemon.status == "retired":
            status = "retired"
            pokemon.career_health = 0
        else:
            status = "active" if pokemon.id in active else "pc"
        if pokemon.status != status:
            pokemon.status = status
            changed = True
    roster = [entry.species for entry in run.pokemon]
    if roster != run.roster:
        run.roster = roster
        changed = True
    return changed