import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RULEBOOK_DIR = ROOT / "files" / "rulebook"
REPORTS_DIR = ROOT / "reports"

PDF_SOURCES = sorted(RULEBOOK_DIR.glob("*.pdf"))

HEADER_DROP = [
    "pokemon tabletop united",
    "playtest pack",
    "table of contents",
    "contents",
    "index",
    "ptu",
]

FREQ_KEYWORDS = [
    "static",
    "at-will",
    "daily",
    "scene",
    "eot",
    "swift",
    "standard",
    "move",
    "shift",
    "free action",
    "swift action",
    "standard action",
    "extended action",
    "interrupt",
]


def _clean_text(value: str) -> str:
    return (value or "").replace("\u00ad", "").replace("\r", "").strip()


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _strip_headers(value: str) -> str:
    if not value:
        return value
    lower = value.lower()
    if any(token in lower for token in HEADER_DROP):
        return ""
    if re.fullmatch(r"\d+", lower):
        return ""
    return value


def _strip_playtest_prefix(value: str) -> str:
    value = re.sub(r"^(May|September)\s+2015\s+Playtest\d*", "", value, flags=re.IGNORECASE).strip()
    value = re.sub(r"^Playtest\d*", "", value, flags=re.IGNORECASE).strip()
    return value


def _is_tag_line(line: str) -> bool:
    return "[" in line and "]" in line


def _parse_tags(line: str) -> list[str]:
    tags = []
    for match in re.findall(r"\[([^\]]+)\]", line):
        tag = match.strip()
        if tag:
            tags.append(tag)
    return tags


def _is_prereq_line(line: str) -> bool:
    return line.lower().startswith("prerequisites")


def _extract_prereq(line: str) -> str:
    return _clean_text(line.split(":", 1)[1] if ":" in line else line)


def _looks_like_frequency(line: str) -> bool:
    lower = line.lower()
    return any(key in lower for key in FREQ_KEYWORDS)


def _is_possible_name(line: str) -> bool:
    if not line:
        return False
    if len(line) < 2 or len(line) > 120:
        return False
    if line.endswith("."):
        return False
    if _is_prereq_line(line):
        return False
    lower = line.lower()
    if lower.startswith("effect"):
        return False
    if lower.startswith("trigger"):
        return False
    if lower.startswith("target"):
        return False
    if lower.startswith("frequency"):
        return False
    if _looks_like_frequency(line):
        return False
    if ":" in line:
        return False
    if re.search(r"\bchapter\b", line, re.IGNORECASE):
        return False
    if re.search(r"\bforeword\b", line, re.IGNORECASE):
        return False
    if re.search(r"\bappendix\b", line, re.IGNORECASE):
        return False
    if re.search(r"\bpage\b", line, re.IGNORECASE):
        return False
    if re.search(r"\d{1,3}\s*[-\u2013]\s*\d{1,3}", line):
        return False
    if not re.fullmatch(r"[A-Za-z0-9'\u2019!?,.\-\s]+", line):
        return False
    if re.fullmatch(r"[0-9]+", line):
        return False
    return True


def _clean_name(line: str) -> str:
    line = _strip_playtest_prefix(line)
    return _collapse_spaces(_clean_text(line))


def extract_from_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    raw_lines = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        raw_lines.extend(text.splitlines())
    lines = []
    for line in raw_lines:
        cleaned = _collapse_spaces(_clean_text(line))
        cleaned = _strip_headers(cleaned)
        if cleaned:
            lines.append(cleaned)

    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_possible_name(line):
            i += 1
            continue
        name = _clean_name(line)
        if not name:
            i += 1
            continue

        lookahead = lines[i + 1 : i + 6]
        has_tags = any(_is_tag_line(entry) for entry in lookahead)
        has_prereq = any(_is_prereq_line(entry) for entry in lookahead)
        has_freq = any(_looks_like_frequency(entry) for entry in lookahead)
        if not (has_tags or has_prereq or has_freq):
            i += 1
            continue

        tags = []
        prereq = ""
        freq = ""
        effects = []

        j = i + 1
        if j < len(lines) and _is_tag_line(lines[j]):
            tags = _parse_tags(lines[j])
            j += 1
        if j < len(lines) and _is_prereq_line(lines[j]):
            prereq = _extract_prereq(lines[j])
            j += 1
        if j < len(lines) and _looks_like_frequency(lines[j]):
            freq = lines[j]
            j += 1

        while j < len(lines):
            next_line = lines[j]
            if _is_possible_name(next_line):
                break
            if _is_tag_line(next_line) and not tags:
                tags = _parse_tags(next_line)
            elif _is_prereq_line(next_line) and not prereq:
                prereq = _extract_prereq(next_line)
            elif _looks_like_frequency(next_line) and not freq:
                freq = next_line
            else:
                effects.append(next_line)
            j += 1

        effects_text = _collapse_spaces(" ".join(effects))
        entry = {
            "name": name,
            "tags": tags,
            "prerequisites": prereq,
            "frequency": freq,
            "effects": effects_text,
            "source_pdf": path.name,
        }
        entries.append(entry)
        i = j

    return entries


def main() -> None:
    all_entries = []
    for pdf in PDF_SOURCES:
        all_entries.extend(extract_from_pdf(pdf))

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [str(p) for p in PDF_SOURCES],
        "entry_count": len(all_entries),
        "entries": all_entries,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "pdf_trainer_content_raw.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
