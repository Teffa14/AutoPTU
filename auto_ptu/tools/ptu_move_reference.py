"""Compact PTU move-conversion reference and AI output sanitizers."""
from __future__ import annotations

from typing import Any

ALLOWED_AI_KEYWORDS = {
    "Blessing",
    "Dash",
    "Exhaust",
    "Five Strike",
    "Friendly",
    "Interrupt",
    "Pass",
    "Priority",
    "Push",
    "Recoil",
    "Set-Up",
    "Sonic",
    "Smite",
}

VALID_CATEGORIES = {"Physical", "Special", "Status"}
VALID_RANGE_KINDS = {"Self", "Melee", "Ranged", "Burst", "Cone", "Line"}

PTU_CONVERSION_REFERENCE = """\
PTU conversion reference:
- DB is PTU Damage Base, not videogame base power. Keep DB in 0-13.
- Typical power to DB mapping: 20->2, 35->3, 45->4, 55->5, 65->6, 75->7, 85->8, 95->9, 110->10, 125->11, 150->12.
- AC is PTU accuracy check target, not videogame percent. 100 accuracy usually maps to AC 2, 90 to AC 3, 80 to AC 4, 70 to AC 5.
- Prefer canonical PTU range text such as:
  Self
  Melee, 1 Target
  Range 6, 1 Target
  Burst 1
  Burst 2, Allies
  Cone 2
  Line 4
- Do not invent custom keywords. Only use established PTU-style keywords when they are clearly appropriate.
- If a property is better expressed as effect text, write it in effects_text instead of keywords.
- Rewrite videogame descriptions into PTU-native effect text.
- Respect user overrides as fixed constraints.

Examples:
- Aqua Cutter:
  Type Water, Category Physical, DB 7, AC 2, Range Melee, 1 Target, effect text "Critical Hits on 18+."
- Armor Cannon:
  Type Fire, Category Special, DB 11, AC 2, Range Range 6, 1 Target, effect text "After the attack resolves, lower the user's Defense and Special Defense by 1 Combat Stage each."
- Thunder Punch:
  Type Electric, Category Physical, DB 6, AC 2, Range Melee, 1 Target, effect text "Paralyze on 19+."
"""


def sanitize_ai_keywords(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, list):
        raw = [str(part).strip() for part in value if str(part).strip()]
    else:
        raw = []
    seen: set[str] = set()
    out: list[str] = []
    for keyword in raw:
        if keyword not in ALLOWED_AI_KEYWORDS:
            continue
        lower = keyword.lower()
        if lower in seen:
            continue
        seen.add(lower)
        out.append(keyword)
    return out


def sanitize_ai_patch(patch: dict[str, Any], baseline: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    clean = dict(patch)
    notes: list[str] = []

    db = clean.get("db")
    if db is not None:
        try:
            db_int = int(db)
        except (TypeError, ValueError):
            clean.pop("db", None)
            notes.append("Dropped invalid AI DB value.")
        else:
            if db_int < 0 or db_int > 13:
                clean.pop("db", None)
                notes.append("Dropped AI DB outside PTU bounds (0-13).")
            else:
                clean["db"] = db_int

    ac = clean.get("ac")
    if ac is not None:
        try:
            ac_int = int(ac)
        except (TypeError, ValueError):
            clean.pop("ac", None)
            notes.append("Dropped invalid AI AC value.")
        else:
            if ac_int < 1 or ac_int > 8:
                clean.pop("ac", None)
                notes.append("Dropped AI AC outside expected PTU bounds.")
            else:
                clean["ac"] = ac_int

    category = str(clean.get("category") or "").strip()
    if category and category not in VALID_CATEGORIES:
        clean.pop("category", None)
        notes.append("Dropped invalid AI category.")

    range_kind = str(clean.get("range_kind") or "").strip()
    if range_kind and range_kind not in VALID_RANGE_KINDS:
        clean.pop("range_kind", None)
        notes.append("Dropped invalid AI range kind.")

    if "keywords" in clean:
        filtered = sanitize_ai_keywords(clean.get("keywords"))
        if filtered:
            clean["keywords"] = filtered
        else:
            clean["keywords"] = list(baseline.get("keywords") or [])
            notes.append("Dropped non-PTU AI keywords.")

    freq = str(clean.get("freq") or "").strip()
    if freq and len(freq) > 40:
        clean.pop("freq", None)
        notes.append("Dropped malformed AI frequency.")

    effects_text = str(clean.get("effects_text") or "").strip()
    if effects_text:
        clean["effects_text"] = effects_text

    range_text = str(clean.get("range_text") or "").strip()
    if range_text:
        clean["range_text"] = range_text

    return clean, notes

