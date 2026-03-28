"""Move regression suite for deterministic validation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from rich.console import Console

from .attack_tester import run_move_test

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUITE = ROOT / "auto_ptu" / "data" / "tests" / "move_regression.json"

console = Console(legacy_windows=False)


@dataclass(frozen=True)
class RegressionResult:
    move: str
    ok: bool
    errors: List[str]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _event_matches(event: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    for key, expected_value in expected.items():
        if key not in event:
            return False
        actual = _normalize_value(event.get(key))
        expect = _normalize_value(expected_value)
        if actual != expect:
            return False
    return True


def _find_match(events: Iterable[Dict[str, Any]], expected: Dict[str, Any]) -> bool:
    for event in events:
        if _event_matches(event, expected):
            return True
    return False


def run_regression_suite(
    *,
    path: Optional[Path] = None,
    seed: int = 1,
    show_log: bool = False,
) -> List[RegressionResult]:
    suite_path = path or DEFAULT_SUITE
    if not suite_path.exists():
        raise FileNotFoundError(f"Regression suite not found: {suite_path}")
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    results: List[RegressionResult] = []
    for case in suite.get("cases", []):
        move = str(case.get("move") or "").strip()
        if not move:
            continue
        battle = run_move_test(move, seed=seed, show_log=show_log)
        events = list(battle.log)
        errors: List[str] = []
        for expected in case.get("expect", []):
            if not _find_match(events, expected):
                errors.append(f"Missing event match: {expected}")
        ok = not errors
        results.append(RegressionResult(move=move, ok=ok, errors=errors))
    return results


def report_regression_suite(
    *,
    path: Optional[Path] = None,
    seed: int = 1,
    show_log: bool = False,
) -> int:
    results = run_regression_suite(path=path, seed=seed, show_log=show_log)
    failures = 0
    for result in results:
        if result.ok:
            console.print(f"[green]OK[/green] {result.move}")
        else:
            failures += 1
            console.print(f"[red]FAIL[/red] {result.move}")
            for error in result.errors:
                console.print(f"  - {error}")
    console.print(f"Failures: {failures}")
    return failures


__all__ = ["run_regression_suite", "report_regression_suite"]
