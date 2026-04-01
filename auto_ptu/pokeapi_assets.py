from __future__ import annotations

import csv
import html
import io
import json
import os
import re
import threading
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .config import FILES_DIR, FOUNDRY_DIR, IMPLEMENTATION_DIR, PTU_DATABASE_DIR

_POKE_API_BASE = "https://pokeapi.co/api/v2"
_USER_AGENT = "AutoPTU-PokeAssets/1.0"
_TIMEOUT = 10
_ABILITY_CSV_FILENAME = "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
_MOVE_CSV_FILENAME = "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
_FOUNDRY_ABILITY_DIRS = [
    FOUNDRY_DIR / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-abilities",
]


def _default_cache_root() -> Path:
    override = os.environ.get("AUTO_PTU_POKEAPI_CACHE")
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "AutoPTU" / "pokeapi"
    return Path.home() / ".autoptu" / "pokeapi"


_CACHE_ROOT = _default_cache_root()
_TYPE_ICON_DIR = _CACHE_ROOT / "type-icons"
_ITEM_ICON_DIR = _CACHE_ROOT / "item-icons"
_CRY_DIR = _CACHE_ROOT / "cries"
_META_DIR = _CACHE_ROOT / "meta"

for _path in (_TYPE_ICON_DIR, _ITEM_ICON_DIR, _CRY_DIR, _META_DIR):
    _path.mkdir(parents=True, exist_ok=True)


_slug_lock = threading.Lock()
_ability_csv_lock = threading.Lock()
_ability_csv_effects: Optional[dict[str, str]] = None
_move_csv_lock = threading.Lock()
_move_csv_effects: Optional[dict[str, str]] = None
_move_meta_lock = threading.Lock()
_move_meta_cache: Optional[dict[str, dict]] = None
_local_cry_index: Optional[dict[str, Path]] = None
_local_cry_index_lock = threading.Lock()
_local_type_icon_index: Optional[dict[str, Path]] = None
_local_type_icon_index_lock = threading.Lock()
_local_item_index: Optional[dict[str, Path]] = None
_local_item_index_lock = threading.Lock()
_ABILITY_SUFFIX_PATTERNS = (
    re.compile(r"\s*\[[^\]]+\]\s*$"),
    re.compile(r"\s*\([^\)]+\)\s*$"),
    re.compile(r"\s*-\s*(errata|playtest|beta|alpha|legacy|ptu)\s*$", re.IGNORECASE),
)


def _slugify(value: str) -> str:
    base = (value or "").strip().lower()
    base = base.replace("\u2640", " female").replace("\u2642", " male")
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = base.replace("(", " ").replace(")", " ")
    base = re.sub(r"[^a-z0-9]+", "-", base)
    return base.strip("-")


def _json_get(payload: dict, path: list[str]) -> Optional[str]:
    current: object = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, str) and current:
        return current
    return None


def _request_json(url: str) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _download_binary(url: str, target: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
            data = response.read()
    except Exception:
        return False
    try:
        target.write_bytes(data)
    except Exception:
        return False
    return True


def _cached_meta(kind: str, slug: str) -> Optional[dict]:
    path = _META_DIR / f"{kind}-{slug}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _store_meta(kind: str, slug: str, payload: dict) -> None:
    path = _META_DIR / f"{kind}-{slug}.json"
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _safe_filename_from_url(url: str, fallback_ext: str) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if not suffix:
        suffix = fallback_ext
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    return suffix


def _normalize_cry_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _normalize_item_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _normalize_type_icon_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _local_cry_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("AUTO_PTU_LOCAL_CRY_DIRS", "")
    if env:
        for raw in env.split(os.pathsep):
            item = Path(raw.strip())
            if item and item.exists() and item.is_dir():
                dirs.append(item)
    default_gen9 = IMPLEMENTATION_DIR / "Generation 9 Pack v3.3.4" / "Audio" / "SE" / "Cries"
    if default_gen9.exists() and default_gen9.is_dir():
        dirs.append(default_gen9)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in dirs:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _local_type_icon_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("AUTO_PTU_LOCAL_TYPE_ICON_DIRS", "")
    if env:
        for raw in env.split(os.pathsep):
            item = Path(raw.strip())
            if item and item.exists() and item.is_dir():
                dirs.append(item)
    default_types = PTU_DATABASE_DIR / "PTUDataEditor" / "Resources" / "Types"
    if default_types.exists() and default_types.is_dir():
        dirs.append(default_types)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in dirs:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _local_item_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("AUTO_PTU_LOCAL_ITEM_ICON_DIRS", "")
    if env:
        for raw in env.split(os.pathsep):
            item = Path(raw.strip())
            if item and item.exists() and item.is_dir():
                dirs.append(item)
    default_items = IMPLEMENTATION_DIR / "Generation 9 Pack v3.3.4" / "Graphics" / "Items"
    if default_items.exists() and default_items.is_dir():
        dirs.append(default_items)
    foundry_items = FOUNDRY_DIR / "ptr2e-Stable" / "ptr2e-Stable" / "static" / "img" / "item-icons"
    if foundry_items.exists() and foundry_items.is_dir():
        dirs.append(foundry_items)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in dirs:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _build_local_cry_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for folder in _local_cry_dirs():
        try:
            files = sorted(folder.glob("*.ogg")) + sorted(folder.glob("*.mp3")) + sorted(folder.glob("*.wav"))
        except Exception:
            files = []
        for file in files:
            token = _normalize_cry_token(file.stem)
            if not token or token in index:
                continue
            index[token] = file
    return index


def _build_local_type_icon_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for folder in _local_type_icon_dirs():
        try:
            files = sorted(folder.glob("*.png")) + sorted(folder.glob("*.webp"))
        except Exception:
            files = []
        for file in files:
            token = _normalize_type_icon_token(file.stem)
            if token and token not in index:
                index[token] = file
    return index


def _build_local_item_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for folder in _local_item_dirs():
        try:
            files = sorted(folder.glob("*.png")) + sorted(folder.glob("*.webp"))
        except Exception:
            files = []
        for file in files:
            token = _normalize_item_token(file.stem)
            if token and token not in index:
                index[token] = file
    return index


def _local_type_icon_path(type_name: str) -> Optional[Path]:
    global _local_type_icon_index
    token = _normalize_type_icon_token(_slugify(type_name))
    if not token:
        return None
    if _local_type_icon_index is None:
        with _local_type_icon_index_lock:
            if _local_type_icon_index is None:
                _local_type_icon_index = _build_local_type_icon_index()
    if not _local_type_icon_index:
        return None
    direct = _local_type_icon_index.get(token)
    if direct and direct.exists():
        return direct
    for key, path in _local_type_icon_index.items():
        if key.startswith(token) and path.exists():
            return path
    return None


def _local_cry_path(pokemon_name: str) -> Optional[Path]:
    global _local_cry_index
    token = _normalize_cry_token(_slugify(pokemon_name))
    if not token:
        return None
    if _local_cry_index is None:
        with _local_cry_index_lock:
            if _local_cry_index is None:
                _local_cry_index = _build_local_cry_index()
    if not _local_cry_index:
        return None
    direct = _local_cry_index.get(token)
    if direct and direct.exists():
        return direct
    # Fallback for names where local files include extra suffixes/forms.
    for key, path in _local_cry_index.items():
        if key.startswith(token) and path.exists():
            return path
    return None


def _local_item_icon_path(item_name: str) -> Optional[Path]:
    global _local_item_index
    token = _normalize_item_token(_slugify(item_name))
    if not token:
        return None
    if _local_item_index is None:
        with _local_item_index_lock:
            if _local_item_index is None:
                _local_item_index = _build_local_item_index()
    if not _local_item_index:
        return None
    direct = _local_item_index.get(token)
    if direct and direct.exists():
        return direct
    for key, path in _local_item_index.items():
        if key.startswith(token) and path.exists():
            return path
    return None


def _decode_text_file(path: Path) -> Optional[str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except Exception:
            continue
    return None


def _normalize_meta_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())


def _is_placeholder_effect(effect: str, name: str) -> bool:
    value = str(effect or "").strip()
    if not value:
        return True
    normalized = _normalize_meta_token(value)
    if not normalized:
        return True
    if normalized in {"none", "na", "n", "unknown", "descriptionunavailable"}:
        return True
    return normalized == _normalize_meta_token(name)


def _build_ability_effect_text(row: dict) -> str:
    parts: list[str] = []
    for key in ("Effect 2", "Effect"):
        value = str(row.get(key) or "").strip()
        if value and value not in parts:
            parts.append(value)
    return "\n".join(parts).strip()


def _strip_foundry_html(text: str) -> str:
    value = str(text or "")
    if not value:
        return ""
    value = re.sub(r"</p>\\s*<p>", "\n\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<br\\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"@\w+\[([^\]]+)\]", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def _ability_effect_from_foundry(ability_name: str) -> str:
    for candidate in _ability_lookup_candidates(ability_name):
        slug = _slugify(candidate)
        if not slug:
            continue
        for base in _FOUNDRY_ABILITY_DIRS:
            path = base / f"{slug}.json"
            if not path.exists():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            system = payload.get("system", {}) if isinstance(payload, dict) else {}
            description = ""
            if isinstance(system, dict):
                description = str(system.get("description") or "").strip()
                if not description:
                    actions = system.get("actions") or []
                    if isinstance(actions, list) and actions:
                        first = actions[0] if isinstance(actions[0], dict) else {}
                        description = str(first.get("description") or "").strip()
            cleaned = _strip_foundry_html(description)
            if cleaned:
                return cleaned
    return ""


def _strip_ability_suffix(name: str) -> str:
    value = str(name or "").strip()
    if not value:
        return ""
    trimmed = value
    for pattern in _ABILITY_SUFFIX_PATTERNS:
        trimmed = pattern.sub("", trimmed).strip()
    return trimmed


def _ability_lookup_candidates(name: str) -> list[str]:
    base = str(name or "").strip()
    if not base:
        return []
    candidates = [base]
    stripped = _strip_ability_suffix(base)
    if stripped and stripped.lower() != base.lower():
        candidates.append(stripped)
    plural_variants: list[str] = []
    for candidate in list(candidates):
        lowered = candidate.lower()
        if lowered.endswith("s"):
            singular = candidate[:-1].strip()
            if singular:
                plural_variants.append(singular)
        else:
            plural_variants.append(f"{candidate}s")
    candidates.extend(plural_variants)
    seen: set[str] = set()
    unique: list[str] = []
    for entry in candidates:
        key = entry.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _load_ptu_ability_effects() -> dict[str, str]:
    global _ability_csv_effects
    if _ability_csv_effects is not None:
        return _ability_csv_effects
    with _ability_csv_lock:
        if _ability_csv_effects is not None:
            return _ability_csv_effects
        effects: dict[str, str] = {}
        path = FILES_DIR / _ABILITY_CSV_FILENAME
        if path.exists():
            text = _decode_text_file(path)
            if text:
                reader = csv.DictReader(io.StringIO(text))
                for row in reader:
                    name = str(row.get("Name") or "").strip()
                    if not name:
                        continue
                    slug = _slugify(name)
                    if not slug:
                        continue
                    effect_text = _build_ability_effect_text(row)
                    if not effect_text:
                        continue
                    if slug not in effects:
                        effects[slug] = effect_text
        _ability_csv_effects = effects
        return effects


def _ability_effect_from_ptu_csv(ability_name: str) -> str:
    for candidate in _ability_lookup_candidates(ability_name):
        slug = _slugify(candidate)
        if not slug:
            continue
        effect = _load_ptu_ability_effects().get(slug, "").strip()
        if effect:
            return effect
    return ""


def _load_ptu_move_effects() -> dict[str, str]:
    global _move_csv_effects
    if _move_csv_effects is not None:
        return _move_csv_effects
    with _move_csv_lock:
        if _move_csv_effects is not None:
            return _move_csv_effects
        effects: dict[str, str] = {}
        path = FILES_DIR / _MOVE_CSV_FILENAME
        if path.exists():
            text = _decode_text_file(path)
            if text:
                lines = text.splitlines()
                header_index = None
                for idx, line in enumerate(lines):
                    cells = [cell.strip() for cell in line.split(",")]
                    if "Name" in cells:
                        header_index = idx
                        break
                if header_index is None:
                    reader = csv.DictReader(io.StringIO(text))
                else:
                    reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])))
                for row in reader:
                    name = str(row.get("Name") or "").strip()
                    if not name:
                        continue
                    slug = _slugify(name)
                    if not slug:
                        continue
                    effect_text = str(row.get("Effects") or "").strip()
                    if not effect_text or _is_placeholder_effect(effect_text, name):
                        continue
                    if slug not in effects:
                        effects[slug] = effect_text
        _move_csv_effects = effects
        return effects


def _load_compiled_move_meta() -> dict[str, dict]:
    global _move_meta_cache
    if _move_meta_cache is not None:
        return _move_meta_cache
    with _move_meta_lock:
        if _move_meta_cache is not None:
            return _move_meta_cache
        meta: dict[str, dict] = {}
        path = Path(__file__).resolve().parent / "data" / "compiled" / "moves.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _move_meta_cache = {}
            return _move_meta_cache
        for entry in data:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            if not name:
                continue
            slug = _slugify(name)
            if not slug:
                continue
            meta[slug] = {
                "name": name,
                "type": entry.get("type"),
                "category": entry.get("category"),
                "frequency": entry.get("frequency"),
                "range": entry.get("range"),
                "ac": entry.get("ac"),
                "damage_base": entry.get("damage_base"),
            }
        _move_meta_cache = meta
        return meta


def type_icon_path(type_name: str) -> Optional[Path]:
    slug = _slugify(type_name)
    if not slug:
        return None
    target = _TYPE_ICON_DIR / f"{slug}.png"
    if target.exists():
        return target
    local = _local_type_icon_path(type_name)
    if local is not None and local.exists():
        return local
    with _slug_lock:
        if target.exists():
            return target
        local = _local_type_icon_path(type_name)
        if local is not None and local.exists():
            return local
        payload = _request_json(f"{_POKE_API_BASE}/type/{slug}")
        if not payload:
            return None
        icon_url = (
            _json_get(payload, ["sprites", "generation-viii", "sword-shield", "name_icon"])
            or _json_get(payload, ["sprites", "generation-ix", "scarlet-violet", "name_icon"])
        )
        if not icon_url:
            return None
        if not _download_binary(icon_url, target):
            return None
    return target if target.exists() else None


def item_icon_path(item_name: str) -> Optional[Path]:
    slug = _slugify(item_name)
    if not slug:
        return None
    target = _ITEM_ICON_DIR / f"{slug}.png"
    if target.exists():
        return target
    local = _local_item_icon_path(item_name)
    if local is not None and local.exists():
        return local
    with _slug_lock:
        if target.exists():
            return target
        local = _local_item_icon_path(item_name)
        if local is not None and local.exists():
            return local
        payload = _request_json(f"{_POKE_API_BASE}/item/{slug}")
        if not payload:
            return None
        icon_url = _json_get(payload, ["sprites", "default"])
        if not icon_url:
            return None
        if not _download_binary(icon_url, target):
            return None
    return target if target.exists() else None


def cry_path(pokemon_name: str) -> Optional[Path]:
    slug = _slugify(pokemon_name)
    if not slug:
        return None
    existing = next(iter(sorted(_CRY_DIR.glob(f"{slug}.*"))), None)
    if existing is not None and existing.exists():
        return existing
    local = _local_cry_path(pokemon_name)
    if local is not None and local.exists():
        return local
    with _slug_lock:
        existing = next(iter(sorted(_CRY_DIR.glob(f"{slug}.*"))), None)
        if existing is not None and existing.exists():
            return existing
        local = _local_cry_path(pokemon_name)
        if local is not None and local.exists():
            return local
        payload = _request_json(f"{_POKE_API_BASE}/pokemon/{slug}")
        if not payload:
            return None
        cry_url = _json_get(payload, ["cries", "latest"]) or _json_get(payload, ["cries", "legacy"])
        if not cry_url:
            return None
        ext = _safe_filename_from_url(cry_url, ".ogg")
        target = _CRY_DIR / f"{slug}{ext}"
        if not _download_binary(cry_url, target):
            return None
    return target if target.exists() else None


def move_metadata(move_name: str) -> Optional[dict]:
    slug = _slugify(move_name)
    if not slug:
        return None
    compiled = _load_compiled_move_meta().get(slug)
    if not compiled:
        return None
    effect = _load_ptu_move_effects().get(slug, "").strip()
    source = "ptu_csv" if effect else "ptu_csv_missing"
    cached = _cached_meta("move", slug)
    if cached:
        patched = dict(cached)
        patched.update(compiled)
        patched["effect"] = effect
        patched["source"] = source
        if patched != cached:
            _store_meta("move", slug, patched)
        return patched
    meta = dict(compiled)
    meta["effect"] = effect
    meta["source"] = source
    _store_meta("move", slug, meta)
    return meta


def ability_metadata(ability_name: str) -> Optional[dict]:
    candidates = _ability_lookup_candidates(ability_name)
    if not candidates:
        return None
    slug = _slugify(ability_name)
    if not slug:
        return None
    fallback_effect = _ability_effect_from_ptu_csv(ability_name)
    source = "ptu_csv"
    if not fallback_effect or _is_placeholder_effect(fallback_effect, ability_name):
        foundry_effect = _ability_effect_from_foundry(ability_name)
        if foundry_effect:
            fallback_effect = foundry_effect
            source = "foundry_core_abilities"
    cached = _cached_meta("ability", slug)
    if cached:
        patched = dict(cached)
        cached_effect = str(patched.get("effect") or "").strip()
        if fallback_effect:
            patched["effect"] = fallback_effect
            patched["source"] = source
        else:
            if patched.get("source") != "ptu_csv" or _is_placeholder_effect(cached_effect, ability_name):
                patched["effect"] = ""
                patched["source"] = "ptu_csv_missing"
        patched.setdefault("name", ability_name)
        if patched != cached:
            _store_meta("ability", slug, patched)
        return patched
    pokeapi_payload = _request_json(f"{_POKE_API_BASE}/ability/{slug}")
    pokeapi_effect = ""
    pokeapi_id = None
    pokeapi_name = ability_name
    pokeapi_generation = None
    if isinstance(pokeapi_payload, dict):
        pokeapi_id = pokeapi_payload.get("id")
        pokeapi_name = str(pokeapi_payload.get("name") or ability_name)
        generation = pokeapi_payload.get("generation")
        if isinstance(generation, dict):
            pokeapi_generation = generation.get("name")
        for entry in pokeapi_payload.get("effect_entries") or []:
            if not isinstance(entry, dict):
                continue
            language = entry.get("language")
            if not isinstance(language, dict) or str(language.get("name") or "").lower() != "en":
                continue
            pokeapi_effect = str(entry.get("short_effect") or entry.get("effect") or "").strip()
            if pokeapi_effect:
                break
    effect_text = fallback_effect or pokeapi_effect
    if not effect_text:
        return None
    meta_source = source if fallback_effect else "pokeapi"
    resolved = {
        "id": pokeapi_id,
        "name": pokeapi_name,
        "generation": pokeapi_generation,
        "effect": effect_text,
        "source": meta_source,
    }
    _store_meta("ability", slug, resolved)
    return resolved


def item_metadata(item_name: str) -> Optional[dict]:
    slug = _slugify(item_name)
    if not slug:
        return None
    from .rules.item_catalog import get_item_entry

    entry = get_item_entry(item_name)
    if entry is None:
        return None
    effect = str(entry.description or "").strip()
    source = sorted(entry.sources) if entry.sources else []
    cached = _cached_meta("item", slug)
    if cached:
        patched = dict(cached)
        patched.update(
            {
                "id": None,
                "name": entry.name,
                "category": None,
                "effect": effect,
                "source": source,
            }
        )
        if patched != cached:
            _store_meta("item", slug, patched)
        return patched
    meta = {
        "id": None,
        "name": entry.name,
        "category": None,
        "effect": effect,
        "source": source,
    }
    _store_meta("item", slug, meta)
    return meta
