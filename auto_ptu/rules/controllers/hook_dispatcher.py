"""Registry execution boundary for abilities, items, perks, and move specials.

This is a placeholder boundary for extracting hook dispatching from BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..battle_state import BattleState
from ..hooks import (
    apply_ability_hooks,
    apply_combat_stage_hooks,
    apply_item_hooks,
    apply_perk_hooks,
    apply_phase_hooks,
)


@dataclass
class HookDispatcher:
    battle: BattleState

    def apply_phase_hooks(self, phase, ctx):
        return apply_phase_hooks(phase, ctx)

    def apply_perk_hooks(self, phase, ctx):
        return apply_perk_hooks(phase, ctx)

    def apply_item_hooks(self, hook_name, ctx):
        return apply_item_hooks(hook_name, ctx)

    def apply_ability_hooks(self, hook_name, ctx):
        return apply_ability_hooks(hook_name, ctx)

    def apply_combat_stage_hooks(self, hook_name, ctx):
        return apply_combat_stage_hooks(hook_name, ctx)
