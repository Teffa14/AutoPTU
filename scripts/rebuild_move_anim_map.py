from __future__ import annotations

import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MOVES_JSON = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
RXDATA = ROOT / "IMPLEMENTATION FILES" / "Gen 9 Move Animation Project" / "Data" / "PkmnAnimations.rxdata"
ANIM_DIR = ROOT / "IMPLEMENTATION FILES" / "Gen 9 Move Animation Project" / "Graphics" / "Animations"
OUT_MAP = ROOT / "auto_ptu" / "data" / "move_anim_map.json"


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _clean_name(value: str) -> str:
    name = Path(value).stem.lower().strip()
    for prefix in (
        "pras- ",
        "prsfx- ",
        "custom_",
        "custom-",
        "gen 9 - ",
        "gen9-",
        "gen8- ",
        "gen8-",
    ):
        if name.startswith(prefix):
            name = name[len(prefix) :]
    name = name.replace("_", " ").replace("-", " ")
    name = re.sub(r"\b(bg|fg)\b", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _extract_ascii_runs(binary: bytes, min_len: int = 4) -> list[str]:
    runs: list[str] = []
    buf: list[str] = []
    for byte in binary:
        if 32 <= byte < 127:
            buf.append(chr(byte))
            continue
        if len(buf) >= min_len:
            runs.append("".join(buf))
        buf = []
    if len(buf) >= min_len:
        runs.append("".join(buf))
    return runs


def _rxdata_png_candidates() -> set[str]:
    if not RXDATA.exists():
        return set()
    runs = _extract_ascii_runs(RXDATA.read_bytes())
    out: set[str] = set()
    for run in runs:
        if ".png" not in run.lower():
            continue
        name = run.strip()
        if "/" in name or "\\" in name:
            name = name.replace("\\", "/").split("/")[-1]
        if name.lower().endswith(".png"):
            out.add(name)
    return out


def _rxdata_move_png_map() -> dict[str, str]:
    if not RXDATA.exists():
        return {}
    runs = _extract_ascii_runs(RXDATA.read_bytes())
    move_pattern = re.compile(r"^Move:([A-Z0-9_]+)$")
    mapping: dict[str, str] = {}
    for index, run in enumerate(runs):
        match = move_pattern.match(run.strip())
        if not match:
            continue
        move_key = _norm(match.group(1))
        if not move_key or move_key in mapping:
            continue
        png_candidates: list[str] = []
        for candidate in runs[index + 1 : index + 18]:
            text = candidate.strip()
            if not text.lower().endswith(".png"):
                continue
            if "/" in text or "\\" in text:
                text = text.replace("\\", "/").split("/")[-1]
            if not (ANIM_DIR / text).exists():
                continue
            if _contains_generic_marker(text):
                continue
            png_candidates.append(text)
        if not png_candidates:
            continue
        preferred = None
        for png in png_candidates:
            stem = Path(png).stem.lower()
            if png.startswith("PRAS-"):
                preferred = png
                if " fg" in stem or stem.endswith("fg"):
                    break
        mapping[move_key] = preferred or png_candidates[0]
    return mapping


def _iter_move_entries() -> Iterable[dict]:
    payload = json.loads(MOVES_JSON.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return payload


def _contains_generic_marker(filename: str) -> bool:
    stem = Path(filename).stem.lower().strip()
    if stem in {"", "!"}:
        return True
    if re.match(r"^\d{3}-", stem):
        return True
    generic_terms = (
        "anim sheet",
        "animsheet",
        "attack",
        "burst",
        "weapon",
        "state",
        "emotion",
    )
    return any(term in stem for term in generic_terms)


def build_map() -> dict:
    if not MOVES_JSON.exists():
        raise FileNotFoundError(f"Missing moves file: {MOVES_JSON}")
    if not ANIM_DIR.exists():
        raise FileNotFoundError(f"Missing animation dir: {ANIM_DIR}")

    all_png = sorted([p.name for p in ANIM_DIR.glob("*.png")])
    rxdata_png = _rxdata_png_candidates()
    rxdata_existing = sorted({name for name in rxdata_png if (ANIM_DIR / name).exists()})
    rxdata_move_map = _rxdata_move_png_map()
    # Use the full uploaded PNG set; rxdata extraction is incomplete for some filenames.
    candidate_png = all_png

    # Prefer non-generic references for fallback matching.
    preferred = [name for name in candidate_png if not _contains_generic_marker(name)]
    if len(preferred) < 150:
        preferred = candidate_png

    normalized_to_file: dict[str, str] = {}
    cleaned_rows: list[tuple[str, str, str]] = []
    for filename in preferred:
        cleaned = _clean_name(filename)
        key = _norm(cleaned)
        if not key:
            continue
        if key and key not in normalized_to_file:
            normalized_to_file[key] = filename
        cleaned_rows.append((filename, cleaned, key))

    type_keywords = {
        "fire": ("fire", "flame", "burn", "lava", "heat", "pyro"),
        "water": ("water", "aqua", "bubble", "wave", "hydro", "rain"),
        "electric": ("electric", "thunder", "spark", "volt", "shock", "lightning"),
        "ice": ("ice", "frost", "freeze", "snow", "blizzard"),
        "dark": ("dark", "shadow", "night", "darkness"),
        "ghost": ("ghost", "shadow", "spirit", "haunt"),
        "ground": ("earth", "ground", "sand", "mud", "quake"),
        "rock": ("rock", "stone", "meteor"),
        "grass": ("grass", "leaf", "vine", "seed", "pollen", "flora"),
        "fairy": ("fairy", "moon", "gleam", "pixie"),
        "dragon": ("dragon", "draco", "drake", "claw"),
        "steel": ("steel", "metal", "iron", "flash"),
        "bug": ("bug", "web", "swarm"),
        "poison": ("poison", "toxic", "acid", "sludge", "venom"),
        "fighting": ("punch", "kick", "smash", "strike", "combat"),
        "flying": ("air", "wind", "aerial", "gust", "wing"),
        "psychic": ("psy", "mind", "cosmo", "tele"),
    }

    def pool_for_type(move_type: str) -> list[tuple[str, str, str]]:
        terms = type_keywords.get(move_type.lower().strip(), ())
        if not terms:
            return cleaned_rows
        pool = [row for row in cleaned_rows if any(term in row[1] for term in terms)]
        return pool if len(pool) >= 6 else cleaned_rows

    mapping: dict[str, str] = {}
    stats = {
        "total_moves": 0,
        "rxdata_direct_match": 0,
        "exact_clean_match": 0,
        "contains_match": 0,
        "similarity_match": 0,
        "fallback_match": 0,
        "candidate_png_total": len(candidate_png),
        "preferred_png_total": len(preferred),
        "rxdata_png_total": len(rxdata_existing),
    }

    type_fallbacks = {
        "fire": "015-Fire01.png",
        "water": "018-Water01.png",
        "electric": "017-Thunder01.png",
        "ice": "016-Ice01.png",
        "dark": "022-Darkness01.png",
        "ghost": "022-Darkness01.png",
        "ground": "Earth1.png",
        "rock": "rockice.png",
        "grass": "DustandGrass.png",
        "fairy": "Anima (1).png",
        "dragon": "dragon claw.png",
    }

    moves = list(_iter_move_entries())
    for row in moves:
        move_name = str(row.get("name") or "").strip()
        if not move_name:
            continue
        stats["total_moves"] += 1
        key = _norm(move_name)
        chosen: str | None = None

        rxdata_direct = rxdata_move_map.get(key)
        if rxdata_direct:
            chosen = rxdata_direct
            stats["rxdata_direct_match"] += 1

        # 1) exact clean-key lookup.
        direct = normalized_to_file.get(key)
        if not chosen and direct:
            chosen = direct
            stats["exact_clean_match"] += 1
        else:
            # 2) "contains" style match based on move words.
            if not chosen:
                words = [w for w in re.split(r"[^a-z0-9]+", move_name.lower()) if w and w not in {"the", "of", "and"}]
                scored: list[tuple[float, int, str]] = []
                for filename, cleaned, cleaned_key in cleaned_rows:
                    score = 0.0
                    if key and (key in cleaned_key or cleaned_key in key):
                        score += 2.0
                    if words:
                        hits = sum(1 for w in words if w in cleaned)
                        score += hits / max(1, len(words))
                    if score > 0:
                        scored.append((score, len(cleaned), filename))
                if scored:
                    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
                    chosen = scored[0][2]
                    stats["contains_match"] += 1

        # 3) approximate similarity in type-aware pool if still unmatched.
        if not chosen:
            move_type = str(row.get("type") or "").strip().lower()
            pool = pool_for_type(move_type)
            source = " ".join(w for w in re.split(r"[^a-z0-9]+", move_name.lower()) if w) or move_name.lower()
            best_score = -1.0
            best_name: str | None = None
            for filename, cleaned, _ in pool:
                ratio = difflib.SequenceMatcher(None, source, cleaned).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_name = filename
            if best_name and best_score >= 0.43:
                chosen = best_name
                stats["similarity_match"] += 1

        # 4) hard fallback to an uploaded file by type.
        if not chosen:
            move_type = str(row.get("type") or "").strip().lower()
            fallback = type_fallbacks.get(move_type)
            if fallback and (ANIM_DIR / fallback).exists():
                chosen = fallback
            else:
                chosen = preferred[0]
            stats["fallback_match"] += 1

        mapping[key] = chosen

    return {
        "version": 5,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "rxdata_strings_plus_uploaded_pngs_closest_name",
        "stats": stats,
        "map": mapping,
    }


def main() -> None:
    payload = build_map()
    OUT_MAP.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = payload["stats"]
    print(f"Wrote {OUT_MAP}")
    print(
        "stats:",
        f"moves={stats['total_moves']}",
        f"rxdata={stats['rxdata_direct_match']}",
        f"exact={stats['exact_clean_match']}",
        f"contains={stats['contains_match']}",
        f"similarity={stats['similarity_match']}",
        f"fallback={stats['fallback_match']}",
        f"rxdata_png={stats['rxdata_png_total']}",
    )


if __name__ == "__main__":
    main()
