"""Hook registries for move, item, and ability extensions."""

from .ability_hooks import (
    AbilityHookContext,
    apply_ability_hooks,
    ensure_ability_hooks_registered,
    register_ability_hook,
)
from .combat_stage_hooks import (
    CombatStageHookContext,
    apply_combat_stage_hooks,
    ensure_combat_stage_hooks_registered,
    register_combat_stage_hook,
)
from .item_hooks import (
    ItemHookContext,
    apply_item_hooks,
    ensure_item_hooks_registered,
    register_item_hook,
)
from .perk_hooks import (
    PerkHookContext,
    apply_perk_hooks,
    ensure_perk_hooks_registered,
    register_perk_hook,
)
from .phase_hooks import (
    PhaseHookContext,
    apply_phase_hooks,
    ensure_phase_hooks_registered,
    register_phase_hook,
)

_ALL_HOOKS_REGISTERED = False


def register_all_hooks() -> None:
    """Load and register all hook modules exactly once."""
    global _ALL_HOOKS_REGISTERED
    if _ALL_HOOKS_REGISTERED:
        return
    ensure_ability_hooks_registered()
    ensure_combat_stage_hooks_registered()
    ensure_item_hooks_registered()
    ensure_perk_hooks_registered()
    ensure_phase_hooks_registered()
    _ALL_HOOKS_REGISTERED = True

__all__ = [
    "AbilityHookContext",
    "apply_ability_hooks",
    "register_ability_hook",
    "CombatStageHookContext",
    "apply_combat_stage_hooks",
    "register_combat_stage_hook",
    "ItemHookContext",
    "apply_item_hooks",
    "register_item_hook",
    "PerkHookContext",
    "apply_perk_hooks",
    "register_perk_hook",
    "PhaseHookContext",
    "apply_phase_hooks",
    "register_phase_hook",
    "register_all_hooks",
]
