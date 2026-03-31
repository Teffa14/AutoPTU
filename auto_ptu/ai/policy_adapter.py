from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PolicyDecision:
    action: object | None
    reason: str
    source: str
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyAdapterContext:
    battle: Any
    actor_id: str
    ai_level: str
    config: Any
    profile_store: Any
    candidates: List[object]
    helper: Dict[str, Callable[..., Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


PolicyAdapter = Callable[[PolicyAdapterContext], Optional[PolicyDecision]]

_POLICY_ADAPTERS: Dict[str, PolicyAdapter] = {}
_ACTIVE_POLICY_ADAPTER = "hybrid_rules"


def register_policy_adapter(name: str, adapter: PolicyAdapter) -> None:
    key = str(name or "").strip().lower()
    if not key:
        raise ValueError("Policy adapter name is required")
    if not callable(adapter):
        raise TypeError("Policy adapter must be callable")
    _POLICY_ADAPTERS[key] = adapter


def unregister_policy_adapter(name: str) -> None:
    key = str(name or "").strip().lower()
    if not key:
        return
    _POLICY_ADAPTERS.pop(key, None)


def get_policy_adapter(name: str) -> Optional[PolicyAdapter]:
    key = str(name or "").strip().lower()
    if not key:
        return None
    return _POLICY_ADAPTERS.get(key)


def list_policy_adapters() -> List[str]:
    return sorted(_POLICY_ADAPTERS.keys())


def set_active_policy_adapter(name: str) -> str:
    global _ACTIVE_POLICY_ADAPTER
    key = str(name or "").strip().lower()
    if not key:
        raise ValueError("Policy adapter name is required")
    if key not in _POLICY_ADAPTERS:
        raise ValueError(f"Unknown policy adapter: {key}")
    _ACTIVE_POLICY_ADAPTER = key
    return _ACTIVE_POLICY_ADAPTER


def get_active_policy_adapter() -> str:
    return _ACTIVE_POLICY_ADAPTER
