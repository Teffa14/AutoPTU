from __future__ import annotations

import contextlib
import csv
import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.error import URLError
from urllib.request import urlopen
import argparse

from auto_ptu.pokeapi_assets import (
    ability_metadata,
    cry_path,
    item_icon_path,
    item_metadata,
    move_metadata,
    type_icon_path,
)
from auto_ptu.sprites import ensure_sprite_filename, sprite_cache_dir, sprite_url_for


_MASTER_DATA_CACHE: dict | None = None
_FOUNDRY_SPECIES_CACHE: dict[str, dict] | None = None
_MOVE_NAME_MAP: dict[str, str] | None = None
_ABILITY_NAME_MAP: dict[str, str] | None = None
_LEARNSET_CACHE: dict[str, list[dict]] | None = None
_ABILITY_POOLS_CACHE: dict[str, dict] | None = None
_ABILITY_CATALOG_SET: set[str] | None = None
_SPECIES_INDEX_CACHE: dict[str, dict] | None = None
_SPRITE_DIR = sprite_cache_dir()
_SPRITE_DIR.mkdir(parents=True, exist_ok=True)


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _builder_root() -> Path:
    candidates = [
        _bundle_root() / "AutoPTUCharacter",
        Path(__file__).resolve().parent / "auto_ptu" / "api" / "static" / "AutoPTUCharacter",
        Path(__file__).resolve().parent / "dist" / "AutoPTUCharacter",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _foundry_species_root() -> Path:
    candidates = [
        _bundle_root() / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-species",
        Path(__file__).resolve().parent / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-species",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _portable_state_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "portable_data"
    return Path.home() / ".autoptu-builder"


def _log_path() -> Path:
    return _portable_state_root() / "builder_launcher.log"


def _write_log(message: str) -> None:
    log_path = _log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{message}\n", encoding="utf-8")
    except Exception:
        pass


def _trace_startup(message: str) -> None:
    try:
        if getattr(sys, "frozen", False):
            trace_path = Path(sys.executable).resolve().parent / "builder_startup_trace.log"
        else:
            trace_path = Path(__file__).resolve().parent / "builder_startup_trace.log"
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except Exception:
        pass


def _pick_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _requested_port() -> int:
    raw = os.environ.get("AUTO_PTU_CHARACTER_BUILDER_PORT", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            return _pick_port()
    return _pick_port()


def _normalize_species_key(value: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    text = text.replace("\u2640", "f").replace("\u2642", "m")
    text = text.replace("\u2019", " ").replace("'", " ").replace(".", " ")
    text = text.replace("(", " ").replace(")", " ").replace("-", " ")
    cleaned = []
    for char in text:
        if char.isalnum() or char in {" ", "%", "+"}:
            cleaned.append(char)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())


def _slug_key(value: str) -> str:
    return "".join(ch for ch in _normalize_species_key(value) if ch.isalnum())


def _title_from_slug(value: str) -> str:
    parts = [part for part in str(value or "").replace("_", "-").split("-") if part]
    if not parts:
        return ""
    return " ".join(part[:1].upper() + part[1:] for part in parts)


def _species_candidate_keys(value: str) -> list[str]:
    normalized = _normalize_species_key(value)
    if not normalized:
        return []
    out: list[str] = []

    def add(entry: str) -> None:
        cleaned = _normalize_species_key(entry)
        if cleaned and cleaned not in out:
            out.append(cleaned)

    add(normalized)
    tokens = normalized.split()
    if tokens:
        add(tokens[0])
    aliases = {
        "alolan": "",
        "galarian": "",
        "hisuian": "",
        "paldean": "",
        "alola": "",
        "galar": "",
        "hisui": "",
        "paldea": "",
        "confined": "hoopa",
        "bound": "hoopa",
        "unbound": "hoopa unbound",
        "standard": "darmanitan",
        "zen": "darmanitan zen",
        "normal": "deoxys",
        "attack": "deoxys attack",
        "defense": "deoxys defense",
        "speed": "deoxys speed",
        "altered": "giratina altered",
        "origin": "giratina origin",
        "average": "gourgeist average",
        "small": "gourgeist small",
        "large": "gourgeist large",
        "super": "gourgeist super",
        "aria": "meloetta aria",
        "pirouette": "meloetta pirouette",
        "incarnate": "landorus incarnate",
        "therian": "landorus therian",
        "white": "kyurem white",
        "black": "kyurem black",
        "female": "nidoran f",
        "male": "nidoran m",
    }
    if len(tokens) > 1:
        suffix = tokens[-1]
        mapped = aliases.get(suffix)
        if mapped:
            add(f"{tokens[0]} {mapped}".strip())
        short_mapped = aliases.get(tokens[1])
        if short_mapped:
            add(f"{tokens[0]} {short_mapped}".strip())
        prefix = aliases.get(tokens[0])
        if prefix == "":
            add(" ".join(tokens[1:]))
            add(" ".join(tokens[1:] + [tokens[0]]))
        if normalized.startswith("primal "):
            add(" ".join(tokens[1:]))
        if normalized.startswith("mega "):
            add(" ".join(tokens[1:] + ["mega"]).strip())
    compact = _slug_key(normalized)
    if compact and compact not in out:
        out.append(compact)
    return out


def _load_master_data() -> dict:
    global _MASTER_DATA_CACHE
    if _MASTER_DATA_CACHE is not None:
        return _MASTER_DATA_CACHE
    payload = {}
    path = _builder_root() / "master_dataset.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    _MASTER_DATA_CACHE = payload
    return payload


def _build_name_maps() -> tuple[dict[str, str], dict[str, str]]:
    global _MOVE_NAME_MAP, _ABILITY_NAME_MAP, _ABILITY_CATALOG_SET
    if _MOVE_NAME_MAP is not None and _ABILITY_NAME_MAP is not None and _ABILITY_CATALOG_SET is not None:
        return _MOVE_NAME_MAP, _ABILITY_NAME_MAP
    master_data = _load_master_data()
    move_map: dict[str, str] = {}
    for entry in master_data.get("pokemon", {}).get("moves", []) or []:
        name = str((entry or {}).get("name") or "").strip()
        if name:
            move_map.setdefault(_slug_key(name), name)
    ability_map: dict[str, str] = {}
    ability_catalog: set[str] = set()
    for entry in master_data.get("pokemon", {}).get("abilities", []) or []:
        name = str((entry or {}).get("name") or "").strip()
        if name:
            ability_map.setdefault(_slug_key(name), name)
            ability_catalog.add(name.casefold())
    for pools in master_data.get("pokemon", {}).get("pokedex_abilities", {}).values():
        if not isinstance(pools, dict):
            continue
        for tier in ("starting", "basic", "advanced", "high"):
            for name in pools.get(tier, []) or []:
                ability_name = str(name or "").strip()
                if ability_name:
                    ability_map.setdefault(_slug_key(ability_name), ability_name)
    _MOVE_NAME_MAP = move_map
    _ABILITY_NAME_MAP = ability_map
    _ABILITY_CATALOG_SET = ability_catalog
    return move_map, ability_map


def _is_known_ability_name(value: str) -> bool:
    _build_name_maps()
    return str(value or "").strip().casefold() in (_ABILITY_CATALOG_SET or set())


def _is_known_move_name(value: str) -> bool:
    _build_name_maps()
    return _slug_key(str(value or "").strip()) in (_MOVE_NAME_MAP or {})


def _resolve_move_name(value: str) -> str:
    move_map, _ability_map = _build_name_maps()
    slug = _slug_key(value)
    return move_map.get(slug) or _title_from_slug(value)


def _resolve_ability_name(value: str) -> str:
    _move_map, ability_map = _build_name_maps()
    slug = _slug_key(value)
    return ability_map.get(slug) or _title_from_slug(value)


def _load_foundry_species_index() -> dict[str, dict]:
    global _FOUNDRY_SPECIES_CACHE
    if _FOUNDRY_SPECIES_CACHE is not None:
        return _FOUNDRY_SPECIES_CACHE
    root = _foundry_species_root()
    cache: dict[str, dict] = {}
    if root.exists():
        for path in root.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("type") or "").strip().lower() != "species":
                continue
            system = payload.get("system") or {}
            candidates = [
                str(payload.get("name") or "").strip(),
                str(system.get("slug") or "").strip(),
                path.stem,
            ]
            for candidate in candidates:
                for key in _species_candidate_keys(candidate):
                    cache.setdefault(key, payload)
    _FOUNDRY_SPECIES_CACHE = cache
    return cache


def _foundry_species_payload(species: str) -> dict | None:
    if not species:
        return None
    index = _load_foundry_species_index()
    for key in _species_candidate_keys(species):
        payload = index.get(key)
        if payload:
            return payload
    return None


def _load_learnset_cache() -> dict[str, list[dict]]:
    global _LEARNSET_CACHE
    if _LEARNSET_CACHE is not None:
        return _LEARNSET_CACHE
    cache: dict[str, list[dict]] = {}
    path = _bundle_root() / "files" / "pokedex_learnset.csv"
    if not path.exists():
        alt = Path(__file__).resolve().parent / "files" / "pokedex_learnset.csv"
        path = alt
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                species_name = str(row.get("species") or "").strip()
                move_name = str(row.get("move") or "").strip()
                if not species_name or not move_name:
                    continue
                try:
                    level = int(row.get("level") or 0)
                except (TypeError, ValueError):
                    level = 0
                record = {"move": move_name, "level": level}
                for key in _species_candidate_keys(species_name):
                    cache.setdefault(key, []).append(record)
    _LEARNSET_CACHE = cache
    return cache


def _load_ability_pools_cache() -> dict[str, dict]:
    global _ABILITY_POOLS_CACHE
    if _ABILITY_POOLS_CACHE is not None:
        return _ABILITY_POOLS_CACHE
    master_data = _load_master_data()
    cache: dict[str, dict] = {}
    for raw_key, payload in (master_data.get("pokemon", {}).get("pokedex_abilities", {}) or {}).items():
        if not isinstance(payload, dict):
            continue
        for key in _species_candidate_keys(str(raw_key)):
            cache.setdefault(key, payload)
    _ABILITY_POOLS_CACHE = cache
    return cache


def _load_species_index() -> dict[str, dict]:
    global _SPECIES_INDEX_CACHE
    if _SPECIES_INDEX_CACHE is not None:
        return _SPECIES_INDEX_CACHE
    master_data = _load_master_data()
    cache: dict[str, dict] = {}
    for entry in master_data.get("pokemon", {}).get("species", []) or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        for key in _species_candidate_keys(name):
            cache.setdefault(key, entry)
    _SPECIES_INDEX_CACHE = cache
    return cache


def _species_entry(species: str) -> dict | None:
    index = _load_species_index()
    for key in _species_candidate_keys(species):
        payload = index.get(key)
        if payload:
            return payload
    return None


def _select_foundry_moves(level_up: list[dict], level: int) -> list[str]:
    seen: set[str] = set()
    eligible = []
    for entry in level_up or []:
        if not isinstance(entry, dict):
            continue
        try:
            required_level = int(entry.get("level") or 0)
        except (TypeError, ValueError):
            required_level = 0
        if required_level > level:
            continue
        name = _resolve_move_name(str(entry.get("name") or "").strip())
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        eligible.append((required_level, name))
    eligible.sort(key=lambda item: (item[0], item[1].casefold()))
    if len(eligible) <= 4:
        return [name for _req, name in eligible]
    recent = eligible[-4:]
    return [name for _req, name in recent]


def _select_foundry_abilities(abilities: dict, level: int) -> list[str]:
    desired = 1 if level < 20 else 2 if level < 40 else 3
    tiers = {
        "starting": [],
        "basic": [],
        "advanced": [],
        "high": [],
        "master": [],
    }
    for tier in tiers:
        for entry in abilities.get(tier, []) or []:
            slug = str((entry or {}).get("slug") or "").strip()
            name = _resolve_ability_name(slug)
            if name:
                tiers[tier].append(name)
    starting = list(dict.fromkeys(tiers["starting"]))
    basic = list(dict.fromkeys(tiers["starting"] + tiers["basic"]))
    advanced = list(dict.fromkeys(tiers["advanced"]))
    high = list(dict.fromkeys(tiers["high"] + tiers["master"]))
    current: list[str] = []

    def pick(pool: list[str]) -> str | None:
        known_choices = [name for name in pool if _is_known_ability_name(name) and name.casefold() not in {entry.casefold() for entry in current}]
        if known_choices:
            return known_choices[0]
        return None

    first = pick(starting) or pick(basic) or pick(advanced) or pick(high)
    if first:
        current.append(first)
    if desired >= 2 and len(current) < 2:
        chosen = pick(basic + advanced)
        if chosen:
            current.append(chosen)
    if desired >= 3 and len(current) < 3:
        chosen = pick(basic + advanced + high)
        if chosen:
            current.append(chosen)
    return current[:desired]


def _select_csv_moves(species: str, level: int) -> list[str]:
    learnset = _load_learnset_cache()
    rows: list[dict] = []
    for key in _species_candidate_keys(species):
        rows = learnset.get(key) or []
        if rows:
            break
    seen: set[str] = set()
    eligible: list[tuple[int, str]] = []
    for entry in rows:
        required_level = int(entry.get("level") or 0)
        if required_level > level:
            continue
        move_name = str(entry.get("move") or "").strip()
        if not move_name or not _is_known_move_name(move_name):
            continue
        canonical = _resolve_move_name(move_name)
        dedupe_key = canonical.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        eligible.append((required_level, canonical))
    eligible.sort(key=lambda item: (item[0], item[1].casefold()))
    if len(eligible) <= 4:
        return [name for _lvl, name in eligible]
    return [name for _lvl, name in eligible[-4:]]


def _eligible_csv_moves(species: str, level: int) -> list[str]:
    learnset = _load_learnset_cache()
    rows: list[dict] = []
    for key in _species_candidate_keys(species):
        rows = learnset.get(key) or []
        if rows:
            break
    seen: set[str] = set()
    eligible: list[tuple[int, str]] = []
    for entry in rows:
        required_level = int(entry.get("level") or 0)
        if required_level > level:
            continue
        move_name = str(entry.get("move") or "").strip()
        if not move_name or not _is_known_move_name(move_name):
            continue
        canonical = _resolve_move_name(move_name)
        dedupe_key = canonical.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        eligible.append((required_level, canonical))
    eligible.sort(key=lambda item: (item[0], item[1].casefold()))
    return [name for _lvl, name in eligible]


def _generate_fallback_moves(species: str) -> list[str]:
    entry = _species_entry(species) or {}
    types = [str(t or "").strip() for t in (entry.get("types") or []) if str(t or "").strip() and str(t or "").strip().lower() != "none"]
    stats = entry.get("base_stats") or {}
    physical = float(stats.get("attack") or 0) >= float(stats.get("special_attack") or 0)
    move_catalog = _load_master_data().get("pokemon", {}).get("moves", []) or []
    by_name = {str(move.get("name") or "").strip().casefold(): str(move.get("name") or "").strip() for move in move_catalog}
    preferred_by_type = {
        "Normal": ["Tackle", "Quick Attack", "Bite", "Protect"],
        "Fire": ["Ember", "Flame Wheel", "Flamethrower", "Fire Fang"],
        "Water": ["Bubble", "Water Gun", "Water Pulse", "Aqua Jet"],
        "Electric": ["Thunder Shock", "Charge Beam", "Spark", "Thunder Wave"],
        "Grass": ["Absorb", "Razor Leaf", "Magical Leaf", "Vine Whip"],
        "Ice": ["Powder Snow", "Icy Wind", "Ice Fang", "Ice Beam"],
        "Fighting": ["Rock Smash", "Low Kick", "Mach Punch", "Brick Break"],
        "Poison": ["Poison Sting", "Acid", "Venoshock", "Poison Jab"],
        "Ground": ["Mud Shot", "Bulldoze", "Sand Tomb", "Dig"],
        "Flying": ["Peck", "Wing Attack", "Air Cutter", "Aerial Ace"],
        "Psychic": ["Confusion", "Psybeam", "Psyshock", "Light Screen"],
        "Bug": ["String Shot", "Bug Bite", "Struggle Bug", "X-Scissor"],
        "Rock": ["Rock Throw", "Ancient Power", "Rock Tomb", "Rock Slide"],
        "Ghost": ["Astonish", "Hex", "Shadow Sneak", "Ominous Wind"],
        "Dragon": ["Twister", "Dragon Breath", "Dragon Pulse", "Scary Face"],
        "Dark": ["Bite", "Snarl", "Assurance", "Dark Pulse"],
        "Steel": ["Metal Claw", "Mirror Shot", "Iron Defense", "Flash Cannon"],
        "Fairy": ["Fairy Wind", "Disarming Voice", "Draining Kiss", "Charm"],
    }
    generic = ["Protect", "Swift", "Rest", "Substitute", "Quick Attack", "Tackle"]
    picks: list[str] = []
    for move_name in [name for typ in types for name in preferred_by_type.get(typ, [])] + generic:
        resolved = by_name.get(move_name.casefold())
        if resolved and resolved not in picks:
            picks.append(resolved)
        if len(picks) >= 4:
            return picks[:4]
    damaging = []
    status = []
    for move in move_catalog:
        name = str(move.get("name") or "").strip()
        if not name:
            continue
        move_type = str(move.get("type") or "").strip()
        category = str(move.get("category") or "").strip().lower()
        damage_base = float(move.get("damage_base") or 0)
        if types and move_type in types and damage_base > 0:
            if physical and category == "physical":
                damaging.append(name)
            elif (not physical) and category == "special":
                damaging.append(name)
        elif damage_base <= 0:
            status.append(name)
    for move_name in damaging + status:
        if move_name not in picks:
            picks.append(move_name)
        if len(picks) >= 4:
            break
    return picks[:4]


def _sanitize_moves(species: str, moves: list[str]) -> list[str]:
    sanitized: list[str] = []
    seen: set[str] = set()
    for move_name in moves or []:
        cleaned = str(move_name or "").strip()
        if not cleaned or not _is_known_move_name(cleaned):
            continue
        canonical = _resolve_move_name(cleaned)
        key = canonical.casefold()
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(canonical)
    if len(sanitized) >= 4:
        return sanitized[:4]
    for move_name in _generate_fallback_moves(species):
        if not _is_known_move_name(move_name):
            continue
        canonical = _resolve_move_name(move_name)
        key = canonical.casefold()
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(canonical)
        if len(sanitized) >= 4:
            break
    return sanitized[:4]


def _legalize_moves_for_species(species: str, level: int, moves: list[str]) -> list[str]:
    legal_pool = _eligible_csv_moves(species, level)
    if not legal_pool:
        return _sanitize_moves(species, moves)
    legal_lookup = {name.casefold(): name for name in legal_pool}
    sanitized: list[str] = []
    seen: set[str] = set()
    for move_name in moves or []:
        key = str(move_name or "").strip().casefold()
        legal_name = legal_lookup.get(key)
        if not legal_name or key in seen:
            continue
        seen.add(key)
        sanitized.append(legal_name)
        if len(sanitized) >= 4:
            return sanitized
    for legal_name in reversed(legal_pool):
        key = legal_name.casefold()
        if key in seen:
            continue
        seen.add(key)
        sanitized.append(legal_name)
        if len(sanitized) >= 4:
            break
    return sanitized[:4]


def _select_compiled_abilities(species: str, level: int) -> list[str]:
    pools_cache = _load_ability_pools_cache()
    pools = None
    for key in _species_candidate_keys(species):
        pools = pools_cache.get(key)
        if pools:
            break
    if not pools:
        return []
    desired = 1 if level < 20 else 2 if level < 40 else 3
    chosen: list[str] = []
    seen: set[str] = set()

    def add_bucket(bucket: str) -> None:
        for name in pools.get(bucket, []) or []:
            ability_name = str(name or "").strip()
            dedupe_key = ability_name.casefold()
            if not ability_name or dedupe_key in seen or not _is_known_ability_name(ability_name):
                continue
            seen.add(dedupe_key)
            chosen.append(ability_name)

    add_bucket("starting")
    add_bucket("basic")
    if level >= 20:
        add_bucket("advanced")
    if level >= 40:
        add_bucket("high")
    return chosen[:desired]


def _generate_fallback_abilities(species: str, level: int) -> list[str]:
    entry = _species_entry(species) or {}
    types = [str(t or "").strip() for t in (entry.get("types") or []) if str(t or "").strip() and str(t or "").strip().lower() != "none"]
    desired = 1 if level < 20 else 2 if level < 40 else 3
    by_type = {
        "Normal": ["Run Away", "Adaptability", "Technician"],
        "Fire": ["Blaze", "Flame Body", "Flash Fire"],
        "Water": ["Torrent", "Swift Swim", "Water Veil"],
        "Electric": ["Static", "Motor Drive", "Volt Absorb"],
        "Grass": ["Overgrow", "Chlorophyll", "Leaf Guard"],
        "Ice": ["Snow Cloak", "Ice Body", "Slush Rush"],
        "Fighting": ["Guts", "Iron Fist", "Steadfast"],
        "Poison": ["Poison Point", "Merciless", "Stench"],
        "Ground": ["Sand Veil", "Sand Force", "Sturdy"],
        "Flying": ["Keen Eye", "Big Pecks", "Gale Wings"],
        "Psychic": ["Synchronize", "Inner Focus", "Telepathy"],
        "Bug": ["Swarm", "Compound Eyes", "Shield Dust"],
        "Rock": ["Sturdy", "Rock Head", "Sand Force"],
        "Ghost": ["Cursed Body", "Frisk", "Infiltrator"],
        "Dragon": ["Pressure", "Inner Focus", "Mold Breaker"],
        "Dark": ["Unnerve", "Run Away", "Dark Aura"],
        "Steel": ["Sturdy", "Clear Body", "Steelworker"],
        "Fairy": ["Cute Charm", "Friend Guard", "Magic Guard"],
    }
    picks: list[str] = []
    for ability_name in [name for typ in types for name in by_type.get(typ, [])] + ["Sturdy", "Adaptability", "Technician"]:
        if _is_known_ability_name(ability_name) and ability_name not in picks:
            picks.append(ability_name)
        if len(picks) >= desired:
            break
    return picks[:desired]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, builder_root: Path, **kwargs):
        self._builder_root = builder_root
        super().__init__(*args, directory=str(builder_root), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        try:
            if self.path in {"/api/character_creation", "/api/character_creation/"}:
                payload = self._builder_root / "character_creation.json"
                if payload.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(payload.stat().st_size))
                    self.end_headers()
                    with payload.open("rb") as handle:
                        self.copyfile(handle, self.wfile)
                    return
            parsed = urlparse(self.path)
            if parsed.path == "/api/sprites/pokemon":
                params = parse_qs(parsed.query or "")
                name = str((params.get("name") or [""])[0] or "").strip()
                url = sprite_url_for(name, allow_download=True)
                if not url:
                    self.send_error(404, "Sprite not found")
                    return
                self.send_response(307)
                self.send_header("Location", url)
                self.end_headers()
                return
            if parsed.path.startswith("/sprites/"):
                filename = parsed.path.rsplit("/", 1)[-1]
                if "/" in filename or "\\" in filename or not filename.lower().endswith(".png"):
                    self.send_error(404, "Invalid sprite path")
                    return
                path = _SPRITE_DIR / filename
                if not path.exists():
                    ensure_sprite_filename(filename)
                if not path.exists():
                    self.send_error(404, "Sprite not found")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with path.open("rb") as handle:
                    self.copyfile(handle, self.wfile)
                return
            if parsed.path.startswith("/api/poke/type_icon/"):
                type_name = parsed.path.rsplit("/", 1)[-1]
                icon = type_icon_path(type_name)
                body = json.dumps(
                    {"available": bool(icon), "url": f"/poke/type-icons/{icon.name}" if icon else None}
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/api/poke/move/"):
                move_name = parsed.path.rsplit("/", 1)[-1]
                data = move_metadata(move_name) or {}
                move_type = data.get("type")
                icon = type_icon_path(str(move_type)) if move_type else None
                payload = dict(data) if data else {}
                payload["available"] = bool(data)
                payload["type_icon_url"] = f"/poke/type-icons/{icon.name}" if icon else None
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/api/poke/ability/"):
                ability_name = parsed.path.rsplit("/", 1)[-1]
                data = ability_metadata(ability_name) or {}
                payload = dict(data) if data else {}
                payload["available"] = bool(data)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/api/poke/item/"):
                item_name = parsed.path.rsplit("/", 1)[-1]
                data = item_metadata(item_name) or {}
                icon = item_icon_path(item_name)
                payload = dict(data) if data else {}
                payload["available"] = bool(data)
                payload["icon_url"] = f"/poke/item-icons/{icon.name}" if icon else None
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/api/poke/cry/"):
                pokemon_name = parsed.path.rsplit("/", 1)[-1]
                path = cry_path(pokemon_name)
                payload = {"available": bool(path), "url": f"/poke/cries/{path.name}" if path else None}
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/poke/type-icons/"):
                filename = parsed.path.rsplit("/", 1)[-1]
                slug = filename[:-4] if filename.lower().endswith(".png") else filename
                path = type_icon_path(slug)
                if not path or not path.exists():
                    self.send_error(404, "Type icon not found")
                    return
                media = "image/png" if path.suffix.lower() == ".png" else "image/webp"
                self.send_response(200)
                self.send_header("Content-Type", media)
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with path.open("rb") as handle:
                    self.copyfile(handle, self.wfile)
                return
            if parsed.path.startswith("/poke/item-icons/"):
                filename = parsed.path.rsplit("/", 1)[-1]
                slug = Path(filename).stem
                path = item_icon_path(slug)
                if not path or not path.exists():
                    self.send_error(404, "Item icon not found")
                    return
                media = "image/png" if path.suffix.lower() == ".png" else "image/webp"
                self.send_response(200)
                self.send_header("Content-Type", media)
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with path.open("rb") as handle:
                    self.copyfile(handle, self.wfile)
                return
            if parsed.path.startswith("/poke/cries/"):
                filename = parsed.path.rsplit("/", 1)[-1]
                stem = Path(filename).stem
                path = cry_path(stem)
                if not path or not path.exists():
                    self.send_error(404, "Cry not found")
                    return
                media = "audio/mpeg" if path.suffix.lower() == ".mp3" else "audio/ogg"
                self.send_response(200)
                self.send_header("Content-Type", media)
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with path.open("rb") as handle:
                    self.copyfile(handle, self.wfile)
                return
            if parsed.path == "/api/pokemon_defaults":
                params = parse_qs(parsed.query or "")
                species = str((params.get("species") or [""])[0] or "").strip()
                level_raw = str((params.get("level") or ["1"])[0] or "1").strip()
                try:
                    level = max(1, min(100, int(level_raw)))
                except ValueError:
                    level = 1
                payload = _pokemon_defaults_payload(species, level)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                status = 200 if payload.get("ok") else 404
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path in {"/favicon.ico", "/favicon.ico/"}:
                icon = self._builder_root / "favicon.ico"
                if icon.exists():
                    return super().do_GET()
                self.send_response(204)
                self.end_headers()
                return
            return super().do_GET()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def _pokemon_defaults_payload(species: str, level: int) -> dict:
    if not species:
        return {"ok": False, "error": "Species is required.", "moves": [], "abilities": []}
    try:
        payload = _foundry_species_payload(species)
        moves: list[str] = []
        abilities: list[str] = []
        if payload:
            system = payload.get("system") or {}
            moves = _select_foundry_moves(system.get("moves", {}).get("levelUp", []) or [], level)
            abilities = _select_foundry_abilities(system.get("abilities", {}) or {}, level)
        if not moves:
            moves = _select_csv_moves(species, level)
        if not moves:
            moves = _generate_fallback_moves(species)
        moves = _legalize_moves_for_species(species, level, _sanitize_moves(species, moves))
        if not abilities:
            abilities = _select_compiled_abilities(species, level)
        if not abilities:
            abilities = _generate_fallback_abilities(species, level)
        if not moves and not abilities:
            return {"ok": False, "error": "Species defaults not found in bundled data.", "species": species, "level": level, "moves": [], "abilities": []}
        return {"ok": bool(moves or abilities), "species": species, "level": level, "moves": moves[:4], "abilities": abilities[:3]}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "species": species, "level": level, "moves": [], "abilities": []}


def _is_server_responding(url: str) -> bool:
    try:
        with urlopen(url, timeout=1):
            return True
    except URLError:
        return False
    except Exception:
        return False


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _is_server_responding(url):
            return True
        time.sleep(0.2)
    return False


def _print_failure(reason: str) -> None:
    print("AutoPTU Character Builder failed to start.")
    if reason:
        print(reason)
    log_path = _log_path()
    if log_path.exists():
        print(f"Log: {log_path}")
    try:
        input("Press Enter to close...")
    except EOFError:
        time.sleep(15)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    args, _unknown = parser.parse_known_args()

    _trace_startup("launcher main entered")
    builder_root = _builder_root()
    _trace_startup(f"builder_root={builder_root}")
    create_path = builder_root / "create.html"
    _trace_startup(f"create_exists={create_path.exists()}")
    if not create_path.exists():
        reason = f"Builder files not found at {builder_root}"
        _write_log(reason)
        _trace_startup(reason)
        _print_failure(reason)
        return 1

    try:
        port = int(args.port) if args.port else _requested_port()
        _trace_startup(f"requested_port={port}")
        handler = lambda *args, **kwargs: _QuietHandler(*args, builder_root=builder_root, **kwargs)
        server = _ThreadingHTTPServer(("127.0.0.1", port), handler)
        _trace_startup("http server created")
    except Exception:
        reason = "Failed to start local builder server.\n" + traceback.format_exc()
        _write_log(reason)
        _trace_startup(reason)
        _print_failure("Failed to start local builder server.")
        return 1

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _trace_startup("serve_forever thread started")

    url = f"http://127.0.0.1:{port}/create.html"
    try:
        if not _wait_for_server(url):
            reason = "Builder server did not become ready in time."
            _write_log(reason)
            _trace_startup(reason)
            _print_failure(reason)
            return 1
        _trace_startup(f"server ready at {url}")
        print(f"AutoPTU Character Builder: {url}")
        if not args.no_browser:
            webbrowser.open(url, new=1)
        while thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    except Exception:
        reason = "Builder launcher crashed unexpectedly.\n" + traceback.format_exc()
        _write_log(reason)
        _print_failure("Builder launcher crashed unexpectedly.")
        return 1
    finally:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
