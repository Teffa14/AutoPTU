from pathlib import Path
import csv
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT / 'files'
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_DATA = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Class Data.csv'
FEATURES_DATA = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Features Data.csv'
PDF_CONTENT = REPORTS_DIR / 'pdf_trainer_content.json'


def _clean_text(value: str) -> str:
    return (value or '').replace('\r', '').strip()


def _parse_class_mechanics(path: Path):
    if not path.exists():
        return {}
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    mechanics = {}
    current_class = None
    for row in rows[2:]:
        if not row:
            continue
        while len(row) < 3:
            row.append('')
        cls = _clean_text(row[0])
        mech = _clean_text(row[1])
        effect = _clean_text(row[2])
        if not (cls or mech or effect):
            continue
        if cls:
            current_class = cls
        if not current_class:
            continue
        if not mech and not effect:
            continue
        mechanics.setdefault(current_class, []).append({
            'name': mech,
            'effects': effect,
        })
    return mechanics


def _parse_feature_rows(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            name = _clean_text(row.get('Name'))
            if not name:
                continue
            rows.append({
                'name': name,
                'tags_raw': _clean_text(row.get('Tags')),
                'prerequisites': _clean_text(row.get('Prerequisites')),
                'frequency': _clean_text(row.get('Frequency/Action')),
                'effects': _clean_text(row.get('Effects')),
            })
    return rows


def _load_pdf_features(path: Path):
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding='utf-8'))
    out = []
    for entry in raw.get('features', []):
        name = _clean_text(entry.get('name'))
        if not name:
            continue
        tags = entry.get('tags') or []
        if isinstance(tags, list):
            tags_raw = " ".join(f"[{tag}]" for tag in tags if tag)
        else:
            tags_raw = _clean_text(tags)
        out.append({
            'name': name,
            'tags_raw': tags_raw,
            'prerequisites': _clean_text(entry.get('prerequisites')),
            'frequency': _clean_text(entry.get('frequency')),
            'effects': _clean_text(entry.get('effects')),
        })
    return out


def _extract_tags(raw: str):
    tags = []
    for match in re.findall(r"\[([^\]]+)\]", raw or ''):
        tag = match.strip()
        if tag:
            tags.append(tag)
    return tags


def _rank_from_tags_or_name(tags, name: str):
    tag_map = {'Ranked 2': 2, 'Ranked 3': 3, 'Ranked 4': 4}
    for tag in tags:
        if tag in tag_map:
            return tag_map[tag]
    name_lower = name.lower()
    name_rank = re.search(r"rank\s*(\d+)", name_lower)
    if name_rank:
        try:
            return int(name_rank.group(1))
        except ValueError:
            pass
    return 1


def _prereq_options(text: str):
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines()]
    options = []
    current = []
    for line in lines:
        if not line:
            continue
        if line.lower() == 'or':
            if current:
                options.append(' '.join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        options.append(' '.join(current).strip())
    return options or [text.strip()]


def _level_requirements(text: str):
    levels = []
    for match in re.findall(r"\bLevel\s*(\d+)", text, re.IGNORECASE):
        try:
            levels.append(int(match))
        except ValueError:
            continue
    return sorted(set(levels))


def _compile_class_patterns(class_names):
    patterns = []
    for name in class_names:
        norm = re.sub(r"\s+", " ", name.strip().lower())
        escaped = re.escape(norm).replace("\\ ", r"\\s+")
        pattern = re.compile(rf"(^|[^a-z0-9]){escaped}([^a-z0-9]|$)", re.IGNORECASE)
        patterns.append((name, pattern))
    return patterns


def generate():
    mechanics_by_class = _parse_class_mechanics(CLASS_DATA)
    feature_rows = _parse_feature_rows(FEATURES_DATA)
    pdf_features = _load_pdf_features(PDF_CONTENT)
    if pdf_features:
        existing = {row['name'].lower() for row in feature_rows if row.get('name')}
        for row in pdf_features:
            if row['name'].lower() in existing:
                continue
            feature_rows.append(row)
            existing.add(row['name'].lower())

    class_rows = []
    for row in feature_rows:
        tags = _extract_tags(row['tags_raw'])
        if any(tag.lower().startswith('class') for tag in tags):
            class_rows.append({
                **row,
                'tags': tags,
            })

    class_names = [row['name'] for row in class_rows]
    class_patterns = _compile_class_patterns(class_names)

    unlockables = {name: [] for name in class_names}
    for row in feature_rows:
        if row['name'] in class_names:
            continue
        prereq = row['prerequisites']
        if not prereq:
            continue
        for class_name, pattern in class_patterns:
            if pattern.search(prereq):
                tags = _extract_tags(row['tags_raw'])
                options = _prereq_options(prereq)
                level_reqs = _level_requirements(prereq)
                rank = _rank_from_tags_or_name(tags, row['name'])
                unlockables[class_name].append({
                    'name': row['name'],
                    'tags': tags,
                    'prerequisites': prereq,
                    'frequency': row['frequency'],
                    'effects': row['effects'],
                    'rank': rank,
                    'level_requirements': level_reqs,
                    'prereq_options': options,
                    'exceptions': options[1:] if len(options) > 1 else [],
                })
                break

    classes_out = []
    for row in class_rows:
        name = row['name']
        class_entry = {
            'name': name,
            'tags': row['tags'],
            'prerequisites': row['prerequisites'],
            'frequency': row['frequency'],
            'effects': row['effects'],
            'mechanics': mechanics_by_class.get(name, []),
            'unlockables': sorted(unlockables.get(name, []), key=lambda x: (x['rank'], x['name'])),
        }
        classes_out.append(class_entry)

    output = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': {
            'class_data_csv': str(CLASS_DATA),
            'features_data_csv': str(FEATURES_DATA),
        },
        'class_count': len(classes_out),
        'classes': sorted(classes_out, key=lambda x: x['name']),
    }

    json_path = REPORTS_DIR / 'trainer_class_catalog.json'
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')

    md_lines = [
        '# Trainer Class Catalog',
        '',
        f'Generated: {output["generated_at_utc"]}',
        '',
        f'Total classes: {output["class_count"]}',
        '',
    ]
    for cls in output['classes']:
        md_lines.append(f'## {cls["name"]}')
        md_lines.append('')
        if cls['prerequisites']:
            md_lines.append(f'- Prerequisites: {cls["prerequisites"]}')
        if cls['frequency']:
            md_lines.append(f'- Frequency/Action: {cls["frequency"]}')
        if cls['tags']:
            md_lines.append(f'- Tags: {", ".join(cls["tags"])}')
        if cls['mechanics']:
            md_lines.append('- Mechanics:')
            for mech in cls['mechanics']:
                label = mech.get('name') or 'Mechanic'
                effects = mech.get('effects') or ''
                md_lines.append(f'  - {label}: {effects}')
        if cls['unlockables']:
            md_lines.append('- Unlockables:')
            for unlock in cls['unlockables']:
                rank = unlock.get('rank', 1)
                prereq = unlock.get('prerequisites')
                md_lines.append(f'  - Rank {rank}: {unlock["name"]}')
                if prereq:
                    md_lines.append(f'    - Prereq: {prereq}')
                if unlock.get('exceptions'):
                    md_lines.append(f'    - Exceptions: {" | ".join(unlock["exceptions"])}')
        md_lines.append('')
    md_path = ROOT / 'TRAINER_CLASS_CATALOG.md'
    md_path.write_text('\n'.join(md_lines).replace('  - ', '- '), encoding='utf-8')


if __name__ == '__main__':
    generate()
