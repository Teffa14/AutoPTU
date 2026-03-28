import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / 'reports'
CATALOG_PATH = REPORTS_DIR / 'trainer_class_catalog.json'

if not CATALOG_PATH.exists():
    raise SystemExit('trainer_class_catalog.json not found')

raw = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
classes = raw.get('classes', [])


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "node"


def mermaid_escape(text: str) -> str:
    return text.replace('"', "'").replace('\n', ' ')


graph = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'class_count': len(classes),
    'nodes': [],
    'edges': [],
    'classes': [],
}

node_index = {}


def ensure_node(node):
    key = node['id']
    if key in node_index:
        return
    node_index[key] = len(graph['nodes'])
    graph['nodes'].append(node)


for cls in classes:
    class_id = f"class:{cls['name']}"
    class_node = {
        'id': class_id,
        'type': 'class',
        'name': cls['name'],
        'tags': cls.get('tags', []),
        'prerequisites': cls.get('prerequisites', ''),
        'frequency': cls.get('frequency', ''),
        'effects': cls.get('effects', ''),
        'mechanics': cls.get('mechanics', []),
    }
    ensure_node(class_node)

    tiers = {}
    for unlock in cls.get('unlockables', []):
        feat_id = f"feature:{unlock['name']}"
        rank = int(unlock.get('rank', 1) or 1)
        node = {
            'id': feat_id,
            'type': 'feature',
            'name': unlock['name'],
            'rank': rank,
            'tags': unlock.get('tags', []),
            'prerequisites': unlock.get('prerequisites', ''),
            'frequency': unlock.get('frequency', ''),
            'effects': unlock.get('effects', ''),
            'level_requirements': unlock.get('level_requirements', []),
            'prereq_options': unlock.get('prereq_options', []),
            'exceptions': unlock.get('exceptions', []),
        }
        ensure_node(node)
        graph['edges'].append({
            'from': class_id,
            'to': feat_id,
            'type': 'unlock',
            'rank': rank,
            'prerequisites': unlock.get('prerequisites', ''),
            'exceptions': unlock.get('exceptions', []),
        })
        tiers.setdefault(rank, []).append(feat_id)

    graph['classes'].append({
        'id': class_id,
        'name': cls['name'],
        'tiers': {str(rank): ids for rank, ids in sorted(tiers.items())},
    })

GRAPH_PATH = REPORTS_DIR / 'trainer_class_graph.json'
GRAPH_PATH.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding='utf-8')

md_lines = [
    '# Trainer Class Skill Trees',
    '',
    f'Generated: {graph["generated_at_utc"]}',
    '',
]

for cls in classes:
    name = cls['name']
    class_slug = slugify(name)
    md_lines.append(f'## {name}')
    md_lines.append('')
    if cls.get('prerequisites'):
        md_lines.append(f'Prerequisites: {cls["prerequisites"]}')
        md_lines.append('')
    if cls.get('mechanics'):
        md_lines.append('Mechanics:')
        for mech in cls['mechanics']:
            label = mech.get('name') or 'Mechanic'
            effects = mech.get('effects') or ''
            md_lines.append(f'- {label}: {effects}')
        md_lines.append('')

    md_lines.append('```mermaid')
    md_lines.append('flowchart TB')
    root_id = f"C_{class_slug}"
    md_lines.append(f"  {root_id}[\"{mermaid_escape(name)}\"]")

    tiers = {}
    for unlock in cls.get('unlockables', []):
        rank = int(unlock.get('rank', 1) or 1)
        tiers.setdefault(rank, []).append(unlock)

    for rank in sorted(tiers.keys()):
        md_lines.append(f"  subgraph {root_id}_R{rank}[\"Rank {rank}\"]")
        for idx, unlock in enumerate(sorted(tiers[rank], key=lambda u: u['name'])):
            node_id = f"{root_id}_R{rank}_{idx}"
            label = unlock['name']
            prereq = unlock.get('prerequisites', '')
            if prereq:
                label = f"{label}\\n{prereq}"
            md_lines.append(f"    {node_id}[\"{mermaid_escape(label)}\"]")
        md_lines.append('  end')

    for rank in sorted(tiers.keys()):
        for idx, _unlock in enumerate(sorted(tiers[rank], key=lambda u: u['name'])):
            node_id = f"{root_id}_R{rank}_{idx}"
            md_lines.append(f"  {root_id} --> {node_id}")

    md_lines.append('```')
    md_lines.append('')

TREE_PATH = ROOT / 'TRAINER_CLASS_TREES.md'
TREE_PATH.write_text('\n'.join(md_lines), encoding='utf-8')
