from __future__ import annotations

import hashlib
import json
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Sequence

from ..csv_repository import PTUCsvRepository
from ..natures import pick_random_nature_name
from .paldea import build_paldea_spec


def build_career_pokemon_spec(
    repo: PTUCsvRepository,
    species: str,
    level: int,
    *,
    nature: str = "",
    abilities: Sequence[str] = (),
    taught_moves: Iterable[str] = (),
):
    """Build one PTU combatant without the repository's cross-species move fallback.

    The generic random-campaign builder deliberately augments short low-level
    movesets so generated encounters are always offensive. Career mode cannot do
    that: every natural move must come from this species' level-up list and every
    extra move must be a legal TM, tutor, egg, or natural source.
    """
    level = max(1, int(level))
    record = repo.get_species(species)
    if record is not None:
        mon = repo.build_pokemon_spec(
            species,
            level=level,
            assign_abilities=not abilities,
            assign_nature=not nature,
            nature=nature or None,
        )
        mon.moves = strict_level_up_moves(repo, record.name, level)
    else:
        mon = build_paldea_spec(species, level, repo)
        if nature:
            mon.nature = nature
        elif not getattr(mon, "nature", ""):
            mon.nature = pick_random_nature_name(repo._rng, root=repo.root)
    if abilities:
        mon.abilities = [{"name": str(name)} for name in abilities if str(name).strip()]
    for move_name in taught_moves:
        canonical = repo.resolve_move_name(str(move_name))
        if not canonical or not is_legal_taught_move(species, canonical):
            continue
        record_move = repo.get_move(canonical)
        if record_move is None or any(move.name.lower() == record_move.name.lower() for move in mon.moves):
            continue
        learned = record_move.to_move_spec()
        replace_index = next(
            (index for index in range(len(mon.moves) - 1, -1, -1) if str(mon.moves[index].category).lower() == "status"),
            len(mon.moves) - 1,
        )
        if replace_index >= 0:
            mon.moves[replace_index] = learned
        else:
            mon.moves.append(learned)
        mon.moves = mon.moves[:4]
    return mon


def strict_level_up_moves(repo: PTUCsvRepository, species: str, level: int):
    record = repo.get_species(species)
    if record is None:
        return []
    repo._ensure_moves()
    repo._ensure_learnsets()
    learnset = []
    for key in repo._learnset_key_candidates(record.name):
        learnset = repo._learnsets.get(key, [])
        if learnset:
            break
    # This compiled dataset stores TM/tutor compatibility as level 0 rows in
    # the same lookup. They are legal sources, but they are not naturally known.
    eligible = [(name, required) for name, required in learnset if 0 < int(required) <= int(level)]
    records = repo._records_from_learnset(eligible)
    moves = repo._build_minmax_moveset(record, records)
    if not moves and records:
        moves = [records[0].to_move_spec()]
    if not moves:
        struggle = repo.get_move("Struggle")
        moves = [struggle.to_move_spec()] if struggle else []
    return moves[:4]


def persistent_identity(
    species: str,
    level: int,
    seed: int,
    *,
    nature: str = "",
    existing_abilities: Sequence[str] = (),
) -> tuple[str, List[str]]:
    selected_nature, cached_abilities = _base_identity(species, int(level), int(seed))
    selected = list(cached_abilities)
    merged = []
    for ability in [*existing_abilities, *selected]:
        if ability and ability.lower() not in {entry.lower() for entry in merged}:
            merged.append(ability)
    return nature or selected_nature, merged


@lru_cache(maxsize=4096)
def _base_identity(species: str, level: int, seed: int) -> tuple[str, tuple[str, ...]]:
    repo = PTUCsvRepository(rng=random.Random(int(seed)))
    record = repo.get_species(species)
    if record is not None:
        # Persistent identity never needs a moveset. Building a full combatant
        # here used to reload every learnset and move table after each season.
        selected_nature = pick_random_nature_name(repo._rng, root=repo.root)
        selected = list(repo._select_abilities(record.name, level))
    else:
        mon = build_paldea_spec(species, level, repo)
        selected_nature = str(getattr(mon, "nature", "")) or pick_random_nature_name(repo._rng, root=repo.root)
        selected = _ability_names(getattr(mon, "abilities", []))
        # Generation 9 PBS lists ability alternatives rather than PTU tiers.
        # Keep a deterministic legal subset as the career advances.
        count = 1 + int(level >= 20) + int(level >= 40)
        rng = random.Random(int(seed))
        selected = list(selected)
        rng.shuffle(selected)
        selected = selected[:count]
    return selected_nature, tuple(selected)


def identity_seed(run_seed: int, pokemon_id: str) -> int:
    # UUIDs identify persistence, but must not alter a seeded daily build.
    ordinal = pokemon_id.rsplit("-p", 1)[-1] if "-p" in pokemon_id else pokemon_id
    payload = f"{run_seed}:{ordinal}:career-pokemon-identity".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0x7FFFFFFF


def is_legal_taught_move(species: str, move: str) -> bool:
    normalized = _normalize(move)
    return any(_normalize(entry) == normalized for entry in legal_taught_move_names(species))


def legal_taught_move_names(species: str) -> List[str]:
    entries, normalized_keys = _move_sources()
    raw = entries.get(species)
    if raw is None:
        raw = entries.get(normalized_keys.get(_normalize_species(species), ""), {})
    if not isinstance(raw, dict):
        return []
    names: List[str] = []
    for source in ("tm", "tutor", "egg", "natural"):
        for name in raw.get(source, []) or []:
            cleaned = str(name).strip()
            if cleaned and cleaned.lower() not in {entry.lower() for entry in names}:
                names.append(cleaned)
    return names


def choose_legal_taught_move(species: str, preferred: Sequence[str], seed: int) -> str:
    legal = legal_taught_move_names(species)
    by_key = {_normalize(entry): entry for entry in legal}
    for candidate in preferred:
        if _normalize(candidate) in by_key:
            return by_key[_normalize(candidate)]
    valid = []
    repo = PTUCsvRepository(rng=random.Random(int(seed)))
    for candidate in legal:
        if repo.get_move(candidate) is not None:
            valid.append(candidate)
    return random.Random(int(seed)).choice(sorted(valid)) if valid else ""


@lru_cache(maxsize=1)
def _move_sources() -> tuple[dict, dict]:
    path = Path(__file__).resolve().parents[1] / "api" / "static" / "pokemon_move_sources.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = dict(payload.get("entries") or {})
    return entries, {_normalize_species(name): name for name in entries}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _normalize_species(value: str) -> str:
    normalized = _normalize(value)
    for suffix in ("alola", "galar", "hisui", "paldea"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)] + suffix
    return normalized


def _ability_names(values: Iterable[object]) -> List[str]:
    result: List[str] = []
    for value in values:
        name = value.get("name") if isinstance(value, dict) else getattr(value, "name", value)
        cleaned = str(name or "").strip()
        if cleaned and cleaned.lower() not in {entry.lower() for entry in result}:
            result.append(cleaned)
    return result
