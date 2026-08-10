from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class CareerFeatureAdapter:
    feature_name: str
    category: str
    season_trigger: str
    magnitude: int
    source_hash: str


_KEYWORDS = {
    "health": ("medic", "heal", "rest", "enduring", "fortress"),
    "scouting": ("capture", "hunter", "research", "chronicler", "survival"),
    "development": ("mentor", "ace", "training", "stat", "commander", "style"),
    "economy": ("chef", "fashion", "backpacker", "craft", "item"),
    "reputation": ("coordinator", "musician", "dancer", "cheer", "provocateur"),
    "battle_plan": ("attack", "defense", "duelist", "roughneck", "ninja", "type"),
    "narrative_unlock": ("oracle", "telepath", "warper", "arcanist", "druid", "occult"),
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
    for feature in sorted(payload.get("features", []), key=lambda entry: str(entry.get("name") or "").lower()):
        name = str(feature.get("name") or "Unnamed PTU feature")
        effects = str(feature.get("effects") or "")
        digest = hashlib.sha256(f"{name}\n{effects}".encode("utf-8", errors="replace")).hexdigest()[:16]
        category = _category(name, effects)
        magnitude = 1 + int(digest[:2], 16) % 3
        trigger = "pre_match" if category == "battle_plan" else "season_decision"
        adapters.append(CareerFeatureAdapter(name, category, trigger, magnitude, digest))
    return {
        "classes": classes,
        "features": [asdict(entry) for entry in adapters],
        "class_count": len(classes),
        "feature_count": len(adapters),
        "unmapped": [],
    }


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
