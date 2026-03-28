"""Ability hook registry for modular ability behaviors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import importlib
import pkgutil


AbilityHook = Callable[["AbilityHookContext"], None]


@dataclass
class AbilityHookContext:
    battle: object
    attacker_id: str
    attacker: object
    defender_id: Optional[str]
    defender: Optional[object]
    move: MoveSpec
    effective_move: MoveSpec
    events: List[dict]
    phase: str
    result: Optional[dict] = None
    hit: Optional[bool] = None
    damage: Optional[int] = None
    defender_fainted: Optional[bool] = None


_ABILITY_HOOKS: Dict[str, List[Tuple[Optional[str], str, AbilityHook]]] = {}
_ABILITY_HOOKS_LOADED = False


def ensure_ability_hooks_registered() -> None:
    global _ABILITY_HOOKS_LOADED
    if _ABILITY_HOOKS_LOADED:
        return
    package_name = __name__.rsplit(".", 1)[0] + ".abilities"
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        _ABILITY_HOOKS_LOADED = True
        return
    for module_info in pkgutil.iter_modules(package.__path__, package_name + "."):
        importlib.import_module(module_info.name)
    _ABILITY_HOOKS_LOADED = True


def _load_ability_hooks() -> None:
    """Backward-compatible alias expected by legacy tests/tools."""
    ensure_ability_hooks_registered()


def register_ability_hook(
    *, phase: str, ability: Optional[str] = None, holder: str = "attacker"
) -> Callable[[AbilityHook], AbilityHook]:
    def decorator(func: AbilityHook) -> AbilityHook:
        _ABILITY_HOOKS.setdefault(phase, []).append(
            (ability.lower() if ability else None, holder, func)
        )
        return func

    return decorator


def apply_ability_hooks(phase: str, ctx: AbilityHookContext) -> List[dict]:
    ensure_ability_hooks_registered()
    hooks = _ABILITY_HOOKS.get(phase, [])
    if not hooks:
        return []
    start = len(ctx.events)
    ignore_defender = False
    if ctx.attacker is not None and getattr(ctx.attacker, "has_ability", None):
        if ctx.attacker.has_ability("Mold Breaker"):
            ignore_defender = True
    suppress_for_attacker = False
    suppress_for_defender = False
    battle = ctx.battle
    if battle is not None and getattr(battle, "abilities_suppressed_for", None):
        if ctx.attacker_id:
            suppress_for_attacker = battle.abilities_suppressed_for(ctx.attacker_id)
        if ctx.defender_id:
            suppress_for_defender = battle.abilities_suppressed_for(ctx.defender_id)
    for ability, holder, func in hooks:
        if ability:
            if holder == "defender":
                if ignore_defender:
                    continue
                if suppress_for_defender:
                    continue
                if not ctx.defender or not getattr(ctx.defender, "has_ability", None):
                    continue
                if not ctx.defender.has_ability(ability):
                    continue
            else:
                if suppress_for_attacker:
                    continue
                if not ctx.attacker or not getattr(ctx.attacker, "has_ability", None):
                    continue
                if not ctx.attacker.has_ability(ability):
                    continue
        func(ctx)
    return ctx.events[start:]
