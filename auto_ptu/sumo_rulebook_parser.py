from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, PROJECT_ROOT
from .swsh_rulebook_parser import parse_swsh_references


RULEBOOK_ROOT = PROJECT_ROOT / "files" / "rulebook"
REFERENCES_PATH = RULEBOOK_ROOT / "SuMo References.pdf"
REFERENCES_OUT = DATA_DIR / "compiled" / "sumo_references.json"


def parse_sumo_references(path: Path = REFERENCES_PATH) -> dict[str, Any]:
    return parse_swsh_references(path)


def compile_sumo_rulebook(
    references_path: Path = REFERENCES_PATH,
    references_out: Path = REFERENCES_OUT,
) -> dict[str, Any]:
    references = parse_sumo_references(references_path)
    references_out.parent.mkdir(parents=True, exist_ok=True)
    references_out.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return references


__all__ = [
    "REFERENCES_OUT",
    "compile_sumo_rulebook",
    "parse_sumo_references",
]
