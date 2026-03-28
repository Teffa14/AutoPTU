"""Generate lookup data identifying Foundry moves that carry the `punch` trait."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FOUNDATION_MOVES_DIR = PROJECT_ROOT / "Foundry" / "ptr2e-Stable" / "ptr2e-Stable" / "packs" / "core-moves"
OUTPUT_PATH = PROJECT_ROOT / "auto_ptu" / "data" / "compiled" / "punch_moves.json"


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def main() -> None:
    if not FOUNDATION_MOVES_DIR.exists():
        raise FileNotFoundError(
            f"Foundry move directory missing: {FOUNDATION_MOVES_DIR}. Sync the ptr2e repo before running this generator."
        )
    punch_moves: set[str] = set()
    for path in FOUNDATION_MOVES_DIR.glob("*.json"):
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw if isinstance(raw, list) else [raw]
        for entry in entries:
            name = entry.get("name") or entry.get("slug") or path.stem
            system = entry.get("system", {}) if isinstance(entry, dict) else {}
            for action in system.get("actions", []) or []:
                for trait in action.get("traits", []) or []:
                    if str(trait).strip().lower() == "punch":
                        punch_moves.add(_normalize(name))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as out:
        json.dump(sorted(punch_moves), out, indent=2)
    print(f"Wrote {len(punch_moves)} punch moves to {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
