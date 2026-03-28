from __future__ import annotations

import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from auto_ptu.hisui_rulebook_parser import HISUIDEX_OUT
from auto_ptu.learnsets import normalize_species_key


ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "PTUDatabase-main" / "Data" / "ptu.1.05.yaml"
OUT_JSON = ROOT / "auto_ptu" / "data" / "compiled" / "hisui_levelup_learnsets.json"
POKEAPI_POKEMON = "https://pokeapi.co/api/v2/pokemon/"
POKEAPI_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/"
HISUI_VERSION_GROUP = "legends-arceus"
USER_AGENT = "AutoPTU-HisuiLearnsetBuilder/1.0"


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


def _slugify(value: str) -> str:
    base = str(value or "").strip().lower()
    base = base.replace("\u2640", " female").replace("\u2642", " male")
    base = re.sub(r"[^a-z0-9]+", "-", base)
    return base.strip("-")


def _fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


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


def _variety_candidates(entry: dict[str, int | str]) -> list[str]:
    canonical_slug = _slugify(str(entry["name"]))
    base_slug = _slugify(str(entry["base_name"]))
    form_slug = _slugify(str(entry["form_name"])) if entry["form_name"] else ""
    candidates: list[str] = []

    def add(value: str) -> None:
        if value and value not in candidates:
            candidates.append(value)

    add(canonical_slug)
    add(base_slug)
    for alias in _species_specific_aliases(base_slug, form_slug):
        add(alias)
    return candidates


def _pick_variety(entry: dict[str, int | str], species_payload: dict) -> str:
    varieties = [item["pokemon"]["name"] for item in species_payload.get("varieties", []) if item.get("pokemon")]
    if not varieties:
        return _slugify(str(entry["base_name"]))
    if len(varieties) == 1:
        return varieties[0]
    default_variety = next(
        (item["pokemon"]["name"] for item in species_payload.get("varieties", []) if item.get("is_default") and item.get("pokemon")),
        varieties[0],
    )
    for candidate in _variety_candidates(entry):
        if candidate in varieties:
            return candidate
    form_tokens = set(_normalize_tokens(str(entry["form_name"])))
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


def _move_title(value: str) -> str:
    text = str(value or "").replace("-", " ").strip()
    special = {
        "u turn": "U-Turn",
        "x scissor": "X-Scissor",
        "v create": "V-Create",
        "double edge": "Double-Edge",
        "baby doll eyes": "Baby-Doll Eyes",
    }
    key = text.lower()
    if key in special:
        return special[key]
    return " ".join(part[:1].upper() + part[1:] for part in text.split())


def _load_yaml_entries() -> list[dict[str, int | str]]:
    raw = yaml.safe_load(DATABASE_PATH.read_text(encoding="utf-8"))
    out: list[dict[str, int | str]] = []
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


def _hisui_level_up_moves(pokemon_payload: dict) -> list[dict[str, int | str]]:
    best: dict[str, int] = {}
    for move_entry in pokemon_payload.get("moves", []):
        move_name = _move_title(move_entry.get("move", {}).get("name") or "")
        if not move_name:
            continue
        for detail in move_entry.get("version_group_details", []):
            if str(detail.get("version_group", {}).get("name") or "").strip().lower() != HISUI_VERSION_GROUP:
                continue
            if str(detail.get("move_learn_method", {}).get("name") or "").strip().lower() != "level-up":
                continue
            try:
                level = int(detail.get("level_learned_at") or 0)
            except (TypeError, ValueError):
                level = 0
            previous = best.get(move_name)
            if previous is None or level < previous:
                best[move_name] = level
    return [
        {"move": move_name, "level": level}
        for move_name, level in sorted(best.items(), key=lambda item: (item[1], item[0].casefold()))
    ]


def main() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit(f"Missing PTU database at {DATABASE_PATH}")
    hisui_species = set()
    if HISUIDEX_OUT.exists():
        payload = json.loads(HISUIDEX_OUT.read_text(encoding="utf-8"))
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            hisui_species = {normalize_species_key(name) for name in entries}

    entries = _load_yaml_entries()
    dex_numbers = sorted({int(entry["dex"]) for entry in entries})
    with ThreadPoolExecutor(max_workers=10) as pool:
        species_futures = {pool.submit(_fetch_json, f"{POKEAPI_SPECIES}{dex}"): dex for dex in dex_numbers}
        species_by_dex: dict[int, dict] = {}
        for future in as_completed(species_futures):
            dex = species_futures[future]
            species_by_dex[dex] = future.result()
    chosen_pokemon_by_entry: dict[str, str] = {}
    for entry in entries:
        chosen_pokemon_by_entry[str(entry["name"])] = _pick_variety(entry, species_by_dex[int(entry["dex"])])

    unique_pokemon = sorted(set(chosen_pokemon_by_entry.values()))
    with ThreadPoolExecutor(max_workers=10) as pool:
        pokemon_futures = {pool.submit(_fetch_json, f"{POKEAPI_POKEMON}{pokemon_name}"): pokemon_name for pokemon_name in unique_pokemon}
        pokemon_payloads: dict[str, dict] = {}
        for future in as_completed(pokemon_futures):
            pokemon_name = pokemon_futures[future]
            pokemon_payloads[pokemon_name] = future.result()

    payload_entries: dict[str, list[dict[str, int | str]]] = {}
    for entry in entries:
        name = str(entry["name"])
        if normalize_species_key(name) in hisui_species:
            continue
        pokemon_name = chosen_pokemon_by_entry[name]
        moves = _hisui_level_up_moves(pokemon_payloads[pokemon_name])
        if moves:
            payload_entries[name] = moves

    payload = {
        "generated_from": "PokeAPI Legends Arceus version group for non-HisuiDex species/forms",
        "species_count": len(payload_entries),
        "entries": payload_entries,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} for {len(payload_entries)} species/forms.")


if __name__ == "__main__":
    main()
