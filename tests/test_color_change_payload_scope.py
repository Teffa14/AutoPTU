from __future__ import annotations

import ast
from pathlib import Path


BATTLE_STATE = Path(__file__).resolve().parents[1] / "auto_ptu" / "rules" / "battle_state.py"


def _color_change_guard(tree: ast.AST, source: str) -> ast.If:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = ast.get_source_segment(source, node.test) or ""
        if "new_type" in test and "defender.spec.types" in test and "[new_type]" in test:
            return node
    raise AssertionError("Color Change type-change guard was not found")


def test_color_change_event_payload_stays_inside_type_change_guard() -> None:
    """Same-type hits must not read a payload that was never initialized."""
    source = BATTLE_STATE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    guard = _color_change_guard(tree, source)

    guarded_calls = {
        ast.get_source_segment(source, node) or ""
        for statement in guard.body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
    }

    assert any("events.append(payload)" in call for call in guarded_calls)
    assert any("self.log_event(payload)" in call for call in guarded_calls)
