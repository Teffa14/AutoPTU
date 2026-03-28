"""Shared ability constants."""

from typing import Dict

COLOR_THEORY_COLORS: Dict[int, str] = {
    1: "Red",
    2: "Red-Orange",
    3: "Orange",
    4: "Yellow-Orange",
    5: "Yellow",
    6: "Yellow-Green",
    7: "Green",
    8: "Blue-Green",
    9: "Blue",
    10: "Blue-Violet",
    11: "Violet",
    12: "Red-Violet",
}

COLOR_THEORY_STAT_KEYS: Dict[str, str] = {
    "Red": "atk",
    "Orange": "def",
    "Yellow": "spatk",
    "Green": "spdef",
    "Blue": "spd",
    "Violet": "hp",
}
