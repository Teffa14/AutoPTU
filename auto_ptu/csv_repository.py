"""Utilities to load PTU data from the provided CSV archives."""
from __future__ import annotations

import csv
import difflib
import json
import random
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

from .config import DATA_DIR, FILES_DIR
from .data_models import MoveSpec, PokemonSpec
from .learnsets import load_learnsets, normalize_species_key
from .foundry_loader import load_foundry_species_abilities, pick_abilities_for_level
from .natures import pick_random_nature_name
from .pokedex_loader import load_pokedex_species_abilities
from .hisui_rulebook_parser import HISUIDEX_OUT as HISUIDEX_PATH, REFERENCES_OUT as HISUI_REFERENCES_PATH
from .swsh_rulebook_parser import GALARDEX_OUT as SWSH_GALARDEX_PATH, REFERENCES_OUT as SWSH_REFERENCES_PATH


def _normalize_heading(value: str, idx: int) -> str:
    if not isinstance(value, str):
        return f"col_{idx}"
    value = value.strip().strip(":")
    value = value.lower()
    value = value.replace("/", "_").replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]", "", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or f"col_{idx}"


def _clean_cell(value: str | float | int | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def _dedupe_names(values: Iterable[str]) -> List[str]:
    results: List[str] = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        if any(existing.lower() == cleaned.lower() for existing in results):
            continue
        results.append(cleaned)
    return results


def _safe_int(value: str | float | int | None, default: int = 0) -> int:
    text = _clean_cell(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        digits = re.findall(r"-?\d+", text)
        if digits:
            try:
                return int(digits[0])
            except ValueError:
                return default
    return default


def _first_int(value: str | None) -> Optional[int]:
    text = _clean_cell(value)
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return None
    return None


def _split_list(value: str | None) -> List[str]:
    text = _clean_cell(value)
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"[;/,]", text)]
    return [p for p in parts if p]


def _normalize_catalog_key(value: str | None) -> str:
    text = _clean_cell(value).lower()
    if not text:
        return ""
    text = text.replace("\u2640", "f").replace("\u2642", "m")
    text = text.replace("’", "'").replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def _regional_form_aliases(name: str) -> List[str]:
    normalized = normalize_species_key(name)
    tokens = [token for token in normalized.split() if token]
    if len(tokens) < 2:
        return []
    regionals = {"alola", "alolan", "galar", "galarian", "hisui", "hisuian", "paldea", "paldean"}
    aliases: List[str] = []
    if tokens[0] in regionals:
        aliases.append(" ".join(tokens[1:] + [tokens[0]]))
    if tokens[-1] in regionals:
        aliases.append(" ".join([tokens[-1]] + tokens[:-1]))
    return aliases


def _load_ability_overrides() -> Dict[str, Dict[str, List[str]]]:
    path = DATA_DIR / "compiled" / "ability_overrides.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    overrides: Dict[str, Dict[str, List[str]]] = {}
    for raw_key, raw_entry in payload.items():
        key = normalize_species_key(str(raw_key))
        if not key or not isinstance(raw_entry, dict):
            continue
        entry: Dict[str, List[str]] = {}
        for tier in ("starting", "basic", "advanced", "high"):
            values = raw_entry.get(tier, [])
            if isinstance(values, str):
                values = [values]
            if not isinstance(values, list):
                values = []
            entry[tier] = _dedupe_names(values)
        overrides[key] = entry
    return overrides


def _load_builder_item_catalog() -> Dict[str, ItemRecord]:
    path = DATA_DIR.parent / "api" / "static" / "character_creation.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    items_root = payload.get("items", {}) if isinstance(payload, dict) else {}
    if not isinstance(items_root, dict):
        return {}
    records: Dict[str, ItemRecord] = {}
    for bucket_name, bucket in items_root.items():
        if not isinstance(bucket, list):
            continue
        for entry in bucket:
            if not isinstance(entry, dict):
                continue
            name = _clean_cell(entry.get("name"))
            if not name:
                continue
            description = _clean_cell(entry.get("description") or entry.get("effects") or entry.get("buff"))
            slot = _clean_cell(entry.get("slot"))
            tags = [_clean_cell(bucket_name)] if _clean_cell(bucket_name) else []
            record = ItemRecord(
                name=name,
                cost=_safe_cost(entry.get("cost")),
                slot=slot,
                description=description,
                tags=[tag for tag in tags if tag],
            )
            records.setdefault(record.name.lower(), record)
    return records


def _load_supplemental_item_catalog() -> Dict[str, ItemRecord]:
    path = DATA_DIR / "compiled" / "item_catalog_overrides.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    entries = payload.get("items", []) if isinstance(payload, dict) else []
    if not isinstance(entries, list):
        return {}
    records: Dict[str, ItemRecord] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = _clean_cell(entry.get("name"))
        if not name:
            continue
        description = _clean_cell(entry.get("description"))
        slot = _clean_cell(entry.get("slot") or "held")
        tags = [str(tag).strip() for tag in (entry.get("tags") or []) if str(tag).strip()]
        source = _clean_cell(entry.get("source"))
        if source:
            tags.append(source)
        records[name.lower()] = ItemRecord(
            name=name,
            cost=_safe_cost(entry.get("cost")),
            slot=slot,
            description=description,
            tags=_dedupe_names(tags),
        )
    return records


def _load_swsh_galardex() -> Dict[str, Any]:
    if not SWSH_GALARDEX_PATH.exists():
        return {}
    try:
        payload = json.loads(SWSH_GALARDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_swsh_references() -> Dict[str, Any]:
    if not SWSH_REFERENCES_PATH.exists():
        return {}
    try:
        payload = json.loads(SWSH_REFERENCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_hisuidex() -> Dict[str, Any]:
    if not HISUIDEX_PATH.exists():
        return {}
    try:
        payload = json.loads(HISUIDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_hisui_references() -> Dict[str, Any]:
    if not HISUI_REFERENCES_PATH.exists():
        return {}
    try:
        payload = json.loads(HISUI_REFERENCES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_swsh_movement_and_capabilities(capabilities: List[str]) -> tuple[Dict[str, int], List[str], List[str]]:
    movement = {
        "overland": 0,
        "sky": 0,
        "swim": 0,
        "levitate": 0,
        "burrow": 0,
        "h_jump": 0,
        "l_jump": 0,
        "power": 0,
    }
    caps: List[str] = []
    naturewalk: List[str] = []
    for raw in capabilities or []:
        text = _clean_cell(raw)
        if not text:
            continue
        lower = text.lower()
        match = re.match(r"^(Overland|Sky|Swim|Levitate|Burrow|Power)\s+(\d+)$", text, re.IGNORECASE)
        if match:
            key = match.group(1).strip().lower()
            movement[key] = _safe_int(match.group(2), 0)
            continue
        jump_match = re.match(r"^Jump\s+(\d+)\s*/\s*(\d+)$", text, re.IGNORECASE)
        if jump_match:
            movement["h_jump"] = _safe_int(jump_match.group(1), 0)
            movement["l_jump"] = _safe_int(jump_match.group(2), 0)
            continue
        if lower.startswith("naturewalk"):
            inner = re.search(r"\(([^)]+)\)", text)
            if inner:
                naturewalk.extend(_split_list(inner.group(1)))
            else:
                naturewalk.append(text)
            continue
        caps.append(text)
    return movement, _dedupe_names(caps), _dedupe_names(naturewalk)


def _parse_swsh_skill_table(skills: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    key_map = {
        "athl": "athletics",
        "acro": "acrobatics",
        "combat": "combat",
        "stealth": "stealth",
        "percep": "perception",
        "focus": "focus",
    }
    for raw in skills or []:
        text = _clean_cell(raw)
        if not text:
            continue
        match = re.match(r"^([A-Za-z]+)\s+(\d+)d6", text)
        if not match:
            continue
        key = key_map.get(match.group(1).strip().lower())
        if not key:
            continue
        out[key] = _safe_int(match.group(2), 0)
    return out


def _first_nonempty(row: object, *keys: str) -> str:
    getter = getattr(row, "get", None)
    for key in keys:
        value = ""
        if callable(getter):
            value = _clean_cell(getter(key))
        if value:
            return value
    return ""


def _read_dataframe(path: Path, header_row: int = 0) -> pd.DataFrame:
    df = pd.read_csv(path, header=header_row)
    df = df.dropna(how="all")
    df.columns = [_normalize_heading(col, idx) for idx, col in enumerate(df.columns)]
    return df


def _parse_range_metadata(text: str | None) -> Dict[str, Any]:
    cleaned = _clean_cell(text)
    info: Dict[str, Any] = {
        "range_kind": "Ranged",
        "range_value": None,
        "target_kind": "Ranged",
        "target_range": 6,
        "area_kind": None,
        "area_value": None,
    }
    if not cleaned:
        return info
    normalized = cleaned.replace("\u2013", "-")
    range_kind: Optional[str] = None
    range_value: Optional[int] = None
    target_kind: Optional[str] = None
    target_range: Optional[int] = None
    area_kind: Optional[str] = None
    area_value: Optional[int] = None

    leading = re.match(r"^\s*(\d+)\s*([,.;]|$)", normalized)
    if leading:
        range_value = int(leading.group(1))
        range_kind = "Ranged"
        target_kind = target_kind or "Ranged"
        target_range = target_range if target_range is not None else range_value

    segments = re.split(r"[;,]", normalized)
    for raw in segments:
        token = raw.strip()
        if not token:
            continue
        low = token.lower()
        area_match = re.search(r"(close|ranged)?\s*(burst|cone|line|blast)\s*(\d+)", low)
        if area_match:
            prefix = (area_match.group(1) or "").strip()
            shape = area_match.group(2)
            value = int(area_match.group(3))
            normalized_shape = shape.capitalize()
            if shape == "blast" and prefix == "close":
                normalized_shape = "CloseBlast"
            if area_kind is None:
                area_kind = normalized_shape
                area_value = value
            if normalized_shape in {"Burst", "Cone", "Line", "CloseBlast"} and prefix != "ranged":
                if range_kind is None:
                    range_kind = normalized_shape
                if target_kind in (None, "Ranged"):
                    target_kind = "Self"
                    target_range = 0
            elif normalized_shape == "Blast" and prefix == "ranged":
                range_kind = range_kind or "Ranged"
                target_kind = target_kind or "Ranged"
            elif normalized_shape == "CloseBlast":
                range_kind = range_kind or "CloseBlast"
                if target_kind in (None, "Ranged"):
                    target_kind = "Self"
                    target_range = 0
            continue
        if low in {"--", "-"}:
            continue
        if low.startswith("melee"):
            range_kind = range_kind or "Melee"
            target_kind = "Melee"
            target_range = 1
            continue
        if low.startswith("ranged"):
            range_kind = range_kind or "Ranged"
            target_kind = target_kind or "Ranged"
            continue
        if "self" in low or "user" in low:
            range_kind = range_kind or "Self"
            target_kind = "Self"
            target_range = 0
            continue
        if low.startswith("field"):
            range_kind = range_kind or "Field"
            target_kind = "Field"
            target_range = None
            continue
        number_match = re.match(r"^\s*(\d+)\s*$", token)
        if number_match and range_value is None:
            range_value = int(number_match.group(1))
            range_kind = range_kind or "Ranged"
            if target_kind is None:
                target_kind = "Ranged"
            target_range = target_range if target_range is not None else range_value

    if range_kind is None:
        range_kind = target_kind or "Ranged"
    if target_kind is None:
        target_kind = range_kind or "Ranged"
    if target_kind == "Ranged" and target_range is None:
        target_range = range_value if range_value is not None else 6
    if range_value is None and target_kind == "Ranged":
        range_value = target_range
    info.update(
        {
            "range_kind": range_kind,
            "range_value": range_value,
            "target_kind": target_kind,
            "target_range": target_range,
            "area_kind": area_kind,
            "area_value": area_value,
        }
    )
    return info


@dataclass
class MoveRecord:
    name: str
    type: str
    category: str
    db: int
    frequency: str
    ac: Optional[int]
    range_text: str
    effects: str

    def to_move_spec(self) -> MoveSpec:
        metadata = _parse_range_metadata(self.range_text)
        category = self.category or "Special"
        db_value = int(self.db or 0)
        if db_value <= 0 and str(category).strip().lower() != "status":
            db_value = 8
        return MoveSpec(
            name=self.name,
            type=self.type or "Normal",
            category=category,
            db=db_value,
            ac=self.ac,
            range_kind=metadata["range_kind"],
            range_value=metadata["range_value"],
            target_kind=metadata["target_kind"],
            target_range=metadata["target_range"],
            area_kind=metadata["area_kind"],
            area_value=metadata["area_value"],
            freq=self.frequency or "EOT",
            effects_text=self.effects or "",
            range_text=self.range_text or "",
        )

    def to_dict(self) -> Dict[str, Any]:  # type: ignore[name-defined]
        return {
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "damage_base": self.db,
            "frequency": self.frequency,
            "ac": self.ac,
            "range": self.range_text,
            "effects": self.effects,
        }


@dataclass
class ItemRecord:
    name: str
    cost: Optional[int]
    slot: str
    description: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "name": self.name,
            "slot": self.slot,
            "description": self.description,
        }
        if self.cost is not None:
            payload["cost"] = self.cost
        if self.tags:
            payload["tags"] = list(self.tags)
        return payload


def _safe_cost(value: str | float | int | None) -> Optional[int]:
    text = _clean_cell(value)
    if not text or text in {"--", "-"}:
        return None
    return _safe_int(text, 0)


def _weapon_tags_from_text(name: str, description: str) -> List[str]:
    text = f"{name} {description}".lower()
    tags: Set[str] = {"weapon"}
    if "shield" in text:
        tags.add("shield")
    if "small melee weapon" in text:
        tags.update({"melee", "small"})
    elif "large melee weapon" in text:
        tags.update({"melee", "large"})
    elif "melee weapon" in text:
        tags.add("melee")
    if "short range weapon" in text or "short-range weapon" in text:
        tags.update({"ranged", "short"})
    elif "long range weapon" in text or "long-range weapon" in text:
        tags.update({"ranged", "long"})
    elif "ranged weapon" in text:
        tags.add("ranged")
    if "reach quality" in text:
        tags.add("reach")
    return sorted(tags)


def _is_weapon_description(description: str) -> bool:
    text = description.lower()
    return any(
        phrase in text
        for phrase in (
            "melee weapon",
            "ranged weapon",
            "short range weapon",
            "short-range weapon",
            "long range weapon",
            "long-range weapon",
        )
    )


@dataclass
class SpeciesRecord:
    name: str
    base_stats: Dict[str, int]
    types: List[str]
    movement: Dict[str, int]
    capabilities: List[str] = field(default_factory=list)
    naturewalk: List[str] = field(default_factory=list)
    size: str = ""
    weight: Optional[float] = None
    egg_groups: List[str] = field(default_factory=list)
    skills: Dict[str, int] = field(default_factory=dict)

    def to_pokemon_spec(self, level: int, moves: List[MoveSpec], nickname: Optional[str] = None) -> PokemonSpec:
        return PokemonSpec(
            name=nickname or self.name,
            species=self.name,
            level=level,
            types=[t for t in self.types if t and t.lower() != "none"],
            hp_stat=self.base_stats.get("hp", 10),
            atk=self.base_stats.get("attack", 10),
            defense=self.base_stats.get("defense", 10),
            spatk=self.base_stats.get("special_attack", 10),
            spdef=self.base_stats.get("special_defense", 10),
            spd=self.base_stats.get("speed", 10),
            moves=moves,
            capabilities=[{"name": cap} for cap in self.capabilities],
            movement=dict(self.movement),
            trainer_features=[],
            statuses=[],
            items=[],
            abilities=[],
            tags=[],
            size=self.size,
            weight=self.weight,
        )

    def to_dict(self) -> Dict[str, Any]:  # type: ignore[name-defined]
        return {
            "name": self.name,
            "types": [t for t in self.types if t],
            "base_stats": dict(self.base_stats),
            "movement": dict(self.movement),
            "capabilities": list(self.capabilities),
            "naturewalk": list(self.naturewalk),
            "size": self.size,
            "weight": self.weight,
            "egg_groups": [g for g in self.egg_groups if g],
            "skills": dict(self.skills),
        }


class PTUCsvRepository:
    """Lazy loader for the CSV sheets dropped in the `files/` directory."""

    def __init__(self, root: Path | None = None, rng: random.Random | None = None):
        self.root = Path(root or FILES_DIR)
        self._species: Dict[str, SpeciesRecord] = {}
        self._moves: Dict[str, MoveRecord] = {}
        self._items: Dict[str, ItemRecord] = {}
        self._weapons: Dict[str, ItemRecord] = {}
        self._learnsets: Dict[str, List[Tuple[str, int]]] = {}
        self._ability_pools: Optional[Dict[str, Dict[str, List[str]]]] = None
        self._species_lookup: Optional[Dict[str, str]] = None
        self._move_lookup: Optional[Dict[str, str]] = None
        self._ability_lookup: Optional[Dict[str, str]] = None
        self._item_lookup: Optional[Dict[str, str]] = None
        self._rng = rng or random.Random()

    # ------------------ public API ------------------
    def available(self) -> bool:
        return self.root.exists()

    def list_species(self) -> Iterable[str]:
        self._ensure_species()
        return sorted(self._species.keys())

    def iter_species(self) -> Iterable[SpeciesRecord]:
        self._ensure_species()
        return self._species.values()

    def list_moves(self) -> Iterable[str]:
        self._ensure_moves()
        return sorted(self._moves.keys())

    def list_weapons(self) -> Iterable[str]:
        self._ensure_weapons()
        return sorted(self._weapons.keys())

    def list_items(self) -> Iterable[str]:
        self._ensure_items()
        return sorted(self._items.keys())

    def iter_moves(self) -> Iterable[MoveRecord]:
        self._ensure_moves()
        return self._moves.values()

    def iter_weapons(self) -> Iterable[ItemRecord]:
        self._ensure_weapons()
        return self._weapons.values()

    def iter_items(self) -> Iterable[ItemRecord]:
        self._ensure_items()
        return self._items.values()

    def get_species(self, name: str) -> Optional[SpeciesRecord]:
        self._ensure_species()
        key = self.resolve_species_name(name)
        if not key:
            return None
        return self._species.get(key.lower())

    def get_move(self, name: str) -> Optional[MoveRecord]:
        self._ensure_moves()
        raw = _clean_cell(name)
        canonical = self.resolve_move_name(name)
        if not canonical:
            return None
        key = canonical.lower()
        record = self._moves.get(key)
        if record is not None:
            if raw.strip().lower() == "toxic thread" and record.name.strip().lower() == "toxic threads":
                return replace(record, name="Toxic Thread")
            return record
        return None

    def resolve_species_name(self, name: str) -> Optional[str]:
        self._ensure_species()
        raw = _clean_cell(name)
        if not raw:
            return None
        direct = self._species.get(raw.lower())
        if direct is not None:
            return direct.name
        self._ensure_species_lookup()
        for candidate in [normalize_species_key(raw), *(_regional_form_aliases(raw))]:
            match = (self._species_lookup or {}).get(candidate)
            if match:
                return match
            compact = _normalize_catalog_key(candidate)
            match = (self._species_lookup or {}).get(compact)
            if match:
                return match
        normalized = _normalize_catalog_key(raw)
        match = (self._species_lookup or {}).get(normalized)
        if match:
            return match
        return self._fuzzy_lookup(normalized, self._species_lookup, cutoff=0.84)

    def resolve_move_name(self, name: str) -> Optional[str]:
        self._ensure_moves()
        raw = _clean_cell(name)
        if not raw:
            return None
        direct = self._moves.get(raw.lower())
        if direct is not None:
            return direct.name
        self._ensure_move_lookup()
        normalized = _normalize_catalog_key(raw)
        match = (self._move_lookup or {}).get(normalized)
        if match:
            return match
        return self._fuzzy_lookup(normalized, self._move_lookup, cutoff=0.88)

    def resolve_ability_name(self, species_name: str, ability_name: str, level: Optional[int] = None) -> Optional[str]:
        self._ensure_ability_pools()
        raw = _clean_cell(ability_name)
        if not raw:
            return None
        allowed_names: List[str] = []
        pools = None
        for key in self._ability_key_candidates(species_name):
            pools = (self._ability_pools or {}).get(key)
            if pools:
                break
        if isinstance(pools, dict):
            if level is not None:
                allowed_names = pick_abilities_for_level(pools, level, self._rng, existing=[])[0]
            if not allowed_names:
                for tier in ("starting", "basic", "advanced", "high"):
                    allowed_names.extend(list(pools.get(tier, []) or []))
        lookup = self._ability_lookup_for_names(allowed_names) if allowed_names else None
        normalized = _normalize_catalog_key(raw)
        if lookup:
            direct = lookup.get(normalized)
            if direct:
                return direct
            fuzzy = self._fuzzy_lookup(normalized, lookup, cutoff=0.88)
            if fuzzy:
                return fuzzy
        self._ensure_ability_lookup()
        direct = (self._ability_lookup or {}).get(normalized)
        if direct:
            return direct
        return self._fuzzy_lookup(normalized, self._ability_lookup, cutoff=0.88)

    def resolve_item_name(self, item_name: str) -> Optional[str]:
        self._ensure_items()
        raw = _clean_cell(item_name)
        if not raw:
            return None
        direct = self._items.get(raw.lower())
        if direct is not None:
            return direct.name
        self._ensure_item_lookup()
        normalized = _normalize_catalog_key(raw)
        match = (self._item_lookup or {}).get(normalized)
        if match:
            return match
        return self._fuzzy_lookup(normalized, self._item_lookup, cutoff=0.88)

    def build_pokemon_spec(
        self,
        name: str,
        level: int = 20,
        move_names: Optional[List[str]] = None,
        nickname: Optional[str] = None,
        assign_abilities: bool = False,
        assign_nature: bool = False,
        nature: Optional[str] = None,
    ) -> PokemonSpec:
        species = self.get_species(name)
        if not species:
            species = self._default_form_record(name)
        if not species:
            raise ValueError(f"Species '{name}' not found in CSV repository at {self.root}")
        moves = self._select_moves(species, move_names, level)
        spec = species.to_pokemon_spec(level=level, moves=moves, nickname=nickname)
        chosen_nature = str(nature or "").strip()
        if not chosen_nature and assign_nature:
            chosen_nature = pick_random_nature_name(self._rng, root=self.root)
        if chosen_nature:
            spec.nature = chosen_nature
        if assign_abilities and not spec.abilities:
            abilities = self._select_abilities(species.name, level)
            if abilities:
                spec.abilities = [{"name": name} for name in abilities]
        return spec

    def _default_form_record(self, name: str) -> Optional[SpeciesRecord]:
        base_key = normalize_species_key(name)
        if not base_key:
            return None
        candidates: List[Tuple[int, SpeciesRecord]] = []
        for record in self._species.values():
            record_key = normalize_species_key(record.name)
            if not record_key:
                continue
            if record_key == base_key:
                return record
            if record_key.startswith(f"{base_key} "):
                form_key = record_key[len(base_key) :].strip()
                score = self._default_form_score(form_key)
                candidates.append((score, record))
        if not candidates:
            return None
        candidates.sort(key=lambda row: (row[0], row[1].name))
        return candidates[-1][1]

    @staticmethod
    def _default_form_score(form_key: str) -> int:
        if not form_key:
            return 200
        tokens = [token for token in form_key.split() if token]
        score = 0
        default_tokens = {
            "normal",
            "base",
            "standard",
            "average",
            "solo",
            "midday",
            "altered",
            "incarnate",
            "hero",
            "50",
        }
        minor_tokens = {"male", "female", "day"}
        mega_tokens = {"mega", "primal", "gmax", "gigantamax"}
        if any(token in default_tokens for token in tokens):
            score += 80
        if any(token in {"n", "default"} for token in tokens):
            score += 60
        if any(token in minor_tokens for token in tokens):
            score += 10
        if any(token in mega_tokens for token in tokens):
            score -= 100
        return score

    # ------------------ internal loaders ------------------
    def _ensure_species(self) -> None:
        if self._species:
            return
        path = self.root / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Pokemon Data.csv"
        if not path.exists():
            raise FileNotFoundError(f"Species CSV not found at {path}")
        df = _read_dataframe(path, header_row=1)
        skill_path = self.root / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Pokemon Skills.csv"
        skills = self._load_skill_table(skill_path) if skill_path.exists() else {}
        species: Dict[str, SpeciesRecord] = {}
        for _, row in df.iterrows():
            species_name = _clean_cell(row.get("pokemon"))
            if not species_name:
                continue
            stats = {
                "hp": _safe_int(row.get("hp"), 10),
                "attack": _safe_int(row.get("attack"), 10),
                "defense": _safe_int(row.get("defense"), 10),
                "special_attack": _safe_int(row.get("special_attack"), 10),
                "special_defense": _safe_int(row.get("special_defense"), 10),
                "speed": _safe_int(row.get("speed"), 10),
            }
            movement = {
                "overland": _safe_int(row.get("overland")),
                "sky": _safe_int(row.get("sky")),
                "swim": _safe_int(row.get("swim")),
                "levitate": _safe_int(row.get("levitate")),
                "burrow": _safe_int(row.get("burrow")),
                "h_jump": _safe_int(row.get("h_jump")),
                "l_jump": _safe_int(row.get("l_jump")),
                "power": _safe_int(row.get("power")),
            }
            capabilities: List[str] = []
            for idx in range(1, 10):
                cap_name = _clean_cell(row.get(f"capability_{idx}"))
                if not cap_name or cap_name == "-":
                    continue
                capabilities.append(cap_name)
            record = SpeciesRecord(
                name=species_name,
                base_stats=stats,
                types=[
                    _first_nonempty(row, "type1", "type_1"),
                    _first_nonempty(row, "type2", "type_2"),
                ],
                movement=movement,
                capabilities=capabilities,
                naturewalk=_split_list(row.get("naturewalk")),
                size=_clean_cell(row.get("size")),
                weight=float(_safe_int(row.get("weight"), 0)),
                egg_groups=[_clean_cell(row.get("egggroup1")), _clean_cell(row.get("egggroup2"))],
                skills=skills.get(species_name.lower(), {}),
            )
            species[species_name.lower()] = record
        swsh_payload = _load_swsh_galardex()
        swsh_entries = swsh_payload.get("entries", {}) if isinstance(swsh_payload, dict) else {}
        if isinstance(swsh_entries, dict):
            for raw_name, raw_entry in swsh_entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                species_name = _clean_cell(raw_name)
                if not species_name:
                    continue
                key = species_name.lower()
                if key in species:
                    continue
                base_stats = raw_entry.get("base_stats", {}) if isinstance(raw_entry.get("base_stats"), dict) else {}
                capabilities_raw = raw_entry.get("capabilities", []) if isinstance(raw_entry.get("capabilities"), list) else []
                movement, capabilities, naturewalk = _parse_swsh_movement_and_capabilities(capabilities_raw)
                record = SpeciesRecord(
                    name=species_name,
                    base_stats={
                        "hp": _safe_int(base_stats.get("hp"), 10),
                        "attack": _safe_int(base_stats.get("attack"), 10),
                        "defense": _safe_int(base_stats.get("defense"), 10),
                        "special_attack": _safe_int(base_stats.get("special_attack"), 10),
                        "special_defense": _safe_int(base_stats.get("special_defense"), 10),
                        "speed": _safe_int(base_stats.get("speed"), 10),
                    },
                    types=[str(value).strip() for value in (raw_entry.get("types") or []) if str(value).strip() and str(value).strip().lower() != "none"],
                    movement=movement,
                    capabilities=capabilities,
                    naturewalk=naturewalk,
                    size=_clean_cell(raw_entry.get("size")),
                    weight=float(raw_entry.get("weight")) if raw_entry.get("weight") not in (None, "") else None,
                    egg_groups=[_clean_cell(value) for value in (raw_entry.get("egg_groups") or []) if _clean_cell(value)],
                    skills=_parse_swsh_skill_table(raw_entry.get("skills") or []),
                )
                species[key] = record
        hisui_payload = _load_hisuidex()
        hisui_entries = hisui_payload.get("entries", {}) if isinstance(hisui_payload, dict) else {}
        if isinstance(hisui_entries, dict):
            for raw_name, raw_entry in hisui_entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                species_name = _clean_cell(raw_name)
                if not species_name:
                    continue
                key = species_name.lower()
                if key in species:
                    continue
                base_stats = raw_entry.get("base_stats", {}) if isinstance(raw_entry.get("base_stats"), dict) else {}
                capabilities_raw = raw_entry.get("capabilities", []) if isinstance(raw_entry.get("capabilities"), list) else []
                movement, capabilities, naturewalk = _parse_swsh_movement_and_capabilities(capabilities_raw)
                record = SpeciesRecord(
                    name=species_name,
                    base_stats={
                        "hp": _safe_int(base_stats.get("hp"), 10),
                        "attack": _safe_int(base_stats.get("attack"), 10),
                        "defense": _safe_int(base_stats.get("defense"), 10),
                        "special_attack": _safe_int(base_stats.get("special_attack"), 10),
                        "special_defense": _safe_int(base_stats.get("special_defense"), 10),
                        "speed": _safe_int(base_stats.get("speed"), 10),
                    },
                    types=[str(value).strip() for value in (raw_entry.get("types") or []) if str(value).strip() and str(value).strip().lower() != "none"],
                    movement=movement,
                    capabilities=capabilities,
                    naturewalk=naturewalk,
                    size=_clean_cell(raw_entry.get("size")),
                    weight=float(raw_entry.get("weight")) if raw_entry.get("weight") not in (None, "") else None,
                    egg_groups=[_clean_cell(value) for value in (raw_entry.get("egg_groups") or []) if _clean_cell(value)],
                    skills=_parse_swsh_skill_table(raw_entry.get("skills") or []),
                )
                species[key] = record
        self._species = species
        self._species_lookup = None

    def _ensure_moves(self) -> None:
        if self._moves:
            return
        path = self.root / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
        if not path.exists():
            raise FileNotFoundError(f"Moves CSV not found at {path}")
        df = _read_dataframe(path, header_row=1)
        moves: Dict[str, MoveRecord] = {}
        for _, row in df.iterrows():
            name = _clean_cell(row.get("name"))
            if not name:
                continue
            move_type = _clean_cell(row.get("type")) or _clean_cell(row.get("type1"))
            category = _clean_cell(row.get("category")) or _clean_cell(row.get("category1"))
            record = MoveRecord(
                name=name,
                type=move_type,
                category=category,
                db=_safe_int(row.get("damage_base"), 0),
                frequency=_clean_cell(row.get("frequency")),
                ac=_first_int(_clean_cell(row.get("ac"))),
                range_text=_clean_cell(row.get("range")),
                effects=_clean_cell(row.get("effects")),
            )
            moves[name.lower()] = record
        swsh_refs = _load_swsh_references()
        swsh_moves = swsh_refs.get("moves", {}) if isinstance(swsh_refs, dict) else {}
        if isinstance(swsh_moves, dict):
            for raw_name, raw_entry in swsh_moves.items():
                if not isinstance(raw_entry, dict):
                    continue
                name = _clean_cell(raw_name)
                if not name or name.lower() in moves:
                    continue
                damage_base = _clean_cell(raw_entry.get("damage_base"))
                db_value = _safe_int(damage_base.split(":", 1)[0] if ":" in damage_base else damage_base, 0)
                record = MoveRecord(
                    name=name,
                    type=_clean_cell(raw_entry.get("type")),
                    category=_clean_cell(raw_entry.get("class")),
                    db=db_value,
                    frequency=_clean_cell(raw_entry.get("frequency")),
                    ac=_first_int(_clean_cell(raw_entry.get("ac"))),
                    range_text=_clean_cell(raw_entry.get("range")),
                    effects=_clean_cell(raw_entry.get("effect")),
                )
                moves[name.lower()] = record
        hisui_refs = _load_hisui_references()
        hisui_moves = hisui_refs.get("moves", {}) if isinstance(hisui_refs, dict) else {}
        if isinstance(hisui_moves, dict):
            for raw_name, raw_entry in hisui_moves.items():
                if not isinstance(raw_entry, dict):
                    continue
                name = _clean_cell(raw_name)
                if not name or name.lower() in moves:
                    continue
                damage_base = _clean_cell(raw_entry.get("damage_base"))
                db_value = _safe_int(damage_base.split(":", 1)[0] if ":" in damage_base else damage_base, 0)
                record = MoveRecord(
                    name=name,
                    type=_clean_cell(raw_entry.get("type")),
                    category=_clean_cell(raw_entry.get("class")),
                    db=db_value,
                    frequency=_clean_cell(raw_entry.get("frequency")),
                    ac=_first_int(_clean_cell(raw_entry.get("ac"))),
                    range_text=_clean_cell(raw_entry.get("range")),
                    effects=_clean_cell(raw_entry.get("effect")),
                )
                moves[name.lower()] = record
        self._moves = moves
        self._move_lookup = None

    def _ensure_items(self) -> None:
        if self._items:
            return
        path = self.root / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv"
        if not path.exists():
            return
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if len(rows) < 3:
            return
        item_records: Dict[str, ItemRecord] = {}
        column_groups = [
            {"start": 0, "kind": "key"},
            {"start": 3, "kind": "key"},
            {"start": 6, "kind": "food"},
            {"start": 9, "kind": "held"},
            {"start": 12, "kind": "ball"},
            {"start": 16, "kind": "equipment"},
        ]
        for raw in rows[2:]:
            if not raw:
                continue
            for group in column_groups:
                start = int(group["start"])
                if start >= len(raw):
                    continue
                name = _clean_cell(raw[start] if start < len(raw) else "")
                if not name:
                    continue
                cost = _safe_cost(raw[start + 1] if start + 1 < len(raw) else "")
                slot = _clean_cell(raw[start + 2] if group["kind"] == "equipment" and start + 2 < len(raw) else "")
                desc_index = start + 3 if group["kind"] == "equipment" else start + 2
                description = _clean_cell(raw[desc_index] if desc_index < len(raw) else "")
                tags = [str(group["kind"])]
                if group["kind"] == "equipment" and slot:
                    tags.append(slot.lower())
                record = ItemRecord(
                    name=name,
                    cost=cost,
                    slot=slot,
                    description=description,
                    tags=tags,
                )
                item_records[record.name.lower()] = record
        for key, record in _load_builder_item_catalog().items():
            item_records.setdefault(key, record)
        for key, record in _load_supplemental_item_catalog().items():
            item_records.setdefault(key, record)
        self._items = item_records
        self._item_lookup = None

    def _ensure_weapons(self) -> None:
        if self._weapons:
            return
        self._ensure_items()
        path = self.root / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv"
        if not path.exists():
            return
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if len(rows) < 2:
            return
        headers = rows[1]
        if len(headers) < 4:
            return
        equip_start = len(headers) - 4
        for raw in rows[2:]:
            if not raw:
                continue
            if len(raw) < len(headers):
                raw = raw + [""] * (len(headers) - len(raw))
            name, cost, slot, description = raw[equip_start : equip_start + 4]
            name = _clean_cell(name)
            if not name:
                continue
            description = _clean_cell(description)
            if not _is_weapon_description(description):
                continue
            tags = _weapon_tags_from_text(name, description)
            record = ItemRecord(
                name=name,
                cost=_safe_cost(cost),
                slot=_clean_cell(slot),
                description=description,
                tags=tags,
            )
            self._weapons[record.name.lower()] = record

    def _ensure_learnsets(self) -> None:
        if self._learnsets:
            return
        self._learnsets = load_learnsets(self.root)

    def _ensure_ability_pools(self) -> None:
        if self._ability_pools is not None:
            return
        pokedex_pools: Dict[str, Dict[str, List[str]]]
        foundry_pools: Dict[str, Dict[str, List[str]]]
        try:
            pokedex_pools = load_pokedex_species_abilities()
        except Exception:
            pokedex_pools = {}
        try:
            foundry_pools = load_foundry_species_abilities()
        except Exception:
            foundry_pools = {}
        swsh_payload = _load_swsh_galardex()
        swsh_pools: Dict[str, Dict[str, List[str]]] = {}
        swsh_entries = swsh_payload.get("entries", {}) if isinstance(swsh_payload, dict) else {}
        if isinstance(swsh_entries, dict):
            for raw_species, raw_entry in swsh_entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                abilities = raw_entry.get("abilities", {})
                if not isinstance(abilities, dict):
                    continue
                key = normalize_species_key(str(raw_species))
                if not key:
                    continue
                swsh_pools[key] = {
                    "starting": _dedupe_names(abilities.get("basic", [])),
                    "basic": _dedupe_names(abilities.get("basic", [])),
                    "advanced": _dedupe_names(abilities.get("advanced", [])),
                    "high": _dedupe_names(abilities.get("high", [])),
                }
        hisui_payload = _load_hisuidex()
        hisui_pools: Dict[str, Dict[str, List[str]]] = {}
        hisui_entries = hisui_payload.get("entries", {}) if isinstance(hisui_payload, dict) else {}
        if isinstance(hisui_entries, dict):
            for raw_species, raw_entry in hisui_entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                abilities = raw_entry.get("abilities", {})
                if not isinstance(abilities, dict):
                    continue
                key = normalize_species_key(str(raw_species))
                if not key:
                    continue
                hisui_pools[key] = {
                    "starting": _dedupe_names(abilities.get("basic", [])),
                    "basic": _dedupe_names(abilities.get("basic", [])),
                    "advanced": _dedupe_names(abilities.get("advanced", [])),
                    "high": _dedupe_names(abilities.get("high", [])),
                }
        overrides = _load_ability_overrides()
        self._ability_pools = {}
        for key in sorted(set(pokedex_pools) | set(foundry_pools) | set(swsh_pools) | set(hisui_pools) | set(overrides)):
            if key in overrides:
                self._ability_pools[key] = overrides[key]
                continue
            pokedex_entry = pokedex_pools.get(key, {})
            foundry_entry = foundry_pools.get(key, {})
            swsh_entry = swsh_pools.get(key, {})
            hisui_entry = hisui_pools.get(key, {})
            prefer_official = any(
                isinstance(entry, dict) and any(entry.get(tier, []) for tier in ("starting", "basic", "advanced", "high"))
                for entry in (pokedex_entry, swsh_entry, hisui_entry)
            )
            merged_entry: Dict[str, List[str]] = {}
            for tier in ("starting", "basic", "advanced", "high"):
                names: List[str] = []
                source_names = (
                    (pokedex_entry.get(tier, []) if isinstance(pokedex_entry, dict) else [])
                    + (swsh_entry.get(tier, []) if isinstance(swsh_entry, dict) else [])
                    + (hisui_entry.get(tier, []) if isinstance(hisui_entry, dict) else [])
                )
                if not prefer_official:
                    source_names += foundry_entry.get(tier, []) if isinstance(foundry_entry, dict) else []
                for name in source_names:
                    cleaned = str(name or "").strip()
                    if not cleaned:
                        continue
                    if any(existing.lower() == cleaned.lower() for existing in names):
                        continue
                    names.append(cleaned)
                merged_entry[tier] = names
            if any(merged_entry[tier] for tier in ("starting", "basic", "advanced", "high")):
                self._ability_pools[key] = merged_entry
        self._ability_lookup = None

    def _ensure_species_lookup(self) -> None:
        if self._species_lookup is not None:
            return
        self._ensure_species()
        lookup: Dict[str, str] = {}
        for record in self._species.values():
            candidates = {
                record.name.lower(),
                normalize_species_key(record.name),
                _normalize_catalog_key(record.name),
            }
            candidates.update(_regional_form_aliases(record.name))
            for alias in list(candidates):
                candidates.add(_normalize_catalog_key(alias))
            for candidate in candidates:
                if candidate:
                    lookup.setdefault(candidate, record.name)
        self._species_lookup = lookup

    def _ensure_move_lookup(self) -> None:
        if self._move_lookup is not None:
            return
        self._ensure_moves()
        lookup: Dict[str, str] = {}
        alias_map = {
            "toxicthread": "Toxic Threads",
            "toxic thread": "Toxic Threads",
        }
        for record in self._moves.values():
            candidates = {
                record.name.lower(),
                _normalize_catalog_key(record.name),
            }
            for candidate in candidates:
                if candidate:
                    lookup.setdefault(candidate, record.name)
        for alias, canonical in alias_map.items():
            lookup[_normalize_catalog_key(alias)] = canonical
        self._move_lookup = lookup

    def _ensure_ability_lookup(self) -> None:
        if self._ability_lookup is not None:
            return
        self._ensure_ability_pools()
        names: List[str] = []
        for pools in (self._ability_pools or {}).values():
            if not isinstance(pools, dict):
                continue
            for tier in ("starting", "basic", "advanced", "high"):
                names.extend(list(pools.get(tier, []) or []))
        self._ability_lookup = self._ability_lookup_for_names(names)

    def _ensure_item_lookup(self) -> None:
        if self._item_lookup is not None:
            return
        self._ensure_items()
        lookup: Dict[str, str] = {}
        alias_map: Dict[str, str] = {}
        overrides_path = DATA_DIR / "compiled" / "item_catalog_overrides.json"
        if overrides_path.exists():
            try:
                override_payload = json.loads(overrides_path.read_text(encoding="utf-8"))
            except Exception:
                override_payload = {}
            for entry in override_payload.get("items", []) if isinstance(override_payload, dict) else []:
                if not isinstance(entry, dict):
                    continue
                canonical = _clean_cell(entry.get("name"))
                if not canonical:
                    continue
                for alias in entry.get("aliases", []) or []:
                    normalized_alias = _normalize_catalog_key(alias)
                    if normalized_alias:
                        alias_map[normalized_alias] = canonical
        for record in self._items.values():
            candidates = {
                record.name.lower(),
                _normalize_catalog_key(record.name),
            }
            for candidate in candidates:
                if candidate:
                    lookup.setdefault(candidate, record.name)
        for alias, canonical in alias_map.items():
            lookup[alias] = canonical
        self._item_lookup = lookup

    @staticmethod
    def _ability_lookup_for_names(names: Iterable[str]) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        for name in _dedupe_names(names):
            normalized = _normalize_catalog_key(name)
            if normalized:
                lookup.setdefault(normalized, name)
        return lookup

    @staticmethod
    def _fuzzy_lookup(value: str, lookup: Optional[Dict[str, str]], cutoff: float = 0.88) -> Optional[str]:
        if not value or not lookup:
            return None
        matches = difflib.get_close_matches(value, list(lookup.keys()), n=1, cutoff=cutoff)
        if not matches:
            return None
        return lookup.get(matches[0])

    def _load_skill_table(self, path: Path) -> Dict[str, Dict[str, int]]:
        df = _read_dataframe(path, header_row=0)
        skill_data: Dict[str, Dict[str, int]] = {}
        for _, row in df.iterrows():
            name = _clean_cell(row.get("pokemon"))
            if not name:
                continue
            entry: Dict[str, int] = {}
            for col, val in row.items():
                if col.endswith("_mod") or col == "pokemon":
                    continue
                entry[col] = _safe_int(val, 0)
            skill_data[name.lower()] = entry
        return skill_data

    def _select_moves(
        self, species: SpeciesRecord, preferred: Optional[List[str]], level: int
    ) -> List[MoveSpec]:
        self._ensure_moves()
        self._ensure_learnsets()
        if preferred:
            moves: List[MoveSpec] = []
            for mv in preferred:
                record = self.get_move(mv)
                if record:
                    moves.append(record.to_move_spec())
            if moves:
                return moves
        learnset: List[Tuple[str, int]] = []
        for species_key in self._learnset_key_candidates(species.name):
            learnset = self._learnsets.get(species_key, [])
            if learnset:
                break
        eligible_learnset = [(move_name, move_level) for move_name, move_level in learnset if move_level <= level]
        candidate_records = self._records_from_learnset(eligible_learnset)
        moves = self._build_minmax_moveset(species, candidate_records)
        if len(moves) < 4 or self._damaging_count(moves) < 2 or self._repeatable_damaging_count(moves) == 0:
            augmented_pool = self._augment_move_pool(species, candidate_records)
            moves = self._build_minmax_moveset(species, augmented_pool)
        if moves and (self._damaging_count(moves) < 2 or self._repeatable_damaging_count(moves) == 0):
            offensive_mode = self._infer_offense_mode(species, candidate_records)
            damaging_pool = [
                record
                for record in self._moves.values()
                if self._is_damaging_record(record) and not self._is_self_destructive_record(record)
            ]
            damaging_pool.sort(
                key=lambda record: (
                    1 if self._is_repeatable_frequency(record.frequency) else 0,
                    self._damage_move_score(species, record, offensive_mode),
                ),
                reverse=True,
            )
            for record in damaging_pool:
                if any(existing.name == record.name for existing in moves):
                    continue
                if len(moves) < 4:
                    moves.append(record.to_move_spec())
                else:
                    replaced = False
                    for idx in range(len(moves) - 1, -1, -1):
                        move = moves[idx]
                        if (move.category or "").strip().lower() == "status" or int(move.db or 0) <= 0:
                            moves[idx] = record.to_move_spec()
                            replaced = True
                            break
                    if not replaced:
                        moves[-1] = record.to_move_spec()
                if self._damaging_count(moves) >= 2 and self._repeatable_damaging_count(moves) >= 1:
                    break
        if not moves and self._moves:
            fallback = next(
                (record for record in self._moves.values() if self._is_damaging_record(record)),
                next(iter(self._moves.values())),
            )
            moves.append(fallback.to_move_spec())
        return moves[:4]

    def _records_from_learnset(self, eligible_learnset: List[Tuple[str, int]]) -> List[MoveRecord]:
        self._ensure_moves()
        grouped: Dict[str, MoveRecord] = {}
        for move_name, _move_level in sorted(eligible_learnset, key=lambda item: item[1], reverse=True):
            record = self._moves.get(move_name.lower())
            if record is None:
                continue
            key = self._move_pool_key(record.name)
            existing = grouped.get(key)
            if existing is None or (self._is_move_family_base(record.name) and not self._is_move_family_base(existing.name)):
                grouped[key] = record
        return list(grouped.values())

    @staticmethod
    def _move_pool_key(name: str) -> str:
        normalized = str(name or "").strip().lower()
        if normalized == "hidden power" or normalized.startswith("hidden power "):
            return "hidden power [type]"
        return normalized

    @staticmethod
    def _is_move_family_base(name: str) -> bool:
        return str(name or "").strip().lower() == "hidden power"

    def _resolve_variant_record(self, record: MoveRecord) -> MoveRecord:
        if self._move_pool_key(record.name) != "hidden power [type]":
            return record
        typed_variants = [
            candidate
            for candidate in self._moves.values()
            if self._move_pool_key(candidate.name) == "hidden power [type]" and not self._is_move_family_base(candidate.name)
        ]
        if not typed_variants:
            return record
        return self._rng.choice(typed_variants)

    def _learnset_key_candidates(self, species_name: str) -> List[str]:
        raw = normalize_species_key(species_name)
        if not raw:
            return []
        candidates: List[str] = []

        def add(value: str) -> None:
            key = normalize_species_key(value)
            if key and key not in candidates:
                candidates.append(key)

        add(raw)
        add(raw.replace("%", "").strip())
        tokens = [token for token in raw.replace("%", "").split() if token]
        if not tokens:
            return candidates
        base = tokens[0]
        add(base)

        token_aliases = {
            "female": "f",
            "male": "m",
            "galarian": "galar",
            "hisuian": "hisui",
            "alolan": "alola",
            "paldean": "paldea",
            "incarnate": "i",
            "therian": "t",
            "average": "average",
            "av": "average",
            "a": "average",
            "small": "small",
            "sm": "small",
            "s": "small",
            "large": "large",
            "la": "large",
            "l": "large",
            "super": "super",
            "su": "super",
            "da": "day",
            "day": "day",
            "night": "night",
            "midday": "day",
            "midnight": "night",
            "po": "pom pom",
            "pau": "pau",
            "pa": "pau",
        }
        mapped_tokens = [token_aliases.get(token, token) for token in tokens]
        add(" ".join(mapped_tokens))

        if base == "nidoran" and len(tokens) > 1:
            if tokens[1] in {"f", "female"}:
                add("nidoran f")
            if tokens[1] in {"m", "male"}:
                add("nidoran m")
        if base == "stunfisk" and len(tokens) > 1 and tokens[1] in {"g", "galar", "galarian"}:
            add("stunfisk galar")
        if base in {"pumpkaboo", "gourgeist"} and len(tokens) > 1:
            size_alias = {"a": "average", "av": "average", "sm": "small", "la": "large", "su": "super"}
            size = size_alias.get(tokens[1], tokens[1])
            add(f"{base} {size}")
        if base == "rotom":
            if len(tokens) > 1:
                rotom_alias = {
                    "n": "normal",
                    "fn": "fan",
                    "fr": "frost",
                    "h": "heat",
                    "m": "mow",
                    "w": "wash",
                }
                form = rotom_alias.get(tokens[1], tokens[1])
                add(f"rotom {form}")
            add("rotom")
        if base == "lycanroc" and len(tokens) > 1:
            lycanroc_alias = {
                "midday": "day",
                "midnight": "night",
                "da": "day",
                "n": "night",
                "d": "dusk",
            }
            form = lycanroc_alias.get(tokens[1], tokens[1])
            add(f"lycanroc {form}")
        evolution_fallbacks = {
            "basculegion": "basculin",
        }
        if base in evolution_fallbacks:
            add(evolution_fallbacks[base])
        return candidates

    @staticmethod
    def _damaging_count(moves: List[MoveSpec]) -> int:
        return sum(1 for move in moves if (move.category or "").strip().lower() != "status" and int(move.db or 0) > 0)

    @classmethod
    def _repeatable_damaging_count(cls, moves: List[MoveSpec]) -> int:
        return sum(
            1
            for move in moves
            if (move.category or "").strip().lower() != "status"
            and int(move.db or 0) > 0
            and cls._is_repeatable_frequency(move.freq)
        )

    @staticmethod
    def _is_repeatable_frequency(frequency: str) -> bool:
        text = str(frequency or "").strip().lower()
        if "at-will" in text or "eot" in text:
            return True
        return text in {"standard", "free", "shift", "action"}

    def _build_minmax_moveset(self, species: SpeciesRecord, candidates: List[MoveRecord]) -> List[MoveSpec]:
        if not candidates:
            return []
        offensive_mode = self._infer_offense_mode(species, candidates)
        damaging_candidates = [record for record in candidates if self._is_damaging_record(record)]
        status_candidates = [record for record in candidates if not self._is_damaging_record(record)]
        damaging_candidates.sort(
            key=lambda record: self._damage_move_score(species, record, offensive_mode),
            reverse=True,
        )
        repeatable_damaging = [
            record for record in damaging_candidates if self._is_repeatable_frequency(record.frequency)
        ]
        burst_damaging = [record for record in damaging_candidates if record not in repeatable_damaging]
        selected_records: List[MoveRecord] = []
        used_names: Set[str] = set()
        used_types: Set[str] = set()
        target_damaging = 3 if status_candidates else 4
        target_damaging = min(target_damaging, len(damaging_candidates))

        def damaging_selected_count() -> int:
            return sum(1 for record in selected_records if self._is_damaging_record(record))

        def try_add(record: MoveRecord, enforce_diversity: bool = True) -> bool:
            key = self._move_pool_key(record.name)
            if key in used_names:
                return False
            move_type = (record.type or "").strip().lower()
            if enforce_diversity and move_type and move_type in used_types and damaging_selected_count() >= 2:
                return False
            if not self._is_damaging_record(record):
                status_count = sum(
                    1
                    for chosen in selected_records
                    if (chosen.category or "").strip().lower() == "status" or int(chosen.db or 0) <= 0
                )
                if status_count >= 2:
                    return False
            selected_records.append(record)
            used_names.add(key)
            if move_type:
                used_types.add(move_type)
            return True

        if repeatable_damaging:
            for record in repeatable_damaging:
                if try_add(record):
                    break

        for record in repeatable_damaging:
            if damaging_selected_count() >= target_damaging:
                break
            try_add(record)

        max_burst = 1 if repeatable_damaging else target_damaging
        burst_added = 0
        for record in burst_damaging:
            if damaging_selected_count() >= target_damaging:
                break
            if repeatable_damaging and burst_added >= max_burst:
                continue
            if try_add(record):
                burst_added += 1

        for record in damaging_candidates:
            if damaging_selected_count() >= target_damaging:
                break
            try_add(record)

        status_slots = max(0, min(2, 4 - len(selected_records)))
        if status_slots > 0 and status_candidates:
            status_candidates.sort(
                key=lambda record: self._status_move_score(species, record, offensive_mode),
                reverse=True,
            )
            for record in status_candidates:
                if len(selected_records) >= 4 or status_slots <= 0:
                    break
                if try_add(record, enforce_diversity=False):
                    status_slots -= 1

        if len(selected_records) < 4:
            for record in damaging_candidates + status_candidates:
                if len(selected_records) >= 4:
                    break
                try_add(record, enforce_diversity=False)

        return [self._resolve_variant_record(record).to_move_spec() for record in selected_records[:4]]

    def _augment_move_pool(self, species: SpeciesRecord, base_pool: List[MoveRecord]) -> List[MoveRecord]:
        seen: Set[str] = {self._move_pool_key(record.name) for record in base_pool}
        pool = list(base_pool)
        species_types = {str(t or "").strip().lower() for t in species.types if str(t or "").strip()}
        offensive_mode = self._infer_offense_mode(species, base_pool)
        stab_damaging: List[MoveRecord] = []
        repeatable_offtype: List[MoveRecord] = []
        fallback_damaging: List[MoveRecord] = []
        utility_status: List[MoveRecord] = []

        for record in self._moves.values():
            key = self._move_pool_key(record.name)
            if key in seen:
                continue
            move_type = (record.type or "").strip().lower()
            if self._is_damaging_record(record):
                if self._is_self_destructive_record(record):
                    continue
                if move_type and move_type in species_types:
                    stab_damaging.append(record)
                    continue
                if self._is_repeatable_frequency(record.frequency):
                    if offensive_mode == "mixed" or self._category_matches_mode(record, offensive_mode):
                        repeatable_offtype.append(record)
                    continue
                if offensive_mode == "mixed" or self._category_matches_mode(record, offensive_mode):
                    fallback_damaging.append(record)
                continue
            if move_type and move_type in species_types:
                utility_status.append(record)
                continue
            if self._is_generic_utility_status(record):
                utility_status.append(record)

        stab_damaging.sort(
            key=lambda record: self._damage_move_score(species, record, offensive_mode),
            reverse=True,
        )
        repeatable_offtype.sort(
            key=lambda record: self._damage_move_score(species, record, offensive_mode),
            reverse=True,
        )
        fallback_damaging.sort(
            key=lambda record: self._damage_move_score(species, record, offensive_mode),
            reverse=True,
        )
        utility_status.sort(
            key=lambda record: self._status_move_score(species, record, offensive_mode),
            reverse=True,
        )

        for bucket, limit in (
            (stab_damaging, 18),
            (repeatable_offtype, 10),
            (utility_status, 8),
            (fallback_damaging, 12),
        ):
            added = 0
            for record in bucket:
                key = self._move_pool_key(record.name)
                if key in seen:
                    continue
                pool.append(record)
                seen.add(key)
                added += 1
                if len(pool) >= 48 or added >= limit:
                    break
            if len(pool) >= 48:
                break
        return pool

    def _infer_offense_mode(self, species: SpeciesRecord, candidates: List[MoveRecord]) -> str:
        atk = int(species.base_stats.get("attack", 10))
        spatk = int(species.base_stats.get("special_attack", 10))
        physical_hits = sum(
            1
            for record in candidates
            if self._is_damaging_record(record) and (record.category or "").strip().lower() == "physical"
        )
        special_hits = sum(
            1
            for record in candidates
            if self._is_damaging_record(record) and (record.category or "").strip().lower() == "special"
        )
        physical_score = atk * 3 + physical_hits * 6
        special_score = spatk * 3 + special_hits * 6
        if abs(physical_score - special_score) <= 8:
            return "mixed"
        return "physical" if physical_score > special_score else "special"

    @staticmethod
    def _frequency_score(frequency: str) -> int:
        text = str(frequency or "").strip().lower()
        if "at-will" in text:
            return 40
        if "eot" in text:
            return 32
        if "scene x3" in text:
            return 20
        if "scene x2" in text:
            return 12
        if "scene" in text:
            return 8
        if "daily x3" in text:
            return -6
        if "daily x2" in text:
            return -12
        if "daily" in text:
            return -18
        if "standard" in text:
            return 16
        if text in {"free", "shift", "action"}:
            return 12
        return 0

    def _damage_move_score(self, species: SpeciesRecord, record: MoveRecord, mode: str) -> float:
        species_types = {str(t or "").strip().lower() for t in species.types if str(t or "").strip()}
        category = (record.category or "").strip().lower()
        db = int(record.db or 0)
        score = float(db) * 2.75
        if mode == "physical":
            if category == "physical":
                score += 16.0
            elif category == "special":
                score -= 14.0
        elif mode == "special":
            if category == "special":
                score += 16.0
            elif category == "physical":
                score -= 14.0
        else:
            if category in {"physical", "special"}:
                score += 8.0
        move_type = (record.type or "").strip().lower()
        if move_type and move_type in species_types:
            score += 20.0
        elif move_type:
            score -= 4.0
        score += float(self._frequency_score(record.frequency))
        ac = record.ac
        if ac is None:
            score += 6.0
        else:
            score += max(0.0, float(7 - int(ac))) * 2.2
            if int(ac) >= 5:
                score -= float(int(ac) - 4) * 4.0
        text = (record.effects or "").strip().lower()
        if "priority" in text:
            score += 6.0
        if "high crit" in text or "critical hit" in text:
            score += 3.0
        if "recoil" in text:
            score -= 10.0
        if "set-up effect" in text:
            score -= 8.0
        if "must use struggle" in text or "must recharge" in text:
            score -= 22.0
        if "causes the target to lose" in text and "damage" not in text:
            score -= 20.0
        if self._is_self_destructive_record(record):
            score -= 120.0
        if (record.name or "").strip().lower() == "struggle":
            score -= 1000.0
        return score

    def _status_move_score(self, species: SpeciesRecord, record: MoveRecord, mode: str) -> float:
        text = f"{record.name} {record.effects}".lower()
        score = float(self._frequency_score(record.frequency)) * 0.6
        if mode == "physical":
            if "attack" in text or "atk" in text or "physical" in text:
                score += 10.0
        elif mode == "special":
            if "special attack" in text or "spatk" in text or "special" in text:
                score += 10.0
        else:
            if "attack" in text or "special attack" in text:
                score += 7.0
        if "speed" in text:
            score += 8.0
        if "accuracy" in text:
            score += 6.0
        if any(token in text for token in ("heal", "recover", "restore", "roost", "wish", "drain")):
            score += 7.0
        if any(token in text for token in ("protect", "detect", "endure", "substitute", "screen")):
            score += 6.0
        if any(
            token in text
            for token in (
                "sleep",
                "drowsy",
                "paraly",
                "poison",
                "burn",
                "confus",
                "taunt",
                "fear",
                "flinch",
                "stun",
                "trap",
                "disable",
                "suppressed",
            )
        ):
            score += 7.0
        species_types = {str(t or "").strip().lower() for t in species.types if str(t or "").strip()}
        move_type = (record.type or "").strip().lower()
        if move_type and move_type in species_types:
            score += 2.0
        if self._is_self_destructive_record(record):
            score -= 100.0
        return score

    @staticmethod
    def _category_matches_mode(record: MoveRecord, mode: str) -> bool:
        category = (record.category or "").strip().lower()
        if mode == "physical":
            return category == "physical"
        if mode == "special":
            return category == "special"
        return category in {"physical", "special"}

    @staticmethod
    def _is_generic_utility_status(record: MoveRecord) -> bool:
        text = f"{record.name} {record.effects}".lower()
        return any(
            token in text
            for token in (
                "protect",
                "detect",
                "endure",
                "substitute",
                "screen",
                "recover",
                "heal",
                "restore",
                "roost",
                "wish",
                "taunt",
                "disable",
                "paraly",
                "poison",
                "burn",
                "sleep",
                "drowsy",
                "confus",
                "speed",
                "accuracy",
                "attack",
                "spatk",
                "defense",
                "spdef",
            )
        )

    @staticmethod
    def _is_self_destructive_record(record: MoveRecord) -> bool:
        name = (record.name or "").strip().lower()
        if name in {
            "explosion",
            "self-destruct",
            "mind blown",
            "steel beam",
            "memento",
            "healing wish",
            "lunar dance",
            "misty explosion",
            "final gambit",
        }:
            return True
        text = (record.effects or "").strip().lower()
        return any(
            token in text
            for token in (
                "hp is set to -50%",
                "hit points are reduced by 50%",
                "the user faints",
                "user faints",
                "faints after",
                "faints, even if this attack misses",
            )
        )

    @staticmethod
    def _has_damaging_move(moves: List[MoveSpec]) -> bool:
        return any(
            (move.category or "").strip().lower() != "status" and int(move.db or 0) > 0
            for move in moves
        )

    @staticmethod
    def _is_damaging_record(record: MoveRecord) -> bool:
        return (record.category or "").strip().lower() != "status" and int(record.db or 0) > 0

    def _select_abilities(self, species_name: str, level: int) -> List[str]:
        self._ensure_ability_pools()
        pools = None
        for key in self._ability_key_candidates(species_name):
            pools = (self._ability_pools or {}).get(key)
            if pools:
                break
        if not pools:
            return []
        abilities, _added = pick_abilities_for_level(pools, level, self._rng, existing=[])
        return abilities

    def _ability_key_candidates(self, species_name: str) -> List[str]:
        raw = normalize_species_key(species_name)
        if not raw:
            return []
        candidates: List[str] = []

        def add(value: str) -> None:
            value = (value or "").strip()
            if value and value not in candidates:
                candidates.append(value)

        add(raw)
        raw_no_percent = raw.replace("%", "").strip()
        add(raw_no_percent)
        raw_tokens = [re.sub(r"[^a-z0-9]+", "", token) for token in raw_no_percent.split()]
        raw_tokens = [token for token in raw_tokens if token]
        if raw_tokens and raw_tokens[0] in {"alolan", "galarian", "hisuian", "paldean"} and len(raw_tokens) > 1:
            add(f"{raw_tokens[1]} {raw_tokens[0]}")
        short_map = {
            "su": "super",
            "la": "large",
            "sm": "small",
            "av": "average",
            "b": "baile",
            "po": "pompom",
            "pa": "pau",
            "i": "incarnate",
            "da": "day",
            "du": "dusk",
            "n": "normal",
            "a": "alola",
            "g": "galar",
            "h": "hisui",
            "p": "paldea",
        }
        expanded = [short_map.get(token, token) for token in raw_tokens]
        add(" ".join(expanded))
        if len(expanded) > 2:
            add(f"{expanded[0]} {''.join(expanded[1:])}")
        if expanded and expanded[0] == "mega" and len(expanded) > 1:
            add(expanded[1])
            if len(expanded) > 2:
                add(f"{expanded[1]} {expanded[2]}")

        head = expanded[0] if expanded else ""
        tail = expanded[1:] if len(expanded) > 1 else []
        if head.startswith("flab"):
            add("flabebe")
        if head == "hakamoo":
            add("hakamo o")
        if head == "jangmoo":
            add("jangmo o")
        if head == "kommoo":
            add("kommo o")
        if head in {"darmanitan", "deoxys", "eiscue"}:
            add(head)
            if head == "darmanitan" and ("galarian" in expanded or "galar" in expanded):
                add("darmanitan galarian")
        if head in {"dialga", "giratina", "palkia"}:
            add(head)
            if any(token in {"o", "origin"} for token in tail):
                add(f"{head} origin")
        if head == "calyrex":
            add("calyrex")
            if "shadow" in tail:
                add("calyrex shadow rider")
            if "ice" in tail:
                add("calyrex ice rider")
        if head == "hoopa":
            if any(token in {"u", "un", "unbound"} for token in tail):
                add("hoopa unbound")
            else:
                add("hoopa")
        if head == "kyurem":
            add("kyurem")
            if any(token in {"r", "reshiram", "white"} for token in tail):
                add("kyurem white")
            if any(token in {"z", "zekrom", "black"} for token in tail):
                add("kyurem black")
        if head == "meloetta":
            add("meloetta")
            if any(token in {"step", "pirouette"} for token in tail):
                add("meloetta pirouette")
        if head == "shaymin":
            add("shaymin")
            if any(token in {"s", "sky"} for token in tail):
                add("shaymin sky")
        if head == "urshifu":
            if any(token in {"r", "rapid", "rapidstrike"} for token in tail):
                add("urshifu rapidstrike")
            if any(token in {"s", "single", "singlestrike"} for token in tail):
                add("urshifu singlestrike")
        if head == "wormadam":
            if any(token in {"p", "plant", "paldea"} for token in tail):
                add("wormadam plant")
            if any(token in {"s", "sand", "sandy"} for token in tail):
                add("wormadam sandy")
            if any(token in {"t", "trash"} for token in tail):
                add("wormadam trash")
        if head in {"enamorus", "landorus", "thundurus", "tornadus"}:
            add(head)
            if any(token in {"t", "therian"} for token in tail):
                add(f"{head} therian")
        if head in {"basculegion", "indeedee"}:
            if any(token in {"f", "female"} for token in tail):
                add(f"{head} female")
            if any(token in {"m", "male"} for token in tail):
                add(f"{head} male")
            if not tail:
                add(f"{head} male")
                add(f"{head} female")
        if head == "lycanroc":
            if any(token in {"night", "midnight"} for token in tail):
                add("lycanroc midnight")
            if any(token in {"n", "normal", "day", "midday"} for token in tail):
                add("lycanroc midday")
            if any(token in {"dusk"} for token in tail):
                add("lycanroc dusk")
        if head in {"zacian", "zamazenta"} and any(token in {"c", "crowned"} for token in tail):
            add(head)
        if head == "nidoran":
            if any(token in {"female", "f"} for token in tail):
                add("nidoran f")
            if any(token in {"male", "m"} for token in tail):
                add("nidoran m")
        if head in {"pyroar", "meowstic"} and not tail:
            add(f"{head} male")
            add(f"{head} female")
        if head in {"zygarde"}:
            if "complete" in expanded:
                add("zygarde complete")
            elif any(token.startswith("10") for token in expanded):
                add("zygarde 10")
            elif any(token.startswith("50") for token in expanded):
                add("zygarde 50")
            else:
                add("zygarde 50")
        if head == "oricorio":
            if "s" in raw_tokens:
                add("oricorio sensu")
            if "b" in raw_tokens:
                add("oricorio baile")
            if "po" in raw_tokens:
                add("oricorio pompom")
            if "pa" in raw_tokens:
                add("oricorio pau")

        form_suffixes = {
            "alola",
            "galar",
            "hisui",
            "paldea",
            "super",
            "large",
            "small",
            "average",
            "origin",
            "altered",
            "incarnate",
            "therian",
            "core",
            "meteor",
            "crowned",
            "hero",
            "dusk",
            "dawn",
            "ultra",
            "male",
            "female",
            "baile",
            "pom",
            "pom-pom",
            "pau",
            "sensu",
            "red",
            "midday",
            "midnight",
            "day",
            "night",
            "school",
            "solo",
            "amped",
            "low",
            "key",
            "hangry",
            "noice",
            "ice",
        }
        trimmed = list(expanded)
        while len(trimmed) > 1 and trimmed[-1] in form_suffixes:
            trimmed = trimmed[:-1]
            add(" ".join(trimmed))

        if expanded and expanded[0] in {"mega", "primal", "gmax", "gigantamax"} and len(expanded) > 1:
            add(" ".join(expanded[1:]))

        if len(expanded) > 1 and expanded[-1].isdigit():
            add(" ".join(expanded[:-1]))
        if expanded and expanded[0] in {
            "gourgeist",
            "pumpkaboo",
            "oricorio",
            "rotom",
            "minior",
            "wishiwashi",
            "toxtricity",
            "meowstic",
            "indeedee",
        }:
            add(expanded[0])
        if expanded:
            official_eons = {
                "eevee",
                "vaporeon",
                "jolteon",
                "flareon",
                "espeon",
                "umbreon",
                "leafeon",
                "glaceon",
                "sylveon",
            }
            head = expanded[0]
            if head.endswith("eon") and head not in official_eons:
                add("eevee")
        return candidates


__all__ = ["PTUCsvRepository", "SpeciesRecord", "MoveRecord", "ItemRecord"]
