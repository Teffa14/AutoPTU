import json
from pathlib import Path
from datetime import datetime, timezone
import re

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / 'reports'
DATA_PATH = REPORTS_DIR / 'trainer_class_catalog.json'

if not DATA_PATH.exists():
    raise SystemExit('trainer_class_catalog.json not found')

raw = json.loads(DATA_PATH.read_text(encoding='utf-8'))
classes = raw.get('classes', [])

name_map = {cls['name']: cls for cls in classes}

missing_mechanics = [cls['name'] for cls in classes if not cls.get('mechanics')]

ambiguous_unlockables = []
for cls in classes:
    for unlock in cls.get('unlockables', []):
        prereq = unlock.get('prerequisites', '')
        if ' or ' in prereq.lower() or '\nOr\n' in prereq or '\nor\n' in prereq:
            ambiguous_unlockables.append({
                'class': cls['name'],
                'unlockable': unlock['name'],
                'prerequisites': prereq,
                'exceptions': unlock.get('exceptions', []),
            })

# Detect unlockables whose prereqs mention more than one class name
# (possible ambiguous attachment due to shared names)
class_names = [cls['name'] for cls in classes]
patterns = []
for name in class_names:
    norm = re.sub(r"\s+", " ", name.strip().lower())
    escaped = re.escape(norm).replace("\\ ", r"\\s+")
    patterns.append((name, re.compile(rf"(^|[^a-z0-9]){escaped}([^a-z0-9]|$)", re.IGNORECASE)))

multi_class_mentions = []
for cls in classes:
    for unlock in cls.get('unlockables', []):
        prereq = unlock.get('prerequisites', '')
        if not prereq:
            continue
        hits = [name for name, pat in patterns if pat.search(prereq)]
        hits = [h for h in hits if h]
        if len(set(hits)) > 1:
            multi_class_mentions.append({
                'class': cls['name'],
                'unlockable': unlock['name'],
                'prerequisites': prereq,
                'mentioned_classes': sorted(set(hits)),
            })

report = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'class_count': len(classes),
    'missing_mechanics_count': len(missing_mechanics),
    'missing_mechanics': sorted(missing_mechanics),
    'ambiguous_unlockables_count': len(ambiguous_unlockables),
    'ambiguous_unlockables': ambiguous_unlockables,
    'multi_class_mentions_count': len(multi_class_mentions),
    'multi_class_mentions': multi_class_mentions,
}

out_path = REPORTS_DIR / 'trainer_class_validation.json'
out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

md = [
    '# Trainer Class Validation',
    '',
    f'Generated: {report["generated_at_utc"]}',
    '',
    f'- Classes: {report["class_count"]}',
    f'- Missing mechanics: {report["missing_mechanics_count"]}',
    f'- Ambiguous unlockables (OR branches): {report["ambiguous_unlockables_count"]}',
    f'- Multi-class mentions: {report["multi_class_mentions_count"]}',
    '',
]
if report['missing_mechanics']:
    md.append('## Missing Mechanics')
    md += [f'- {name}' for name in report['missing_mechanics']]
    md.append('')
if report['ambiguous_unlockables']:
    md.append('## Ambiguous Unlockables (OR Branches)')
    for entry in report['ambiguous_unlockables']:
        md.append(f"- {entry['class']} -> {entry['unlockable']}")
        md.append(f"  - Prereq: {entry['prerequisites']}")
        if entry.get('exceptions'):
            md.append(f"  - Exceptions: {' | '.join(entry['exceptions'])}")
    md.append('')
if report['multi_class_mentions']:
    md.append('## Multi-Class Mentions')
    for entry in report['multi_class_mentions']:
        md.append(f"- {entry['class']} -> {entry['unlockable']}")
        md.append(f"  - Mentioned: {', '.join(entry['mentioned_classes'])}")
        md.append(f"  - Prereq: {entry['prerequisites']}")
    md.append('')

md_path = ROOT / 'TRAINER_CLASS_VALIDATION.md'
md_path.write_text('\n'.join(md).replace('  - ', '- '), encoding='utf-8')
