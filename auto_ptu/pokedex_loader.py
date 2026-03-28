"""Load species ability pools from the PTU Pokedex PDF rulebooks."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import DATA_DIR, PROJECT_ROOT
from .learnsets import normalize_species_key


_COMPILED_PATH = DATA_DIR / "compiled" / "pokedex_abilities.json"
_SWSH_GALARDEX_PATH = DATA_DIR / "compiled" / "swsh_galardex.json"
_HISUIDEX_PATH = DATA_DIR / "compiled" / "hisuidex.json"
_POKEDEX_CACHE: Optional[Dict[str, Dict[str, List[str]]]] = None
_BASIC_RE = re.compile(r"Basic Ability(?:\s*\d+)?\s*:\s*([^\n\r]+)", re.IGNORECASE)
_ADV_RE = re.compile(r"(?:Adv|Advanced) Ability(?:\s*\d+)?\s*:\s*([^\n\r]+)", re.IGNORECASE)
_HIGH_RE = re.compile(r"High Ability(?:\s*\d+)?\s*:\s*([^\n\r]+)", re.IGNORECASE)


def _dedupe(values: Iterable[str]) -> List[str]:
    results: List[str] = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        if any(existing.lower() == cleaned.lower() for existing in results):
            continue
        results.append(cleaned)
    return results


def _rulebook_pokedex_paths(rulebook_root: Path) -> List[Path]:
    candidates = [
        rulebook_root / "Pokedex 1.05.pdf",
        rulebook_root / "GalarDex + Armor_Crown.pdf",
        rulebook_root / "HisuiDex.pdf",
        rulebook_root / "PTU 1.05" / "Pokedex 1.05.pdf",
    ]
    paths: List[Path] = []
    seen: set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        key = str(path.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return paths


def _clean_species_name(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = cleaned.replace("\u2013", "-").replace("\u2014", "-")
    cleaned = cleaned.replace("�", "e")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned


def _clean_ability_name(value: str) -> str:
    cleaned = str(value or "").replace("\u2013", "-").replace("\u2014", "-")
    cleaned = cleaned.replace("�", "e")
    cleaned = cleaned.replace("\n", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;:-")
    if not cleaned:
        return ""
    if cleaned.lower() in {"-", "--", "none", "n/a"}:
        return ""
    cleaned = re.sub(r"\s*\((hidden ability|ha|dw)\)\s*$", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def _extract_species_name(page_text: str) -> str:
    if not re.search(r"\bBase Stats\b", page_text, flags=re.IGNORECASE):
        return ""
    prefix = re.split(r"Base Stats\s*:", page_text, maxsplit=1, flags=re.IGNORECASE)[0]
    lines = []
    for raw in prefix.splitlines():
        line = _clean_species_name(raw)
        if not line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    if not lines:
        return ""
    return lines[-1]


def _extract_ability_values(pattern: re.Pattern[str], page_text: str) -> List[str]:
    values: List[str] = []
    for match in pattern.finditer(page_text):
        raw = match.group(1)
        if not raw:
            continue
        parts = re.split(r"\s*/\s*|\s*,\s*", raw)
        for part in parts:
            name = _clean_ability_name(part)
            if name:
                values.append(name)
    return _dedupe(values)


def _extract_page_ability_pool(page_text: str) -> Optional[Dict[str, List[str]]]:
    basic = _extract_ability_values(_BASIC_RE, page_text)
    advanced = _extract_ability_values(_ADV_RE, page_text)
    high = _extract_ability_values(_HIGH_RE, page_text)
    if not basic and not advanced and not high:
        return None
    return {
        "starting": list(basic),
        "basic": list(basic),
        "advanced": list(advanced),
        "high": list(high),
    }


def _merge_pool_entries(base: Dict[str, List[str]], update: Dict[str, List[str]]) -> Dict[str, List[str]]:
    merged: Dict[str, List[str]] = {}
    for tier in ("starting", "basic", "advanced", "high"):
        merged[tier] = _dedupe([*(base.get(tier) or []), *(update.get(tier) or [])])
    return merged


def _normalize_loaded_pools(payload: object) -> Dict[str, Dict[str, List[str]]]:
    if not isinstance(payload, dict):
        return {}
    pools: Dict[str, Dict[str, List[str]]] = {}
    for raw_key, raw_entry in payload.items():
        key = normalize_species_key(str(raw_key))
        if not key or not isinstance(raw_entry, dict):
            continue
        entry: Dict[str, List[str]] = {}
        for tier in ("starting", "basic", "advanced", "high"):
            values = raw_entry.get(tier)
            if not isinstance(values, list):
                entry[tier] = []
            else:
                entry[tier] = _dedupe(str(value) for value in values)
        pools[key] = entry
    return pools


def build_pokedex_species_abilities(rulebook_root: Optional[Path] = None) -> Dict[str, Dict[str, List[str]]]:
    # Local import keeps runtime fast when using the compiled cache.
    from pypdf import PdfReader

    root = Path(rulebook_root or (PROJECT_ROOT / "files" / "rulebook"))
    pools: Dict[str, Dict[str, List[str]]] = {}
    for pdf_path in _rulebook_pokedex_paths(root):
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            continue
        for page in reader.pages:
            page_text = page.extract_text() or ""
            species_name = _extract_species_name(page_text)
            if not species_name:
                continue
            entry = _extract_page_ability_pool(page_text)
            if not entry:
                continue
            key = normalize_species_key(species_name)
            if not key:
                continue
            existing = pools.get(key)
            pools[key] = _merge_pool_entries(existing or {}, entry)
    if _SWSH_GALARDEX_PATH.exists():
        try:
            payload = json.loads(_SWSH_GALARDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_entry in entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                abilities = raw_entry.get("abilities", {})
                if not isinstance(abilities, dict):
                    continue
                key = normalize_species_key(str(raw_species))
                if not key:
                    continue
                entry = {
                    "starting": _dedupe(abilities.get("basic", [])),
                    "basic": _dedupe(abilities.get("basic", [])),
                    "advanced": _dedupe(abilities.get("advanced", [])),
                    "high": _dedupe(abilities.get("high", [])),
                }
                if not any(entry[tier] for tier in ("starting", "basic", "advanced", "high")):
                    continue
                existing = pools.get(key)
                pools[key] = _merge_pool_entries(existing or {}, entry)
    if _HISUIDEX_PATH.exists():
        try:
            payload = json.loads(_HISUIDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        entries = payload.get("entries", {}) if isinstance(payload, dict) else {}
        if isinstance(entries, dict):
            for raw_species, raw_entry in entries.items():
                if not isinstance(raw_entry, dict):
                    continue
                abilities = raw_entry.get("abilities", {})
                if not isinstance(abilities, dict):
                    continue
                key = normalize_species_key(str(raw_species))
                if not key:
                    continue
                entry = {
                    "starting": _dedupe(abilities.get("basic", [])),
                    "basic": _dedupe(abilities.get("basic", [])),
                    "advanced": _dedupe(abilities.get("advanced", [])),
                    "high": _dedupe(abilities.get("high", [])),
                }
                if not any(entry[tier] for tier in ("starting", "basic", "advanced", "high")):
                    continue
                existing = pools.get(key)
                pools[key] = _merge_pool_entries(existing or {}, entry)
    return pools


def load_pokedex_species_abilities() -> Dict[str, Dict[str, List[str]]]:
    global _POKEDEX_CACHE
    if _POKEDEX_CACHE is not None:
        return _POKEDEX_CACHE
    if _COMPILED_PATH.exists():
        try:
            payload = json.loads(_COMPILED_PATH.read_text(encoding="utf-8"))
            _POKEDEX_CACHE = _normalize_loaded_pools(payload)
            if _POKEDEX_CACHE:
                return _POKEDEX_CACHE
        except Exception:
            pass
    _POKEDEX_CACHE = build_pokedex_species_abilities()
    return _POKEDEX_CACHE


def compile_pokedex_species_abilities(output_path: Optional[Path] = None) -> Dict[str, Dict[str, List[str]]]:
    output = Path(output_path or _COMPILED_PATH)
    pools = build_pokedex_species_abilities()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(pools, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return pools


__all__ = [
    "build_pokedex_species_abilities",
    "compile_pokedex_species_abilities",
    "load_pokedex_species_abilities",
]
