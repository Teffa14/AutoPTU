"""Item hook registry for modular item behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import importlib
import pkgutil


ItemHook = Callable[["ItemHookContext"], None]


@dataclass
class ItemHookContext:
    battle: object
    events: List[dict]
    holder_id: str
    holder: object
    attacker_id: str
    attacker: object
    move: object
    result: Dict[str, object]
    phase: str
    target_id: Optional[str] = None
    target: Optional[object] = None
    attack_context: Optional[object] = None
    damage_dealt: Optional[int] = None
    has_contact: Optional[bool] = None


_ITEM_HOOKS: Dict[str, List[ItemHook]] = {}
_ITEM_HOOKS_LOADED = False


def ensure_item_hooks_registered() -> None:
    global _ITEM_HOOKS_LOADED
    if _ITEM_HOOKS_LOADED:
        return
    package_name = __name__.rsplit(".", 1)[0] + ".item_effects"
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        _ITEM_HOOKS_LOADED = True
        return
    for module_info in pkgutil.iter_modules(package.__path__, package_name + "."):
        importlib.import_module(module_info.name)
    _ITEM_HOOKS_LOADED = True


def register_item_hook(phase: str) -> Callable[[ItemHook], ItemHook]:
    def decorator(func: ItemHook) -> ItemHook:
        _ITEM_HOOKS.setdefault(phase, []).append(func)
        return func

    return decorator


def apply_item_hooks(phase: str, ctx: ItemHookContext) -> List[dict]:
    ensure_item_hooks_registered()
    hooks = _ITEM_HOOKS.get(phase, [])
    if not hooks:
        return []
    start = len(ctx.events)
    for func in hooks:
        func(ctx)
    return ctx.events[start:]
