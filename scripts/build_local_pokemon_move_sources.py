from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PTU_YAML = ROOT / "PTUDatabase-main" / "Data" / "ptu.1.05.yaml"
POKEDEX_TEXT = ROOT / "audit_sources" / "Pokedex 1.05.txt"
SWSH_DEX = ROOT / "auto_ptu" / "data" / "compiled" / "swsh_galardex.json"
HISUI_DEX = ROOT / "auto_ptu" / "data" / "compiled" / "hisuidex.json"
OUT_JSON = ROOT / "auto_ptu" / "api" / "static" / "pokemon_move_sources.json"
OUT_EMBED = ROOT / "auto_ptu" / "api" / "static" / "pokemon_move_sources.embed.js"


def _match_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _clean_header_name(value: str) -> str:
    text = re.sub(r"^\d+", "", value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _clean_move_name(value: str) -> tuple[str, bool]:
    text = str(value or "").strip()
    if not text:
        return "", False
    natural = bool(re.search(r"\(\s*N\s*\)", text, flags=re.IGNORECASE))
    text = re.sub(r"\(\s*N\s*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^.*?Tutor Move List\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^[A-Z]\d+\s+", "", text)
    text = re.sub(r"^\d+\s+", "", text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip(" .;-")
    return text, natural


def _split_move_list(section: str) -> tuple[set[str], set[str]]:
    text = section.replace("\r", "\n")
    text = re.sub(r"([A-Za-z])-[\s\n]+([a-z])", r"\1\2", text)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    moves: set[str] = set()
    natural: set[str] = set()
    for raw in text.split(","):
        name, is_natural = _clean_move_name(raw)
        if not name or "Move List" in name or "Base Stats" in name:
            continue
        moves.add(name)
        if is_natural:
            natural.add(name)
    return moves, natural


def _empty_sources() -> dict[str, set[str]]:
    return {"egg": set(), "tm": set(), "tutor": set(), "natural": set()}


def _load_yaml_payload() -> dict[str, Any]:
    return yaml.safe_load(PTU_YAML.read_text(encoding="utf-8"))


def _valid_move_keys(payload: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for move in payload.get("Moves", []) or []:
        name = str(move.get("Name") or "").strip()
        if name:
            keys.add(_match_key(name))
    return keys


def _load_yaml_sources(payload: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    out: dict[str, dict[str, set[str]]] = {}
    for species in payload.get("Species", []):
        base_name = str(species.get("Name") or "").strip()
        for form in species.get("Forms", []) or []:
            form_name = str(form.get("Name") or "").strip()
            name = base_name if not form_name or form_name.lower() in {"normal", base_name.lower()} else f"{base_name} {form_name}"
            bucket = out.setdefault(name, _empty_sources())
            for move_entry in form.get("Moves", []) or []:
                requirement = str(move_entry.get("RequirementType") or "").strip().lower()
                move_name = str((move_entry.get("Move") or {}).get("Name") or "").strip()
                if requirement == "machine" and move_name:
                    bucket["tm"].add(move_name)
    return out


def _filter_valid_moves(moves: set[str], valid_move_keys: set[str]) -> set[str]:
    return {name for name in moves if _match_key(name) in valid_move_keys}


def _load_core_text_sources(canonical_names: list[str], valid_move_keys: set[str]) -> dict[str, dict[str, set[str]]]:
    if not POKEDEX_TEXT.exists():
        return {}
    text = POKEDEX_TEXT.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    name_by_key = {_match_key(name): name for name in canonical_names}
    headers: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not re.match(r"^\d*[A-Z][A-Z0-9 .'\-()♀♂ÃÉÈ]+$", stripped):
            continue
        if any("Base Stats" in lines[j] for j in range(idx + 1, min(idx + 8, len(lines)))):
            name = _clean_header_name(stripped)
            canonical = name_by_key.get(_match_key(name))
            if canonical:
                headers.append((idx, canonical))
    out: dict[str, dict[str, set[str]]] = {}
    for pos, (start, name) in enumerate(headers):
        end = headers[pos + 1][0] if pos + 1 < len(headers) else len(lines)
        block = "\n".join(lines[start:end])
        bucket = out.setdefault(name, _empty_sources())
        egg_match = re.search(r"Egg Move List(?P<body>.*?)(?:Tutor Move List|$)", block, flags=re.IGNORECASE | re.DOTALL)
        tutor_match = re.search(r"Tutor Move List(?P<body>.*)$", block, flags=re.IGNORECASE | re.DOTALL)
        if egg_match:
            egg, natural = _split_move_list(egg_match.group("body"))
            bucket["egg"].update(_filter_valid_moves(egg, valid_move_keys))
            bucket["natural"].update(_filter_valid_moves(natural, valid_move_keys))
        if tutor_match:
            tutor, natural = _split_move_list(tutor_match.group("body"))
            bucket["tutor"].update(_filter_valid_moves(tutor, valid_move_keys))
            bucket["natural"].update(_filter_valid_moves(natural, valid_move_keys))
    return out


def _load_compiled_supplement(path: Path) -> dict[str, dict[str, set[str]]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
    out: dict[str, dict[str, set[str]]] = {}
    for species_name, entry in entries.items():
        moves = entry.get("moves", {}) if isinstance(entry, dict) else {}
        bucket = out.setdefault(str(species_name), _empty_sources())
        for raw in moves.get("tm", []) or []:
            move_name = raw.get("move") if isinstance(raw, dict) else raw
            cleaned, natural = _clean_move_name(move_name)
            if cleaned:
                bucket["tm"].add(cleaned)
                if natural:
                    bucket["natural"].add(cleaned)
        for raw in moves.get("egg", []) or []:
            cleaned, natural = _clean_move_name(raw)
            if cleaned:
                bucket["egg"].add(cleaned)
                if natural:
                    bucket["natural"].add(cleaned)
        for raw in moves.get("tutor", []) or []:
            cleaned, natural = _clean_move_name(raw)
            if cleaned:
                bucket["tutor"].add(cleaned)
                if natural:
                    bucket["natural"].add(cleaned)
    return out


def _merge_sources(*sources: dict[str, dict[str, set[str]]]) -> dict[str, dict[str, list[str]]]:
    merged: dict[str, dict[str, set[str]]] = defaultdict(_empty_sources)
    for source in sources:
        for species_name, buckets in source.items():
            target = merged[species_name]
            for key in ("egg", "tm", "tutor", "natural"):
                target[key].update(buckets.get(key, set()))
    return {
        species_name: {key: sorted(values, key=str.casefold) for key, values in buckets.items()}
        for species_name, buckets in sorted(merged.items(), key=lambda item: item[0].casefold())
    }


def main() -> None:
    yaml_payload = _load_yaml_payload()
    valid_move_keys = _valid_move_keys(yaml_payload)
    yaml_sources = _load_yaml_sources(yaml_payload)
    canonical_names = list(yaml_sources)
    core_text_sources = _load_core_text_sources(canonical_names, valid_move_keys)
    swsh_sources = _load_compiled_supplement(SWSH_DEX)
    hisui_sources = _load_compiled_supplement(HISUI_DEX)
    entries = _merge_sources(yaml_sources, core_text_sources, swsh_sources, hisui_sources)
    payload: dict[str, Any] = {
        "generated_from": [
            str(PTU_YAML.relative_to(ROOT)),
            str(POKEDEX_TEXT.relative_to(ROOT)),
            str(SWSH_DEX.relative_to(ROOT)),
            str(HISUI_DEX.relative_to(ROOT)),
        ],
        "species_count": len(entries),
        "entries": entries,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUT_EMBED.write_text(
        "window.__AUTO_PTU_POKEMON_MOVE_SOURCES = " + json.dumps(payload, separators=(",", ":"), sort_keys=True) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_EMBED.relative_to(ROOT)} for {len(entries)} species/forms.")


if __name__ == "__main__":
    main()
