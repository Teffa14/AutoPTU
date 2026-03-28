"""Perk hook registry for modular perk behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import importlib
import pkgutil


PerkHook = Callable[["PerkHookContext"], None]


@dataclass
class PerkHookContext:
    battle: object
    events: List[dict]
    actor_id: str
    actor: object
    phase: str


_PERK_HOOKS: Dict[str, List[Tuple[Optional[str], PerkHook]]] = {}
_PERK_HOOKS_LOADED = False


def ensure_perk_hooks_registered() -> None:
    global _PERK_HOOKS_LOADED
    if _PERK_HOOKS_LOADED:
        return
    package_name = __name__.rsplit(".", 1)[0] + ".perk_effects"
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        _PERK_HOOKS_LOADED = True
        return
    for module_info in pkgutil.iter_modules(package.__path__, package_name + "."):
        importlib.import_module(module_info.name)
    _PERK_HOOKS_LOADED = True


def register_perk_hook(
    phase: str, perk: Optional[str] = None
) -> Callable[[PerkHook], PerkHook]:
    def decorator(func: PerkHook) -> PerkHook:
        _PERK_HOOKS.setdefault(phase, []).append(
            (perk.lower() if perk else None, func)
        )
        return func

    return decorator


def apply_perk_hooks(phase: str, ctx: PerkHookContext) -> List[dict]:
    ensure_perk_hooks_registered()
    hooks = _PERK_HOOKS.get(phase, [])
    if not hooks:
        return []
    start = len(ctx.events)
    for perk, func in hooks:
        if perk:
            if not getattr(ctx.actor, "has_trainer_feature", None):
                continue
            if not ctx.actor.has_trainer_feature(perk):
                continue
        func(ctx)
    return ctx.events[start:]
