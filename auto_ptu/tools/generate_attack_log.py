"""Utility to regenerate ATTACK_LOG.md from the compiled move data."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Tuple

from auto_ptu.rules.move_traits import (
    forced_movement_instruction,
    has_range_keyword,
    is_setup_move,
    recoil_fraction,
    recoil_fraction_label,
    strike_count,
)

ROOT = Path(__file__).resolve().parents[2]
MOVES_PATH = ROOT / "auto_ptu" / "data" / "compiled" / "moves.json"
ATTACK_LOG = ROOT / "ATTACK_LOG.md"
OVERRIDES_PATH = ROOT / "auto_ptu" / "data" / "attack_status_overrides.json"
OVERRIDES: dict[str, dict] = {}
if OVERRIDES_PATH.exists():
    raw = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    for name, payload in raw.items():
        OVERRIDES[name.strip().lower()] = payload or {}


HOOK_SOURCES = (
    ROOT / "auto_ptu" / "rules" / "battle_state.py",
    ROOT / "auto_ptu" / "rules" / "calculations.py",
)


def _discover_hooked_moves() -> set[str]:
    """Best-effort scan for bespoke move hooks in the rules engine."""

    discovered: set[str] = set()
    pattern_equals = re.compile(r"""move_name\s*==\s*(['"])(?P<name>(?:(?!\1).)+)\1""")
    pattern_in = re.compile(r"""move_name\s*in\s*\{(?P<body>[^}]+)\}""")
    pattern_quoted = re.compile(r"""(['"])(?P<name>(?:(?!\1).)+)\1""")
    pattern_find_known = re.compile(
        r"""_find_known_move\([^,]+,\s*(['"])(?P<name>[^'"]+)\1\)"""
    )

    for path in HOOK_SOURCES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern_equals.finditer(text):
            discovered.add(match.group("name").strip().lower())
        for match in pattern_in.finditer(text):
            body = match.group("body")
            for inner in pattern_quoted.finditer(body):
                discovered.add(inner.group("name").strip().lower())
        for match in pattern_find_known.finditer(text):
            discovered.add(match.group("name").strip().lower())
    return discovered


HOOKED_MOVES = _discover_hooked_moves()


def _coerce_effects_text(move: dict) -> str:
    """Return normalized effects text for keyword inspection."""
    raw = move.get("effects") or move.get("effects_text") or move.get("description") or ""
    return str(raw).strip().lower()


def _move_status(move: dict) -> Tuple[str, str]:
    """Return (status, notes)."""
    tags = []
    move_name = (move.get("name") or "").strip().lower()
    if move_name in HOOKED_MOVES:
        tags.append("Bespoke move hook")
    if is_setup_move(move):
        tags.append("Set-Up/Resolution")
    strike = strike_count(move)
    if strike:
        tags.append(f"{strike}-Strike multi-hit")
    recoil = recoil_fraction(move)
    if recoil:
        tags.append(f"Recoil {recoil_fraction_label(recoil)} self-damage")
    forced = forced_movement_instruction(move)
    if forced:
        distance = forced.get("distance", 1)
        tags.append(f"{forced.get('kind', '').title()} {distance} forced movement")
    effects_text = _coerce_effects_text(move).lower()
    if "cannot miss" in effects_text:
        tags.append("Always-hit accuracy")
    if move_name == "aeroblast":
        tags.append("Critical on even roll accuracy")
    if move_name == "acid":
        tags.append("10% chance to lower SP. DEF by -1 stage for 5 activations on hit")
    if move_name == "after you":
        tags.append("Inserts the target right after the user's turn via initiative order")
    if move_name == "acid spray":
        tags.append("Lowers SP. DEF by -2 stages for 5 activations when it hits")
    if move_name == "acrobatics":
        tags.append("Damage Base becomes 11 (3d10+10/27) when the user has no held item")
    if move_name == "acupressure":
        tags.append(
            "Roll 1d8: 1-6 boosts Attack/Defense/S. Atk/S. Def/Speed/Accuracy by +2 CS, 8 picks the lowest stage"
        )
    if move_name == "agility":
        tags.append("Raises Speed by +2 CS")
    if move_name == "air cutter":
        tags.append("Auto-critical on accuracy rolls of 18+")
    if move_name == "air slash":
        tags.append("Roll of 15+ causes the target to flinch")
    if move_name == "night slash":
        tags.append("Critical hit on accuracy rolls of 18+")
    if move_name == "nightmare":
        tags.append("Applies Bad Sleep to sleeping targets")
    if move_name == "no retreat":
        tags.append("Raises all stats by +1 CS and prevents switching out")
    if move_name == "noble roar":
        tags.append("Lowers Attack and Special Attack by -1 CS on hit")
    if move_name == "nuzzle":
        tags.append("Paralyzes the target on hit")
    if move_name == "ally switch":
        tags.append("Swaps the user and target positions on resolve")
    if has_range_keyword(move, "smite"):
        tags.append("Smite miss-damage support")
    if tags:
        note = " + ".join(tags) + " supported by autonomous engine."
        status = "done"
    else:
        status = "pending"
        note = "Hook pending; covered only by baseline attack pipeline."
    override = OVERRIDES.get(move_name)
    if override:
        status = override.get("status", status)
        note = override.get("note", note)
    return status, note


def main() -> None:
    moves = json.loads(MOVES_PATH.read_text(encoding="utf-8"))
    moves.sort(key=lambda entry: (entry.get("name") or "").lower())
    total = len(moves)
    implemented = 0
    rows: list[Tuple[str, str, str, str, str]] = []
    for idx, move in enumerate(moves, 1):
        name = (move.get("name") or "Unknown").strip().replace("`", "'")
        category = (move.get("category") or "Special").strip()
        status, notes = _move_status(move)
        if status == "done":
            implemented += 1
        rows.append((str(idx), name, category, status, notes))
    pending = total - implemented
    lines = [
        "# Attack Implementation Log",
        "",
        "Master list of PTU moves sourced from `auto_ptu/data/compiled/moves.json`. "
        "This mirrors the Foundry data so we can track which attacks have bespoke "
        "hooks in our autonomous engine.",
        "",
        f"- **Total moves**: {total}",
        f"- **Implemented**: {implemented}",
        f"- **Pending**: {pending}",
        "",
        "Status values: `pending` = no dedicated hook yet, `in progress` = actively "
        "implementing, `done` = code + tests + scenario coverage exist. The base attack "
        "pipeline already handles core damage math for every move; this table is for "
        "move-specific keywords/effects.",
        "",
        "| # | Move | Category | Status | Notes |",
        "|---|------|----------|--------|-------|",
    ]
    for idx, name, category, status, notes in rows:
        lines.append(f"| {idx} | `{name}` | {category} | {status} | {notes} |")
    ATTACK_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
