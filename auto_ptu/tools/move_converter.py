"""Standalone move / ability / item to move converter."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from ..data_models import MoveSpec
from ..pokeapi_assets import ability_metadata, item_metadata, move_metadata
from ..rules.item_catalog import get_item_entry
from .ptu_move_reference import PTU_CONVERSION_REFERENCE, sanitize_ai_patch

SourceKind = Literal["move", "ability", "item"]

_TYPE_NAMES = [
    "Normal",
    "Fire",
    "Water",
    "Electric",
    "Grass",
    "Ice",
    "Fighting",
    "Poison",
    "Ground",
    "Flying",
    "Psychic",
    "Bug",
    "Rock",
    "Ghost",
    "Dragon",
    "Dark",
    "Steel",
    "Fairy",
]
_TYPE_WORDS = {name.lower(): name for name in _TYPE_NAMES}
_TYPE_HINTS = {
    "Normal": ("normal", "neutral", "plain", "tackle", "slam"),
    "Fire": ("fire", "flame", "ember", "burn", "blaze", "heat", "inferno"),
    "Water": ("water", "aqua", "tidal", "wave", "steam", "bubble"),
    "Electric": ("electric", "thunder", "lightning", "volt", "shock", "spark", "zap"),
    "Grass": ("grass", "leaf", "vine", "seed", "spore", "nature", "flora"),
    "Ice": ("ice", "frost", "frozen", "snow", "blizzard", "icy", "hail"),
    "Fighting": ("fighting", "punch", "kick", "jab", "uppercut", "martial"),
    "Poison": ("poison", "toxic", "venom", "acid", "sludge"),
    "Ground": ("ground", "earth", "mud", "sand", "quake", "burrow"),
    "Flying": ("flying", "wind", "air", "sky", "gust", "aerial"),
    "Psychic": ("psychic", "mind", "psy", "telekin", "telepath", "mental"),
    "Bug": ("bug", "insect", "swarm", "sting", "web"),
    "Rock": ("rock", "stone", "boulder", "crystal"),
    "Ghost": ("ghost", "shadow", "spectral", "phantom", "haunt"),
    "Dragon": ("dragon", "draco", "wyrm"),
    "Dark": ("dark", "night", "sinister", "shade", "black"),
    "Steel": ("steel", "metal", "iron", "blade"),
    "Fairy": ("fairy", "charm", "moon", "starlight", "pixie"),
}
_MOVE_CACHE: Optional[dict[str, dict[str, Any]]] = None
_DEFAULT_HTTP_TIMEOUT = 30
_AI_HTTP_TIMEOUT = 120


@dataclass
class LocalModelConfig:
    enabled: bool = False
    provider: str = "ollama"
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2


@dataclass
class ConversionRequest:
    kind: SourceKind
    name: str = ""
    text: str = ""
    movement_mode: str = ""
    range_override: str = ""
    keywords_override: str = ""
    type_override: str = ""
    category_override: str = ""
    frequency_override: str = ""
    db_override: Optional[int] = None
    use_ai: bool = False
    local_model: Optional[LocalModelConfig] = None


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u00a0", " ")).strip()


def _parse_keywords(value: str | None) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def _override_summary(request: ConversionRequest) -> dict[str, Any]:
    return {
        "range_override": request.range_override,
        "keywords_override": _parse_keywords(request.keywords_override),
        "type_override": request.type_override,
        "category_override": request.category_override,
        "frequency_override": request.frequency_override,
        "db_override": request.db_override,
    }


def _dedupe_sentences(text: str) -> str:
    clean = _clean_text(text)
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", clean)
    seen: list[str] = []
    for part in parts:
        candidate = _clean_text(part)
        if not candidate:
            continue
        if candidate in seen:
            continue
        seen.append(candidate)
    return " ".join(seen)


def _normalize_freq(value: str | None, fallback: str = "Scene x2") -> str:
    text = _clean_text(value)
    if not text:
        return fallback
    text = (
        text.replace(" - ", " ")
        .replace("- ", " ")
        .replace("Free Action", "Free")
        .replace("Swift Action", "Swift")
        .replace("Standard Action", "Standard")
        .replace("Extended Action", "Extended")
    )
    return _clean_text(text)


def _load_move_cache() -> dict[str, dict[str, Any]]:
    global _MOVE_CACHE
    if _MOVE_CACHE is not None:
        return _MOVE_CACHE
    path = Path(__file__).resolve().parents[1] / "data" / "compiled" / "moves.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = []
    cache: dict[str, dict[str, Any]] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        name = _clean_text(row.get("name"))
        if not name:
            continue
        cache[name.lower()] = row
    _MOVE_CACHE = cache
    return cache


def _lookup_move_row(name: str) -> Optional[dict[str, Any]]:
    if not name:
        return None
    cache = _load_move_cache()
    exact = cache.get(name.strip().lower())
    if exact:
        return exact
    compact = re.sub(r"[^a-z0-9]+", "", name.lower())
    for key, row in cache.items():
        if re.sub(r"[^a-z0-9]+", "", key) == compact:
            return row
    return None


def _parse_structured_move_text(text: str) -> dict[str, Any]:
    raw = str(text or "")
    compact = _clean_text(raw)
    if not compact:
        return {}
    fields: dict[str, Any] = {}
    patterns = {
        "type": r"\bType\s+([A-Za-z]+)\b",
        "category": r"\bCategory\s+([A-Za-z]+)\b",
        "power": r"\bPower\s+(\d+)\b",
        "accuracy": r"\bAccuracy\s+(\d+)\b",
        "pp": r"\bPP\s+(\d+)\b",
        "introduced": r"\bIntroduced\s+(Generation\s+\d+)\b",
        "contact": r"\bMakes contact\?\s+(Yes|No)\b",
        "effects": r"\bEffects\s+(.+?)(?=\bMove target\b|\bFlavor text\b|\bLearnt by\b|$)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if not match:
            continue
        value = _clean_text(match.group(1))
        if key in {"power", "accuracy", "pp"}:
            fields[key] = int(value)
        elif key == "contact":
            fields[key] = value.lower() == "yes"
        else:
            fields[key] = value
    if "type" in fields or "power" in fields or "accuracy" in fields:
        fields["structured"] = True
    return fields


def _infer_type(name: str, text: str, fallback: str = "Normal") -> str:
    haystack = f"{name} {text}".lower()
    for token, type_name in _TYPE_WORDS.items():
        if re.search(rf"\b{re.escape(token)}\b", haystack):
            return type_name
    for type_name, hints in _TYPE_HINTS.items():
        if any(re.search(rf"\b{re.escape(hint)}\b", haystack) for hint in hints):
            return type_name
    return fallback


def _infer_target_profile(text: str) -> dict[str, Any]:
    clean = _clean_text(text)
    lower = clean.lower()
    if not clean:
        return {
            "range_kind": "Self",
            "range_value": None,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": None,
            "area_value": None,
            "range_text": "Self",
        }
    burst = re.search(r"\bburst\s+(\d+)\b", lower)
    if burst:
        value = int(burst.group(1))
        return {
            "range_kind": "Burst",
            "range_value": value,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Burst",
            "area_value": value,
            "range_text": f"Burst {value}",
        }
    line = re.search(r"\bline\s+(\d+)\b", lower)
    if line:
        value = int(line.group(1))
        return {
            "range_kind": "Line",
            "range_value": value,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Line",
            "area_value": value,
            "range_text": f"Line {value}",
        }
    cone = re.search(r"\bcone\s+(\d+)\b", lower)
    if cone:
        value = int(cone.group(1))
        return {
            "range_kind": "Cone",
            "range_value": value,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Cone",
            "area_value": value,
            "range_text": f"Cone {value}",
        }
    if any(token in lower for token in ("all nearby enemies", "nearby enemies", "all nearby foes", "nearby foes")):
        return {
            "range_kind": "Burst",
            "range_value": 2,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Burst",
            "area_value": 2,
            "range_text": "Burst 2, Enemies",
        }
    if any(token in lower for token in ("all adjacent enemies", "adjacent enemies", "adjacent foes")):
        return {
            "range_kind": "Burst",
            "range_value": 1,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Burst",
            "area_value": 1,
            "range_text": "Burst 1, Enemies",
        }
    if any(token in lower for token in ("all allies", "nearby allies", "adjacent allies", "all friendly targets", "restores allies", "heals allies", "allied targets", "allies")):
        value = 2 if "nearby" in lower else 1
        return {
            "range_kind": "Burst",
            "range_value": value,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": "Burst",
            "area_value": value,
            "range_text": f"Burst {value}, Allies",
        }
    ranged = re.search(r"\b(?:range|within)\s+(\d+)\b", lower)
    if ranged:
        value = int(ranged.group(1))
        return {
            "range_kind": "Ranged",
            "range_value": value,
            "target_kind": "Ranged",
            "target_range": value,
            "area_kind": None,
            "area_value": None,
            "range_text": f"Range {value}, 1 Target",
        }
    if "adjacent" in lower or "melee" in lower or "touch" in lower or any(token in lower for token in ("punch", "kick", "jab", "bite", "claw", "slash", "slam", "strike")):
        return {
            "range_kind": "Melee",
            "range_value": 1,
            "target_kind": "Melee",
            "target_range": 1,
            "area_kind": None,
            "area_value": None,
            "range_text": "Melee, 1 Target",
        }
    if any(token in lower for token in ("projectile", "beam", "bolt", "shot", "missile", "blast")):
        return {
            "range_kind": "Ranged",
            "range_value": 6,
            "target_kind": "Ranged",
            "target_range": 6,
            "area_kind": None,
            "area_value": None,
            "range_text": "Range 6, 1 Target",
        }
    return {
        "range_kind": "Self",
        "range_value": None,
        "target_kind": "Self",
        "target_range": 0,
        "area_kind": None,
        "area_value": None,
        "range_text": "Self",
    }


def _default_profile_for_attack(category: str, name: str, text: str, structured: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    lower = f"{name} {text}".lower()
    if category == "Status":
        return {
            "range_kind": "Self",
            "range_value": None,
            "target_kind": "Self",
            "target_range": 0,
            "area_kind": None,
            "area_value": None,
            "range_text": "Self",
        }
    melee_hints = ("punch", "kick", "jab", "bite", "claw", "slash", "slam", "strike", "cutter", "tail", "fang")
    if category == "Physical" and any(token in lower for token in melee_hints):
        return {
            "range_kind": "Melee",
            "range_value": 1,
            "target_kind": "Melee",
            "target_range": 1,
            "area_kind": None,
            "area_value": None,
            "range_text": "Melee, 1 Target",
        }
    if category == "Physical" and structured and structured.get("contact") is True:
        return {
            "range_kind": "Melee",
            "range_value": 1,
            "target_kind": "Melee",
            "target_range": 1,
            "area_kind": None,
            "area_value": None,
            "range_text": "Melee, 1 Target",
        }
    return {
        "range_kind": "Ranged",
        "range_value": 6,
        "target_kind": "Ranged",
        "target_range": 6,
        "area_kind": None,
        "area_value": None,
        "range_text": "Range 6, 1 Target",
    }


def _build_status_move(
    *,
    name: str,
    move_type: str,
    freq: str,
    effects_text: str,
    target_profile: Optional[dict[str, Any]] = None,
) -> MoveSpec:
    profile = target_profile or _infer_target_profile(effects_text)
    return MoveSpec(
        name=name,
        type=move_type,
        category="Status",
        db=0,
        ac=None,
        range_kind=str(profile.get("range_kind") or "Self"),
        range_value=profile.get("range_value"),
        target_kind=str(profile.get("target_kind") or "Self"),
        target_range=profile.get("target_range"),
        area_kind=profile.get("area_kind"),
        area_value=profile.get("area_value"),
        freq=freq,
        effects_text=_clean_text(effects_text),
        range_text=str(profile.get("range_text") or ""),
    )


def _infer_move_category(name: str, text: str, target_profile: dict[str, Any]) -> str:
    lower = f"{name} {text}".lower()
    has_explicit_db = bool(re.search(r"\b(?:db|damage base)\s*\d+\b", lower))
    offensive_cues = (
        "punch",
        "kick",
        "jab",
        "strike",
        "slash",
        "claw",
        "bite",
        "projectile",
        "beam",
        "blast",
        "bolt",
        "shot",
        "hits",
        "deals damage",
        "damages",
    )
    if has_explicit_db:
        if any(token in lower for token in ("physical", "punch", "kick", "bite", "claw", "slam", "strike")):
            return "Physical"
        if any(token in lower for token in ("special", "beam", "blast", "pulse", "wave", "burst", "bolt")):
            return "Special"
        if str(target_profile.get("range_kind") or "").lower() == "melee":
            return "Physical"
        return "Special"
    if any(token in lower for token in offensive_cues):
        if any(token in lower for token in ("punch", "kick", "jab", "strike", "slash", "claw", "bite", "slam")):
            return "Physical"
        return "Special"
    if any(token in lower for token in ("status", "heal", "heals", "restores", "raise", "lower", "flinch", "confuse", "burn", "poison", "paralyze", "sleep")):
        return "Status"
    if any(token in lower for token in ("physical", "punch", "kick", "bite", "claw", "slam", "strike")):
        return "Physical"
    if any(token in lower for token in ("special", "beam", "blast", "pulse", "wave", "burst", "bolt")):
        return "Special"
    if str(target_profile.get("range_kind") or "").lower() == "melee":
        return "Physical"
    return "Special"


def _power_to_db(power: int) -> int:
    if power <= 0:
        return 0
    if power <= 20:
        return 2
    if power <= 35:
        return 3
    if power <= 45:
        return 4
    if power <= 55:
        return 5
    if power <= 65:
        return 6
    if power <= 75:
        return 7
    if power <= 85:
        return 8
    if power <= 95:
        return 9
    if power <= 110:
        return 10
    if power <= 125:
        return 11
    if power <= 150:
        return 12
    return 13


def _accuracy_to_ac(accuracy: int | None, category: str) -> Optional[int]:
    if category == "Status" and accuracy in (None, 0):
        return None
    if accuracy is None:
        return None if category == "Status" else 2
    if accuracy >= 100:
        return 2
    if accuracy >= 90:
        return 3
    if accuracy >= 80:
        return 4
    if accuracy >= 70:
        return 5
    return 6


def _infer_move_frequency(text: str, fallback: str = "At-Will", structured: Optional[dict[str, Any]] = None) -> str:
    lower = text.lower()
    for marker in ("daily x2", "daily", "scene x2", "scene", "eot", "at-will"):
        if marker in lower:
            return marker.replace("eot", "EOT").replace("at-will", "At-Will").replace("scene", "Scene").replace("daily", "Daily")
    if structured:
        try:
            pp = int(structured.get("pp")) if structured.get("pp") not in (None, "") else None
        except (TypeError, ValueError):
            pp = None
        try:
            power = int(structured.get("power")) if structured.get("power") not in (None, "") else None
        except (TypeError, ValueError):
            power = None
        if pp is not None and pp <= 5:
            return "Scene x2"
        if power is not None and power >= 110:
            return "Scene x2"
    if any(token in lower for token in ("over time", "lingers", "field effect", "terrain", "song")):
        return "Scene x2"
    return fallback


def _infer_move_db(name: str, text: str, category: str) -> int:
    if category == "Status":
        return 0
    explicit = re.search(r"\b(?:db|damage base)\s*(\d+)\b", text.lower())
    if explicit:
        return max(1, int(explicit.group(1)))
    lower = text.lower()
    if any(token in lower for token in ("fast", "quick", "swift")):
        return 5
    if any(token in lower for token in ("heavy", "massive", "powerful", "devastating", "explosive")):
        return 8
    if any(token in text.lower() for token in ("basic", "quick", "starter", "early")):
        return 5
    if any(token in text.lower() for token in ("heavy", "strong", "signature", "finisher")):
        return 8
    return 6


def _range_from_move_row(row: dict[str, Any]) -> dict[str, Any]:
    return _infer_target_profile(str(row.get("range") or ""))


def _structured_effect_text(structured: dict[str, Any], fallback: str = "") -> str:
    effects = _clean_text(str(structured.get("effects") or fallback or ""))
    lower = effects.lower()
    notes: list[str] = []
    if any(
        token in lower
        for token in (
            "increased critical-hit ratio",
            "high critical-hit ratio",
            "increased critical hit ratio",
        )
    ):
        notes.append("Critical Hits on 18+.")
    stage_drop = re.search(
        r"lowers the user's ([a-z ]+?) and ([a-z ]+?) stats? by one stage each after attacking",
        lower,
    )
    if stage_drop:
        stat_one = _clean_text(stage_drop.group(1)).title()
        stat_two = _clean_text(stage_drop.group(2)).title()
        notes.append(
            f"After the attack resolves, lower the user's {stat_one} and {stat_two} by 1 Combat Stage each."
        )
    status_proc = re.search(
        r"(?:the target is|may leave the target)\s+(burned|paralyzed|poisoned|frozen|asleep|confused)\s+on\s+(\d+)\+",
        lower,
    )
    if status_proc:
        status_map = {
            "burned": "Burn",
            "paralyzed": "Paralyze",
            "poisoned": "Poison",
            "frozen": "Freeze",
            "asleep": "Sleep",
            "confused": "Confuse",
        }
        notes.append(f"{status_map.get(status_proc.group(1), status_proc.group(1).title())} on {status_proc.group(2)}+.")
    cleaned = re.sub(
        r"\bStats can be lowered to a minimum of -6 stages each\.?",
        "",
        effects,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b[A-Z][A-Za-z ]+ deals damage,?\s*", "", cleaned).strip()
    cleaned = _clean_text(cleaned)
    if stage_drop and "lowers the user's" in cleaned.lower():
        cleaned = ""
    if cleaned and cleaned.lower() not in {note.lower() for note in notes}:
        notes.append(cleaned)
    if not notes and effects:
        notes.append(effects)
    return _dedupe_sentences(" ".join(notes))


def _prefer_ranged_profile_for_structured_special(structured: dict[str, Any], source_text: str, category: str) -> bool:
    if category != "Special":
        return False
    if structured.get("contact") is not False:
        return False
    lower = source_text.lower()
    if "melee" in lower or "touch" in lower:
        return False
    if "targets a single adjacent" in lower or "single adjacent pok" in lower:
        return True
    if any(token in lower for token in ("beam", "blast", "cannon", "projectile", "bolt", "shot", "missile")):
        return True
    return False


def _convert_move(request: ConversionRequest) -> dict[str, Any]:
    source_text = _clean_text(request.text)
    structured = _parse_structured_move_text(request.text)
    existing = _lookup_move_row(request.name)
    if existing and not source_text:
        profile = _range_from_move_row(existing)
        meta = move_metadata(request.name) or {}
        move = MoveSpec(
            name=str(existing.get("name") or request.name or "Move"),
            type=request.type_override or str(existing.get("type") or "Normal"),
            category=request.category_override or str(existing.get("category") or "Special"),
            db=int(request.db_override if request.db_override is not None else existing.get("damage_base") or 0),
            ac=int(existing["ac"]) if existing.get("ac") not in (None, "") else None,
            range_kind=str(profile.get("range_kind") or "Ranged"),
            range_value=profile.get("range_value"),
            target_kind=str(profile.get("target_kind") or "Ranged"),
            target_range=profile.get("target_range"),
            area_kind=profile.get("area_kind"),
            area_value=profile.get("area_value"),
            freq=request.frequency_override or _normalize_freq(existing.get("frequency"), fallback="At-Will"),
            effects_text=_clean_text(str(meta.get("effect") or existing.get("effects") or "")),
            range_text=str(existing.get("range") or profile.get("range_text") or ""),
        )
        return {
            "move": move,
            "template": "existing_move",
            "source_name": request.name,
            "metadata_source": str(meta.get("source") or "compiled_moves"),
            "notes": [
                "Matched against the local PTU move dataset and normalized into MoveSpec output.",
            ],
            "source_text": _clean_text(str(meta.get("effect") or existing.get("effects") or "")),
        }
    initial_profile = _infer_target_profile(source_text)
    category = request.category_override or _clean_text(str(structured.get("category") or "")) or _infer_move_category(request.name, source_text, initial_profile)
    profile = initial_profile
    if structured.get("structured") and _prefer_ranged_profile_for_structured_special(structured, source_text, category):
        profile = _default_profile_for_attack(category, request.name, source_text, structured)
    if category != "Status" and str(profile.get("range_kind") or "").lower() == "self" and not profile.get("area_kind"):
        profile = _default_profile_for_attack(category, request.name, source_text, structured)
    if request.range_override:
        profile = _infer_target_profile(request.range_override)
        profile["range_text"] = _clean_text(request.range_override)
    power = structured.get("power")
    accuracy = structured.get("accuracy")
    effects_text = _structured_effect_text(structured, source_text) if structured.get("structured") else (source_text or "Custom move text pending.")
    crit_range = 18 if "high critical hit rate" in effects_text.lower() or "increased critical-hit ratio" in effects_text.lower() else 20
    move = MoveSpec(
        name=request.name or "Custom Move",
        type=request.type_override or _clean_text(str(structured.get("type") or "")) or _infer_type(request.name, source_text, fallback="Normal"),
        category=category,
        db=int(request.db_override if request.db_override is not None else (_power_to_db(int(power)) if power not in (None, "") else _infer_move_db(request.name, source_text, category))),
        ac=_accuracy_to_ac(int(accuracy) if accuracy not in (None, "") else None, category),
        range_kind=str(profile.get("range_kind") or ("Ranged" if category != "Status" else "Self")),
        range_value=profile.get("range_value"),
        target_kind=str(profile.get("target_kind") or ("Ranged" if category != "Status" else "Self")),
        target_range=profile.get("target_range"),
        area_kind=profile.get("area_kind"),
        area_value=profile.get("area_value"),
        freq=request.frequency_override or _infer_move_frequency(source_text or request.name, structured=structured),
        effects_text=effects_text,
        range_text=str(profile.get("range_text") or ("Range 4, 1 Target" if category != "Status" else "Self")),
        crit_range=crit_range,
    )
    return {
        "move": move,
        "template": "custom_move",
        "source_name": request.name,
        "metadata_source": "structured_move_text" if structured.get("structured") else "inline_move_text",
        "notes": [
            "Custom move baselines follow the Making/Fixing PTU Pokemon guidance to keep attacks immediately usable.",
            "When a move is not found in the compiled dataset, the converter defaults to conservative PTU-style templates.",
        ],
        "source_text": source_text,
    }


def _apply_move_overrides(move: MoveSpec, request: ConversionRequest) -> None:
    if request.category_override:
        move.category = request.category_override
    if request.frequency_override:
        move.freq = request.frequency_override
    if request.type_override:
        move.type = request.type_override
    if request.db_override is not None:
        move.db = int(request.db_override)
    if request.range_override:
        profile = _infer_target_profile(request.range_override)
        move.range_kind = str(profile.get("range_kind") or move.range_kind)
        move.range_value = profile.get("range_value")
        move.target_kind = str(profile.get("target_kind") or move.target_kind)
        move.target_range = profile.get("target_range")
        move.area_kind = profile.get("area_kind")
        move.area_value = profile.get("area_value")
        move.range_text = _clean_text(request.range_override)
    keywords = _parse_keywords(request.keywords_override)
    if keywords:
        seen = {entry.lower() for entry in move.keywords}
        for keyword in keywords:
            if keyword.lower() in seen:
                continue
            move.keywords.append(keyword)
            seen.add(keyword.lower())


def _reassert_structured_move_rules(move: MoveSpec, request: ConversionRequest) -> list[str]:
    structured = _parse_structured_move_text(request.text)
    if not structured.get("structured"):
        return []
    notes: list[str] = []
    source_text = _clean_text(request.text)

    if not request.type_override and structured.get("type"):
        move.type = _clean_text(str(structured.get("type")))
    if not request.category_override and structured.get("category"):
        move.category = _clean_text(str(structured.get("category")))

    if request.db_override is None and structured.get("power") not in (None, ""):
        expected_db = _power_to_db(int(structured["power"]))
        if move.db != expected_db:
            move.db = expected_db
            notes.append("Re-applied PTU DB mapping from the structured move sheet.")

    if structured.get("accuracy") not in (None, ""):
        expected_ac = _accuracy_to_ac(int(structured["accuracy"]), move.category)
        if move.ac != expected_ac:
            move.ac = expected_ac
            notes.append("Re-applied PTU AC mapping from the structured move sheet.")

    if not request.frequency_override:
        expected_freq = _infer_move_frequency(source_text or request.name, structured=structured)
        if move.freq != expected_freq:
            move.freq = expected_freq
            notes.append("Re-applied PTU frequency heuristics from the structured move sheet.")

    if not request.range_override:
        profile = _infer_target_profile(source_text)
        if _prefer_ranged_profile_for_structured_special(structured, source_text, move.category):
            profile = _default_profile_for_attack(move.category, request.name, source_text, structured)
        elif move.category != "Status" and str(profile.get("range_kind") or "").lower() == "self" and not profile.get("area_kind"):
            profile = _default_profile_for_attack(move.category, request.name, source_text, structured)
        if move.range_text != str(profile.get("range_text") or move.range_text):
            notes.append("Re-applied PTU range heuristics from the structured move sheet.")
        move.range_kind = str(profile.get("range_kind") or move.range_kind)
        move.range_value = profile.get("range_value")
        move.target_kind = str(profile.get("target_kind") or move.target_kind)
        move.target_range = profile.get("target_range")
        move.area_kind = profile.get("area_kind")
        move.area_value = profile.get("area_value")
        move.range_text = str(profile.get("range_text") or move.range_text)

    expected_effects = _structured_effect_text(structured, source_text)
    if expected_effects and move.effects_text != expected_effects:
        move.effects_text = expected_effects
        notes.append("Rewrote structured move effects into PTU-native text.")

    expected_crit = 18 if "critical hits on 18+." in expected_effects.lower() else 20
    if move.crit_range != expected_crit:
        move.crit_range = expected_crit
        notes.append("Re-applied critical hit range from the structured move sheet.")

    return notes


def _ability_effect_and_source(request: ConversionRequest) -> tuple[str, str]:
    if request.text:
        return _dedupe_sentences(request.text), "inline_text"
    meta = ability_metadata(request.name)
    if meta:
        return _dedupe_sentences(str(meta.get("effect") or "")), str(meta.get("source") or "ability_metadata")
    return "", "missing"


def _ability_frequency(request: ConversionRequest, effect_text: str) -> str:
    if request.frequency_override:
        return request.frequency_override
    lower = effect_text.lower()
    if "trigger -" in lower or "interrupt" in lower:
        return "Scene x2"
    meta = ability_metadata(request.name)
    if meta and meta.get("source") and request.name:
        pass
    # PTU ability CSV frequency is not returned by ability_metadata, so infer from the effect.
    if "immune" in lower or "defensive" in lower or "bonus to all accuracy" in lower:
        return "Scene x2"
    return "Scene x2"


def _ability_effect_to_move_text(name: str, effect_text: str) -> str:
    lower = effect_text.lower()
    if "trigger -" in lower:
        body = re.sub(r"(?i)^trigger\s*-\s*", "", effect_text).strip()
        for marker in (
            "The attacking foe",
            "The target",
            "The user",
            "All ",
            "Choose ",
            "Gain ",
            "Lower ",
            "Raise ",
            "Until ",
            "You ",
        ):
            idx = body.lower().find(marker.lower())
            if idx > 0:
                return f"Trigger - You are hit. {body[idx:].strip()}"
        return f"Trigger - You are hit. {body}"
    if any(token in lower for token in ("immune", "resist", "reduced damage", "damage reduction", "bonus to evasion", "bonus to defense")):
        return f"Activate {name}: until the end of your next turn, gain the following benefit: {effect_text}"
    if any(token in lower for token in ("when hit", "when the user is hit", "attacking foe", "upon being hit")):
        return f"Trigger - You are hit. {effect_text}"
    if any(token in lower for token in ("priority", "next move", "next attack", "next melee move")):
        return f"Activate {name}: {effect_text}"
    return f"Activate {name}: {effect_text}"


def _convert_ability(request: ConversionRequest) -> dict[str, Any]:
    effect_text, metadata_source = _ability_effect_and_source(request)
    if not effect_text:
        effect_text = request.text or "Apply the ability's effect as an activated combat option."
    move_type = request.type_override or _infer_type(request.name, effect_text, fallback="Normal")
    freq = _ability_frequency(request, effect_text)
    move = _build_status_move(
        name=request.name or "Ability Move",
        move_type=move_type,
        freq=freq,
        effects_text=_ability_effect_to_move_text(request.name or "Ability", effect_text),
    )
    return {
        "move": move,
        "template": "ability_action",
        "source_name": request.name,
        "metadata_source": metadata_source,
        "notes": [
            "Passive and trigger abilities are converted into explicit activatable PTU-style moves.",
            "This follows the rulebook guidance to prefer abilities that make a turn more interesting.",
        ],
        "source_text": effect_text,
    }


def _item_effect_and_source(request: ConversionRequest) -> tuple[str, str]:
    if request.text:
        return _dedupe_sentences(request.text), "inline_text"
    meta = item_metadata(request.name)
    if meta:
        source = meta.get("source") or []
        if isinstance(source, list):
            source_text = ", ".join(str(part) for part in source if str(part).strip())
        else:
            source_text = str(source)
        return _dedupe_sentences(str(meta.get("effect") or "")), source_text or "item_metadata"
    return "", "missing"


def _item_frequency(name: str, effect_text: str) -> str:
    entry = get_item_entry(name)
    traits = {trait.lower() for trait in (entry.traits if entry else set())}
    lower = effect_text.lower()
    if "berry" in name.lower() or any(word in lower for word in ("consume", "restores", "take the pill", "upon taking", "eat", "drinks")):
        return "Daily"
    if "held" in traits or "combat" in traits or "accessory" in lower or "holder" in lower or "wearer" in lower:
        return "Scene x2"
    return "Daily"


def _item_effect_to_move_text(name: str, effect_text: str) -> str:
    lower = effect_text.lower()
    if any(word in lower for word in ("holder", "wearer", "user")):
        return f"Use {name}: {effect_text}"
    return f"Use {name}: apply the following effect. {effect_text}"


def _convert_item(request: ConversionRequest) -> dict[str, Any]:
    effect_text, metadata_source = _item_effect_and_source(request)
    if not effect_text:
        effect_text = request.text or "Apply the item's combat effect."
    move_type = request.type_override or _infer_type(request.name, effect_text, fallback="Normal")
    move = _build_status_move(
        name=request.name or "Item Move",
        move_type=move_type,
        freq=request.frequency_override or _item_frequency(request.name, effect_text),
        effects_text=_item_effect_to_move_text(request.name or "Item", effect_text),
    )
    return {
        "move": move,
        "template": "item_action",
        "source_name": request.name,
        "metadata_source": metadata_source,
        "notes": [
            "Items are converted into direct use actions so both users and automation can call them uniformly.",
        ],
        "source_text": effect_text,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = _clean_text(text)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}


def _post_json(
    url: str,
    payload: dict,
    headers: Optional[dict[str, str]] = None,
    *,
    timeout: int = _DEFAULT_HTTP_TIMEOUT,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        if value:
            req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        detail = _clean_text(detail)
        if detail:
            raise ValueError(f"HTTP {exc.code}: {detail}") from exc
        raise


def _ollama_message_content(response: dict[str, Any]) -> str:
    message = ((response.get("message") or {}) if isinstance(response, dict) else {})
    return str(message.get("content") or "")


def _refine_move_with_local_model(result: dict[str, Any], request: ConversionRequest) -> dict[str, Any]:
    config = request.local_model or LocalModelConfig()
    if not request.use_ai:
        result["ai_refined"] = False
        result["ai_status"] = "not_used"
        result["ai_detail"] = "AI refinement was not used for this conversion."
        return result
    if not config.model:
        result["ai_refined"] = False
        result["ai_status"] = "not_used"
        result["ai_detail"] = "AI refinement was requested, but no model name was provided."
        return result
    move_payload = result["move"].to_engine_dict()
    prompt = (
        "You are refining a Pokemon Tabletop United move conversion. Return JSON only with optional keys from this schema: "
        "name,type,category,db,ac,range_kind,range_value,target_kind,target_range,area_kind,area_value,"
        "freq,keywords,priority,crit_range,effects_text,range_text,notes. "
        "Keep the move balanced and close to the baseline. Prefer Status moves for items and passive abilities. "
        "Rewrite videogame-style descriptions into PTU-ready effect text. "
        "Do not invent non-standard PTU keywords; if a concept belongs in effect text, put it in effects_text instead of keywords. "
        "Respect any user overrides as fixed constraints."
    )
    user_payload = {
        "ptu_reference": PTU_CONVERSION_REFERENCE,
        "request": {
            "kind": request.kind,
            "name": request.name,
            "text": request.text,
            "movement_mode": request.movement_mode,
        },
        "baseline_move": move_payload,
        "user_overrides": _override_summary(request),
        "source_text": result.get("source_text", ""),
        "notes": result.get("notes", []),
    }
    refined: dict[str, Any] = {}
    ai_detail = ""
    ai_raw_response = ""
    ai_reasoning: list[str] = []
    try:
        if config.provider == "ollama":
            base_url = (config.base_url or os.environ.get("AUTO_PTU_OLLAMA_URL") or "http://127.0.0.1:11434").rstrip("/")
            payload = {
                "model": config.model,
                "stream": False,
                "format": "json",
                "options": {"temperature": config.temperature},
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
            }
            response = _post_json(f"{base_url}/api/chat", payload, timeout=_AI_HTTP_TIMEOUT)
            content = _ollama_message_content(response)
            ai_raw_response = content
            refined = _extract_json_object(content)
            if not refined:
                retry_payload = {
                    "model": config.model,
                    "stream": False,
                    "options": {"temperature": config.temperature},
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"{prompt} Respond with a single JSON object and no markdown, no prose, and no code fences."
                            ),
                        },
                        {"role": "user", "content": json.dumps(user_payload)},
                    ],
                }
                retry_response = _post_json(f"{base_url}/api/chat", retry_payload, timeout=_AI_HTTP_TIMEOUT)
                retry_content = _ollama_message_content(retry_response)
                ai_raw_response = retry_content or ai_raw_response
                refined = _extract_json_object(retry_content)
                if refined:
                    ai_detail = "AI refinement applied after retrying the Ollama response without strict JSON mode."
                else:
                    preview = _clean_text(retry_content or content)[:220]
                    ai_detail = (
                        "Ollama responded, but it did not return usable structured move JSON."
                        + (f" Response preview: {preview}" if preview else "")
                    )
            else:
                ai_detail = "AI refinement applied from the Ollama response."
        else:
            base_url = (config.base_url or os.environ.get("AUTO_PTU_OPENAI_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")
            api_key = config.api_key or os.environ.get("AUTO_PTU_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
            payload = {
                "model": config.model,
                "temperature": config.temperature,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
            }
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            response = _post_json(f"{base_url}/v1/chat/completions", payload, headers=headers, timeout=_AI_HTTP_TIMEOUT)
            choices = response.get("choices") if isinstance(response, dict) else []
            content = ""
            if isinstance(choices, list) and choices:
                content = str((((choices[0] or {}).get("message") or {}).get("content")) or "")
            ai_raw_response = content
            refined = _extract_json_object(content)
            if refined:
                ai_detail = "AI refinement applied from the OpenAI-compatible endpoint."
            else:
                preview = _clean_text(content)[:220]
                ai_detail = (
                    "The model endpoint responded, but it did not return usable structured move JSON."
                    + (f" Response preview: {preview}" if preview else "")
                )
    except (OSError, ValueError, urllib.error.URLError, TimeoutError) as exc:
        refined = {}
        ai_detail = f"AI refinement failed to complete: {exc}"
    if not refined:
        result["ai_refined"] = False
        result["ai_status"] = "attempted_no_change"
        result["ai_detail"] = ai_detail or "AI refinement was attempted, but no usable structured changes were returned."
        result["ai_raw_response"] = _clean_text(ai_raw_response)
        result["ai_reasoning"] = ai_reasoning
        return result
    base_dict = move_payload
    allowed = {
        "name",
        "type",
        "category",
        "db",
        "ac",
        "range_kind",
        "range_value",
        "target_kind",
        "target_range",
        "area_kind",
        "area_value",
        "freq",
        "keywords",
        "priority",
        "crit_range",
        "effects_text",
        "range_text",
    }
    refined, sanitize_notes = sanitize_ai_patch(refined, base_dict)
    merged = dict(base_dict)
    for key, value in refined.items():
        if key in allowed:
            merged[key] = value
    result["move"] = MoveSpec.from_dict(merged)
    notes = result.setdefault("notes", [])
    notes.extend(sanitize_notes)
    if isinstance(refined.get("notes"), list):
        cleaned_notes = [_clean_text(str(entry)) for entry in refined["notes"] if _clean_text(str(entry))]
        notes.extend(cleaned_notes)
        ai_reasoning.extend(cleaned_notes)
    if isinstance(refined.get("reasoning"), list):
        ai_reasoning.extend(_clean_text(str(entry)) for entry in refined["reasoning"] if _clean_text(str(entry)))
    elif refined.get("reasoning"):
        text = _clean_text(str(refined.get("reasoning")))
        if text:
            ai_reasoning.append(text)
    result["ai_refined"] = True
    result["ai_status"] = "applied"
    result["ai_detail"] = ai_detail or "AI refinement was applied."
    result["ai_raw_response"] = _clean_text(ai_raw_response)
    result["ai_reasoning"] = ai_reasoning
    return result


def convert_to_move(request: ConversionRequest) -> dict[str, Any]:
    effective_kind = "move" if request.kind == "movement" else request.kind
    if effective_kind == "move":
        result = _convert_move(request)
    elif effective_kind == "ability":
        result = _convert_ability(request)
    elif effective_kind == "item":
        result = _convert_item(request)
    else:
        raise ValueError(f"Unsupported conversion kind: {request.kind}")
    result = _refine_move_with_local_model(result, request)
    move = result["move"]
    reassert_notes = _reassert_structured_move_rules(move, request)
    if reassert_notes:
        result.setdefault("notes", []).extend(reassert_notes)
        if result.get("ai_status") == "applied":
            result.setdefault("ai_reasoning", []).extend(reassert_notes)
    _apply_move_overrides(move, request)
    result.setdefault("ai_refined", False)
    result.setdefault("ai_status", "not_used")
    result.setdefault("ai_detail", "AI refinement was not used for this conversion.")
    result.setdefault("ai_raw_response", "")
    result.setdefault("ai_reasoning", [])
    return {
        "request": {
            "kind": effective_kind,
            "name": request.name,
            "text": request.text,
            "movement_mode": request.movement_mode,
            "range_override": request.range_override,
            "keywords_override": request.keywords_override,
            "type_override": request.type_override,
            "category_override": request.category_override,
            "frequency_override": request.frequency_override,
            "db_override": request.db_override,
            "use_ai": request.use_ai,
            "local_model": {
                "enabled": bool((request.local_model or LocalModelConfig()).enabled),
                "provider": (request.local_model or LocalModelConfig()).provider,
                "model": (request.local_model or LocalModelConfig()).model,
                "base_url": (request.local_model or LocalModelConfig()).base_url,
                "api_key_present": bool((request.local_model or LocalModelConfig()).api_key),
            },
        },
        "move": result["move"].to_engine_dict(),
        "template": result.get("template"),
        "metadata_source": result.get("metadata_source"),
        "source_text": result.get("source_text"),
        "notes": result.get("notes", []),
        "ai_refined": bool(result.get("ai_refined")),
        "ai_status": result.get("ai_status"),
        "ai_detail": result.get("ai_detail"),
        "ai_raw_response": result.get("ai_raw_response"),
        "ai_reasoning": result.get("ai_reasoning", []),
        "rulebook_basis": {
            "file": "files/rulebook/Making_Fixing PTU Pokemon.pdf",
            "summary": [
                "Give every Pokemon immediately usable options.",
                "Prefer interesting activatable abilities over passive flat bonuses.",
                "Use simple, accessible move templates when official data is thin or missing.",
            ],
        },
    }


def request_from_payload(payload: dict[str, Any]) -> ConversionRequest:
    kind = str(payload.get("kind") or "").strip().lower()
    if kind not in {"move", "movement", "ability", "item"}:
        raise ValueError("kind must be one of: move, ability, item")
    local_model_payload = payload.get("local_model") or {}
    config = LocalModelConfig(
        enabled=bool(local_model_payload.get("enabled", False)),
        provider=str(local_model_payload.get("provider") or "ollama"),
        model=str(local_model_payload.get("model") or ""),
        base_url=str(local_model_payload.get("base_url") or ""),
        api_key=str(local_model_payload.get("api_key") or ""),
        temperature=float(local_model_payload.get("temperature", 0.2) or 0.2),
    )
    return ConversionRequest(
        kind=kind,  # type: ignore[arg-type]
        name=str(payload.get("name") or ""),
        text=str(payload.get("text") or ""),
        movement_mode=str(payload.get("movement_mode") or ""),
        range_override=str(payload.get("range_override") or ""),
        keywords_override=str(payload.get("keywords_override") or ""),
        type_override=str(payload.get("type_override") or ""),
        category_override=str(payload.get("category_override") or ""),
        frequency_override=str(payload.get("frequency_override") or ""),
        db_override=int(payload["db_override"]) if payload.get("db_override") not in (None, "") else None,
        use_ai=bool(payload.get("use_ai", False)),
        local_model=config,
    )


__all__ = [
    "ConversionRequest",
    "LocalModelConfig",
    "convert_to_move",
    "request_from_payload",
]
