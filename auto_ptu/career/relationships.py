from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from .models import CareerRun


def _bond_value(value: object) -> int:
    """Return a safe non-negative relationship bond from persisted input."""
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def calculate_relationship_effects(relationships: Dict[str, int]) -> Dict[str, Any]:
    """Translate social bonds into small, explicit career advantages.

    Relationships are intentionally capped: they should make a contact matter
    without replacing roster quality, preparation, or match performance.
    Rivalry intensity is continuity information only and never grants a career
    or combat modifier. Invalid persisted bond values are ignored instead of
    breaking a career load.
    """
    positive = sorted(
        (
            (str(name).strip(), bond)
            for name, value in relationships.items()
            if str(name).strip() and (bond := _bond_value(value)) > 0
        ),
        key=lambda entry: (-entry[1], entry[0]),
    )
    best_name, best_value = positive[0] if positive else ("", 0)
    active_contacts = sum(1 for _, value in positive if value >= 2)
    support_contacts = 0
    contact_effects = []
    support_value = 0
    rival_scouting_bonus = 0
    mentor_training_bonus = 0
    owner_recovery_bonus = 0
    owner_guard = False
    for name, value in positive:
        parts = name.split(" · ")
        role = parts[1].strip().lower() if len(parts) > 1 else "contact"
        tier = "confidant" if value >= 6 else "ally" if value >= 4 else "active" if value >= 2 else "known"
        if role == "mentor":
            amount = min(2, value // 3)
            mentor_training_bonus = max(mentor_training_bonus, amount)
            benefit = "partner_training"
        elif role == "rival":
            # Rivalry may drive callbacks and scouting context, but intensity
            # cannot alter PTU levels, preparation, recovery, or contracts.
            amount = 0
            benefit = "rival_read"
        elif role == "owner":
            amount = min(3, value // 2)
            owner_recovery_bonus = max(owner_recovery_bonus, amount)
            owner_guard = owner_guard or value >= 5
            benefit = "club_protection"
        else:
            amount = min(2, value // 3)
            benefit = "preparation"
        if role != "rival":
            support_value = max(support_value, value)
            if value >= 2:
                support_contacts += 1
        contact_effects.append({
            "name": name, "role": role, "bond": value, "tier": tier,
            "benefit": benefit, "amount": amount,
            "next_unlock": 2 if value < 2 else 4 if value < 4 else 6 if value < 6 else None,
        })
    return {
        "best_contact": best_name,
        "best_value": best_value,
        "active_contacts": active_contacts,
        "home_level_bonus": min(2, support_value // 2),
        "season_recovery": min(3, support_contacts),
        "contract_guard": owner_guard or support_value >= 6,
        "mentor_training_bonus": mentor_training_bonus,
        "rival_scouting_bonus": rival_scouting_bonus,
        "owner_recovery_bonus": owner_recovery_bonus,
        "contact_effects": contact_effects,
    }


def refresh_relationship_effects(run: "CareerRun") -> Dict[str, Any]:
    effects = calculate_relationship_effects(run.relationships)
    run.relationship_effects = effects
    return effects
