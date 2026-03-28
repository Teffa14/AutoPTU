"""Combat stage hook registry for reactive ability behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import importlib
import pkgutil


CombatStageHook = Callable[["CombatStageHookContext"], None]


@dataclass
class CombatStageHookContext:
    battle: object
    events: List[dict]
    attacker_id: str
    target_id: str
    move: object
    target: object
    stat: str
    delta: int
    applied_delta: int
    effect: str
    description: str
    roll: int | None
    skip_minus_swsh: bool
    skip_plus_swsh: bool


_COMBAT_STAGE_HOOKS: Dict[str, List[CombatStageHook]] = {}
_COMBAT_STAGE_HOOKS_LOADED = False


def ensure_combat_stage_hooks_registered() -> None:
    global _COMBAT_STAGE_HOOKS_LOADED
    if _COMBAT_STAGE_HOOKS_LOADED:
        return
    package_name = __name__.rsplit(".", 1)[0] + ".abilities"
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        _COMBAT_STAGE_HOOKS_LOADED = True
        return
    for module_info in pkgutil.iter_modules(package.__path__, package_name + "."):
        importlib.import_module(module_info.name)
    _COMBAT_STAGE_HOOKS_LOADED = True


def register_combat_stage_hook(phase: str) -> Callable[[CombatStageHook], CombatStageHook]:
    def decorator(func: CombatStageHook) -> CombatStageHook:
        _COMBAT_STAGE_HOOKS.setdefault(phase, []).append(func)
        return func

    return decorator


def apply_combat_stage_hooks(phase: str, ctx: CombatStageHookContext) -> List[dict]:
    ensure_combat_stage_hooks_registered()
    hooks = _COMBAT_STAGE_HOOKS.get(phase, [])
    if not hooks:
        return []
    start = len(ctx.events)
    for func in hooks:
        func(ctx)
    return ctx.events[start:]
