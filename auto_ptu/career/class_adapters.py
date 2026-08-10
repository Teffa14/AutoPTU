from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class CareerFeatureAdapter:
    feature_name: str
    category: str
    season_trigger: str
    magnitude: int
    source_hash: str


@dataclass(frozen=True)
class CareerClassAdapter:
    class_name: str
    focus: str
    battle: Dict[str, int]
    season: Dict[str, int]
    decision_affinity: str
    description_es: str
    description_en: str
    feature_names: tuple[str, ...]


_KEYWORDS = {
    "health": ("medic", "heal", "rest", "enduring", "fortress"),
    "scouting": ("capture", "hunter", "research", "chronicler", "survival"),
    "development": ("mentor", "ace", "training", "stat", "commander", "style"),
    "economy": ("chef", "fashion", "backpacker", "craft", "item"),
    "reputation": ("coordinator", "musician", "dancer", "cheer", "provocateur"),
    "battle_plan": ("attack", "defense", "duelist", "roughneck", "ninja", "type"),
    "narrative_unlock": ("oracle", "telepath", "warper", "arcanist", "druid", "occult"),
}

_FOCUS_EFFECTS = {
    "health": ({}, {"health": 4}, "health", "Recupera 4 de salud tras cada temporada.", "Recover 4 health after every season."),
    "scouting": ({"away_level_bonus": -1}, {}, "capture", "Reduce en 1 nivel la preparación PTU rival.", "Reduce opposing PTU preparation by 1 level."),
    "development": ({}, {"partner_levels": 1}, "training", "Tu compañero gana 1 nivel adicional por temporada.", "Your partner gains 1 additional level each season."),
    "economy": ({}, {"finances": 1}, "economy", "Genera 1 recurso de club tras cada temporada.", "Generate 1 club resource after every season."),
    "reputation": ({}, {"reputation": 1}, "media", "Gana 1 reputación adicional tras cada temporada.", "Gain 1 additional reputation after every season."),
    "battle_plan": ({"home_level_bonus": 1}, {}, "rivalry", "Aporta +1 nivel de preparación legal desde el banquillo.", "Provide +1 legal preparation level from the bench."),
    "narrative_unlock": ({"away_level_bonus": -1}, {}, "research", "La previsión reduce en 1 nivel la preparación rival.", "Foresight reduces opposing preparation by 1 level."),
    "preparation": ({"home_level_bonus": 1}, {}, "training", "Aporta +1 nivel de preparación general al equipo.", "Provide +1 general preparation level to the team."),
}

_FOCUS_OVERRIDES = {
    **{name: "battle_plan" for name in (
        "attack ace", "defense ace", "special attack ace", "special defense ace", "speed ace",
        "type ace", "duelist", "commander", "berserker", "earth shaker", "fire bringer",
        "frost touched", "juggler", "maelstrom", "marksman", "martial artist", "miasmic",
        "ninja", "prism", "rider", "rogue", "roughneck", "shade caller", "skirmisher",
        "spark master", "stat ace", "stone warrior", "swarmlord", "telekinetic", "trickster",
        "tumbler", "wind runner",
    )},
    **{name: "health" for name in ("athlete", "enduring soul", "fortress", "medic", "steelheart")},
    **{name: "scouting" for name in ("capture specialist", "chronicler", "hunter", "researcher", "survivalist")},
    **{name: "development" for name in ("ace trainer", "mentor", "style expert", "taskmaster")},
    **{name: "economy" for name in ("backpacker", "chef", "fashionista", "hobbyist")},
    **{name: "reputation" for name in (
        "cheerleader", "cheerleader [playtest]", "coordinator", "dancer", "glamour weaver",
        "herald of pride", "musician", "provocateur",
    )},
    **{name: "narrative_unlock" for name in (
        "apparition", "arcanist", "channeler", "druid", "glitch bender", "hex maniac", "oracle",
        "rune master", "sage", "telepath", "warper",
    )},
}


def _dataset_path() -> Path:
    return Path(__file__).resolve().parents[1] / "api" / "static" / "character_creation.json"


def _category(name: str, effects: str) -> str:
    haystack = f"{name} {effects}".lower()
    for category, words in _KEYWORDS.items():
        if any(word in haystack for word in words):
            return category
    return "preparation"


@lru_cache(maxsize=1)
def compile_class_adapters() -> Dict[str, object]:
    payload = json.loads(_dataset_path().read_text(encoding="utf-8"))
    classes = sorted(
        ({"id": str(entry.get("id") or entry.get("name")), "name": str(entry.get("name") or entry.get("id"))} for entry in payload.get("classes", [])),
        key=lambda entry: (entry["name"].lower(), entry["id"]),
    )
    adapters: List[CareerFeatureAdapter] = []
    raw_features = {str(entry.get("name") or ""): entry for entry in payload.get("features", [])}
    for feature in sorted(payload.get("features", []), key=lambda entry: str(entry.get("name") or "").lower()):
        name = str(feature.get("name") or "Unnamed PTU feature")
        effects = str(feature.get("effects") or "")
        digest = hashlib.sha256(f"{name}\n{effects}".encode("utf-8", errors="replace")).hexdigest()[:16]
        category = _category(name, effects)
        magnitude = 1 + int(digest[:2], 16) % 3
        trigger = "pre_match" if category == "battle_plan" else "season_decision"
        adapters.append(CareerFeatureAdapter(name, category, trigger, magnitude, digest))
    class_adapters: List[CareerClassAdapter] = []
    raw_classes = {str(entry.get("name") or entry.get("id")): entry for entry in payload.get("classes", [])}
    for entry in classes:
        class_name = entry["name"]
        raw_class = raw_classes.get(class_name, {})
        feature_ids = [
            str(feature_id).removeprefix("feature:")
            for tier in (raw_class.get("tiers") or {}).values()
            for feature_id in (tier or [])
        ]
        feature_text = " ".join(
            f"{name} {raw_features.get(name, {}).get('effects', '')}"
            for name in feature_ids
        )
        focus = _FOCUS_OVERRIDES.get(class_name.lower()) or _category(class_name, feature_text)
        battle, season, affinity, description_es, description_en = _FOCUS_EFFECTS[focus]
        class_adapters.append(CareerClassAdapter(
            class_name=class_name,
            focus=focus,
            battle=dict(battle),
            season=dict(season),
            decision_affinity=affinity,
            description_es=description_es,
            description_en=description_en,
            feature_names=tuple(feature_ids),
        ))
    class_payload = {
        entry.class_name: {**asdict(entry), "feature_names": list(entry.feature_names)}
        for entry in class_adapters
    }
    return {
        "classes": [{**entry, **class_payload[entry["name"]]} for entry in classes],
        "features": [asdict(entry) for entry in adapters],
        "class_effects": class_payload,
        "class_count": len(classes),
        "feature_count": len(adapters),
        "unmapped": [],
    }


def selected_class_effects(class_names: Iterable[str]) -> dict:
    available = compile_class_adapters()["class_effects"]
    selected = [available[name] for name in class_names if name in available]
    battle: Dict[str, int] = {}
    season: Dict[str, int] = {}
    for adapter in selected:
        for key, value in adapter["battle"].items():
            battle[key] = battle.get(key, 0) + int(value)
        for key, value in adapter["season"].items():
            season[key] = season.get(key, 0) + int(value)
    return {"adapters": selected, "battle": battle, "season": season}


def validate_selected_classes(class_names: List[str]) -> List[str]:
    available = {str(entry["name"]).lower(): str(entry["name"]) for entry in compile_class_adapters()["classes"]}
    normalized = []
    for raw in class_names:
        key = str(raw).strip().lower()
        if not key or key not in available:
            raise ValueError(f"Unknown PTU trainer class: {raw}")
        if available[key] not in normalized:
            normalized.append(available[key])
    if not normalized:
        raise ValueError("Choose at least one PTU trainer class.")
    return normalized
