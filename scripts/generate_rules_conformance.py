from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
RULES_DIR = ROOT / "auto_ptu" / "rules"
MOVE_SPECIALS_FILE = RULES_DIR / "hooks" / "move_specials.py"
ABILITY_HOOKS_DIR = RULES_DIR / "hooks" / "abilities"
MOVES_JSON = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
MOVES_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
ABILITIES_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
ITEM_LOG = ROOT / "ITEM_LOG.md"
OUT_JSON = ROOT / "reports" / "rules_conformance.json"
OUT_MD = ROOT / "RULES_CONFORMANCE.md"


@dataclass(frozen=True)
class MoveConformance:
    name: str
    effect_text: str
    has_special_handler: bool
    test_mention: bool
    status: str


@dataclass(frozen=True)
class AbilityConformance:
    name: str
    effect_text: str
    has_hook: bool
    test_mention: bool
    status: str


@dataclass(frozen=True)
class ItemConformance:
    name: str
    log_status: str
    notes: str
    test_mention: bool
    status: str


def _iter_py_files(path: Path) -> Iterable[Path]:
    for item in path.rglob("*.py"):
        if item.name.startswith("__"):
            continue
        yield item


def _load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _clean(text: str) -> str:
    if not text:
        return ""
    return " ".join(str(text).split()).strip()


def _load_test_text() -> str:
    chunks: List[str] = []
    for file in _iter_py_files(TESTS_DIR):
        chunks.append(_load_text(file).lower())
    return "\n".join(chunks)


def _parse_move_special_names() -> Set[str]:
    source = _load_text(MOVE_SPECIALS_FILE)
    pattern = re.compile(r"@register_move_special\(([^)]*)\)")
    names: Set[str] = set()
    for match in pattern.finditer(source):
        args = match.group(1)
        for part in args.split(","):
            chunk = part.strip()
            if not chunk or "=" in chunk:
                continue
            if chunk.startswith(("'", '"')) and chunk.endswith(("'", '"')):
                names.add(chunk.strip("'\"").lower())
    return names


def _parse_ability_hook_names() -> Set[str]:
    names: Set[str] = set()
    pattern = re.compile(r"@register_ability_hook\(([^)]*)\)")
    ability_pattern = re.compile(r"ability\s*=\s*([\"'])(.+?)\1")
    for file in _iter_py_files(ABILITY_HOOKS_DIR):
        source = _load_text(file)
        for match in pattern.finditer(source):
            args = match.group(1)
            ability_match = ability_pattern.search(args)
            if not ability_match:
                continue
            names.add(ability_match.group(2).strip().lower())
    return names


def _load_moves_effect_map() -> Dict[str, str]:
    if not MOVES_CSV.exists():
        return {}
    text = _load_text(MOVES_CSV)
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.startswith("Name,")), None)
    if header_index is None:
        return {}
    effects: Dict[str, str] = {}
    with MOVES_CSV.open("r", encoding="utf-8-sig") as handle:
        for _ in range(header_index):
            next(handle, None)
        reader = csv.DictReader(handle)
        for row in reader:
            name = _clean(str(row.get("Name") or ""))
            if not name:
                continue
            effects[name.lower()] = _clean(str(row.get("Effects") or ""))
    return effects


def _load_moves() -> List[MoveConformance]:
    source = json.loads(_load_text(MOVES_JSON))
    effects_map = _load_moves_effect_map()
    special_names = _parse_move_special_names()
    tests_blob = _load_test_text()
    rows: List[MoveConformance] = []
    for entry in source:
        if not isinstance(entry, dict):
            continue
        name = _clean(str(entry.get("name") or ""))
        if not name:
            continue
        effect = effects_map.get(name.lower()) or _clean(str(entry.get("effects_text") or entry.get("effects") or ""))
        has_special = name.lower() in special_names
        test_mention = name.lower() in tests_blob
        if effect and not has_special and not test_mention:
            status = "needs_rule_review"
        elif effect and (has_special or test_mention):
            status = "covered"
        elif not effect:
            status = "generic_or_blank"
        else:
            status = "covered"
        rows.append(
            MoveConformance(
                name=name,
                effect_text=effect,
                has_special_handler=has_special,
                test_mention=test_mention,
                status=status,
            )
        )
    rows.sort(key=lambda row: row.name.lower())
    return rows


def _load_abilities() -> List[AbilityConformance]:
    if not ABILITIES_CSV.exists():
        return []
    hook_names = _parse_ability_hook_names()
    tests_blob = _load_test_text()
    rows: List[AbilityConformance] = []
    with ABILITIES_CSV.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = _clean(str(row.get("Name") or ""))
            if not name:
                continue
            effect = _clean("\n".join(v for v in [str(row.get("Effect") or ""), str(row.get("Effect 2") or "")] if v))
            lower = name.lower()
            has_hook = lower in hook_names
            test_mention = lower in tests_blob
            if effect and not has_hook and not test_mention:
                status = "needs_rule_review"
            elif effect and (has_hook or test_mention):
                status = "covered"
            else:
                status = "generic_or_blank"
            rows.append(
                AbilityConformance(
                    name=name,
                    effect_text=effect,
                    has_hook=has_hook,
                    test_mention=test_mention,
                    status=status,
                )
            )
    rows.sort(key=lambda row: row.name.lower())
    return rows


def _parse_item_log_rows() -> List[ItemConformance]:
    if not ITEM_LOG.exists():
        return []
    tests_blob = _load_test_text()
    rows: List[ItemConformance] = []
    pattern = re.compile(r"^\|\s*\d+\s*\|\s*`?(.*?)`?\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")
    for line in _load_text(ITEM_LOG).splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name = _clean(match.group(1).strip("`"))
        log_status = _clean(match.group(2))
        notes = _clean(match.group(3))
        if not name or name.lower() == "item":
            continue
        test_mention = name.lower() in tests_blob
        if log_status.lower() != "done":
            status = "needs_rule_review"
        elif ("placeholder" in notes.lower() or "out-of-combat" in notes.lower()) and not test_mention:
            status = "needs_rule_review"
        else:
            status = "covered"
        rows.append(
            ItemConformance(
                name=name,
                log_status=log_status,
                notes=notes,
                test_mention=test_mention,
                status=status,
            )
        )
    rows.sort(key=lambda row: row.name.lower())
    return rows


def _write_outputs(moves: List[MoveConformance], abilities: List[AbilityConformance], items: List[ItemConformance]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "moves": [row.__dict__ for row in moves],
        "abilities": [row.__dict__ for row in abilities],
        "items": [row.__dict__ for row in items],
        "summary": {
            "moves_total": len(moves),
            "moves_needs_rule_review": sum(1 for row in moves if row.status == "needs_rule_review"),
            "abilities_total": len(abilities),
            "abilities_needs_rule_review": sum(1 for row in abilities if row.status == "needs_rule_review"),
            "items_total": len(items),
            "items_needs_rule_review": sum(1 for row in items if row.status == "needs_rule_review"),
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        "# Rules Conformance",
        "",
        "Per-entry conformance matrix for moves, abilities, and items.",
        "Status legend:",
        "- `covered`: has explicit hook/logic and/or test evidence",
        "- `generic_or_blank`: no specific text effect to validate or generic handling applies",
        "- `needs_rule_review`: effect text exists but explicit hook/test evidence is weak",
        "",
        "## Summary",
        f"- Moves: {payload['summary']['moves_total']} total, {payload['summary']['moves_needs_rule_review']} need rule review",
        f"- Abilities: {payload['summary']['abilities_total']} total, {payload['summary']['abilities_needs_rule_review']} need rule review",
        f"- Items: {payload['summary']['items_total']} total, {payload['summary']['items_needs_rule_review']} need rule review",
        "",
        "## Moves Needing Rule Review",
    ]
    for row in [row for row in moves if row.status == "needs_rule_review"][:250]:
        md_lines.append(
            f"- `{row.name}` | special_handler={row.has_special_handler} | test_mention={row.test_mention} | effect: {row.effect_text[:180]}"
        )
    if not any(row.status == "needs_rule_review" for row in moves):
        md_lines.append("- None")
    md_lines += ["", "## Abilities Needing Rule Review"]
    for row in [row for row in abilities if row.status == "needs_rule_review"][:250]:
        md_lines.append(
            f"- `{row.name}` | has_hook={row.has_hook} | test_mention={row.test_mention} | effect: {row.effect_text[:180]}"
        )
    if not any(row.status == "needs_rule_review" for row in abilities):
        md_lines.append("- None")
    md_lines += ["", "## Items Needing Rule Review"]
    for row in [row for row in items if row.status == "needs_rule_review"][:250]:
        md_lines.append(
            f"- `{row.name}` | item_log_status={row.log_status} | test_mention={row.test_mention} | notes: {row.notes[:180]}"
        )
    if not any(row.status == "needs_rule_review" for row in items):
        md_lines.append("- None")
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> None:
    moves = _load_moves()
    abilities = _load_abilities()
    items = _parse_item_log_rows()
    _write_outputs(moves, abilities, items)


if __name__ == "__main__":
    main()
