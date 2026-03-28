"""Generate lightweight campaign files that showcase every Foundry move keyword."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FOUNDATION_MOVES_DIR = PROJECT_ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-moves"
COMPILED_MOVES_PATH = PROJECT_ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
OUTPUT_DIR = PROJECT_ROOT / "auto_ptu" / "data" / "campaigns" / "keyword_demos"
MANIFEST_PATH = OUTPUT_DIR / "_manifest.json"


@dataclass
class ActionRecord:
    move_name: str
    action: dict


def _normalize(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _slugify_trait(trait: str) -> str:
    slug = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in trait.lower())
    slug = "-".join(filter(None, slug.split("-")))
    return slug or "trait"


def _trait_label(trait: str) -> str:
    words = [
        word.upper() if word.isupper() else word.capitalize()
        for word in trait.replace("_", " ").replace("-", " ").split()
        if word
    ]
    return " ".join(words) or trait.title()


def _load_foundry_trait_map() -> Dict[str, List[ActionRecord]]:
    if not FOUNDATION_MOVES_DIR.exists():
        raise FileNotFoundError(
            f"Foundry move directory missing: {FOUNDATION_MOVES_DIR}. "
            "Sync the ptr2e repository before generating keyword demos."
        )
    trait_map: Dict[str, List[ActionRecord]] = {}
    for path in FOUNDATION_MOVES_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            system = entry.get("system", {}) if isinstance(entry, dict) else {}
            for action in system.get("actions", []) or []:
                move_name = entry.get("name") or action.get("name") or path.stem
                for trait in action.get("traits", []) or []:
                    slug = trait.strip().lower()
                    if not slug:
                        continue
                    trait_map.setdefault(slug, []).append(ActionRecord(move_name=move_name, action=action))
    if not trait_map:
        raise RuntimeError(f"No traits discovered under {FOUNDATION_MOVES_DIR}")
    return trait_map


def _load_compiled_moves() -> Dict[str, dict]:
    if not COMPILED_MOVES_PATH.exists():
        raise FileNotFoundError(f"Compiled move data missing: {COMPILED_MOVES_PATH}")
    moves = json.loads(COMPILED_MOVES_PATH.read_text(encoding="utf-8"))
    lookup: Dict[str, dict] = {}
    for entry in moves:
        name = entry.get("name")
        if not name:
            continue
        lookup[_normalize(name)] = entry
    return lookup


def _select_action(
    records: Sequence[ActionRecord], compiled_lookup: Dict[str, dict]
) -> Tuple[ActionRecord, Optional[dict]]:
    for record in records:
        compiled = compiled_lookup.get(_normalize(record.move_name))
        if compiled:
            return record, compiled
    # fallback to the first available entry
    record = records[0]
    return record, compiled_lookup.get(_normalize(record.move_name))


def _coerce_int(value: object, default: Optional[int] = None) -> Optional[int]:
    if value in (None, "", 0):
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _infer_range(action: dict) -> Tuple[str, Optional[int], Optional[str], Optional[int], str]:
    rng = action.get("range") or {}
    target = str(rng.get("target", "")).lower()
    distance = _coerce_int(rng.get("distance"))
    size = _coerce_int(rng.get("size"))

    range_kind = "Ranged"
    range_value: Optional[int] = distance or 6
    area_kind: Optional[str] = None
    area_value: Optional[int] = None
    target_kind = range_kind

    if target in {"self"}:
        range_kind = target_kind = "Self"
        range_value = 0
    elif target in {"field", "allied-aura"}:
        range_kind = target_kind = "Field"
        range_value = None
        area_kind = "Burst"
        area_value = size or distance or 1
    elif target in {"ally", "enemy", "creature", "object"}:
        if distance and distance <= 1:
            range_kind = target_kind = "Melee"
            range_value = 1
        else:
            range_kind = target_kind = "Ranged"
            range_value = distance or 6
    elif target in {"blast", "cone", "line", "wide-line", "emanation"}:
        mapping = {
            "blast": "Burst",
            "cone": "Cone",
            "line": "Line",
            "wide-line": "Line",
            "emanation": "Burst",
        }
        area_kind = mapping[target]
        area_value = size or distance or 1
        if target == "emanation":
            range_kind = target_kind = "Self"
            range_value = 0
        else:
            range_kind = target_kind = "Ranged"
            range_value = distance or 6
    return range_kind, range_value, area_kind, area_value, target_kind


def _base_range_label(range_kind: str, range_value: Optional[int], area_kind: Optional[str], area_value: Optional[int]) -> str:
    pieces: List[str] = []
    if range_value:
        pieces.append(f"{range_kind} {range_value}")
    else:
        pieces.append(range_kind)
    if area_kind and area_value:
        pieces.append(f"{area_kind} {area_value}")
    return ", ".join(pieces)


def _build_keywords(trait: str) -> List[str]:
    keywords = {trait}
    if trait.startswith("push"):
        keywords.add("push")
    if trait.startswith("pull") or trait.startswith("draw-in"):
        keywords.add("pull")
    if trait == "smite":
        keywords.add("smite")
    if trait in {"set-up", "resolution"}:
        keywords.add(trait)
    return sorted({word for word in keywords if word})


def _fraction_from_trait(trait: str) -> Optional[str]:
    # Traits like recoil-1-3 encode numerator/denominator pairs.
    if "-" not in trait:
        return None
    prefix, *rest = trait.split("-")
    if prefix not in {"recoil", "drain"}:
        return None
    if len(rest) != 2:
        return None
    num, den = rest
    if not (num.isdigit() and den.isdigit()):
        return None
    return f"{num}/{den}"


def _build_move_payload(
    trait: str,
    move_name: str,
    action: dict,
    compiled_entry: Optional[dict],
) -> dict:
    trait_label = _trait_label(trait)
    range_kind, range_value, area_kind, area_value, target_kind = _infer_range(action)
    display_range = _base_range_label(range_kind, range_value, area_kind, area_value)

    db = compiled_entry.get("db") if compiled_entry else None
    if db is None:
        db = compiled_entry.get("damage_base") if compiled_entry else None
    db_value = _coerce_int(db, 8)

    move = {
        "name": move_name,
        "type": (compiled_entry or {}).get("type", "Normal"),
        "category": (compiled_entry or {}).get("category", (action.get("category") or "special")).title(),
        "db": db_value or 8,
        "ac": _coerce_int((compiled_entry or {}).get("ac")),
        "range_kind": range_kind,
        "range_value": range_value,
        "target_kind": target_kind,
        "target_range": range_value,
        "area_kind": area_kind,
        "area_value": area_value,
        "freq": (compiled_entry or {}).get("frequency", "EOT"),
        "keywords": _build_keywords(trait),
        "priority": _coerce_int((compiled_entry or {}).get("priority"), 0),
        "crit_range": _coerce_int((compiled_entry or {}).get("crit_range"), 20),
    }

    range_text = (compiled_entry or {}).get("range", display_range)
    trait_note = f"{display_range}, Trait: {trait_label}"
    if range_text:
        range_text = f"{range_text} / {trait_note}"
    else:
        range_text = trait_note
    move["range_text"] = range_text

    effects = (compiled_entry or {}).get("effects", "") or action.get("description", "")
    note = f"This attack highlights the {trait_label} keyword imported from Foundry."
    fraction = _fraction_from_trait(trait)
    if fraction and trait.startswith("recoil"):
        note += f" Recoil {fraction} is pre-encoded in the range text."
    move["effects_text"] = "\n\n".join([text for text in (effects, note) if text])
    return move


def _demo_actor(name: str, move: dict) -> dict:
    move_copy = json.loads(json.dumps(move))
    fallback_move = {
        "name": "Tackle",
        "type": "Normal",
        "category": "Physical",
        "db": 6,
        "ac": 2,
        "range_kind": "Melee",
        "range_value": 1,
        "target_kind": "Melee",
        "target_range": 1,
        "freq": "At-Will",
        "range_text": "Melee 1",
        "effects_text": "Fallback basic attack.",
    }
    return {
        "name": name,
        "species": name,
        "level": 30,
        "types": [move_copy.get("type") or "Normal"],
        "hp_stat": 15,
        "atk": 12,
        "def": 12,
        "spatk": 12,
        "spdef": 12,
        "spd": 12,
        "moves": [move_copy, fallback_move],
        "movement": {
            "overland": 6,
            "sky": 0,
            "swim": 4,
            "levitate": 0,
            "burrow": 0,
            "h_jump": 2,
            "l_jump": 2,
            "power": 4,
        },
    }


def _demo_target() -> dict:
    return {
        "name": "Target Dummy",
        "species": "Target Dummy",
        "level": 28,
        "types": ["Normal"],
        "hp_stat": 12,
        "atk": 8,
        "def": 8,
        "spatk": 8,
        "spdef": 8,
        "spd": 6,
        "moves": [
            {
                "name": "Harden",
                "type": "Normal",
                "category": "Status",
                "db": 0,
                "ac": None,
                "range_kind": "Self",
                "range_value": 0,
                "target_kind": "Self",
                "target_range": 0,
                "freq": "At-Will",
                "range_text": "Self",
                "effects_text": "The dummy braces for impact.",
            }
        ],
        "movement": {
            "overland": 4,
            "sky": 0,
            "swim": 2,
            "levitate": 0,
            "burrow": 0,
            "h_jump": 1,
            "l_jump": 1,
            "power": 2,
        },
    }


def _build_campaign(trait: str, move_name: str, move_payload: dict) -> dict:
    trait_label = _trait_label(trait)
    slug = _slugify_trait(trait)
    return {
        "name": f"Keyword Demo – {trait_label}",
        "description": (
            f"Autogenerated scenario highlighting the {trait_label} keyword via {move_name}. "
            f"Launch with `auto-ptu play keyword_demos/{slug}_demo`."
        ),
        "default_weather": "Clear",
        "grid": {"width": 10, "height": 6, "blockers": [], "tiles": {}},
        "players": [_demo_actor("Keyword Ace", move_payload)],
        "foes": [_demo_target()],
    }


def main() -> None:
    trait_map = _load_foundry_trait_map()
    compiled_lookup = _load_compiled_moves()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTPUT_DIR.glob("*.json"):
        if stale.name.startswith("_"):
            continue
        stale.unlink()

    manifest_entries: List[dict] = []
    for trait in sorted(trait_map):
        records = trait_map[trait]
        record, compiled = _select_action(records, compiled_lookup)
        move_payload = _build_move_payload(trait, record.move_name, record.action, compiled)
        campaign = _build_campaign(trait, record.move_name, move_payload)
        slug = _slugify_trait(trait)
        filename = OUTPUT_DIR / f"{slug}_demo.json"
        filename.write_text(json.dumps(campaign, indent=2) + "\n", encoding="utf-8")
        manifest_entries.append(
            {
                "trait": trait,
                "label": _trait_label(trait),
                "move": record.move_name,
                "campaign": f"keyword_demos/{slug}_demo",
            }
        )

    manifest = {"count": len(manifest_entries), "traits": manifest_entries}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(manifest_entries)} keyword demos to {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
