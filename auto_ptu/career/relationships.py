from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .models import CareerRun


def calculate_relationship_effects(relationships: Dict[str, int]) -> Dict[str, Any]:
    """Translate social bonds into small, explicit career advantages.

    Relationships are intentionally capped: they should make a contact matter
    without replacing roster quality, PTU preparation, or match performance.
    """
    positive = sorted(
        ((str(name), max(0, int(value))) for name, value in relationships.items() if int(value) > 0),
        key=lambda entry: (-entry[1], entry[0]),
    )
    best_name, best_value = positive[0] if positive else ("", 0)
    active_contacts = sum(1 for _, value in positive if value >= 2)
    return {
        "best_contact": best_name,
        "best_value": best_value,
        "active_contacts": active_contacts,
        "home_level_bonus": min(2, best_value // 2),
        "season_recovery": min(3, active_contacts),
        "contract_guard": best_value >= 6,
    }


def refresh_relationship_effects(run: "CareerRun") -> Dict[str, Any]:
    effects = calculate_relationship_effects(run.relationships)
    run.relationship_effects = effects
    return effects
