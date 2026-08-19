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
                reason_getter=lambda: "emergency_shift",
                source="bt_emergency_shift",
            ),
            _DecisionLeaf(
                "Hybrid Tactical",
                context=context,
                action_getter=lambda: context.hybrid_action,
                reason_getter=lambda: "hybrid_tactical_choice",
                source="bt_hybrid",
                info_getter=lambda: context.hybrid_info,
            ),
            _DecisionLeaf(
                "MCTS Tactical",
                context=context,
                action_getter=lambda: context.mcts_action,
                reason_getter=lambda: "mcts_tactical_choice",
                source="bt_mcts",
                info_getter=lambda: context.mcts_info,
            ),
            _DecisionLeaf(
                "Grapple",
                context=context,
                action_getter=lambda: context.grapple_action,
                reason_getter=lambda: "grapple_control",
                source="bt_grapple",
                info_getter=lambda: context.grapple_info,
            ),
            _DecisionLeaf(
                "Fallback",
                context=context,
                action_getter=lambda: context.fallback_action,
                reason_getter=lambda: "fallback",
                source="bt_fallback",
                info_getter=lambda: context.fallback_info,
            ),
        ]
    )
    tree = py_trees.trees.BehaviourTree(root)
    tree.tick()
    try:
        context.tree_ascii = py_trees.display.unicode_tree(root, show_status=True)
    except Exception:
        context.tree_ascii = ""
    decision = context.decision
    if decision is None:
        return None, {"source": "bt_no_action", "tree": context.tree_ascii}
    info = dict(decision.info)
    info.update({"reason": decision.reason, "source": decision.source, "tree": context.tree_ascii})
    return decision.action, info
