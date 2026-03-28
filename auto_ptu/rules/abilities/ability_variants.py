"""Helpers for handling ability variants such as Errata entries."""

from __future__ import annotations

from typing import Iterable


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


_EQUIVALENT_ABILITIES = {
    "huge power / pure power [errata]": {
        "huge power / pure power [errata]",
        "huge power [errata]",
        "pure power [errata]",
    },
    "huge power [errata]": {
        "huge power [errata]",
        "huge power / pure power [errata]",
    },
    "pure power [errata]": {
        "pure power [errata]",
        "huge power / pure power [errata]",
    },
}


def has_ability_exact(pokemon: object, name: str) -> bool:
    target = _normalize(name)
    if not target:
        return False
    ability_names = getattr(pokemon, "ability_names", None)
    if ability_names is None:
        return False
    for ability in ability_names():
        normalized = _normalize(str(ability))
        if normalized == target:
            return True
        equivalents = _EQUIVALENT_ABILITIES.get(normalized)
        if equivalents and target in equivalents:
            return True
    return False


def has_errata(pokemon: object, base_name: str) -> bool:
    return has_ability_exact(pokemon, f"{base_name} [Errata]")


def ability_variant_name(base_name: str, variant: str = "Errata") -> str:
    return f"{base_name} [{variant}]"
