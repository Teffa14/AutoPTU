from __future__ import annotations

import json
from pathlib import Path

from auto_ptu.learnsets import load_learnsets


ROOT = Path(__file__).resolve().parents[1]
OUT_STATIC_JSON = ROOT / "auto_ptu" / "api" / "static" / "pokedex_learnset.json"
OUT_STATIC_EMBED = ROOT / "auto_ptu" / "api" / "static" / "pokedex_learnset.embed.js"
OUT_STATIC_CHARACTER_JSON = ROOT / "auto_ptu" / "api" / "static" / "AutoPTUCharacter" / "pokedex_learnset.json"


def main() -> None:
    learnsets = load_learnsets()
    payload = {
        species: [{"move": move_name, "level": level} for move_name, level in entries]
        for species, entries in sorted(learnsets.items())
    }
    json_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    embed_text = "window.__AUTO_PTU_POKEDEX_LEARNSET = " + json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + ";\n"
    OUT_STATIC_CHARACTER_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_STATIC_JSON.write_text(json_text, encoding="utf-8")
    OUT_STATIC_CHARACTER_JSON.write_text(json_text, encoding="utf-8")
    OUT_STATIC_EMBED.write_text(embed_text, encoding="utf-8")
    print(
        f"Wrote learnset payloads for {len(payload)} species/forms to "
        f"{OUT_STATIC_JSON} and {OUT_STATIC_EMBED}."
    )


if __name__ == "__main__":
    main()
