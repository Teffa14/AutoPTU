from __future__ import annotations

import random
from collections import Counter
from typing import Dict, Iterable, List, Sequence

from .catalogs import LEAGUES, REGIONS
from .models import BattleSpec, BattleTranscript, CareerPokemon, CareerRun


EVOLUTIONS: Dict[str, tuple[str, int]] = {
    "Rattata": ("Raticate", 20), "Caterpie": ("Metapod", 10), "Metapod": ("Butterfree", 20),
    "Weedle": ("Kakuna", 10), "Kakuna": ("Beedrill", 20), "Spearow": ("Fearow", 20),
    "Paras": ("Parasect", 20), "Venonat": ("Venomoth", 30), "Krabby": ("Kingler", 28),
    "Cubone": ("Marowak", 28), "Horsea": ("Seadra", 30), "Seadra": ("Kingdra", 40),
    "Goldeen": ("Seaking", 25), "Magikarp": ("Gyarados", 20),
    "Sentret": ("Furret", 15), "Hoothoot": ("Noctowl", 20), "Ledyba": ("Ledian", 20),
    "Spinarak": ("Ariados", 20), "Chinchou": ("Lanturn", 20), "Natu": ("Xatu", 25),
    "Wooper": ("Quagsire", 20), "Snubbull": ("Granbull", 20), "Slugma": ("Magcargo", 30),
    "Remoraid": ("Octillery", 25),
    "Poochyena": ("Mightyena", 20), "Zigzagoon": ("Linoone", 20), "Wurmple": ("Silcoon", 10),
    "Silcoon": ("Beautifly", 20), "Lotad": ("Lombre", 20), "Lombre": ("Ludicolo", 30),
    "Seedot": ("Nuzleaf", 20), "Nuzleaf": ("Shiftry", 30), "Taillow": ("Swellow", 20),
    "Surskit": ("Masquerain", 22), "Whismur": ("Loudred", 20), "Loudred": ("Exploud", 40),
    "Skitty": ("Delcatty", 25), "Gulpin": ("Swalot", 25), "Spoink": ("Grumpig", 30),
    "Bidoof": ("Bibarel", 15), "Kricketot": ("Kricketune", 15), "Shinx": ("Luxio", 15),
    "Luxio": ("Luxray", 30), "Burmy": ("Wormadam", 20), "Combee": ("Vespiquen", 21),
    "Buizel": ("Floatzel", 25), "Cherubi": ("Cherrim", 20), "Shellos": ("Gastrodon", 30),
    "Stunky": ("Skuntank", 30), "Finneon": ("Lumineon", 30),
    "Patrat": ("Watchog", 20), "Lillipup": ("Herdier", 16), "Herdier": ("Stoutland", 32),
    "Purrloin": ("Liepard", 20), "Pidove": ("Tranquill", 20), "Tranquill": ("Unfezant", 35),
    "Blitzle": ("Zebstrika", 25), "Roggenrola": ("Boldore", 20), "Boldore": ("Gigalith", 35),
    "Woobat": ("Swoobat", 20), "Tympole": ("Palpitoad", 20), "Palpitoad": ("Seismitoad", 35),
    "Sewaddle": ("Swadloon", 20), "Swadloon": ("Leavanny", 30), "Venipede": ("Whirlipede", 20),
    "Whirlipede": ("Scolipede", 35), "Dwebble": ("Crustle", 25),
    "Bunnelby": ("Diggersby", 20), "Fletchling": ("Fletchinder", 17), "Fletchinder": ("Talonflame", 35),
    "Scatterbug": ("Spewpa", 10), "Spewpa": ("Vivillon", 20), "Litleo": ("Pyroar", 30),
    "Flabebe": ("Floette", 20), "Floette": ("Florges", 35), "Skiddo": ("Gogoat", 25),
    "Pancham": ("Pangoro", 30), "Espurr": ("Meowstic", 25), "Spritzee": ("Aromatisse", 25),
    "Swirlix": ("Slurpuff", 25), "Inkay": ("Malamar", 30),
    "Pikipek": ("Trumbeak", 15), "Trumbeak": ("Toucannon", 30), "Yungoos": ("Gumshoos", 20),
    "Grubbin": ("Charjabug", 20), "Charjabug": ("Vikavolt", 35), "Crabrawler": ("Crabominable", 30),
    "Cutiefly": ("Ribombee", 25), "Rockruff": ("Lycanroc", 25), "Mudbray": ("Mudsdale", 30),
    "Dewpider": ("Araquanid", 25), "Fomantis": ("Lurantis", 25), "Morelull": ("Shiinotic", 25),
    "Salandit": ("Salazzle", 33),
    "Skwovet": ("Greedent", 25), "Rookidee": ("Corvisquire", 20), "Corvisquire": ("Corviknight", 40),
    "Blipbug": ("Dottler", 10), "Dottler": ("Orbeetle", 30), "Nickit": ("Thievul", 20),
    "Gossifleur": ("Eldegoss", 20), "Wooloo": ("Dubwool", 25), "Chewtle": ("Drednaw", 20),
    "Yamper": ("Boltund", 25), "Rolycoly": ("Carkol", 20), "Carkol": ("Coalossal", 40),
    "Silicobra": ("Sandaconda", 30), "Arrokuda": ("Barraskewda", 25), "Clobbopus": ("Grapploct", 30),
    "Lechonk": ("Oinkologne", 20), "Tarountula": ("Spidops", 15), "Nymble": ("Lokix", 25),
    "Pawmi": ("Pawmo", 18), "Pawmo": ("Pawmot", 32), "Tandemaus": ("Maushold", 25),
    "Fidough": ("Dachsbun", 25), "Smoliv": ("Dolliv", 20), "Dolliv": ("Arboliva", 35),
    "Nacli": ("Naclstack", 20), "Naclstack": ("Garganacl", 40), "Charcadet": ("Armarouge", 30),
    "Tadbulb": ("Bellibolt", 25), "Wattrel": ("Kilowattrel", 25),
}


def initialize_roster(run: CareerRun, stable_seed: int) -> bool:
    """Upgrade old one-partner runs and stage the regional academy capture trial."""
    changed = False
    if not run.pokemon:
        existing = run.roster or [run.build.starter]
        for index, species in enumerate(existing):
            run.pokemon.append(_pokemon(run, str(species), index == 0, _base_level(run)))
        changed = True
    if not any(entry.is_partner for entry in run.pokemon):
        run.pokemon[0].is_partner = True
        changed = True

    missing = max(0, 8 - len(run.pokemon))
    if missing:
        captured = _capture(run, missing, stable_seed)
        run.build.pokeballs = max(0, run.build.pokeballs - len(captured))
        _capture_event(run, captured, "academy.intake")
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


def capture_between_seasons(run: CareerRun, stable_seed: int, count: int = 3) -> List[CareerPokemon]:
    run.build.pokeballs = min(20, run.build.pokeballs + 5)
    captured = _capture(run, min(count, run.build.pokeballs), stable_seed)
    run.build.pokeballs -= len(captured)
    _capture_event(run, captured, "offseason.scouting")
    _sync(run)
    return captured


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
    appearances = Counter(spec.home_pokemon_id for spec in specs if spec.home_pokemon_id)
    wins = Counter(
        transcript.spec.home_pokemon_id
        for transcript in transcripts
        if transcript.winner_team == "career-home" and transcript.spec.home_pokemon_id
    )
    used: List[str] = []
    evolutions: List[dict] = []
    active_ids = set(run.active_roster)
    for pokemon in run.pokemon:
        played = appearances[pokemon.id]
        pokemon.matches += played
        pokemon.wins += wins[pokemon.id]
        if played:
            pokemon.level += 5 + played * 3
            used.append(pokemon.species)
        elif pokemon.id in active_ids:
            pokemon.level += 3
        else:
            pokemon.level += 1
        while pokemon.species in EVOLUTIONS and pokemon.level >= EVOLUTIONS[pokemon.species][1]:
            previous = pokemon.species
            evolved, threshold = EVOLUTIONS[previous]
            pokemon.species = evolved
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
    partner = next((entry for entry in run.pokemon if entry.is_partner), None)
    if partner:
        run.build.starter = partner.species
    _sync(run)
    return {"pokemon_used": used, "evolutions": evolutions}


def _capture(run: CareerRun, count: int, seed: int) -> List[CareerPokemon]:
    region = REGIONS[run.build.region]
    owned = Counter(entry.caught_species for entry in run.pokemon)
    pool = [species for species in region.underdogs if owned[species] == 0 and species != run.build.starter]
    fallback = [species for species in region.underdogs if species != run.build.starter]
    rng = random.Random(seed)
    rng.shuffle(pool)
    rng.shuffle(fallback)
    choices: List[str] = []
    while len(choices) < count:
        if pool:
            choices.append(pool.pop())
        elif fallback:
            choices.append(fallback[(len(choices) + len(run.pokemon)) % len(fallback)])
        else:
            break
    captured: List[CareerPokemon] = []
    for species in choices:
        pokemon = _pokemon(run, species, False, _base_level(run))
        run.pokemon.append(pokemon)
        captured.append(pokemon)
    return captured


def _pokemon(run: CareerRun, species: str, partner: bool, level: int) -> CareerPokemon:
    return CareerPokemon(
        id=f"{run.id}-p{len(run.pokemon) + 1:03d}",
        species=species,
        caught_species=species,
        level=level,
        acquired_season=run.season_number,
        acquired_age=run.age,
        capture_region=run.build.region,
        is_partner=partner,
        status="active" if len(run.pokemon) < 6 else "pc",
    )


def _base_level(run: CareerRun) -> int:
    return LEAGUES[run.league].min_level + min(15, max(0, run.season_number - 1))


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
