from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARITY_JSON = ROOT / "audit_parity.json"
SOURCES_DIR = ROOT / "audit_sources"
OUT_PATH = ROOT / "AUDIT_CHECKLIST.md"


def _load_parity() -> dict:
    return json.loads(PARITY_JSON.read_text(encoding="utf-8"))


def _load_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    if not SOURCES_DIR.exists():
        return sources
    for path in SOURCES_DIR.glob("*.txt"):
        try:
            sources[path.name] = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
    return sources


def _find_sources(name: str, sources: dict[str, str]) -> list[str]:
    needle = name.lower()
    hits: list[str] = []
    for source_name, text in sources.items():
        if needle in text:
            hits.append(source_name)
    return hits


def _render_section(
    title: str,
    items: list[tuple[str, str]],
    sources: dict[str, str],
    touchpoints: str,
) -> list[str]:
    lines = [f"## {title}", f"- Count: {len(items)}", ""]
    for label, lookup in items:
        srcs = _find_sources(lookup, sources)
        src_text = ", ".join(srcs) if srcs else "NOT FOUND IN SOURCES"
        lines.append(f"- {label} :: sources: {src_text} :: touchpoints: {touchpoints}")
    if not items:
        lines.append("- None")
    return lines


def main() -> None:
    data = _load_parity()
    sources = _load_sources()

    moves = data.get("moves", [])
    abilities = data.get("abilities", [])

    missing_handlers = sorted(m["name"] for m in moves if not m.get("has_special_handler"))
    abilities_not_done = sorted(
        a["name"] for a in abilities if str(a.get("status") or "").lower() != "done"
    )
    abilities_done_no_tests = sorted(
        a["name"]
        for a in abilities
        if str(a.get("status") or "").lower() == "done" and not a.get("test_mention")
    )

    lines = [
        "# Parity Audit Checklist",
        "",
        "Generated from `audit_parity.json` and source text in `audit_sources/`.",
        "",
    ]
    lines += _render_section(
        "Moves Without Special Handlers (May Be Generic)",
        [(name, name) for name in missing_handlers],
        sources,
        "tests/ (add coverage), auto_ptu/rules/*; no handler does not imply missing behavior",
    )
    lines += ["", *(_render_section(
        "Abilities Not Done",
        [(f"{name} (pending)", name) for name in abilities_not_done],
        sources,
        "auto_ptu/rules/hooks/abilities/*.py, ABILITY_HOOKS.md",
    ))]
    lines += ["", *(_render_section(
        "Abilities Done Without Test Mentions",
        [(name, name) for name in abilities_done_no_tests],
        sources,
        "tests/ (add coverage), auto_ptu/rules/hooks/abilities/*.py",
    ))]

    OUT_PATH.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
