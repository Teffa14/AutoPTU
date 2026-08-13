from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auto_ptu.career.catalogs import REGIONS
from auto_ptu.sprites import _fallback_slugs, _local_sprite_path_for_slug, _slugify


SPECIES_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "species.json"
OUTPUT_DIR = ROOT / "auto_ptu" / "api" / "static" / "career" / "sprites"
PLACEHOLDER = ROOT / "Animated Pokemon Sprites" / "Graphics" / "Pokemon" / "Front" / "000.png"


def main() -> None:
    rows = json.loads(SPECIES_PATH.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    resolved: set[str] = set()
    names = {
        str(row.get("name") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("name") or "").strip()
    }
    names.update(name for region in REGIONS.values() for name in region.partner_choices)
    for name in sorted(names):
        slug = _slugify(name)
        source = _local_sprite_path_for_slug(slug)
        if source is None:
            source = next(
                (candidate for fallback in _fallback_slugs(slug) if (candidate := _local_sprite_path_for_slug(fallback)) is not None),
                None,
            )
        if not slug or source is None:
            continue
        shutil.copy2(source, OUTPUT_DIR / f"{slug}.png")
        copied += 1
        resolved.add(name.casefold())
    if PLACEHOLDER.exists():
        shutil.copy2(PLACEHOLDER, OUTPUT_DIR / "000.png")
    required = {name.casefold() for region in REGIONS.values() for name in region.partner_choices}
    missing = sorted(required - resolved)
    if missing:
        raise RuntimeError(f"Career sprite build is missing regional choices: {', '.join(missing)}")
    if copied < 900:
        raise RuntimeError(f"Career sprite build is incomplete: only {copied} species resolved.")
    print(f"Career sprite pack: {copied} species")


if __name__ == "__main__":
    main()
