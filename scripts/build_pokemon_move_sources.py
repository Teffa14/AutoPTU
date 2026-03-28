from __future__ import annotations

import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

from auto_ptu.sprites import _slugify


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "PTUDatabase-main" / "Data" / "ptu.1.05.yaml"
OUT_JSON = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "pokemon_move_sources.json"
OUT_EMBED = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "pokemon_move_sources.embed.js"
USER_AGENT = "AutoPTU-MoveSourceBuilder/1.0"
POKEAPI_POKEMON = "https://pokeapi.co/api/v2/pokemon/"
POKEAPI_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/"
SWSH_GALARDEX_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "swsh_galardex.json"
HISUIDEX_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "hisuidex.json"


def _canonical_species_name(base: str, form_name: str | None) -> str:
    if not form_name:
        return base
    normalized = form_name.strip()
    if not normalized:
        return base
    lower = normalized.lower()
    if lower in {"normal", "base", base.lower()}:
        return base
    return f"{base} {normalized}"


def _fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _load_yaml_entries() -> list[dict[str, Any]]:
    raw = yaml.safe_load(DATABASE_PATH.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for species in raw.get("Species", []):
        base_name = str(species.get("Name") or "").strip()
        dex = int(species.get("NationalDexNumber") or 0)
        if not base_name or dex <= 0:
            continue
        for form in species.get("Forms", []):
            form_name = str(form.get("Name") or "").strip()
            out.append(
                {
                    "name": _canonical_species_name(base_name, form_name),
                    "base_name": base_name,
                    "form_name": form_name,
                    "dex": dex,
                }
            )
    return out


def _normalize_tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _species_specific_aliases(base_slug: str, form_slug: str) -> list[str]:
    last = form_slug.split("-")[-1] if form_slug else ""
    aliases: list[str] = []
    lookup = {
        "deoxys": {"n": "normal", "a": "attack", "d": "defense", "s": "speed"},
        "landorus": {"i": "incarnate", "t": "therian"},
        "thundurus": {"i": "incarnate", "t": "therian"},
        "tornadus": {"i": "incarnate", "t": "therian"},
        "enamorus": {"i": "incarnate", "t": "therian"},
        "giratina": {"a": "altered", "o": "origin"},
        "shaymin": {"l": "land", "s": "sky"},
        "darmanitan": {"s": "standard", "z": "zen"},
        "hoopa": {"c": "confined", "b": "confined", "u": "unbound"},
        "kyurem": {"r": "white", "reshiram": "white", "z": "black", "zekrom": "black"},
        "rotom": {"n": "", "fn": "fan", "fr": "frost", "h": "heat", "m": "mow", "w": "wash"},
        "pumpkaboo": {"a": "average", "sm": "small", "l": "large", "su": "super"},
        "gourgeist": {"a": "average", "sm": "small", "l": "large", "su": "super"},
        "meloetta": {"a": "aria", "p": "pirouette", "s": "pirouette"},
        "aegislash": {"": "shield", "n": "shield", "b": "blade"},
        "basculin": {"": "red-striped", "r": "red-striped", "b": "blue-striped", "w": "white-striped"},
        "keldeo": {"": "ordinary", "n": "ordinary", "r": "resolute"},
        "meowstic": {"": "male", "m": "male", "f": "female"},
        "frillish": {"": "male", "m": "male", "f": "female"},
        "jellicent": {"": "male", "m": "male", "f": "female"},
        "pyroar": {"": "male", "m": "male", "f": "female"},
        "indeedee": {"": "male", "m": "male", "f": "female"},
    }
    mapping = lookup.get(base_slug)
    if mapping is None:
        return aliases
    if form_slug in mapping:
        target = mapping[form_slug]
        aliases.append(f"{base_slug}-{target}" if target else base_slug)
    elif last in mapping:
        target = mapping[last]
        aliases.append(f"{base_slug}-{target}" if target else base_slug)
    return aliases


def _variety_candidates(entry: dict[str, Any]) -> list[str]:
    canonical_slug = _slugify(entry["name"])
    base_slug = _slugify(entry["base_name"])
    form_slug = _slugify(entry["form_name"]) if entry["form_name"] else ""
    candidates: list[str] = []

    def add(value: str) -> None:
        if value and value not in candidates:
            candidates.append(value)

    add(canonical_slug)
    add(base_slug)
    for alias in _species_specific_aliases(base_slug, form_slug):
        add(alias)

    token_alias = {
        "i": "incarnate",
        "t": "therian",
        "d": "defense",
        "o": "origin",
        "z": "zen",
        "u": "unbound",
        "p": "pirouette",
        "h": "heat",
        "w": "wash",
        "m": "mow",
        "fn": "fan",
        "fr": "frost",
        "sm": "small",
        "su": "super",
        "l": "large",
        "c": "confined",
        "r": "white",
    }
    if form_slug:
        tokens = form_slug.split("-")
        expanded = "-".join(token_alias.get(token, token) for token in tokens)
        add(f"{base_slug}-{expanded}" if expanded and expanded != base_slug else base_slug)
    return candidates


def _pick_variety(entry: dict[str, Any], species_payload: dict[str, Any]) -> str:
    varieties = [item["pokemon"]["name"] for item in species_payload.get("varieties", []) if item.get("pokemon")]
    if not varieties:
        return _slugify(entry["base_name"])
    if len(varieties) == 1:
        return varieties[0]

    default_variety = next(
        (item["pokemon"]["name"] for item in species_payload.get("varieties", []) if item.get("is_default") and item.get("pokemon")),
        varieties[0],
    )
    for candidate in _variety_candidates(entry):
        if candidate in varieties:
            return candidate

    form_tokens = set(_normalize_tokens(entry["form_name"]))
    if form_tokens:
        best_name = default_variety
        best_score = -1
        for variety in varieties:
            variety_tokens = set(_normalize_tokens(variety))
            score = len(form_tokens & variety_tokens)
            if score > best_score:
                best_score = score
                best_name = variety
        if best_score > 0:
            return best_name
    return default_variety


def _move_sources_from_pokemon(pokemon_payload: dict[str, Any]) -> dict[str, list[str]]:
    egg: set[str] = set()
    tm: set[str] = set()
    tutor: set[str] = set()
    for move_entry in pokemon_payload.get("moves", []):
        move_name = str(move_entry.get("move", {}).get("name") or "").strip()
        if not move_name:
            continue
        methods = {
            str(detail.get("move_learn_method", {}).get("name") or "").strip().lower()
            for detail in move_entry.get("version_group_details", [])
        }
        if "egg" in methods:
            egg.add(move_name)
        if "machine" in methods:
            tm.add(move_name)
        if "tutor" in methods:
            tutor.add(move_name)
    return {"egg": sorted(egg), "tm": sorted(tm), "tutor": sorted(tutor)}


def _clean_natural_tutor_move_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text or "(N)" not in text:
        return ""
    text = re.sub(r"^.*?Tutor Move List\s+", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*\(N\)\s*$", "", text).strip()
    return text


def _load_supplemental_natural_moves() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for path in (SWSH_GALARDEX_PATH, HISUIDEX_PATH):
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("entries", {}) if isinstance(raw, dict) else {}
        for species_name, entry in entries.items():
            moves = entry.get("moves", {}) if isinstance(entry, dict) else {}
            tutor_list = moves.get("tutor", []) if isinstance(moves, dict) else []
            for raw_move in tutor_list:
                move_name = _clean_natural_tutor_move_name(raw_move)
                if not move_name:
                    continue
                out.setdefault(str(species_name).strip(), set()).add(move_name)
    return out


def _build_parent_map(species_by_dex: dict[int, dict[str, Any]]) -> dict[int, int | None]:
    parent_map: dict[int, int | None] = {}
    name_to_dex = {payload.get("name"): dex for dex, payload in species_by_dex.items()}
    for dex, payload in species_by_dex.items():
        parent = payload.get("evolves_from_species") or {}
        parent_name = parent.get("name")
        parent_map[dex] = name_to_dex.get(parent_name)
    return parent_map


def _inherit_egg_moves(
    dex: int,
    by_dex_direct: dict[int, set[str]],
    parent_map: dict[int, int | None],
    cache: dict[int, set[str]],
) -> set[str]:
    if dex in cache:
        return cache[dex]
    moves = set(by_dex_direct.get(dex, set()))
    parent_dex = parent_map.get(dex)
    if parent_dex:
        moves.update(_inherit_egg_moves(parent_dex, by_dex_direct, parent_map, cache))
    cache[dex] = moves
    return moves


def main() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit(f"Missing PTU database at {DATABASE_PATH}")

    entries = _load_yaml_entries()
    dex_numbers = sorted({entry["dex"] for entry in entries})

    with ThreadPoolExecutor(max_workers=10) as pool:
        species_futures = {
            pool.submit(_fetch_json, f"{POKEAPI_SPECIES}{dex}"): dex
            for dex in dex_numbers
        }
        species_by_dex: dict[int, dict[str, Any]] = {}
        for future in as_completed(species_futures):
            dex = species_futures[future]
            species_by_dex[dex] = future.result()

    chosen_pokemon_by_entry: dict[str, str] = {}
    for entry in entries:
        chosen_pokemon_by_entry[entry["name"]] = _pick_variety(entry, species_by_dex[entry["dex"]])

    unique_pokemon = sorted(set(chosen_pokemon_by_entry.values()))
    with ThreadPoolExecutor(max_workers=10) as pool:
        pokemon_futures = {
            pool.submit(_fetch_json, f"{POKEAPI_POKEMON}{pokemon_name}"): pokemon_name
            for pokemon_name in unique_pokemon
        }
        pokemon_payloads: dict[str, dict[str, Any]] = {}
        for future in as_completed(pokemon_futures):
            pokemon_name = pokemon_futures[future]
            pokemon_payloads[pokemon_name] = future.result()

    direct_sources: dict[str, dict[str, list[str]]] = {}
    direct_egg_by_dex: dict[int, set[str]] = {}
    supplemental_natural = _load_supplemental_natural_moves()
    normalized_natural = {_slugify(name): moves for name, moves in supplemental_natural.items()}
    for entry in entries:
        pokemon_name = chosen_pokemon_by_entry[entry["name"]]
        sources = _move_sources_from_pokemon(pokemon_payloads[pokemon_name])
        direct_sources[entry["name"]] = sources
        direct_egg_by_dex.setdefault(entry["dex"], set()).update(sources["egg"])

    parent_map = _build_parent_map(species_by_dex)
    inherited_egg_cache: dict[int, set[str]] = {}
    final_sources: dict[str, dict[str, list[str]]] = {}
    for entry in entries:
        inherited_egg = _inherit_egg_moves(entry["dex"], direct_egg_by_dex, parent_map, inherited_egg_cache)
        natural_moves = supplemental_natural.get(entry["name"], set()) or normalized_natural.get(_slugify(entry["name"]), set()) or set()
        final_sources[entry["name"]] = {
            "egg": sorted(set(direct_sources[entry["name"]]["egg"]) | inherited_egg),
            "tm": sorted(set(direct_sources[entry["name"]]["tm"])),
            "tutor": sorted(set(direct_sources[entry["name"]]["tutor"])),
            "natural": sorted(set(natural_moves)),
        }

    payload = {
        "generated_from": "PokeAPI + PTU Database 1.05 species forms",
        "species_count": len(final_sources),
        "entries": final_sources,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUT_EMBED.write_text(
        "window.__AUTO_PTU_POKEMON_MOVE_SOURCES = " + json.dumps(payload, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT_JSON} and {OUT_EMBED} for {len(final_sources)} species/forms.")


if __name__ == "__main__":
    main()
