from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

import py_trees


@dataclass
class BTDecision:
    action: object | None
    reason: str
    source: str
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BTContext:
    actor_id: str
    ai_level: str
    item_action: object | None = None
    emergency_shift: object | None = None
    hybrid_action: object | None = None
    hybrid_info: Dict[str, Any] = field(default_factory=dict)
    mcts_action: object | None = None
    mcts_info: Dict[str, Any] = field(default_factory=dict)
    grapple_action: object | None = None
    grapple_info: Dict[str, Any] = field(default_factory=dict)
    fallback_action: object | None = None
    fallback_info: Dict[str, Any] = field(default_factory=dict)
    decision: BTDecision | None = None
    tree_ascii: str = ""


class _DecisionLeaf(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        *,
        context: BTContext,
        action_getter: Callable[[], object | None],
        reason_getter: Callable[[], str],
        source: str,
        info_getter: Callable[[], Dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(name=name)
        self.context = context
        self.action_getter = action_getter
        self.reason_getter = reason_getter
        self.source = source
        self.info_getter = info_getter or (lambda: {})

    def update(self) -> py_trees.common.Status:
        action = self.action_getter()
        if action is None:
            return py_trees.common.Status.FAILURE
        self.context.decision = BTDecision(
            action=action,
            reason=self.reason_getter(),
            source=self.source,
            info=dict(self.info_getter() or {}),
        )
        return py_trees.common.Status.SUCCESS


def choose_action(context: BTContext) -> tuple[object | None, Dict[str, Any]]:
    root = py_trees.composites.Selector(name="AI Decision", memory=False)
    root.add_children(
        [
            _DecisionLeaf(
                "Use Item",
                context=context,
                action_getter=lambda: context.item_action,
                reason_getter=lambda: "use_item_priority",
                source="bt_item_priority",
            ),
            _DecisionLeaf(
                "Emergency Shift",
                context=context,
                action_getter=lambda: context.emergency_shift,
                reason_getter=lambda: "royale_emergency_shift",
                source="bt_emergency_shift",
            ),
            _DecisionLeaf(
                "MCTS Tactical",
                context=context,
                action_getter=lambda: context.mcts_action,
                reason_getter=lambda: str((context.mcts_info or {}).get("reason") or "mcts"),
                source="bt_mcts",
                info_getter=lambda: context.mcts_info,
            ),
            _DecisionLeaf(
                "Hybrid Policy",
                context=context,
                action_getter=lambda: context.hybrid_action,
                reason_getter=lambda: str((context.hybrid_info or {}).get("reason") or "hybrid"),
                source="bt_hybrid",
                info_getter=lambda: context.hybrid_info,
            ),
            _DecisionLeaf(
                "Grapple Policy",
                context=context,
                action_getter=lambda: context.grapple_action,
                reason_getter=lambda: str((context.grapple_info or {}).get("reason") or "grapple"),
                source="bt_grapple",
                info_getter=lambda: context.grapple_info,
            ),
            _DecisionLeaf(
                "Fallback Rules",
                context=context,
                action_getter=lambda: context.fallback_action,
                reason_getter=lambda: str((context.fallback_info or {}).get("reason") or "fallback"),
                source="bt_fallback",
                info_getter=lambda: context.fallback_info,
            ),
        ]
    )
    tree = py_trees.trees.BehaviourTree(root=root)
    tree.tick()
    try:
        context.tree_ascii = py_trees.display.unicode_tree(root=root, show_status=True)
    except Exception:
        context.tree_ascii = ""
    if context.decision is None:
        return None, {
            "reason": "bt_no_decision",
            "policy": "py_trees",
            "tree_ascii": context.tree_ascii,
        }
    info = dict(context.decision.info or {})
    info.setdefault("policy", "py_trees")
    if context.tree_ascii:
        info.setdefault("tree_ascii", context.tree_ascii)
    return context.decision.action, {
        "reason": context.decision.reason,
        "source": context.decision.source,
        **info,
    }

