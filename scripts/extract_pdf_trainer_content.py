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

NAME_BLOCK_PATTERNS = [
    r"skills, edges",
    r"skills, edges, feats",
    r"trainer classes",
    r"trainer features",
    r"trainer edges",
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


def _is_bad_name(name: str) -> bool:
    lower = name.lower()
    if len(lower) < 2 or len(lower) > 80:
        return True
    if any(re.search(pat, lower) for pat in NAME_BLOCK_PATTERNS):
        return True
    if re.search(r"\d", lower):
        return True
    if "," in name:
        return True
    if lower.startswith("and ") or lower.startswith("or "):
        return True
    words = name.split()
    if len(words) > 7:
        return True
    if not any(w[:1].isupper() for w in words if w):
        return True
    return False


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


def extract_lines(path: Path) -> list[str]:
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
    return lines


def extract_from_lines(lines: list[str], path: Path) -> list[dict]:
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_possible_name(line):
            i += 1
            continue
        name = _clean_name(line)
        if not name or _is_bad_name(name):
            i += 1
            continue

        lookahead = lines[i + 1 : i + 8]
        has_prereq = any(_is_prereq_line(entry) for entry in lookahead)
        has_effect = any(entry.lower().startswith("effect") for entry in lookahead)
        if not (has_prereq and has_effect):
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
            "source_pdf_path": str(path),
        }
        entries.append(entry)
        i = j

    return entries


def extract_from_pdf(path: Path) -> list[dict]:
    return extract_from_lines(extract_lines(path), path)


def classify_entries(entries: list[dict]) -> dict:
    features = []
    edges = []
    skills = []
    seen = set()
    for entry in entries:
        name = entry.get("name") or ""
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        tags = entry.get("tags") or []
        if tags:
            features.append(entry)
        else:
            prereq = entry.get("prerequisites") or ""
            if prereq:
                edges.append(entry)
    return {"features": features, "edges": edges, "skills": skills}


def _confidence(entry: dict, name_hits: int) -> float:
    score = 0.4
    name = entry.get("name") or ""
    tags = entry.get("tags") or []
    prereq = entry.get("prerequisites") or ""
    freq = entry.get("frequency") or ""
    effects = entry.get("effects") or ""

    if tags:
        score += 0.2
    if prereq:
        score += 0.1
    if freq:
        score += 0.1
    if effects and len(effects) >= 60:
        score += 0.1
    if name_hits >= 2:
        score += 0.1
    if _is_bad_name(name):
        score -= 0.4
    if len(name.split()) > 7:
        score -= 0.2
    if any(re.search(pat, name.lower()) for pat in NAME_BLOCK_PATTERNS):
        score -= 0.2

    return max(0.0, min(1.0, round(score, 2)))


def _normalize_line(line: str) -> str:
    return _collapse_spaces(_clean_text(line)).lower()


def _verify_entry(entry: dict, lines: list[str]) -> dict:
    name = entry.get("name") or ""
    if not name:
        return {"status": "rejected", "reason": "missing name"}
    target = _normalize_line(name)
    hit_indices = [i for i, line in enumerate(lines) if _normalize_line(line) == target]
    for idx in hit_indices:
        window = lines[idx + 1 : idx + 12]
        has_prereq = any(_is_prereq_line(item) for item in window)
        has_effect = any(item.lower().startswith("effect") for item in window)
        if has_prereq and has_effect:
            return {
                "status": "confirmed",
                "reason": "name + prerequisites + effect within 12 lines",
                "line_index": idx,
            }
    return {"status": "rejected", "reason": "no matching prereq/effect near name"}


def main() -> None:
    all_entries = []
    name_counts = {}
    pdf_lines = {}
    for pdf in PDF_SOURCES:
        lines = extract_lines(pdf)
        pdf_lines[str(pdf)] = lines
        entries = extract_from_lines(lines, pdf)
        for entry in entries:
            key = entry["name"].lower()
            name_counts[key] = name_counts.get(key, 0) + 1
        all_entries.extend(entries)

    classified = classify_entries(all_entries)

    # Attach confidence + verdict and verification
    for entry in classified["features"] + classified["edges"]:
        hits = name_counts.get(entry["name"].lower(), 1)
        entry["confidence"] = _confidence(entry, hits)
        entry["verdict"] = "keep" if entry["confidence"] >= 0.8 else "review"

        if entry["confidence"] < 0.8:
            source_path = entry.get("source_pdf_path") or ""
            lines = pdf_lines.get(source_path, [])
            verification = _verify_entry(entry, lines)

            if verification["status"] != "confirmed" and hits > 1:
                for path, candidate_lines in pdf_lines.items():
                    if path == source_path:
                        continue
                    verification = _verify_entry(entry, candidate_lines)
                    if verification["status"] == "confirmed":
                        verification["source_pdf_path"] = path
                        break

            entry["verification"] = verification
            if verification["status"] == "confirmed":
                entry["confidence"] = max(entry["confidence"], 0.9)
                entry["verdict"] = "keep"
            else:
                entry["confidence"] = min(entry["confidence"], 0.2)
                entry["verdict"] = "drop"
        else:
            entry["verification"] = {"status": "assumed", "reason": "confidence >= 0.8"}

    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [str(p) for p in PDF_SOURCES],
        "feature_count": len(classified["features"]),
        "edge_count": len(classified["edges"]),
        "skill_count": len(classified["skills"]),
        "features": classified["features"],
        "edges": classified["edges"],
        "skills": classified["skills"],
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "pdf_trainer_content.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
