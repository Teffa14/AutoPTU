from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RULES = ROOT / "auto_ptu" / "rules"
HOOKS = RULES / "hooks"
ABILITY_HOOKS_DIR = HOOKS / "abilities"
TESTS = ROOT / "tests"


@dataclass(frozen=True)
class AbilityHookInfo:
    ability: str
    phase: str
    holder: str
    file: str
    function: str


@dataclass(frozen=True)
class MoveSpecialInfo:
    move: str
    phase: str
    file: str
    function: str


def _iter_py_files(path: Path) -> Iterable[Path]:
    for item in path.rglob("*.py"):
        if item.name.startswith("__"):
            continue
        yield item


def _parse_ability_hooks() -> List[AbilityHookInfo]:
    hooks: List[AbilityHookInfo] = []
    decorator_re = re.compile(r"@register_ability_hook\((?P<args>[^)]*)\)\s*def\s+(?P<name>\w+)", re.MULTILINE)
    for file in _iter_py_files(ABILITY_HOOKS_DIR):
        source = file.read_text(encoding="utf-8")
        for match in decorator_re.finditer(source):
            args = match.group("args")
            func_name = match.group("name")
            phase = _extract_kwarg(args, "phase") or "post_damage"
            ability = _extract_kwarg(args, "ability")
            holder = _extract_kwarg(args, "holder") or "attacker"
            if not ability or ability == "None":
                continue
            ability_clean = ability.strip().strip("\"'")
            hooks.append(
                AbilityHookInfo(
                    ability=ability_clean,
                    phase=phase.strip().strip("\"'"),
                    holder=holder.strip().strip("\"'"),
                    file=str(file.relative_to(ROOT)),
                    function=func_name,
                )
            )
    return hooks


def _extract_kwarg(args: str, name: str) -> Optional[str]:
    pattern = re.compile(rf"{name}\s*=\s*([^,]+)")
    match = pattern.search(args)
    if not match:
        return None
    return match.group(1).strip()


def _parse_move_specials() -> List[MoveSpecialInfo]:
    file = HOOKS / "move_specials.py"
    source = file.read_text(encoding="utf-8")
    specials: List[MoveSpecialInfo] = []
    decorator_re = re.compile(r"@register_move_special\((?P<args>[^)]*)\)\s*def\s+(?P<name>\w+)", re.MULTILINE)
    for match in decorator_re.finditer(source):
        args = match.group("args")
        func_name = match.group("name")
        phase = _extract_kwarg(args, "phase") or "post_damage"
        move_names = _extract_positional_names(args)
        for move in move_names:
            specials.append(
                MoveSpecialInfo(
                    move=move,
                    phase=phase.strip().strip("\"'"),
                    file=str(file.relative_to(ROOT)),
                    function=func_name,
                )
            )
    return specials


def _extract_positional_names(args: str) -> List[str]:
    if not args:
        return []
    # strip kwargs
    cleaned = []
    for part in args.split(","):
        part = part.strip()
        if not part or "=" in part:
            continue
        cleaned.append(part.strip())
    names = []
    for entry in cleaned:
        entry = entry.strip()
        if entry.startswith("*"):
            continue
        names.append(entry.strip().strip("\"'"))
    return names


def _load_moves() -> Dict[str, dict]:
    effects_map = _load_move_effects_csv()
    path = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    moves = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name:
            continue
        if effects_map and not entry.get("effects_text"):
            effects_text = effects_map.get(name.lower())
            if effects_text:
                entry = dict(entry)
                entry["effects_text"] = effects_text
        moves[name.lower()] = entry
    return moves


def _load_move_effects_csv() -> Dict[str, str]:
    path = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Moves Data.csv"
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_index = None
    for idx, line in enumerate(lines):
        if line.startswith("Name,"):
            header_index = idx
            break
    if header_index is None:
        return {}
    import csv

    effects: Dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig") as handle:
        for _ in range(header_index):
            next(handle, None)
        reader = csv.DictReader(handle)
        for row in reader:
            name = str(row.get("Name") or "").strip()
            if not name:
                continue
            text = str(row.get("Effects") or "").strip()
            if text:
                effects[name.lower()] = text
    return effects


def _load_abilities_csv() -> Dict[str, str]:
    path = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
    effects: Dict[str, str] = {}
    if not path.exists():
        return effects
    import csv

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = str(row.get("Name") or "").strip()
            if not name:
                continue
            effect = str(row.get("Effect") or "").strip()
            effect2 = str(row.get("Effect 2") or "").strip()
            text = "\n".join(part for part in (effect, effect2) if part)
            effects[name] = text
    return effects


def _load_test_moves() -> Set[str]:
    moves: Set[str] = set()
    pattern = re.compile(
        r"move_name\s*=\s*\"([^\"]+)\"|MoveSpec\(name=\"([^\"]+)\"",
        re.IGNORECASE,
    )
    for file in _iter_py_files(TESTS):
        source = file.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            name = match.group(1) or match.group(2)
            if name:
                moves.add(name.strip().lower())
    return moves


def _load_test_abilities() -> Set[str]:
    abilities: Set[str] = set()
    patterns = [
        re.compile(r"abilities\s*=\s*\[\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\]"),
        re.compile(r"\.abilities\s*=\s*\[\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\]"),
        re.compile(r"abilities\.append\(\s*\{\s*[\"']name[\"']\s*:\s*[\"']([^\"']+)[\"']\s*\}\s*\)"),
    ]
    for file in _iter_py_files(TESTS):
        source = file.read_text(encoding="utf-8")
        for pattern in patterns:
            for match in pattern.finditer(source):
                name = match.group(1)
                if name:
                    abilities.add(name.strip())
    return abilities


def _ascii_clean(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": "\"",
        "\u201d": "\"",
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.encode("ascii", "ignore").decode("ascii")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    deduped: List[str] = []
    seen: Set[str] = set()
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        deduped.append(line)
    return "\n".join(deduped)


def _missing_test_abilities(all_abilities: Iterable[str], tested: Set[str]) -> Set[str]:
    return {ability for ability in all_abilities if ability not in tested}


def _find_ability_refs(ability: str) -> List[str]:
    refs: Set[str] = set()
    pattern = re.compile(re.escape(ability))
    for file in _iter_py_files(RULES):
        try:
            source = file.read_text(encoding="utf-8")
        except OSError:
            continue
        if pattern.search(source):
            refs.add(str(file.relative_to(ROOT)))
    return sorted(refs)


def _render() -> str:
    ability_hooks = _parse_ability_hooks()
    ability_effects = _load_abilities_csv()
    test_abilities = _load_test_abilities()
    missing_test_abilities = _missing_test_abilities(ability_effects.keys(), test_abilities)

    move_specials = _parse_move_specials()
    moves = _load_moves()
    test_moves = _load_test_moves()

    abilities_by_name: Dict[str, List[AbilityHookInfo]] = {}
    for hook in ability_hooks:
        abilities_by_name.setdefault(hook.ability, []).append(hook)

    moves_by_name: Dict[str, List[MoveSpecialInfo]] = {}
    for info in move_specials:
        moves_by_name.setdefault(info.move.lower(), []).append(info)

    lines: List[str] = []
    lines.append("# Implementation Status")
    lines.append("")
    lines.append("This document enumerates what is **fully implemented** in AutoPTU as of generation time.")
    lines.append("\"Fully implemented\" here means: a behavior has explicit code hooks and a corresponding test reference.")
    lines.append("")

    lines.append("## Abilities (Implemented + Tested)")
    for ability in sorted(test_abilities):
        hooks = abilities_by_name.get(ability, [])
        if ability in missing_test_abilities:
            continue
        refs = _find_ability_refs(ability)
        lines.append(f"- `{ability}`")
        effect = _ascii_clean(ability_effects.get(ability, "").strip())
        if effect:
            lines.append(f"  Effect: {effect}")
        if hooks:
            for hook in hooks:
                lines.append(
                    f"  Code: `{hook.file}` -> `{hook.function}` (phase `{hook.phase}`, holder `{hook.holder}`)"
                )
        if refs:
            lines.append(f"  References: {', '.join(f'`{ref}`' for ref in refs)}")
    lines.append("")

    lines.append("## Moves (Implemented + Tested)")
    for move_name in sorted(test_moves):
        info = moves_by_name.get(move_name)
        if not info:
            continue
        move = moves.get(move_name)
        lines.append(f"- `{move_name}`")
        if move:
            effect = _ascii_clean(str(move.get("effects") or move.get("effects_text") or "").strip())
            if effect:
                lines.append(f"  Effect: {effect}")
        for entry in info:
            lines.append(
                f"  Code: `{entry.file}` -> `{entry.function}` (phase `{entry.phase}`)"
            )
    lines.append("")

    lines.append("## Generic Move Text Resolution")
    lines.append("Moves without explicit handlers rely on `auto_ptu/rules/hooks/move_specials.py`.")
    lines.append("These generic resolvers parse effect text for:")
    lines.append("- Status inflictions with thresholds (e.g., “burns on 17+”)")
    lines.append("- Always-on status inflictions")
    lines.append("- Sleep inflictions")
    lines.append("- Stat raises/lowers with explicit CS amounts")
    lines.append("- Critical hit thresholds and even-roll crits")
    lines.append("- “Cannot miss / always hit”")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    output = ROOT / "IMPLEMENTATION_STATUS.md"
    output.write_text(_render(), encoding="utf-8")


if __name__ == "__main__":
    main()
