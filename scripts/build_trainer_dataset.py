import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FILES = ROOT / "files"
STATIC = ROOT / "auto_ptu" / "api" / "static"

CSV_FEATURES = FILES / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Features Data.csv"
CSV_EDGES = FILES / "Copia de Fancy PTU 1.05 Sheet - Version Hisui - Edges Data.csv"
CSV_TRAINER = FILES / "Fancy PTU 1.05 Sheet - Version Hisui - Trainer.csv"
PDF_CONTENT = REPORTS / "pdf_trainer_content.json"
CHAR_CREATION = REPORTS / "character_creation.json"

import csv

def _clean_text(value: str) -> str:
    return (value or "").replace("\r", "").strip()


def load_csv_features():
    out = []
    if not CSV_FEATURES.exists():
        return out
    with CSV_FEATURES.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _clean_text(row.get("Name"))
            if not name:
                continue
            out.append({
                "name": name,
                "tags": _clean_text(row.get("Tags")),
                "prerequisites": _clean_text(row.get("Prerequisites")),
                "frequency": _clean_text(row.get("Frequency/Action")),
                "effects": _clean_text(row.get("Effects")),
                "source": "csv_features",
            })
    return out


def load_csv_edges():
    out = []
    if not CSV_EDGES.exists():
        return out
    with CSV_EDGES.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    for row in rows[1:]:
        if not row:
            continue
        while len(row) < 3:
            row.append("")
        name = _clean_text(row[0])
        prereq = _clean_text(row[1])
        effect = _clean_text(row[2])
        if not name:
            continue
        out.append({
            "name": name,
            "prerequisites": prereq if prereq not in {"-", "--"} else "",
            "effects": effect,
            "source": "csv_edges",
        })
    return out


def load_csv_skills():
    out = []
    if not CSV_TRAINER.exists():
        return out
    with CSV_TRAINER.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    in_skills = False
    for row in rows:
        if not row:
            continue
        first = (row[0] or "").strip().lower()
        if first == "skill":
            in_skills = True
            continue
        if in_skills:
            name = _clean_text(row[0])
            if not name:
                continue
            if name.lower() in {"training feature", "trainer advancement bonuses", "bonus features/edges"}:
                break
            if name.lower() in {"skill", "stat", "hp"}:
                continue
            out.append({"name": name, "source": "csv_trainer"})
    return out


def load_pdf_content():
    if not PDF_CONTENT.exists():
        return {"features": [], "edges": [], "skills": []}
    return json.loads(PDF_CONTENT.read_text(encoding="utf-8"))


def load_classes_from_character_creation():
    if not CHAR_CREATION.exists():
        return []
    obj = json.loads(CHAR_CREATION.read_text(encoding="utf-8"))
    classes = obj.get("classes", [])
    out = []
    for cls in classes:
        out.append({
            "id": cls.get("id"),
            "name": cls.get("name"),
            "tiers": cls.get("tiers", {}),
            "source": "character_creation",
            "confidence": 0.95,
            "verdict": "keep",
        })
    return out


def dedupe_by_name(items):
    seen = set()
    out = []
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)

    features = load_csv_features()
    edges = load_csv_edges()
    skills = load_csv_skills()

    pdf = load_pdf_content()
    pdf_features = pdf.get("features", [])
    pdf_edges = pdf.get("edges", [])
    pdf_skills = pdf.get("skills", [])

    # Normalize pdf entries to align with dataset
    for entry in pdf_features:
        entry["source"] = entry.get("source_pdf") or "pdf"
        entry.setdefault("confidence", 0.0)
        entry.setdefault("verdict", "review")
    for entry in pdf_edges:
        entry["source"] = entry.get("source_pdf") or "pdf"
        entry.setdefault("confidence", 0.0)
        entry.setdefault("verdict", "review")
    for entry in pdf_skills:
        if isinstance(entry, dict):
            entry["source"] = entry.get("source_pdf") or "pdf"
        else:
            entry = {"name": str(entry), "source": "pdf"}

    # Keep only verified pdf entries; csv is trusted.
    pdf_features = [entry for entry in pdf_features if entry.get("verdict") == "keep"]
    pdf_edges = [entry for entry in pdf_edges if entry.get("verdict") == "keep"]

    for entry in features:
        entry.setdefault("confidence", 0.95)
        entry.setdefault("verdict", "keep")
    for entry in edges:
        entry.setdefault("confidence", 0.95)
        entry.setdefault("verdict", "keep")

    features = dedupe_by_name(features + pdf_features)
    edges = dedupe_by_name(edges + pdf_edges)

    skill_items = skills[:]
    for entry in pdf_skills:
        if isinstance(entry, dict):
            skill_items.append(entry)
        else:
            skill_items.append({"name": str(entry), "source": "pdf"})
    skills = dedupe_by_name(skill_items)
    for entry in skills:
        entry.setdefault("confidence", 0.95)
        entry.setdefault("verdict", "keep")

    classes = load_classes_from_character_creation()

    dataset = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "csv_features": str(CSV_FEATURES),
            "csv_edges": str(CSV_EDGES),
            "csv_trainer": str(CSV_TRAINER),
            "pdf_content": str(PDF_CONTENT),
            "character_creation": str(CHAR_CREATION),
        },
        "counts": {
            "features": len(features),
            "edges": len(edges),
            "skills": len(skills),
            "classes": len(classes),
        },
        "features": features,
        "edges": edges,
        "skills": skills,
        "classes": classes,
    }

    out_path = REPORTS / "trainer_content_dataset.json"
    out_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
