from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARITY_JSON = ROOT / "audit_parity.json"
OUT_PATH = ROOT / "AUDIT_PARITY_REPORT.md"


def _load() -> dict:
    return json.loads(PARITY_JSON.read_text(encoding="utf-8"))


def _render_moves(moves: list[dict]) -> list[str]:
    total = len(moves)
    not_in_sources = sorted(m["name"] for m in moves if not m.get("in_sources"))
    no_handler = sorted(m["name"] for m in moves if not m.get("has_special_handler"))
    no_tests = sorted(m["name"] for m in moves if not m.get("test_mention"))

    lines = [
        "## Moves",
        f"- Total moves: {total}",
        f"- Not found by name in sources: {len(not_in_sources)}",
        f"- Without special handlers: {len(no_handler)}",
        f"- Without test mentions: {len(no_tests)}",
        "",
        "### Moves Not Found By Name In Sources",
    ]
    lines += [f"- {name}" for name in not_in_sources] or ["- None"]
    lines += ["", "### Moves Without Special Handlers"]
    lines += [f"- {name}" for name in no_handler] or ["- None"]
    lines += ["", "### Moves Without Test Mentions"]
    lines += [f"- {name}" for name in no_tests] or ["- None"]
    return lines


def _render_abilities(abilities: list[dict]) -> list[str]:
    total = len(abilities)
    not_in_sources = sorted(a["name"] for a in abilities if not a.get("in_sources"))
    not_done = sorted(a["name"] for a in abilities if str(a.get("status") or "").lower() != "done")
    done_no_tests = sorted(
        a["name"]
        for a in abilities
        if str(a.get("status") or "").lower() == "done" and not a.get("test_mention")
    )

    lines = [
        "## Abilities",
        f"- Total abilities: {total}",
        f"- Not found by name in sources: {len(not_in_sources)}",
        f"- Not done (pending/in progress): {len(not_done)}",
        f"- Done but without test mentions: {len(done_no_tests)}",
        "",
        "### Abilities Not Found By Name In Sources",
    ]
    lines += [f"- {name}" for name in not_in_sources] or ["- None"]
    lines += ["", "### Abilities Not Done (Pending/In Progress)"]
    lines += [f"- {name} (pending)" for name in not_done] or ["- None"]
    lines += ["", "### Abilities Done Without Test Mentions"]
    lines += [f"- {name}" for name in done_no_tests] or ["- None"]
    return lines


def main() -> None:
    data = _load()
    moves = data.get("moves", [])
    abilities = data.get("abilities", [])

    lines = [
        "# Parity Audit Report",
        "",
        "Generated from `audit_parity.json`.",
        "Moves without special handlers may still be fully implemented by generic rules; lack of a handler alone is not a bug.",
        "",
    ]
    lines += _render_moves(moves)
    lines += ["", *(_render_abilities(abilities))]

    OUT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
