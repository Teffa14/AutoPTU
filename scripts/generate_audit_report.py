from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARITY_JSON = ROOT / "audit_parity.json"
MOVES_JSON = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
MOVES_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
OUT_PATH = ROOT / "AUDIT_REPORT.md"


def _load_parity() -> dict:
    return json.loads(PARITY_JSON.read_text(encoding="utf-8"))


def _load_moves() -> dict[str, dict]:
    moves = {}
    for entry in json.loads(MOVES_JSON.read_text(encoding="utf-8")):
        name = str(entry.get("name") or "").strip().lower()
        if name:
            moves[name] = entry
    if MOVES_CSV.exists():
        # fill missing effects_text from CSV if needed
        import csv

        effects = {}
        with MOVES_CSV.open("r", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = str(row.get("Name") or "").strip().lower()
                text = str(row.get("Effects") or "").strip()
                if name and text:
                    effects[name] = text
        for name, entry in moves.items():
            if not entry.get("effects_text") and effects.get(name):
                entry["effects_text"] = effects[name]
    return moves


def _has_effect_text(entry: dict) -> bool:
    text = str(entry.get("effects_text") or entry.get("effects") or "").strip()
    if not text or text == "--":
        return False
    return True


def main() -> None:
    parity = _load_parity()
    moves = parity.get("moves", [])
    move_data = _load_moves()

    total = len(moves)
    with_handlers = sum(1 for m in moves if m.get("has_special_handler"))
    without_handlers = total - with_handlers

    no_handler_no_effect = []
    no_handler_has_effect = []
    for move in moves:
        if move.get("has_special_handler"):
            continue
        name = str(move.get("name") or "").strip().lower()
        entry = move_data.get(name, {})
        if _has_effect_text(entry):
            no_handler_has_effect.append(name)
        else:
            no_handler_no_effect.append(name)

    lines = [
        "# Audit Report",
        "",
        "This report summarizes coverage risk areas (handlers/tests) relative to data sources.",
        "It does NOT claim rulebook parity; it highlights where parity is less certain.",
        "Moves without special handlers may still be fully implemented by generic rules; lack of a handler alone is not a bug.",
        "",
        "## Moves",
        f"- Total moves: {total}",
        f"- Moves with special handlers: {with_handlers}",
        f"- Moves without special handlers: {without_handlers}",
        f"- Moves without special handlers AND empty/\"--\" effects text: {len(no_handler_no_effect)}",
        f"- Moves without special handlers BUT with non-empty effects text (handled generically): {len(no_handler_has_effect)}",
        "",
        "### Moves Without Handlers + No Effects Text",
    ]
    lines += [f"- {name}" for name in sorted(no_handler_no_effect)] or ["- None"]
    lines += ["", "### Moves Without Handlers + Effects Text"]
    lines += [f"- {name}" for name in sorted(no_handler_has_effect)] or ["- None"]

    OUT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
