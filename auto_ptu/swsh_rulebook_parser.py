from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import DATA_DIR, PROJECT_ROOT


RULEBOOK_ROOT = PROJECT_ROOT / "files" / "rulebook"
GALARDEX_PATH = RULEBOOK_ROOT / "GalarDex + Armor_Crown.pdf"
REFERENCES_PATH = RULEBOOK_ROOT / "SwSh + Armor_Crown References.pdf"
GALARDEX_OUT = DATA_DIR / "compiled" / "swsh_galardex.json"
REFERENCES_OUT = DATA_DIR / "compiled" / "swsh_references.json"

_BASE_STAT_RE = re.compile(r"^(HP|Attack|Defense|Special Attack|Special Defense|Speed):\s*([0-9]+)\s*$", re.MULTILINE)
_TYPE_RE = re.compile(r"^Type:\s*(.+)$", re.MULTILINE)
_ABILITY_LINE_RE = re.compile(r"^(Basic Ability \d+|Adv Ability \d+|High Ability):\s*(.+)$", re.MULTILINE)
_SECTION_RE = re.compile(r"^\s*(Basic Information|Evolution:|Size Information|Breeding Information|Capability List|Skill List|Move List)\s*$", re.MULTILINE)
_LEVEL_MOVE_RE = re.compile(r"^\s*(Evo|§?\s*\d+)\s+(.+?)\s*-\s*([A-Za-z/ ]+)\s*$", re.MULTILINE)
_TM_MOVE_RE = re.compile(r"(?:^|,\s*)(\d{1,3})\s+([^,\n]+)")
_REFERENCE_MOVE_RE = re.compile(r"Move:\s*(.+?)(?=\nMove: |\Z)", re.DOTALL)
_REFERENCE_ABILITY_RE = re.compile(r"Ability:\s*(.+?)(?=\nAbility: |\Z)", re.DOTALL)


def _load_pdf_reader(path: Path):
    from pypdf import PdfReader

    return PdfReader(str(path))


def _clean_text(value: str) -> str:
    text = str(value or "")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00a7", "").replace("\u200b", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    return text.strip()


def _clean_name(value: str) -> str:
    text = _clean_text(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -")


def _clean_species_name(value: str) -> str:
    text = _clean_name(value)
    if not text:
        return ""
    return " ".join(part[:1].upper() + part[1:].lower() if part else "" for part in text.split())


def _extract_block(text: str, start: str, end: str | None) -> str:
    pattern = re.escape(start) + r"\s*(.*)"
    start_match = re.search(pattern, text, re.DOTALL)
    if not start_match:
        return ""
    remainder = start_match.group(1)
    if not end:
        return remainder.strip()
    end_match = re.search(rf"\n\s*{re.escape(end)}\s*", remainder)
    if not end_match:
        return remainder.strip()
    return remainder[: end_match.start()].strip()


def _first_nonempty_line(text: str) -> str:
    for raw in text.splitlines():
        line = _clean_name(raw)
        if line:
            return line
    return ""


def _parse_types(text: str) -> list[str]:
    match = _TYPE_RE.search(text)
    if not match:
        return []
    return [_clean_name(part) for part in match.group(1).split("/") if _clean_name(part)]


def _parse_abilities(text: str) -> dict[str, list[str]]:
    out = {"basic": [], "advanced": [], "high": []}
    for label, raw_value in _ABILITY_LINE_RE.findall(text):
        value = _clean_name(raw_value)
        if not value:
            continue
        if label.startswith("Basic"):
            out["basic"].append(value)
        elif label.startswith("Adv"):
            out["advanced"].append(value)
        else:
            out["high"].append(value)
    return out


def _parse_base_stats(text: str) -> dict[str, int]:
    key_map = {
        "HP": "hp",
        "Attack": "attack",
        "Defense": "defense",
        "Special Attack": "special_attack",
        "Special Defense": "special_defense",
        "Speed": "speed",
    }
    out: dict[str, int] = {}
    for label, value in _BASE_STAT_RE.findall(text):
        out[key_map[label]] = int(value)
    return out


def _parse_evolution_lines(text: str) -> list[str]:
    block = _extract_block(text, "Evolution:", "Size Information")
    return [_clean_name(line) for line in block.splitlines() if _clean_name(line)]


def _parse_size_and_weight(text: str) -> tuple[str, float | None]:
    block = _extract_block(text, "Size Information", "Breeding Information")
    size = ""
    weight: float | None = None
    size_match = re.search(r"Height:\s*.+\(([^)]+)\)", block)
    if size_match:
        size = _clean_name(size_match.group(1))
    weight_match = re.search(r"Weight:\s*([\d.]+)\s*lbs", block, re.IGNORECASE)
    if weight_match:
        try:
            weight = float(weight_match.group(1))
        except ValueError:
            weight = None
    return size, weight


def _parse_egg_groups(text: str) -> list[str]:
    block = _extract_block(text, "Breeding Information", "Diet:")
    match = re.search(r"Egg Group:\s*(.+)", block)
    if not match:
        return []
    return [_clean_name(part) for part in match.group(1).split("/") if _clean_name(part)]


def _parse_capabilities(text: str) -> list[str]:
    block = _extract_block(text, "Capability List", "Skill List")
    normalized = re.sub(r"\n", " ", block)
    return [_clean_name(part) for part in normalized.split(",") if _clean_name(part)]


def _parse_skills(text: str) -> list[str]:
    block = _extract_block(text, "Skill List", "Move List")
    normalized = re.sub(r"\n", " ", block)
    return [_clean_name(part) for part in normalized.split(",") if _clean_name(part)]


def _parse_level_up_moves(text: str) -> list[dict[str, Any]]:
    block = _extract_block(text, "Level Up Move List", "TM Move List")
    if not block:
        block = _extract_block(text, "Level Up Move List", "Egg Move List")
    if not block:
        block = _extract_block(text, "Level Up Move List", "Tutor Move List")
    moves: list[dict[str, Any]] = []
    for requirement, move_name, move_type in _LEVEL_MOVE_RE.findall(block):
        req = _clean_name(requirement)
        move = _clean_name(move_name)
        type_name = _clean_name(move_type)
        if not move:
            continue
        moves.append(
            {
                "requirement": req,
                "level": 0 if req.lower() == "evo" else int(re.sub(r"[^0-9]", "", req) or 0),
                "move": move,
                "type": type_name,
            }
        )
    return moves


def _parse_tm_moves(text: str) -> list[dict[str, Any]]:
    block = _extract_block(text, "TM Move List", "Egg Move List")
    if not block:
        block = _extract_block(text, "TM Move List", "Tutor Move List")
    entries: list[dict[str, Any]] = []
    normalized = re.sub(r"\n", " ", block)
    for tm_no, move_name in _TM_MOVE_RE.findall(normalized):
        cleaned = _clean_name(move_name)
        if cleaned:
            entries.append({"tm": tm_no, "move": cleaned})
    return entries


def _parse_comma_moves(text: str, header: str, next_header: str | None = None) -> list[str]:
    block = _extract_block(text, header, next_header)
    normalized = re.sub(r"\n", " ", block)
    return [_clean_name(part) for part in normalized.split(",") if _clean_name(part)]


def parse_galardex(path: Path = GALARDEX_PATH) -> dict[str, Any]:
    reader = _load_pdf_reader(path)
    entries: dict[str, Any] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if "Base Stats:" not in text or "Move List" not in text:
            continue
        species_name = _clean_species_name(_first_nonempty_line(text.split("Base Stats:", 1)[0]))
        if not species_name or species_name.lower().startswith("table of contents"):
            continue
        entries[species_name] = {
            "name": species_name,
            "page": page_number,
            "base_stats": _parse_base_stats(text),
            "types": _parse_types(text),
            "abilities": _parse_abilities(text),
            "evolution": _parse_evolution_lines(text),
            "size": _parse_size_and_weight(text)[0],
            "weight": _parse_size_and_weight(text)[1],
            "egg_groups": _parse_egg_groups(text),
            "capabilities": _parse_capabilities(text),
            "skills": _parse_skills(text),
            "moves": {
                "level_up": _parse_level_up_moves(text),
                "tm": _parse_tm_moves(text),
                "egg": _parse_comma_moves(text, "Egg Move List", "Tutor Move List"),
                "tutor": _parse_comma_moves(text, "Tutor Move List", None),
            },
            "source": path.name,
        }
    return {
        "source": path.name,
        "species_count": len(entries),
        "entries": entries,
    }


def _parse_reference_fields(block: str, labels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    text = block.strip()
    for index, label in enumerate(labels):
        pattern = re.escape(label + ":")
        match = re.search(pattern, text)
        if not match:
            continue
        start = match.end()
        rest = text[start:]
        end = len(rest)
        for next_label in labels[index + 1 :]:
            next_match = re.search(rf"\n{re.escape(next_label + ':')}", rest)
            if next_match:
                end = min(end, next_match.start())
        out[label.lower().replace(" ", "_")] = _clean_text(rest[:end])
    return out


def _parse_reference_ability_block(block: str) -> dict[str, str]:
    lines = [_clean_text(line) for line in block.strip().splitlines() if _clean_text(line)]
    if not lines:
        return {}
    out: dict[str, str] = {}
    if ":" not in lines[0]:
        out["frequency"] = lines[0]
        lines = lines[1:]
    current_key = ""
    buffer: list[str] = []
    key_map = {
        "Trigger:": "trigger",
        "Effect:": "effect",
        "Bonus:": "bonus",
        "Special:": "special",
    }
    for line in lines:
        matched = False
        for label, key in key_map.items():
            if line.startswith(label):
                if current_key and buffer:
                    out[current_key] = _clean_text(" ".join(buffer))
                current_key = key
                buffer = [line[len(label) :].strip()]
                matched = True
                break
        if not matched and current_key:
            buffer.append(line)
    if current_key and buffer:
        out[current_key] = _clean_text(" ".join(buffer))
    return out


def _parse_reference_move_block(block: str) -> dict[str, str]:
    lines = [_clean_text(line) for line in block.strip().splitlines() if _clean_text(line)]
    out: dict[str, str] = {}
    current_key = ""
    buffer: list[str] = []
    for line in lines:
        if line.startswith("Type:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "type"
            buffer = [line[len("Type:") :].strip()]
        elif line.startswith("Frequency:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "frequency"
            buffer = [line[len("Frequency:") :].strip()]
        elif line.startswith("AC:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "ac"
            buffer = [line[len("AC:") :].strip()]
        elif line.startswith("Damage Base"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "damage_base"
            buffer = [line[len("Damage Base") :].strip(" :")]
        elif line.startswith("Class:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "class"
            buffer = [line[len("Class:") :].strip()]
        elif line.startswith("Range:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "range"
            buffer = [line[len("Range:") :].strip()]
        elif line.startswith("Effect:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "effect"
            buffer = [line[len("Effect:") :].strip()]
        elif line.startswith("Contest Type:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "contest_type"
            buffer = [line[len("Contest Type:") :].strip()]
        elif line.startswith("Contest Effect:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "contest_effect"
            buffer = [line[len("Contest Effect:") :].strip()]
        elif line.startswith("Special:"):
            if current_key and buffer:
                out[current_key] = _clean_text(" ".join(buffer))
            current_key = "special"
            buffer = [line[len("Special:") :].strip()]
        elif current_key:
            buffer.append(line)
    if current_key and buffer:
        out[current_key] = _clean_text(" ".join(buffer))
    return out


def parse_swsh_references(path: Path = REFERENCES_PATH) -> dict[str, Any]:
    reader = _load_pdf_reader(path)
    full_text = "\n".join(_clean_text(page.extract_text() or "") for page in reader.pages)

    capabilities: dict[str, Any] = {}
    cap_match = re.search(r"New Capabilities:\s*(.+?)\n\s*New Abilities:", full_text, re.DOTALL)
    if cap_match:
        block = cap_match.group(1).strip()
        parts = re.split(r"\n(?=[A-Z][A-Za-z' -]+:)", block)
        for part in parts:
            if ":" not in part:
                continue
            name, desc = part.split(":", 1)
            capability_name = _clean_name(name)
            if capability_name:
                capabilities[capability_name] = {"name": capability_name, "text": _clean_text(desc), "source": path.name}

    abilities: dict[str, Any] = {}
    ability_match = re.search(r"New Abilities:\s*(.+?)\n\s*(?:Dark Moves:|Dragon Moves:|Electric Moves:)", full_text, re.DOTALL)
    if ability_match:
        for block in _REFERENCE_ABILITY_RE.findall(ability_match.group(1)):
            lines = block.strip().splitlines()
            name = _clean_name(lines[0])
            fields = _parse_reference_ability_block("\n".join(lines[1:]))
            if name:
                abilities[name] = {"name": name, **fields, "source": path.name}

    moves: dict[str, Any] = {}
    move_section_match = re.search(r"(?:Dark Moves:|Dragon Moves:|Electric Moves:)(.+)$", full_text, re.DOTALL)
    if move_section_match:
        current_type = ""
        chunks = re.split(r"\n(?=[A-Z][A-Za-z]+ Moves:)", move_section_match.group(0))
        for chunk in chunks:
            lines = [line for line in chunk.splitlines() if _clean_name(line)]
            if not lines:
                continue
            heading = _clean_name(lines[0])
            if heading.endswith("Moves:"):
                current_type = heading.replace("Moves:", "").strip()
                content = "\n".join(lines[1:])
            else:
                content = "\n".join(lines)
            for block in _REFERENCE_MOVE_RE.findall(content):
                block_lines = block.strip().splitlines()
                name = _clean_name(block_lines[0])
                fields = _parse_reference_move_block("\n".join(block_lines[1:]))
                if name:
                    entry = {"name": name, **fields, "source": path.name}
                    if current_type and "type" not in entry:
                        entry["type"] = current_type
                    moves[name] = entry

    return {
        "source": path.name,
        "capability_count": len(capabilities),
        "ability_count": len(abilities),
        "move_count": len(moves),
        "capabilities": capabilities,
        "abilities": abilities,
        "moves": moves,
    }


def compile_swsh_rulebooks(
    galardex_path: Path = GALARDEX_PATH,
    references_path: Path = REFERENCES_PATH,
    galardex_out: Path = GALARDEX_OUT,
    references_out: Path = REFERENCES_OUT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    galardex = parse_galardex(galardex_path)
    references = parse_swsh_references(references_path)
    galardex_out.parent.mkdir(parents=True, exist_ok=True)
    galardex_out.write_text(json.dumps(galardex, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    references_out.write_text(json.dumps(references, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return galardex, references


__all__ = [
    "GALARDEX_OUT",
    "REFERENCES_OUT",
    "compile_swsh_rulebooks",
    "parse_galardex",
    "parse_swsh_references",
]
