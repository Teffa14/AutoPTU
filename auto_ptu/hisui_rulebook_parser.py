from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, PROJECT_ROOT
from .swsh_rulebook_parser import parse_galardex, parse_swsh_references


RULEBOOK_ROOT = PROJECT_ROOT / "files" / "rulebook"
HISUIDEX_PATH = RULEBOOK_ROOT / "HisuiDex.pdf"
REFERENCES_PATH = RULEBOOK_ROOT / "Arceus References.pdf"
HISUIDEX_OUT = DATA_DIR / "compiled" / "hisuidex.json"
REFERENCES_OUT = DATA_DIR / "compiled" / "hisui_references.json"


def parse_hisuidex(path: Path = HISUIDEX_PATH) -> dict[str, Any]:
    return parse_galardex(path)


def parse_hisui_references(path: Path = REFERENCES_PATH) -> dict[str, Any]:
    return parse_swsh_references(path)


def compile_hisui_rulebooks(
    hisuidex_path: Path = HISUIDEX_PATH,
    references_path: Path = REFERENCES_PATH,
    hisuidex_out: Path = HISUIDEX_OUT,
    references_out: Path = REFERENCES_OUT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    hisuidex = parse_hisuidex(hisuidex_path)
    references = parse_hisui_references(references_path)
    hisuidex_out.parent.mkdir(parents=True, exist_ok=True)
    hisuidex_out.write_text(json.dumps(hisuidex, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    references_out.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return hisuidex, references


__all__ = [
    "HISUIDEX_OUT",
    "REFERENCES_OUT",
    "compile_hisui_rulebooks",
    "parse_hisuidex",
    "parse_hisui_references",
]
