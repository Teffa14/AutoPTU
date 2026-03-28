"""Phase hook registry for ability-driven start/end/command effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import importlib
import pkgutil


PhaseHook = Callable[["PhaseHookContext"], None]


@dataclass
class PhaseHookContext:
    battle: object
    actor_id: str
    pokemon: object
    phase: str
    events: List[dict]
    confusion_status_names: set
    status_afflictions: set


_PHASE_HOOKS: Dict[str, List[Tuple[Optional[str], PhaseHook]]] = {}
_PHASE_HOOKS_LOADED = False


def ensure_phase_hooks_registered() -> None:
    global _PHASE_HOOKS_LOADED
    if _PHASE_HOOKS_LOADED:
        return
    package_name = __name__.rsplit(".", 1)[0] + ".abilities"
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        _PHASE_HOOKS_LOADED = True
        return
    for module_info in pkgutil.iter_modules(package.__path__, package_name + "."):
        importlib.import_module(module_info.name)
    _PHASE_HOOKS_LOADED = True


def register_phase_hook(phase: str, ability: Optional[str] = None) -> Callable[[PhaseHook], PhaseHook]:
    def decorator(func: PhaseHook) -> PhaseHook:
        _PHASE_HOOKS.setdefault(phase, []).append(
            (ability.lower() if ability else None, func)
        )
        return func

    return decorator


def apply_phase_hooks(phase: object, ctx: PhaseHookContext) -> List[dict]:
    ensure_phase_hooks_registered()
    phase_value = phase.value if hasattr(phase, "value") else str(phase).lower()
    ctx.phase = phase_value
    hooks = _PHASE_HOOKS.get(phase_value, [])
    if not hooks:
        return []
    start = len(ctx.events)
    for ability, func in hooks:
        if ability:
            if not getattr(ctx.pokemon, "has_ability", None):
                continue
            if not ctx.pokemon.has_ability(ability):
                continue
        func(ctx)
    return ctx.events[start:]
