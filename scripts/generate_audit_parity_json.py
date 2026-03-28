from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MOVES_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
ABILITIES_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
MOVES_JSON = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
RULES_DIR = ROOT / "auto_ptu" / "rules"
TESTS_DIR = ROOT / "tests"
OUT_PATH = ROOT / "audit_parity.json"


def _iter_py_files(path: Path) -> Iterable[Path]:
    for item in path.rglob("*.py"):
        if item.name.startswith("__"):
            continue
        yield item


def _load_csv_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    names: list[str] = []
    text = path.read_text(encoding="utf-8-sig")
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
        if name:
            names.append(name)
    return names


def _load_moves_json_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    names: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _load_code_text(path: Path) -> str:
    buf: list[str] = []
    for item in _iter_py_files(path):
        try:
            buf.append(item.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(buf).lower()


def _load_test_mentions(names: list[str]) -> set[str]:
    if not TESTS_DIR.exists():
        return set()
    lower_map = {name.lower(): name for name in names}
    mentions: set[str] = set()
    for path in _iter_py_files(TESTS_DIR):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for lower_name, original in lower_map.items():
            if lower_name in text:
                mentions.add(original)
    return mentions


def _load_hook_abilities() -> set[str]:
    abilities: set[str] = set()
    pattern = re.compile(r"ability\\s*=\\s*['\\\"]([^'\\\"]+)['\\\"]")
    hooks_dir = RULES_DIR / "hooks" / "abilities"
    if not hooks_dir.exists():
        return abilities
    for path in _iter_py_files(hooks_dir):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            if name:
                abilities.add(name)
    return abilities


def _load_move_handlers(names: list[str]) -> set[str]:
    try:
        from auto_ptu.rules.hooks import move_specials
    except Exception:
        return set()

    try:
        move_specials.initialize_move_specials()
    except Exception:
        return set()

    handlers: set[str] = set()
    for name in names:
        if move_specials._has_specific_handler(name.lower()):
            handlers.add(name)
    return handlers


def main() -> None:
    move_source_names = _load_csv_names(MOVES_CSV)
    move_compiled_names = _load_moves_json_names(MOVES_JSON)
    move_names = sorted({*move_compiled_names})

    ability_source_names = _load_csv_names(ABILITIES_CSV)
    ability_hook_names = _load_hook_abilities()
    ability_names = sorted({*ability_source_names, *ability_hook_names})

    move_handlers = _load_move_handlers(move_names)
    move_test_mentions = _load_test_mentions(move_names)
    ability_test_mentions = _load_test_mentions(ability_names)

    moves = []
    move_sources = {name.lower() for name in move_source_names}
    for name in move_names:
        moves.append(
            {
                "name": name,
                "in_sources": name.lower() in move_sources,
                "has_special_handler": name in move_handlers,
                "test_mention": name in move_test_mentions,
            }
        )

    abilities = []
    ability_sources = {name.lower() for name in ability_source_names}
    for name in ability_names:
        test_mention = name in ability_test_mentions
        status = "done" if test_mention else "pending"
        abilities.append(
            {
                "name": name,
                "in_sources": name.lower() in ability_sources,
                "status": status,
                "test_mention": test_mention,
            }
        )

    OUT_PATH.write_text(
        json.dumps({"moves": moves, "abilities": abilities}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
