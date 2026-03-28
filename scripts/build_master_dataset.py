import csv
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from auto_ptu.species_filters import filter_user_selectable_species
from auto_ptu.rules.item_catalog import load_item_catalog

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FILES = ROOT / "files"
STATIC = ROOT / "auto_ptu" / "api" / "static"
BUILDER_STATIC = STATIC / "AutoPTUCharacter"
DATA = ROOT / "auto_ptu" / "data" / "compiled"

CHARACTER_CREATION = REPORTS / "character_creation.json"
MOVES_JSON = DATA / "moves.json"
SPECIES_JSON = DATA / "species.json"
WEAPONS_JSON = DATA / "weapons.json"
POKEDEX_ABILITIES_JSON = DATA / "pokedex_abilities.json"
ABILITY_OVERRIDES_JSON = DATA / "ability_overrides.json"
SWSH_GALARDEX_JSON = DATA / "swsh_galardex.json"
SWSH_REFERENCES_JSON = DATA / "swsh_references.json"
HISUIDEX_JSON = DATA / "hisuidex.json"
HISUI_REFERENCES_JSON = DATA / "hisui_references.json"
SUMO_REFERENCES_JSON = DATA / "sumo_references.json"

ABILITIES_CSV = FILES / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
ITEMS_CSV = FILES / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Item Data.csv"
INV_CSV = FILES / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv"
RULEBOOK_PATHS = [
    FILES / "rulebook" / "Pokemon Tabletop United 1.05 Core.pdf",
    FILES / "rulebook" / "PTU 1.05" / "Pokemon Tabletop United 1.05 Core.pdf",
]

OUT_REPORT = REPORTS / "master_dataset.json"
OUT_STATIC = STATIC / "master_dataset.json"
OUT_STATIC_EMBED = STATIC / "master_dataset.embed.js"
OUT_BUILDER_STATIC = BUILDER_STATIC / "master_dataset.json"
OUT_BUILDER_STATIC_EMBED = BUILDER_STATIC / "master_dataset.embed.js"

REPORTS.mkdir(parents=True, exist_ok=True)
STATIC.mkdir(parents=True, exist_ok=True)
BUILDER_STATIC.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _clean(value: str) -> str:
    return (value or "").replace("\r", "").strip()


def _norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def load_abilities_csv():
    out = []
    if not ABILITIES_CSV.exists():
        return out
    with ABILITIES_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _clean(row.get("Name"))
            if not name:
                continue
            out.append(
                {
                    "name": name,
                    "frequency": _clean(row.get("Frequency")),
                    "effect": _clean(row.get("Effect")),
                    "trigger": _clean(row.get("Trigger")),
                    "target": _clean(row.get("Target")),
                    "keywords": _clean(row.get("Keywords")),
                    "effect_2": _clean(row.get("Effect 2")),
                    "source": "fancy_abilities_csv",
                }
            )
    return out


def load_swsh_reference_abilities():
    payload = _read_json(SWSH_REFERENCES_JSON, {})
    entries = payload.get("abilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "frequency": _clean(entry.get("frequency")),
                "effect": _clean(entry.get("effect")),
                "trigger": _clean(entry.get("trigger")),
                "target": "",
                "keywords": "",
                "effect_2": _clean(entry.get("bonus") or entry.get("special")),
                "source": "swsh_references_pdf",
                "version": "SwSh + Armor/Crown References",
            }
        )
    return out


def load_sumo_reference_abilities():
    payload = _read_json(SUMO_REFERENCES_JSON, {})
    entries = payload.get("abilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "frequency": _clean(entry.get("frequency")),
                "effect": _clean(entry.get("effect")),
                "trigger": _clean(entry.get("trigger")),
                "target": "",
                "keywords": "",
                "effect_2": _clean(entry.get("bonus") or entry.get("special")),
                "source": "sumo_references_pdf",
                "version": "SuMo References",
            }
        )
    return out


def load_hisui_reference_abilities():
    payload = _read_json(HISUI_REFERENCES_JSON, {})
    entries = payload.get("abilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "frequency": _clean(entry.get("frequency")),
                "effect": _clean(entry.get("effect")),
                "trigger": _clean(entry.get("trigger")),
                "target": "",
                "keywords": "",
                "effect_2": _clean(entry.get("bonus") or entry.get("special")),
                "source": "hisui_references_pdf",
                "version": "Arceus References",
            }
        )
    return out


def load_swsh_reference_moves():
    payload = _read_json(SWSH_REFERENCES_JSON, {})
    entries = payload.get("moves", {}) if isinstance(payload, dict) else {}
    out = {}
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out[_norm_key(cleaned)] = {
            "source": "swsh_references_pdf",
            "version": "SwSh + Armor/Crown References",
        }
    return out


def load_sumo_reference_moves():
    payload = _read_json(SUMO_REFERENCES_JSON, {})
    entries = payload.get("moves", {}) if isinstance(payload, dict) else {}
    out = {}
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out[_norm_key(cleaned)] = {
            "source": "sumo_references_pdf",
            "version": "SuMo References",
        }
    return out


def load_hisui_reference_moves():
    payload = _read_json(HISUI_REFERENCES_JSON, {})
    entries = payload.get("moves", {}) if isinstance(payload, dict) else {}
    out = {}
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out[_norm_key(cleaned)] = {
            "source": "hisui_references_pdf",
            "version": "Arceus References",
        }
    return out


def load_items_csv():
    payload = {
        "food_items": [],
        "held_items": [],
        "capabilities": [],
        "weather": [],
    }
    if not ITEMS_CSV.exists():
        return payload

    with ITEMS_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return payload

    headers = [h.strip() for h in rows[0]]
    def idx(name, after=-1):
        for i in range(after + 1, len(headers)):
            if headers[i] == name:
                return i
        return -1

    food_name_i = idx("Food Item")
    food_buff_i = idx("Digestion/Food Buff")
    held_name_i = idx("Held Item")
    held_desc_i = idx("Description", held_name_i)
    cap_name_i = idx("Capability")
    cap_desc_i = idx("Description", cap_name_i)
    weather_name_i = idx("Weather")
    weather_effect_i = idx("Effect")

    for row in rows[1:]:
        if not row:
            continue
        while len(row) < len(headers):
            row.append("")

        if food_name_i >= 0:
            name = _clean(row[food_name_i])
            if name:
                payload["food_items"].append(
                    {
                        "name": name,
                        "buff": _clean(row[food_buff_i]) if food_buff_i >= 0 else "",
                        "source": "fancy_items_csv",
                    }
                )
        if held_name_i >= 0:
            name = _clean(row[held_name_i])
            if name:
                payload["held_items"].append(
                    {
                        "name": name,
                        "description": _clean(row[held_desc_i]) if held_desc_i >= 0 else "",
                        "source": "fancy_items_csv",
                    }
                )
        if cap_name_i >= 0:
            name = _clean(row[cap_name_i])
            if name:
                payload["capabilities"].append(
                    {
                        "name": name,
                        "description": _clean(row[cap_desc_i]) if cap_desc_i >= 0 else "",
                        "source": "fancy_items_csv",
                    }
                )
        if weather_name_i >= 0:
            name = _clean(row[weather_name_i])
            if name:
                payload["weather"].append(
                    {
                        "name": name,
                        "effect": _clean(row[weather_effect_i]) if weather_effect_i >= 0 else "",
                        "source": "fancy_items_csv",
                    }
                )

    return payload


def load_inventory_csv():
    payload = []
    if not INV_CSV.exists():
        return payload

    with INV_CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        return payload

    category_row = rows[0]
    header_row = rows[1]
    categories = []
    current = ""
    for idx, cell in enumerate(category_row):
        if _clean(cell):
            current = _clean(cell)
        categories.append(current or "Unknown")

    for row in rows[2:]:
        if not row or not any(_clean(cell) for cell in row):
            continue
        while len(row) < len(header_row):
            row.append("")
        per_category = {}
        for i, value in enumerate(row):
            category = categories[i]
            key = _clean(header_row[i]) or f"col_{i}"
            if category not in per_category:
                per_category[category] = {}
            per_category[category][key] = _clean(value)

        for category, fields in per_category.items():
            name = fields.get("Name", "")
            if not name:
                continue
            entry = {
                "category": category,
                "name": name,
                "cost": fields.get("Cost", ""),
                "description": fields.get("Description", ""),
                "mod": fields.get("Mod", ""),
                "slot": fields.get("Slot", ""),
                "source": "fancy_inventory_csv",
            }
            payload.append(entry)

    return payload


def augment_inventory_with_catalog(items_payload, inventory_payload):
    existing_names = {
        _norm_key(entry.get("name", ""))
        for bucket in ("food_items", "held_items", "weather")
        for entry in items_payload.get(bucket, [])
        if isinstance(entry, dict) and entry.get("name")
    }
    existing_names.update(
        _norm_key(entry.get("name", ""))
        for entry in inventory_payload
        if isinstance(entry, dict) and entry.get("name")
    )
    for entry in load_item_catalog().values():
        name = (entry.name or "").strip()
        if not name:
            continue
        norm = _norm_key(name)
        if not norm or norm in existing_names:
            continue
        inventory_payload.append(
            {
                "category": "Foundry Gear",
                "name": name,
                "cost": "",
                "description": (entry.description or "").strip(),
                "mod": "",
                "slot": "",
                "source": "foundry_core_gear",
            }
        )
        existing_names.add(norm)
    return inventory_payload


def load_rulebook_capabilities():
    path = next((p for p in RULEBOOK_PATHS if p.exists()), None)
    if not path:
        return {}
    reader = PdfReader(str(path))
    start_page = None
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if "Special Capabilities" in text:
            start_page = i + 1
            break
    if not start_page:
        return {}
    chunks = []
    for page_num in range(start_page, min(start_page + 6, len(reader.pages) + 1)):
        text = reader.pages[page_num - 1].extract_text() or ""
        if "Glossary of Terms" in text:
            break
        chunks.append(text)
    raw = " ".join(chunks)
    raw = raw.replace("PokÃƒÂ©mon", "Pokemon").replace("PokÃ©mon", "Pokemon").replace("PokÃ©", "Poke")
    raw = raw.replace("Y ou", "You")
    raw = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    pattern = re.compile(r"([A-Z][A-Za-z'\- ]{2,50}?)\s*:\s")
    matches = list(pattern.finditer(raw))
    blocked = {"Special Capabilities", "Indices and Reference", "Chapter"}
    results = {}
    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        if not name or name in blocked:
            continue
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        desc = raw[match.end():end].strip()
        if not desc:
            continue
        results[name] = desc
    return results


def merge_capabilities(species_caps, item_caps):
    rulebook_caps = load_rulebook_capabilities()
    rulebook_by_key = { _norm_key(name): desc for name, desc in rulebook_caps.items() }
    merged = {}
    for cap in species_caps:
        name = _clean(cap)
        if not name:
            continue
        key = name.lower()
        merged[key] = {
            "name": name,
            "description": "",
            "sources": ["species"],
        }
    for entry in item_caps:
        name = _clean(entry.get("name"))
        if not name:
            continue
        key = name.lower()
        if key not in merged:
            merged[key] = {
                "name": name,
                "description": entry.get("description") or "",
                "sources": [entry.get("source") or "items"],
            }
        else:
            if entry.get("description") and not merged[key].get("description"):
                merged[key]["description"] = entry.get("description")
            if entry.get("source") and entry.get("source") not in merged[key]["sources"]:
                merged[key]["sources"].append(entry.get("source"))
    if rulebook_by_key:
        for entry in merged.values():
            key = _norm_key(entry["name"])
            desc = rulebook_by_key.get(key)
            if desc and not entry.get("description"):
                entry["description"] = desc
            if desc and "rulebook_core" not in entry.get("sources", []):
                entry.setdefault("sources", []).append("rulebook_core")
    return sorted(merged.values(), key=lambda x: x["name"].lower())


def load_swsh_capabilities():
    payload = _read_json(SWSH_REFERENCES_JSON, {})
    entries = payload.get("capabilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "description": _clean(entry.get("text")),
                "source": "swsh_references_pdf",
            }
        )
    return out


def load_hisui_capabilities():
    payload = _read_json(HISUI_REFERENCES_JSON, {})
    entries = payload.get("capabilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "description": _clean(entry.get("text")),
                "source": "hisui_references_pdf",
            }
        )
    return out


def load_sumo_capabilities():
    payload = _read_json(SUMO_REFERENCES_JSON, {})
    entries = payload.get("capabilities", {}) if isinstance(payload, dict) else {}
    out = []
    if not isinstance(entries, dict):
        return out
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        cleaned = _clean(name)
        if not cleaned:
            continue
        out.append(
            {
                "name": cleaned,
                "description": _clean(entry.get("text")),
                "source": "sumo_references_pdf",
            }
        )
    return out


def _species_source_membership():
    membership = {}

    def add(entries, source, version):
        if isinstance(entries, dict):
            iterable = entries.values()
        elif isinstance(entries, list):
            iterable = entries
        else:
            return
        for entry in iterable:
            if not isinstance(entry, dict):
                continue
            name = _clean(entry.get("name") or entry.get("species"))
            if not name:
                continue
            key = _norm_key(name)
            if not key:
                continue
            history = membership.setdefault(key, [])
            payload = {"source": source, "version": version}
            if payload not in history:
                history.append(payload)

    add((_read_json(SWSH_GALARDEX_JSON, {}) or {}).get("entries", {}), "swsh_galardex_json", "SwSh GalarDex + Armor/Crown")
    add((_read_json(HISUIDEX_JSON, {}) or {}).get("entries", {}), "hisuidex_json", "HisuiDex / Arceus")
    return membership


MAY_2015_PLAYTEST_CLASS_NAMES = {
    "Backpacker",
}


SEPTEMBER_2015_PLAYTEST_CLASS_NAMES = {
    "Medic",
    "Cheerleader [Playtest]",
}


MAY_2015_PLAYTEST_FEATURE_NAMES = {
    "Backpacker",
    "Item Mastery",
    "Equipment Savant",
    "Hero's Journey",
    "Call to Adventure",
    "Frisk",
    "Handyman",
    "Hat Trick",
    "Movement Mastery",
    "Sole Power",
    "Wayfarer",
    "Wear It Better",
}


SEPTEMBER_2015_PLAYTEST_FEATURE_NAMES = {
    "Cheerleader [Playtest]",
    "Moment of Action [Playtest]",
    "Cheers [Playtest]",
    "Bring It On! [Playtest]",
    "Inspirational Support [Playtest]",
    "Go, Fight, Win! [Playtest]",
    "Keep Fighting! [Playtest]",
    "Medic",
    "Front Line Healer",
    "Medical Techniques [Medic]",
    "I'm a Doctor",
    "Proper Care",
    "Stay With Us!",
}


MAY_2015_PLAYTEST_ITEM_NAMES = {
    "Traditional Medicine Reference [5-15 Playtest]",
    "Cap Cannon [5-15 Playtest]",
    "Bean Cap [5-15 Playtest]",
    "Glue Cap [5-15 Playtest]",
    "Net Cap [5-15 Playtest]",
}


SEPTEMBER_2015_PLAYTEST_ITEM_NAMES = {
    "Combat Medic's Primer [9-15 Playtest]",
    "Shield [9-15 Playtest]",
    "Light Armor [9-15 Playtest]",
    "Special Armor [9-15 Playtest]",
    "Heavy Armor [9-15 Playtest]",
}


SEPTEMBER_2015_PLAYTEST_MOVE_NAMES = {
    "Defense Curl",
    "Hold Hands",
    "Withdraw",
}


PORYGON_DREAM_CLASS_NAMES = {
    "Engineer",
    "Jailbreaker",
    "Upgrader",
    "Glitch Bender",
}


GAME_OF_THROHS_CLASS_NAMES = {
    "Apparition",
    "Arcanist",
    "Berserker",
    "Druid",
    "Earth Shaker",
    "Fire Bringer",
    "Fortress",
    "Frost Touched",
    "Glamour Weaver",
    "Herald of Pride",
    "Maelstrom",
    "Marksman",
    "Miasmic",
    "Prism",
    "Rune Master",
    "Shade Caller",
    "Skirmisher",
    "Spark Master",
    "Steelheart",
    "Stone Warrior",
    "Swarmlord",
    "Wind Runner",
}


PORYGON_DREAM_EDGE_NAMES = {
    "Glitched Existence",
    "Pokébot Training",
    "Pokebot Training",
}


GAME_OF_THROHS_EDGE_NAMES = {
    "Arcane Favor",
    "Elemental Connection",
    "Mystic Senses",
    "Weapon of Choice",
}


PORYGON_DREAM_POKE_EDGE_NAMES = {
    "Digital Avatar",
    "Type Sync",
}


BLESSED_AND_DAMNED_EDGE_NAMES = {
    "Touched",
    "Soulbound",
}


BLESSED_AND_DAMNED_FEATURE_NAMES = {
    "Major Gift",
    "Pact Gift",
    "Signer",
    "Sign Mastery Rank 1",
    "Sign Mastery Rank 2",
    "Sign Mastery Rank 3",
    "Sign Mastery Rank 4",
    "Messiah",
    "In My Name Rank 1",
    "In My Name Rank 2",
    "In My Name Rank 3",
    "In My Name Rank 4",
    "Branded",
    "Usurper",
    "Shared Strengths Rank 1",
    "Shared Strengths Rank 2",
    "Shared Strengths Rank 3",
    "True Power",
    "Gift of Power",
    "Gift of Command",
    "Symbolsight",
    "Giftsapper",
    "Godslayer",
}


def _annotate_playtest_entry(entry, source, version):
    if not isinstance(entry, dict):
        return entry
    row = dict(entry)
    row["source"] = source
    row["version"] = version
    return row


def _annotate_sourcebook_entry(entry, source, version):
    if not isinstance(entry, dict):
        return entry
    row = dict(entry)
    row["source"] = source
    row["version"] = version
    return row


def _append_supplemental_source(entry, source, version):
    if not isinstance(entry, dict):
        return entry
    row = dict(entry)
    history = list(row.get("supplemental_sources") or [])
    payload = {"source": source, "version": version}
    if payload not in history:
        history.append(payload)
    row["supplemental_sources"] = history
    return row


def _annotate_trainer_playtest_entries(entries, kind):
    annotated = []
    for entry in entries or []:
        row = dict(entry) if isinstance(entry, dict) else entry
        name = _clean(row.get("name")) if isinstance(row, dict) else ""
        if kind == "class":
            if name in MAY_2015_PLAYTEST_CLASS_NAMES:
                row = _annotate_playtest_entry(row, "may_2015_playtest_packet", "PTU May 2015 Playtest Packet")
            elif name in SEPTEMBER_2015_PLAYTEST_CLASS_NAMES:
                row = _annotate_playtest_entry(row, "september_2015_playtest_packet", "PTU September 2015 Playtest Packet")
        elif kind == "feature":
            if name in MAY_2015_PLAYTEST_FEATURE_NAMES:
                row = _annotate_playtest_entry(row, "may_2015_playtest_packet", "PTU May 2015 Playtest Packet")
            elif name in SEPTEMBER_2015_PLAYTEST_FEATURE_NAMES:
                row = _annotate_playtest_entry(row, "september_2015_playtest_packet", "PTU September 2015 Playtest Packet")
        annotated.append(row)
    return annotated


def _collect_descendant_feature_names(character_creation, class_names):
    classes = character_creation.get("classes", []) or []
    features = character_creation.get("features", []) or []
    edges_graph = character_creation.get("edges", []) or []

    class_ids = {
        _clean(entry.get("id"))
        for entry in classes
        if isinstance(entry, dict) and _clean(entry.get("name")) in class_names
    }
    feature_name_by_id = {
        _clean(entry.get("id")): _clean(entry.get("name"))
        for entry in features
        if isinstance(entry, dict) and _clean(entry.get("id")) and _clean(entry.get("name"))
    }
    adjacency = {}
    for edge in edges_graph:
        if not isinstance(edge, dict):
            continue
        origin = _clean(edge.get("from"))
        target = _clean(edge.get("to"))
        if not origin or not target:
            continue
        adjacency.setdefault(origin, set()).add(target)

    feature_names = set()
    queue = list(class_ids)
    seen = set(class_ids)
    while queue:
        current = queue.pop(0)
        for target in adjacency.get(current, ()):
            if target in seen:
                continue
            seen.add(target)
            queue.append(target)
            if target.startswith("feature:"):
                feature_name = feature_name_by_id.get(target)
                if feature_name:
                    feature_names.add(feature_name)
    return feature_names


def _annotate_sourcebook_entries(entries, names, source, version):
    annotated = []
    for entry in entries or []:
        row = dict(entry) if isinstance(entry, dict) else entry
        name = _clean(row.get("name")) if isinstance(row, dict) else ""
        if name in names:
            row = _annotate_sourcebook_entry(row, source, version)
        annotated.append(row)
    return annotated


def _annotate_blessed_and_damned_features(entries):
    annotated = []
    for entry in entries or []:
        row = dict(entry) if isinstance(entry, dict) else entry
        tags = row.get("tags") if isinstance(row, dict) else []
        if isinstance(tags, str):
            tags = [tags]
        normalized_tags = {
            _clean(tag).strip("[]")
            for tag in (tags or [])
            if _clean(tag)
        }
        if "Patron Stat" in normalized_tags or _clean(row.get("name")) in BLESSED_AND_DAMNED_FEATURE_NAMES:
            row = _annotate_sourcebook_entry(row, "blessed_and_damned", "Blessed and the Damned")
        annotated.append(row)
    return annotated


def main():
    character_creation = _read_json(CHARACTER_CREATION, {})
    moves = _read_json(MOVES_JSON, [])
    species = filter_user_selectable_species(_read_json(SPECIES_JSON, []))
    weapons = _read_json(WEAPONS_JSON, [])
    pokedex_abilities = _read_json(POKEDEX_ABILITIES_JSON, {})
    ability_overrides = _read_json(ABILITY_OVERRIDES_JSON, {})
    species_source_membership = _species_source_membership()
    porygon_dream_feature_names = _collect_descendant_feature_names(character_creation, PORYGON_DREAM_CLASS_NAMES)
    game_of_throhs_feature_names = _collect_descendant_feature_names(character_creation, GAME_OF_THROHS_CLASS_NAMES)

    move_source_overrides = {}
    move_source_overrides.update(load_sumo_reference_moves())
    move_source_overrides.update(load_swsh_reference_moves())
    move_source_overrides.update(load_hisui_reference_moves())
    annotated_moves = []
    for entry in moves:
        if not isinstance(entry, dict):
            continue
        row = dict(entry)
        meta = move_source_overrides.get(_norm_key(row.get("name", "")), {})
        row.setdefault("source", meta.get("source", "fancy_moves_csv"))
        row.setdefault("version", meta.get("version", "Official PTU 1.05 + Hisui Sheet"))
        if meta:
            row["supplemental_sources"] = [
                {
                    "source": meta.get("source", ""),
                    "version": meta.get("version", ""),
                }
            ]
        if _clean(row.get("name")) in SEPTEMBER_2015_PLAYTEST_MOVE_NAMES:
            row = _append_supplemental_source(row, "september_2015_playtest_packet", "PTU September 2015 Playtest Packet")
        annotated_moves.append(row)

    abilities = load_abilities_csv()
    sumo_abilities = load_sumo_reference_abilities()
    swsh_abilities = load_swsh_reference_abilities()
    hisui_abilities = load_hisui_reference_abilities()
    ability_keys = {_norm_key(entry.get("name", "")) for entry in abilities}
    ability_map = {_norm_key(entry.get("name", "")): entry for entry in abilities if _norm_key(entry.get("name", ""))}
    for entry in [*sumo_abilities, *swsh_abilities, *hisui_abilities]:
        key = _norm_key(entry.get("name", ""))
        if key in ability_keys:
            existing = ability_map.get(key)
            if isinstance(existing, dict):
                history = list(existing.get("supplemental_sources") or [])
                history.append({"source": entry.get("source", ""), "version": entry.get("version", "")})
                deduped = []
                seen = set()
                for item in history:
                    sig = (str(item.get("source", "")).strip().lower(), str(item.get("version", "")).strip().lower())
                    if sig in seen:
                        continue
                    seen.add(sig)
                    deduped.append(item)
                existing["supplemental_sources"] = deduped
            continue
        abilities.append(entry)
        ability_keys.add(key)
        ability_map[key] = entry
    items = load_items_csv()
    for key in ("food_items", "held_items", "weather"):
        annotated_group = []
        for entry in items.get(key, []) or []:
            row = dict(entry) if isinstance(entry, dict) else entry
            name = _clean(row.get("name")) if isinstance(row, dict) else ""
            if name in MAY_2015_PLAYTEST_ITEM_NAMES:
                row = _annotate_playtest_entry(row, "may_2015_playtest_packet", "PTU May 2015 Playtest Packet")
            elif name in SEPTEMBER_2015_PLAYTEST_ITEM_NAMES:
                row = _annotate_playtest_entry(row, "september_2015_playtest_packet", "PTU September 2015 Playtest Packet")
            annotated_group.append(row)
        items[key] = annotated_group
    inventory = load_inventory_csv()
    inventory = augment_inventory_with_catalog(items, inventory)
    inventory = [
        _annotate_playtest_entry(entry, "may_2015_playtest_packet", "PTU May 2015 Playtest Packet")
        if _clean(entry.get("name")) in MAY_2015_PLAYTEST_ITEM_NAMES
        else _annotate_playtest_entry(entry, "september_2015_playtest_packet", "PTU September 2015 Playtest Packet")
        if _clean(entry.get("name")) in SEPTEMBER_2015_PLAYTEST_ITEM_NAMES
        else entry
        for entry in inventory
    ]

    species_caps = []
    for entry in species:
        for cap in entry.get("capabilities", []) or []:
            species_caps.append(cap)

    capabilities = merge_capabilities(
        species_caps,
        items.get("capabilities", []) + load_sumo_capabilities() + load_swsh_capabilities() + load_hisui_capabilities(),
    )

    annotated_species = []
    for entry in species:
        if not isinstance(entry, dict):
            continue
        row = dict(entry)
        key = _norm_key(row.get("name", ""))
        row.setdefault("source", "species_json")
        row.setdefault("version", "Official PTU Species Dataset")
        supplemental = list(species_source_membership.get(key, []))
        if supplemental:
            row["supplemental_sources"] = supplemental
        annotated_species.append(row)

    trainer_classes = _annotate_trainer_playtest_entries(character_creation.get("classes", []), "class")
    trainer_classes = _annotate_sourcebook_entries(
        trainer_classes,
        PORYGON_DREAM_CLASS_NAMES,
        "porygon_dream_of_mareep",
        "Do Porygon Dream of Mareep?",
    )
    trainer_classes = _annotate_sourcebook_entries(
        trainer_classes,
        GAME_OF_THROHS_CLASS_NAMES,
        "game_of_throhs",
        "Game of Throhs",
    )

    trainer_features = _annotate_trainer_playtest_entries(character_creation.get("features", []), "feature")
    trainer_features = _annotate_blessed_and_damned_features(trainer_features)
    trainer_features = _annotate_sourcebook_entries(
        trainer_features,
        porygon_dream_feature_names | PORYGON_DREAM_CLASS_NAMES,
        "porygon_dream_of_mareep",
        "Do Porygon Dream of Mareep?",
    )
    trainer_features = _annotate_sourcebook_entries(
        trainer_features,
        game_of_throhs_feature_names | GAME_OF_THROHS_CLASS_NAMES,
        "game_of_throhs",
        "Game of Throhs",
    )

    trainer_edges = _annotate_sourcebook_entries(
        character_creation.get("edges_catalog", []),
        BLESSED_AND_DAMNED_EDGE_NAMES,
        "blessed_and_damned",
        "Blessed and the Damned",
    )
    trainer_edges = _annotate_sourcebook_entries(
        trainer_edges,
        PORYGON_DREAM_EDGE_NAMES,
        "porygon_dream_of_mareep",
        "Do Porygon Dream of Mareep?",
    )
    trainer_edges = _annotate_sourcebook_entries(
        trainer_edges,
        GAME_OF_THROHS_EDGE_NAMES,
        "game_of_throhs",
        "Game of Throhs",
    )

    trainer_poke_edges = _annotate_sourcebook_entries(
        character_creation.get("poke_edges_catalog", []),
        PORYGON_DREAM_POKE_EDGE_NAMES,
        "porygon_dream_of_mareep",
        "Do Porygon Dream of Mareep?",
    )

    dataset = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "character_creation": str(CHARACTER_CREATION),
            "moves": str(MOVES_JSON),
            "species": str(SPECIES_JSON),
            "weapons": str(WEAPONS_JSON),
            "pokedex_abilities": str(POKEDEX_ABILITIES_JSON),
            "ability_overrides": str(ABILITY_OVERRIDES_JSON),
            "swsh_galardex": str(SWSH_GALARDEX_JSON),
            "swsh_references": str(SWSH_REFERENCES_JSON),
            "hisuidex": str(HISUIDEX_JSON),
            "hisui_references": str(HISUI_REFERENCES_JSON),
            "sumo_references": str(SUMO_REFERENCES_JSON),
            "abilities_csv": str(ABILITIES_CSV),
            "items_csv": str(ITEMS_CSV),
            "inventory_csv": str(INV_CSV),
        },
        "counts": {
            "classes": len(character_creation.get("classes", [])),
            "features": len(character_creation.get("features", [])),
            "edges": len(character_creation.get("edges_catalog", [])),
            "poke_edges": len(character_creation.get("poke_edges_catalog", [])),
            "skills": len(character_creation.get("skills", [])),
            "skills_catalog": len(character_creation.get("skills_catalog", [])),
            "moves": len(annotated_moves),
            "species": len(species),
            "abilities": len(abilities),
            "capabilities": len(capabilities),
            "weapons": len(weapons),
            "inventory_items": len(inventory),
            "food_items": len(items.get("food_items", [])),
            "held_items": len(items.get("held_items", [])),
            "weather": len(items.get("weather", [])),
        },
        "trainer": {
            "classes": trainer_classes,
            "features": trainer_features,
            "edges": trainer_edges,
            "poke_edges": trainer_poke_edges,
            "skills": character_creation.get("skills", []),
            "skills_catalog": character_creation.get("skills_catalog", []),
            "skill_rules": character_creation.get("skill_rules", {}),
            "feature_slots_by_rank": character_creation.get("feature_slots_by_rank", {}),
            "nodes": character_creation.get("nodes", []),
            "edges_graph": character_creation.get("edges", []),
        },
        "pokemon": {
            "moves": annotated_moves,
            "species": annotated_species,
            "abilities": abilities,
            "pokedex_abilities": pokedex_abilities,
            "ability_overrides": ability_overrides,
            "capabilities": capabilities,
        },
        "items": {
            "food_items": items.get("food_items", []),
            "held_items": items.get("held_items", []),
            "weather": items.get("weather", []),
            "inventory": inventory,
            "weapons": weapons,
        },
    }

    OUT_REPORT.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_STATIC.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_STATIC_EMBED.write_text(
        "window.__AUTO_PTU_MASTER_DATA = " + json.dumps(dataset, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    OUT_BUILDER_STATIC.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_BUILDER_STATIC_EMBED.write_text(
        "window.__AUTO_PTU_MASTER_DATA = " + json.dumps(dataset, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
