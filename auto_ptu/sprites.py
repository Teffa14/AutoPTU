from __future__ import annotations

import json
import os
import re
import threading
import unicodedata
import urllib.request
from pathlib import Path
from typing import Optional

from .config import IMPLEMENTATION_DIR


def _default_cache_dir() -> Path:
    override = os.environ.get("AUTO_PTU_SPRITE_DIR")
    if override:
        return Path(override)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "AutoPTU" / "sprites"
    return Path.home() / ".autoptu" / "sprites"


_DEFAULT_CACHE_DIR = _default_cache_dir()
_LEGACY_CACHE_DIR = Path(__file__).resolve().parent / "data" / "sprites"
_IMPLEMENTATION_DIR = IMPLEMENTATION_DIR
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_API_BASE = "https://pokeapi.co/api/v2/pokemon/"
_SPECIES_API_BASE = "https://pokeapi.co/api/v2/pokemon-species/"
_USER_AGENT = "AutoPTU-SpriteFetcher/1.0"

_EXCEPTIONS = {
    "mr. mime": "mr-mime",
    "mr mime": "mr-mime",
    "mime jr.": "mime-jr",
    "farfetchd": "farfetchd",
    "sirfetchd": "sirfetchd",
    "type: null": "type-null",
    "tapu koko": "tapu-koko",
    "tapu lele": "tapu-lele",
    "tapu bulu": "tapu-bulu",
    "tapu fini": "tapu-fini",
    "jangmo-o": "jangmo-o",
    "hakamo-o": "hakamo-o",
    "kommo-o": "kommo-o",
    "lycanrock": "lycanroc",
    "lycanrock night": "lycanroc-midnight",
    "lycanrock-night": "lycanroc-midnight",
    "lycanrock day": "lycanroc-midday",
    "lycanrock-day": "lycanroc-midday",
    "lycanrock dusk": "lycanroc-dusk",
    "lycanrock-dusk": "lycanroc-dusk",
    "lycanroc night": "lycanroc-midnight",
    "lycanroc-night": "lycanroc-midnight",
    "lycanroc day": "lycanroc-midday",
    "lycanroc-day": "lycanroc-midday",
    "lycanroc da": "lycanroc-midday",
    "lycanroc-da": "lycanroc-midday",
    "lycanroc du": "lycanroc-dusk",
    "lycanroc-du": "lycanroc-dusk",
    "lycanroc n": "lycanroc-midnight",
    "lycanroc-n": "lycanroc-midnight",
    "rotom-n": "rotom",
    "rotom normal": "rotom",
    "rotom-normal": "rotom",
    "nidoran female": "nidoran-f",
    "nidoran male": "nidoran-m",
    "flabebe": "flabebe",
    "meloetta a": "meloetta-aria",
    "meloetta-a": "meloetta-aria",
    "meloetta aria": "meloetta-aria",
    "meloetta-aria": "meloetta-aria",
    "meloetta p": "meloetta-pirouette",
    "meloetta-p": "meloetta-pirouette",
    "meloetta pirouette": "meloetta-pirouette",
    "meloetta-pirouette": "meloetta-pirouette",
    "meloetta s": "meloetta-pirouette",
    "meloetta-s": "meloetta-pirouette",
    "meloetta step": "meloetta-pirouette",
    "meloetta-step": "meloetta-pirouette",
}

_LOCAL_SPRITE_INDEX_LOCK = threading.Lock()
_LOCAL_SPRITE_INDEX: dict[str, Path] = {}
_LOCAL_SPRITE_INDEX_KEY: tuple[str, ...] = ()
_SPECIES_ALIAS_KEYS: dict[str, list[str]] | None = None


def _slugify(name: str) -> str:
    base = name.strip().lower()
    base = base.replace("\u2640", " female").replace("\u2642", " male")
    base = base.replace("\u00e2\u2122\u20ac", " female").replace("\u00e2\u2122\u201a", " male")
    base = base.replace("â™€", " female").replace("â™‚", " male")
    base = base.replace("â€™", "").replace("\u2019", "").replace("'", "")
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = base.replace("(", " ").replace(")", " ")
    base = re.sub(r"\s+", " ", base).strip()
    if base in _EXCEPTIONS:
        return _EXCEPTIONS[base]
    # Do not collapse generic *eon names (for example, Inteleon) to Eevee.
    base = re.sub(r"^(player|foe)[-\s_]*\d+[:\s_-]+", "", base).strip()

    if base.startswith("nidoran"):
        tokens = base.replace("-", " ").split()
        if len(tokens) >= 2:
            suffix = tokens[1]
            if suffix.startswith("f") or "female" in tokens:
                return "nidoran-f"
            if suffix.startswith("m") or "male" in tokens:
                return "nidoran-m"

    if base.startswith("oricorio"):
        form_text = " ".join(base.split()[1:]).strip()
        if form_text:
            if form_text in {"b", "baile"}:
                return "oricorio-baile"
            if form_text in {"pom", "pom pom", "pom-pom", "po"}:
                return "oricorio-pom-pom"
            if form_text in {"pau", "pa"}:
                return "oricorio-pau"
            if form_text in {"sensu", "s"}:
                return "oricorio-sensu"

    if base.startswith("minior"):
        form_text = re.sub(r"^minior[-_\s]*", "", base).strip()
        normalized_form = form_text.replace("-", " ").replace("_", " ").strip()
        if normalized_form in {"meteor", "m"}:
            return "minior-red-meteor"
        if normalized_form in {"core", "c"}:
            return "minior-red-core"

    if base.startswith("enamorus"):
        form_text = " ".join(base.split()[1:]).strip()
        if form_text in {"incarnate", "i"}:
            return "enamorus-incarnate"
        if form_text in {"therian", "t"}:
            return "enamorus-therian"

    if base.startswith("necrozma"):
        form_text = " ".join(base.split()[1:]).strip()
        if form_text in {"dusk", "du", "dusk mane", "dusk-mane"}:
            return "necrozma-dusk-mane"
        if form_text in {"dawn", "da", "dawn wings", "dawn-wings"}:
            return "necrozma-dawn-wings"
        if form_text in {"ultra"}:
            return "necrozma-ultra"

    if base.startswith("zacian"):
        form_text = " ".join(base.split()[1:]).strip()
        if form_text in {"crowned", "c"}:
            return "zacian-crowned"
        if form_text in {"hero", "h"}:
            return "zacian"

    if base.startswith("basculegion"):
        form_text = " ".join(base.split()[1:]).strip()
        if form_text in {"m", "male"}:
            return "basculegion-male"
        if form_text in {"f", "female"}:
            return "basculegion-female"

    if base.startswith("mega "):
        rest = base[5:].strip()
        parts = rest.split()
        if parts and parts[-1] in {"x", "y"}:
            base = " ".join(parts[:-1] + ["mega", parts[-1]])
        else:
            base = f"{rest} mega"
    elif base.startswith("primal "):
        base = f"{base[7:].strip()} primal"

    region_map = {
        "alolan": "alola",
        "galarian": "galar",
        "hisuian": "hisui",
        "paldean": "paldea",
    }
    parts = base.split()
    if parts and parts[0] in region_map:
        tag = region_map[parts.pop(0)]
        parts.append(tag)
    if parts and parts[-1] in region_map:
        tag = region_map[parts.pop(-1)]
        parts.append(tag)
    base = " ".join(parts)

    base = base.replace(" forme", "")
    base = base.replace(" form", "")
    base = re.sub(r"[^a-z0-9]+", "-", base)
    base = base.strip("-")
    return base


def _strip_trainer_prefix_slug(slug: str) -> str:
    return re.sub(r"^(player|foe)[-_]*\d+[-_]+", "", slug)


def _normalize_local_sprite_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _species_data_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "compiled" / "species.json"


def _species_alias_signature(entry: dict) -> str:
    payload = {
        "base_stats": entry.get("base_stats") or {},
        "types": entry.get("types") or [],
        "movement": entry.get("movement") or {},
        "capabilities": entry.get("capabilities") or [],
        "size": entry.get("size") or "",
        "weight": entry.get("weight") or "",
        "egg_groups": entry.get("egg_groups") or [],
        "naturewalk": entry.get("naturewalk") or [],
        "skills": entry.get("skills") or {},
    }
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
    except Exception:
        return ""


def _species_alias_map() -> dict[str, list[str]]:
    global _SPECIES_ALIAS_KEYS
    if _SPECIES_ALIAS_KEYS is not None:
        return _SPECIES_ALIAS_KEYS
    alias_map: dict[str, list[str]] = {}
    try:
        raw = json.loads(_species_data_path().read_text(encoding="utf-8"))
    except Exception:
        _SPECIES_ALIAS_KEYS = alias_map
        return alias_map
    entries = raw.values() if isinstance(raw, dict) else raw
    grouped: dict[str, list[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        signature = _species_alias_signature(entry)
        if not signature:
            continue
        grouped.setdefault(signature, []).append(name)
    for names in grouped.values():
        unique_names: list[str] = []
        seen_names: set[str] = set()
        for name in names:
            key = name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)
            unique_names.append(name)
        if len(unique_names) < 2:
            continue
        sibling_slugs: list[str] = []
        seen_slugs: set[str] = set()
        for candidate in unique_names:
            slug = _slugify(candidate)
            if not slug or slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            sibling_slugs.append(slug)
        if not sibling_slugs:
            continue
        lookup_keys: set[str] = set()
        for candidate in unique_names:
            lookup_keys.add(_normalize_local_sprite_key(candidate))
            lookup_keys.add(_normalize_local_sprite_key(_slugify(candidate)))
        for key in lookup_keys:
            if not key:
                continue
            alias_map[key] = list(sibling_slugs)
    _SPECIES_ALIAS_KEYS = alias_map
    return alias_map


def _species_alias_slugs(slug: str) -> list[str]:
    key = _normalize_local_sprite_key(slug)
    if not key:
        return []
    related = _species_alias_map().get(key, [])
    candidates: list[str] = []
    seen: set[str] = set()
    for sibling in related:
        if not sibling or sibling == slug or sibling in seen:
            continue
        seen.add(sibling)
        candidates.append(sibling)
    return candidates


def _local_sprite_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("AUTO_PTU_LOCAL_SPRITE_DIRS", "")
    if env:
        for raw in env.split(os.pathsep):
            p = Path(raw.strip())
            if p.exists() and p.is_dir():
                dirs.append(p)
    candidate_dirs = [
        _PROJECT_ROOT / "Animated Pokemon Sprites" / "Graphics" / "Pokemon" / "Front",
        _IMPLEMENTATION_DIR / "Animated Pokemon Sprites" / "Graphics" / "Pokemon" / "Front",
        _PROJECT_ROOT / "Generation 9 Pack v3.3.4" / "Graphics" / "Pokemon" / "Front",
        _IMPLEMENTATION_DIR / "Generation 9 Pack v3.3.4" / "Graphics" / "Pokemon" / "Front",
    ]
    for candidate in candidate_dirs:
        if candidate.exists() and candidate.is_dir():
            dirs.append(candidate)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in dirs:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _refresh_local_sprite_index() -> None:
    global _LOCAL_SPRITE_INDEX, _LOCAL_SPRITE_INDEX_KEY
    dirs = _local_sprite_dirs()
    key = tuple(str(path.resolve()) for path in dirs)
    if key == _LOCAL_SPRITE_INDEX_KEY and _LOCAL_SPRITE_INDEX:
        return
    index: dict[str, Path] = {}
    for folder in dirs:
        try:
            entries = sorted(
                [candidate for candidate in folder.iterdir() if candidate.is_file() and candidate.suffix.lower() == ".png"]
            )
        except Exception:
            entries = []
        for file in entries:
            raw_key = _normalize_local_sprite_key(file.stem)
            if raw_key and raw_key not in index:
                index[raw_key] = file
            slug_key = _normalize_local_sprite_key(_slugify(file.stem))
            if slug_key and slug_key not in index:
                index[slug_key] = file
    _LOCAL_SPRITE_INDEX = index
    _LOCAL_SPRITE_INDEX_KEY = key


def _local_sprite_path_for_slug(slug: str) -> Optional[Path]:
    token = _normalize_local_sprite_key(slug)
    if not token:
        return None
    with _LOCAL_SPRITE_INDEX_LOCK:
        _refresh_local_sprite_index()
        match = _LOCAL_SPRITE_INDEX.get(token)
        if match is not None and match.exists():
            return match
        for key, path in _LOCAL_SPRITE_INDEX.items():
            if key.startswith(token) and path.exists():
                return path
    return None


class SpriteCache:
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or _DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._missing: set[str] = set()
        self._indexed = False
        self._alias_map: dict[str, Path] = {}

    def sprite_url_for(self, name: str, *, allow_download: bool = False) -> Optional[str]:
        slug = _slugify(name or "")
        if not slug:
            return None
        filename = f"{slug}.png"
        target = self.cache_dir / filename
        local = _local_sprite_path_for_slug(slug)
        if local is not None:
            try:
                if not target.exists() or target.stat().st_size != local.stat().st_size:
                    target.write_bytes(local.read_bytes())
                return f"/sprites/{filename}"
            except Exception:
                return f"/sprites/{local.name}"
        if target.exists():
            return f"/sprites/{filename}"
        aliased = self._find_existing(slug)
        if aliased is not None:
            try:
                if aliased.name != filename:
                    target.write_bytes(aliased.read_bytes())
                    return f"/sprites/{filename}"
            except Exception:
                return f"/sprites/{aliased.name}"
            return f"/sprites/{aliased.name}"
        legacy = _LEGACY_CACHE_DIR / filename
        if legacy.exists():
            try:
                target.write_bytes(legacy.read_bytes())
                return f"/sprites/{filename}"
            except Exception:
                return f"/sprites/{filename}"
        for fallback in _fallback_slugs(slug):
            fallback_name = f"{fallback}.png"
            fallback_target = self.cache_dir / fallback_name
            if fallback_target.exists():
                return f"/sprites/{fallback_name}"
            fallback_local = _local_sprite_path_for_slug(fallback)
            if fallback_local is not None:
                try:
                    fallback_target.write_bytes(fallback_local.read_bytes())
                    return f"/sprites/{fallback_name}"
                except Exception:
                    return f"/sprites/{fallback_local.name}"
        if not allow_download:
            return None
        if not self._download_sprite(slug, target):
            for fallback in _fallback_slugs(slug):
                fallback_name = f"{fallback}.png"
                fallback_target = self.cache_dir / fallback_name
                if fallback_target.exists() or self._download_sprite(fallback, fallback_target):
                    return f"/sprites/{fallback_name}"
            self._missing.add(slug)
            return None
        return f"/sprites/{filename}"

    def sprite_path_for(self, name: str) -> Optional[str]:
        slug = _slugify(name or "")
        if not slug:
            return None
        filename = f"{slug}.png"
        target = self.cache_dir / filename
        local = _local_sprite_path_for_slug(slug)
        if local is not None:
            try:
                if not target.exists() or target.stat().st_size != local.stat().st_size:
                    target.write_bytes(local.read_bytes())
                return f"/sprites/{filename}"
            except Exception:
                return f"/sprites/{local.name}"
        if target.exists():
            return f"/sprites/{filename}"
        aliased = self._find_existing(slug)
        if aliased is not None:
            return f"/sprites/{aliased.name}"
        for fallback in _fallback_slugs(slug):
            fallback_name = f"{fallback}.png"
            fallback_path = self.cache_dir / fallback_name
            if fallback_path.exists():
                return f"/sprites/{fallback_name}"
        return f"/sprites/{slug}.png"

    def ensure_sprite_filename(self, filename: str) -> bool:
        if not filename:
            return False
        if not filename.lower().endswith(".png"):
            return False
        slug = filename[:-4]
        if not slug:
            return False
        target = self.cache_dir / filename
        if target.exists():
            return True
        local = _local_sprite_path_for_slug(slug)
        if local is not None:
            try:
                target.write_bytes(local.read_bytes())
                return True
            except Exception:
                return local.exists()
        if self._download_sprite(slug, target):
            return True
        for fallback in _fallback_slugs(slug):
            fallback_name = f"{fallback}.png"
            fallback_path = self.cache_dir / fallback_name
            local_fallback = _local_sprite_path_for_slug(fallback)
            if local_fallback is not None and not fallback_path.exists():
                try:
                    fallback_path.write_bytes(local_fallback.read_bytes())
                except Exception:
                    pass
            if fallback_path.exists() or self._download_sprite(fallback, fallback_path):
                try:
                    target.write_bytes(fallback_path.read_bytes())
                    return True
                except Exception:
                    return fallback_path.exists()
        return False

    def _find_existing(self, slug: str) -> Optional[Path]:
        if not self._indexed:
            self._index_cache()
        match = self._alias_map.get(slug)
        if match is not None and match.exists():
            return match
        # Fall back to a lightweight scan if cache changed after indexing.
        for candidate in self.cache_dir.glob("*.png"):
            if _slugify(candidate.stem) == slug:
                self._alias_map[slug] = candidate
                return candidate
        return None

    def _index_cache(self) -> None:
        self._alias_map.clear()
        for candidate in self.cache_dir.glob("*.png"):
            slug = _slugify(candidate.stem)
            if slug:
                self._alias_map.setdefault(slug, candidate)
        self._indexed = True

    def _download_sprite(self, slug: str, target: Path) -> bool:
        if os.environ.get("AUTO_PTU_DISABLE_SPRITES"):
            return False
        slug = _strip_trainer_prefix_slug(slug)
        with self._lock:
            if target.exists():
                return True
            payload = _fetch_pokemon_payload(slug)
            if payload is None:
                resolved = _resolve_variant_slug(slug)
                if resolved and resolved != slug:
                    payload = _fetch_pokemon_payload(resolved)
            if payload is None:
                return False
            sprite_url = (
                _deep_get(payload, ["sprites", "versions", "generation-vii", "ultra-sun-ultra-moon", "front_default"])
                or _deep_get(payload, ["sprites", "versions", "generation-viii", "icons", "front_default"])
                or _deep_get(payload, ["sprites", "other", "official-artwork", "front_default"])
                or _deep_get(payload, ["sprites", "front_default"])
            )
            if not sprite_url:
                return False
            sprite_request = urllib.request.Request(sprite_url, headers={"User-Agent": _USER_AGENT})
            try:
                with urllib.request.urlopen(sprite_request, timeout=10) as response:
                    target.write_bytes(response.read())
            except Exception:
                return False
        return True


def _deep_get(payload: dict, keys: list[str]) -> Optional[str]:
    current: object = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, str) and current:
        return current
    return None


def _fetch_pokemon_payload(slug: str) -> Optional[dict]:
    api_url = f"{_API_BASE}{slug}"
    request = urllib.request.Request(api_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _fetch_species_payload(slug: str) -> Optional[dict]:
    api_url = f"{_SPECIES_API_BASE}{slug}"
    request = urllib.request.Request(api_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _normalize_variant_token(token: str) -> str:
    token = (token or "").strip().lower()
    aliases = {
        "m": "male",
        "f": "female",
        "du": "dusk",
        "da": "dawn",
        "c": "crowned",
        "h": "hero",
        "i": "incarnate",
        "t": "therian",
    }
    return aliases.get(token, token)


def _score_variety_tokens(form_tokens: list[str], variety_tokens: list[str]) -> int:
    normalized_form = [_normalize_variant_token(t) for t in form_tokens]
    normalized_variety = [_normalize_variant_token(t) for t in variety_tokens]
    form_set = {t for t in normalized_form if t}
    variety_set = {t for t in normalized_variety if t}
    if "male" in form_set and "female" in variety_set:
        return -1
    if "female" in form_set and "male" in variety_set:
        return -1
    score = 0
    for token in form_set:
        if token in variety_set:
            score += 4
            continue
        if any(v.startswith(token) for v in variety_set if token):
            score += 1
    return score


def _resolve_variant_slug(slug: str) -> Optional[str]:
    slug = _strip_trainer_prefix_slug(slug)
    if not slug:
        return None
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return None
    species_payload = None
    base_candidate = None
    for cut in range(len(parts), 0, -1):
        candidate = "-".join(parts[:cut])
        payload = _fetch_species_payload(candidate)
        if payload is not None:
            base_candidate = candidate
            species_payload = payload
            break
    if not species_payload:
        return None
    varieties = species_payload.get("varieties") or []
    variety_names = [
        str(entry.get("pokemon", {}).get("name") or "")
        for entry in varieties
        if isinstance(entry, dict)
    ]
    if slug in variety_names:
        return slug
    if not base_candidate:
        return None
    base_tokens = [p for p in base_candidate.split("-") if p]
    slug_tokens = [p for p in slug.split("-") if p]
    form_tokens = slug_tokens[len(base_tokens) :]
    if not form_tokens:
        return base_candidate
    best_name = None
    best_score = -1
    for name in variety_names:
        if not name:
            continue
        variety_tokens = [p for p in name.split("-") if p]
        score = _score_variety_tokens(form_tokens, variety_tokens)
        if score > best_score:
            best_score = score
            best_name = name
    if best_name and best_score > 0:
        return best_name
    return base_candidate


_FORM_SUFFIXES = {
    "alola",
    "galar",
    "hisui",
    "paldea",
    "mega",
    "primal",
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
    "sky",
    "land",
    "dusk",
    "dawn",
    "midnight",
    "midday",
    "sunny",
    "rainy",
    "snowy",
}


def _fallback_slugs(slug: str) -> list[str]:
    slug = _strip_trainer_prefix_slug(slug)
    fallbacks: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        candidate = str(candidate or "").strip()
        if not candidate or candidate == slug or candidate in seen:
            return
        seen.add(candidate)
        fallbacks.append(candidate)

    if slug == "shaymin":
        add("shaymin-land")
        add("shaymin-sky")
    if slug in {"lycanroc-da", "lycanroc-day"}:
        add("lycanroc-midday")
        add("lycanroc")
    if slug in {"lycanroc-du", "lycanroc-dusk"}:
        add("lycanroc-dusk")
        add("lycanroc")
    if slug in {"lycanroc-n", "lycanroc-night"}:
        add("lycanroc-midnight")
        add("lycanroc")
    for alias in _species_alias_slugs(slug):
        add(alias)
    parts = [p for p in slug.split("-") if p]
    if len(parts) <= 1:
        return fallbacks
    if len(parts[-1]) == 1:
        add("-".join(parts[:-1]))
    if slug.startswith("minior-"):
        add("minior")
    if slug.startswith("oricorio-"):
        add("oricorio")
    if slug.startswith("enamorus-"):
        add("enamorus")
    if slug.startswith("necrozma-"):
        add("necrozma")
    if slug.startswith("zacian-"):
        add("zacian")
    if slug.startswith("basculegion-"):
        add("basculegion")
    if parts[-1] in _FORM_SUFFIXES:
        add("-".join(parts[:-1]))
    # Generic progressive fallback for unknown form suffixes.
    for cut in range(len(parts) - 1, 0, -1):
        candidate = "-".join(parts[:cut])
        add(candidate)
    return fallbacks


_GLOBAL_CACHE = SpriteCache()
_download_thread: Optional[threading.Thread] = None
_download_status = {"state": "idle", "total": 0, "done": 0, "errors": 0}


def sprite_url_for(name: str, *, allow_download: bool = False) -> Optional[str]:
    return _GLOBAL_CACHE.sprite_url_for(name, allow_download=allow_download)


def sprite_path_for(name: str) -> Optional[str]:
    return _GLOBAL_CACHE.sprite_path_for(name)


def ensure_sprite_filename(filename: str) -> bool:
    return _GLOBAL_CACHE.ensure_sprite_filename(filename)


def sprite_cache_dir() -> Path:
    return _GLOBAL_CACHE.cache_dir


def download_status() -> dict:
    status = dict(_download_status)
    total = int(status.get("total") or 0)
    done = int(status.get("done") or 0)
    errors = int(status.get("errors") or 0)
    completed = done + errors
    status["completed"] = completed
    status["pending"] = max(total - completed, 0)
    status["complete"] = bool(total and completed >= total)
    return status


def start_download_all() -> dict:
    global _download_thread
    if _download_thread and _download_thread.is_alive():
        return download_status()
    _download_thread = threading.Thread(target=_download_all_worker, daemon=True)
    _download_thread.start()
    return download_status()


def _download_all_worker() -> None:
    from pathlib import Path

    species_path = Path(__file__).resolve().parent / "data" / "compiled" / "species.json"
    if not species_path.exists():
        _download_status.update(state="error", total=0, done=0, errors=1)
        return
    try:
        payload = json.loads(species_path.read_text(encoding="utf-8"))
    except Exception:
        _download_status.update(state="error", total=0, done=0, errors=1)
        return
    _download_status.update(state="running", total=len(payload), done=0, errors=0)
    try:
        for entry in payload:
            name = str(entry.get("name") or "").strip()
            if not name:
                _download_status["errors"] += 1
                continue
            try:
                url = sprite_url_for(name, allow_download=True)
            except Exception:
                _download_status["errors"] += 1
                continue
            if url:
                _download_status["done"] += 1
            else:
                _download_status["errors"] += 1
    finally:
        _download_status["state"] = "done"
