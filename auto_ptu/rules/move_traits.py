"""Helpers for inferring Foundry-style move traits from PTU metadata."""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Optional

from ..data_models import MoveSpec

_STRIKE_TOKEN_MAP = {
    "two": 2,
    "double": 2,
    "triple": 3,
    "three": 3,
    "quadruple": 4,
    "four": 4,
    "quintuple": 5,
    "five": 5,
    "sextuple": 6,
    "six": 6,
    "septuple": 7,
    "seven": 7,
    "octuple": 8,
    "eight": 8,
    "nonuple": 9,
    "nine": 9,
    "decuple": 10,
    "ten": 10,
}
_STRIKE_PATTERN = re.compile(
    r"\b(?P<token>(?:\d+|double|triple|quadruple|quintuple|sextuple|septuple|"  
    r"octuple|nonuple|decuple|two|three|four|five|six|seven|eight|nine|ten))"   
    r"[-\s]*strike\b",
    re.IGNORECASE,
)
_RECOIL_PATTERN = re.compile(r"recoil\s+(?P<num>\d+)(?:\s*/\s*(?P<den>\d+))?", re.IGNORECASE)
_CRASH_PATTERN = re.compile(
    r"\bif\b[^.]*\bmiss(?:es|ed)?\b[^.]*\blose(?:s|d)?\b[^.]*hit points\b",
    re.IGNORECASE,
)
_CONTACT_MOVES_PATH = Path(__file__).resolve().parents[1] / "data" / "compiled" / "contact_moves.json"
_CONTACT_MOVE_CACHE: set[str] | None = None
_PUNCH_MOVES_PATH = Path(__file__).resolve().parents[1] / "data" / "compiled" / "punch_moves.json"
_PUNCH_MOVE_CACHE: set[str] | None = None


def _coerce_range_text(move: MoveSpec | dict[str, Any] | None) -> str:
    if move is None:
        return ""
    if isinstance(move, MoveSpec):
        return (move.range_text or move.range_kind or "").strip()
    for key in ("range_text", "range_detail", "range_label", "range"):
        raw = move.get(key) if isinstance(move, dict) else None
        if raw:
            return str(raw).strip()
    return ""


def _coerce_effects_text(move: MoveSpec | dict[str, Any] | None) -> str:
    if move is None:
        return ""
    if isinstance(move, MoveSpec):
        return (move.effects_text or "").strip()
    for key in ("effects_text", "effects", "text", "description"):
        raw = move.get(key) if isinstance(move, dict) else None
        if raw:
            return str(raw).strip()
    return ""


def _strike_token_value(token: str) -> Optional[int]:
    normalized = token.lower()
    if normalized.isdigit():
        try:
            value = int(normalized)
        except ValueError:
            return None
        return value if value >= 2 else None
    return _STRIKE_TOKEN_MAP.get(normalized)


def is_setup_move(move: MoveSpec | dict[str, Any] | None) -> bool:
    """Return True if the move references a Set-Up/Resolution effect."""
    range_text = _coerce_range_text(move).lower()
    effects_text = _coerce_effects_text(move).lower()
    combined = f"{range_text} {effects_text}"
    return any(token in combined for token in ("set-up", "setup", "set up"))


def strike_count(move: MoveSpec | dict[str, Any] | None) -> Optional[int]:
    """Return the max number of hits for an X-Strike move, if any."""
    search_space = f"{_coerce_range_text(move)} {_coerce_effects_text(move)}"
    match = _STRIKE_PATTERN.search(search_space)
    if not match:
        return None
    value = _strike_token_value(match.group("token"))
    if value is None or value < 2:
        return None
    return value


def recoil_fraction(move: MoveSpec | dict[str, Any] | None) -> Optional[Fraction]:
    """Return the recoil fraction (e.g., 1/3) if present."""
    search_space = f"{_coerce_range_text(move)} {_coerce_effects_text(move)}"
    match = _RECOIL_PATTERN.search(search_space)
    if not match:
        return None
    try:
        numerator = int(match.group("num"))
    except (TypeError, ValueError):
        return None
    denominator_raw = match.group("den")
    denominator = int(denominator_raw) if denominator_raw else 1
    if numerator <= 0 or denominator <= 0:
        return None
    return Fraction(numerator, denominator)


def recoil_fraction_label(value: Fraction) -> str:
    """Format the recoil fraction for logs."""
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def move_has_crash_trait(move: MoveSpec | dict[str, Any] | None) -> bool:
    """Return True if the move has a crash-on-miss penalty."""
    if move is None:
        return False
    if isinstance(move, MoveSpec):
        keywords = [str(keyword).lower() for keyword in move.keywords]
    elif isinstance(move, dict):
        keywords = [str(keyword).lower() for keyword in move.get("keywords", [])]
    else:
        keywords = []
    if any(keyword.startswith("crash") or keyword == "crash" for keyword in keywords):
        return True
    text = f"{_coerce_range_text(move)} {_coerce_effects_text(move)}".lower()
    if "crash" in text:
        return True
    return bool(_CRASH_PATTERN.search(text))


def forced_movement_instruction(move: MoveSpec | dict[str, Any] | None) -> Optional[dict]:
    """Return forced movement details if the move pushes or pulls."""
    if move is None:
        return None
    desc = _coerce_effects_text(move).lower()
    if isinstance(move, MoveSpec):
        keywords = [str(keyword).lower() for keyword in move.keywords]
    elif isinstance(move, dict):
        keywords = [str(keyword).lower() for keyword in move.get("keywords", [])]
    else:
        keywords = []
    for kind in ("push", "pull"):
        if kind in keywords or kind in desc:
            distance = 1
            match = re.search(rf"{kind}\D*(\d+)", desc)
            if match:
                try:
                    distance = max(1, int(match.group(1)))
                except ValueError:
                    distance = 1
            return {"kind": kind, "distance": distance}
    return None


def move_has_keyword(move: MoveSpec | dict[str, Any] | None, keyword: str) -> bool:
    """Return True if the move lists the requested keyword."""
    if move is None or not keyword:
        return False
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    if isinstance(move, MoveSpec):
        keywords = move.keywords
    elif isinstance(move, dict):
        keywords = move.get("keywords", [])
    else:
        keywords = []
    for entry in keywords:
        if not entry:
            continue
        if str(entry).strip().lower() == normalized:
            return True
    return False


def has_range_keyword(move: MoveSpec | dict[str, Any] | None, keyword: str) -> bool:
    """Return True if the range text lists the given keyword."""
    text = _coerce_range_text(move).lower()
    return keyword.lower() in text


def _load_contact_moves() -> set[str]:
    global _CONTACT_MOVE_CACHE
    if _CONTACT_MOVE_CACHE is not None:
        return _CONTACT_MOVE_CACHE
    if _CONTACT_MOVES_PATH.exists():
        try:
            data = json.loads(_CONTACT_MOVES_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = []
    else:
        data = []
    normalized = {str(entry).strip().lower() for entry in data if entry}
    _CONTACT_MOVE_CACHE = normalized
    return normalized


def _load_punch_moves() -> set[str]:
    global _PUNCH_MOVE_CACHE
    if _PUNCH_MOVE_CACHE is not None:
        return _PUNCH_MOVE_CACHE
    if _PUNCH_MOVES_PATH.exists():
        try:
            data = json.loads(_PUNCH_MOVES_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = []
    else:
        data = []
    normalized = {str(entry).strip().lower() for entry in data if entry}
    _PUNCH_MOVE_CACHE = normalized
    return normalized


def move_has_contact_trait(move: MoveSpec | dict[str, Any] | None) -> bool:
    name = ""
    if isinstance(move, MoveSpec):
        name = move.name or ""
    elif isinstance(move, dict):
        name = move.get("name", "") or ""
    normalized = "".join(ch for ch in name.lower() if ch.isalnum())
    if not normalized:
        return False
    if normalized in _load_contact_moves():
        return True
    if isinstance(move, MoveSpec):
        if move_has_keyword(move, "contact"):
            return True
        range_kind = (move.range_kind or move.target_kind or "").lower()
        if "melee" in range_kind:
            return True
        if "melee" in _coerce_range_text(move).lower():
            return True
    elif isinstance(move, dict):
        keywords = [str(keyword).strip().lower() for keyword in move.get("keywords", [])]
        if "contact" in keywords:
            return True
        range_kind = str(
            move.get("range_kind") or move.get("range") or move.get("target_kind") or ""
        ).lower()
        if "melee" in range_kind:
            return True
        if "melee" in _coerce_range_text(move).lower():
            return True
    return False


def move_has_punch_trait(move: MoveSpec | dict[str, Any] | None) -> bool:
    name = ""
    if isinstance(move, MoveSpec):
        name = move.name or ""
    elif isinstance(move, dict):
        name = move.get("name", "") or ""
    normalized = "".join(ch for ch in name.lower() if ch.isalnum())
    if not normalized:
        return False
    return normalized in _load_punch_moves()
