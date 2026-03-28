from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ABILITY_CSV = ROOT / "files" / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv"
PARITY_JSON = ROOT / "audit_parity.json"
OUTPUT_LOG = ROOT / "ABILITY_LOG.md"
RULES_DIR = ROOT / "auto_ptu" / "rules"
TESTS_DIR = ROOT / "tests"


def _load_parity_status() -> Dict[str, Dict[str, object]]:
    if not PARITY_JSON.exists():
        return {}
    data = json.loads(PARITY_JSON.read_text(encoding="utf-8"))
    result: Dict[str, Dict[str, object]] = {}
    for entry in data.get("abilities", []):
        name = str(entry.get("name") or "").strip()
        if name:
            result[name] = entry
    return result


def _iter_py_files(path: Path) -> Iterable[Path]:
    for item in path.rglob("*.py"):
        if item.name.startswith("__"):
            continue
        yield item


def _load_code_text() -> str:
    buf: List[str] = []
    for path in _iter_py_files(RULES_DIR):
        try:
            buf.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(buf).lower()


def _find_test_name(lines: List[str], idx: int) -> str | None:
    for j in range(idx, max(-1, idx - 30), -1):
        match = re.match(r"\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", lines[j])
        if match:
            return match.group(1)
    return None


def _load_test_refs(abilities: Iterable[str]) -> Dict[str, List[str]]:
    pending_lower = {name.lower(): name for name in abilities}
    refs: Dict[str, List[str]] = {name: [] for name in abilities}
    for path in _iter_py_files(TESTS_DIR):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        lower_lines = [line.lower() for line in lines]
        for i, line in enumerate(lower_lines):
            for key, name in pending_lower.items():
                if key in line:
                    test_name = _find_test_name(lines, i)
                    if test_name:
                        ref = f"{path.as_posix()}::{test_name}"
                        if ref not in refs[name]:
                            refs[name].append(ref)
    return refs


def _in_code(name: str, code_text: str) -> bool:
    base = re.sub(r"\s*\[[^\]]+\]\s*", "", name).strip()
    parts = [part.strip() for part in base.split("/") if part.strip()] or [base]
    return any(part.lower() in code_text for part in parts)


def main() -> None:
    enc = "utf-8"
    parity = _load_parity_status()
    entries: List[Tuple[str, str, str]] = []
    names: List[str] = []
    with ABILITY_CSV.open(encoding=enc, newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            name = (row.get('Name') or '').strip()
            if not name:
                continue
            names.append(name)

    code_text = _load_code_text()
    test_refs = _load_test_refs(names)

    for name in names:
        entry = parity.get(name, {})
        status = str(entry.get("status") or "").strip().lower()
        if status not in {"done", "pending", "in progress"}:
            status = "done" if test_refs.get(name) else "pending"
        if test_refs.get(name):
            note = "Verified via tests " + ", ".join(f"`{ref}`" for ref in test_refs[name]) + "."
            status = "done"
        else:
            note = "Referenced in code; no test coverage located." if _in_code(name, code_text) else "No code references found."
        entries.append((name, status, note))

    with OUTPUT_LOG.open("w", encoding=enc, newline="") as out:
        out.write("# Ability Implementation Log\n\n")
        out.write("Generated from the CSV, code scan, and test references.\n\n")
        out.write("| # | Ability | Status | Notes |\n")
        out.write("|---|---------|--------|-------|\n")
        for idx, (name, status, note) in enumerate(entries, start=1):
            safe_name = name.replace("|", "\\|")
            safe_notes = note.replace("|", "\\|")
            out.write(f"| {idx} | `{safe_name}` | {status} | {safe_notes} |\n")


if __name__ == '__main__':
    main()
