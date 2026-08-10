from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from ..csv_repository import PTUCsvRepository
from ..data_models import MoveSpec, PokemonSpec


def _pbs_path() -> Path:
    return Path(__file__).resolve().parents[2] / "IMPLEMENTATION FILES" / "Generation 9 Pack v3.3.4" / "PBS" / "pokemon_base_Gen_9_Pack.txt"


@lru_cache(maxsize=1)
def paldea_records() -> Dict[str, dict]:
    path = _pbs_path()
    if not path.exists():
        return {}
    records: Dict[str, dict] = {}
    current: Dict[str, str] = {}
    section = ""
    for raw_line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw_line.strip()
        match = re.fullmatch(r"\[([^]]+)\]", line)
        if match:
            if current.get("Name"):
                records[current["Name"].lower()] = dict(current)
            section = match.group(1)
            current = {"Id": section}
            continue
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        current[key.strip()] = value.strip()
    if current.get("Name"):
        records[current["Name"].lower()] = dict(current)
    return records


def build_paldea_spec(name: str, level: int, repo: PTUCsvRepository) -> PokemonSpec:
    record = paldea_records().get(name.lower())
    if not record:
        raise ValueError(f"Paldea species '{name}' is not present in the bundled Generation 9 PBS.")
    stats = [int(value) for value in str(record.get("BaseStats") or "50,50,50,50,50,50").split(",")[:6]]
    while len(stats) < 6:
        stats.append(50)
    types = [value.strip().title() for value in str(record.get("Types") or "NORMAL").split(",") if value.strip()]
    move_names = _level_moves(str(record.get("Moves") or ""), level)
    moves: List[MoveSpec] = []
    for move_name in move_names[-4:]:
        resolved = repo.resolve_move_name(move_name) or move_name
        move = repo.get_move(resolved)
        if move:
            moves.append(move.to_move_spec())
    if not moves:
        tackle = repo.get_move("Tackle")
        if tackle:
            moves.append(tackle.to_move_spec())
    spec = PokemonSpec(
        species=str(record.get("Name") or name),
        name=str(record.get("Name") or name),
        level=level,
        types=types,
        hp_stat=math.ceil(stats[0] / 10),
        atk=math.ceil(stats[1] / 10),
        defense=math.ceil(stats[2] / 10),
        spatk=math.ceil(stats[3] / 10),
        spdef=math.ceil(stats[4] / 10),
        spd=math.ceil(stats[5] / 10),
        moves=moves,
        abilities=[{"name": _display_id(value)} for value in str(record.get("Abilities") or "").split(",") if value.strip()],
        movement={"overland": 5, "h_jump": 1, "l_jump": 1, "power": max(1, math.ceil(stats[1] / 20))},
        size="Small" if float(record.get("Height") or 1) < 1 else "Medium",
        weight=float(record.get("Weight") or 0),
        loyalty=2,
    )
    return spec


def _level_moves(raw: str, level: int) -> List[str]:
    values = [value.strip() for value in raw.split(",") if value.strip()]
    names: List[str] = []
    for index in range(0, len(values) - 1, 2):
        try:
            required = int(values[index])
        except ValueError:
            continue
        if required <= level:
            names.append(_display_id(values[index + 1]))
    return names


def _display_id(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z][a-z])", " ", value.replace("_", " ")).title()
