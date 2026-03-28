"""Build the compiled species ability index from Pokedex PDFs."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auto_ptu.pokedex_loader import compile_pokedex_species_abilities


def main() -> int:
    pools = compile_pokedex_species_abilities()
    print(f"Wrote {len(pools)} species ability pools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
