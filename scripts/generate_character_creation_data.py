import csv
import re
import json
from pathlib import Path
from datetime import datetime, timezone
import unicodedata
from PyPDF2 import PdfReader
from auto_ptu.species_filters import filter_user_selectable_species
from auto_ptu.rules.item_catalog import load_item_catalog

ROOT = Path(__file__).resolve().parents[1]
FILES_DIR = ROOT / 'files'
REPORTS_DIR = ROOT / 'reports'
STATIC_DIR = ROOT / 'auto_ptu' / 'api' / 'static'
COMPILED_DIR = ROOT / 'auto_ptu' / 'data' / 'compiled'

CATALOG_PATH = REPORTS_DIR / 'trainer_class_catalog.json'
GRAPH_PATH = REPORTS_DIR / 'trainer_class_graph.json'
FEATURES_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Features Data.csv'
EDGES_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Edges Data.csv'
POKE_EDGES_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Poke Edges.csv'
TRAINER_PATH = FILES_DIR / 'Fancy PTU 1.05 Sheet - Version Hisui - Trainer.csv'
CLASS_DATA_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Class Data.csv'
PDF_CONTENT = REPORTS_DIR / 'pdf_trainer_content.json'
RULEBOOK_PATHS = [
    FILES_DIR / 'rulebook' / 'Pokemon Tabletop United 1.05 Core.pdf',
    FILES_DIR / 'rulebook' / 'PTU 1.05' / 'Pokemon Tabletop United 1.05 Core.pdf',
]
SPECIES_PATH = COMPILED_DIR / 'species.json'
EVOLUTION_MIN_LEVELS_PATH = COMPILED_DIR / 'evolution_min_levels.json'
WEAPONS_PATH = COMPILED_DIR / 'weapons.json'
ITEMS_CSV_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Item Data.csv'
INV_CSV_PATH = FILES_DIR / 'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Inv Data.csv'

if not CATALOG_PATH.exists() or not GRAPH_PATH.exists():
    raise SystemExit('trainer class catalog/graph missing')

catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
graph = json.loads(GRAPH_PATH.read_text(encoding='utf-8'))

def _clean_text(value: str) -> str:
    return (value or '').replace('\r', '').strip()


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


features = []
with FEATURES_PATH.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = _clean_text(row.get('Name'))
        if not name:
            continue
        features.append({
            'name': name,
            'tags': _clean_text(row.get('Tags')),
            'prerequisites': _clean_text(row.get('Prerequisites')),
            'frequency': _clean_text(row.get('Frequency/Action')),
            'effects': _clean_text(row.get('Effects')),
        })

edges = []
with EDGES_PATH.open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.reader(f))
    for row in rows[1:]:
        if not row:
            continue
        while len(row) < 3:
            row.append('')
        name = _clean_text(row[0])
        prereq = _clean_text(row[1])
        effect = _clean_text(row[2])
        if not name:
            continue
        edges.append({
            'name': name,
            'prerequisites': prereq if prereq not in {'-', '--'} else '',
            'effects': effect,
        })

class_mechanics = {}
if CLASS_DATA_PATH.exists():
    with CLASS_DATA_PATH.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    # Skip headers
    for row in rows[2:]:
        if not row:
            continue
        while len(row) < 3:
            row.append('')
        class_name = _clean_text(row[0])
        mechanic = _clean_text(row[1])
        effect = _clean_text(row[2])
        if not class_name or not mechanic or not effect:
            continue
        class_mechanics.setdefault(class_name, []).append({
            'name': mechanic,
            'effects': effect,
        })

poke_edges = []
if POKE_EDGES_PATH.exists():
    with POKE_EDGES_PATH.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = _clean_text(row.get('Name'))
            if not name:
                continue
            poke_edges.append({
                'name': name,
                'prerequisites': _clean_text(row.get('Prerequisites')),
                'effects': _clean_text(row.get('Effect')),
                'cost': _clean_text(row.get('Cost')),
            })

skills = []
if TRAINER_PATH.exists():
    with TRAINER_PATH.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    in_skills = False
    for row in rows:
        if not row:
            continue
        first = (row[0] or '').strip().lower()
        if first == 'skill':
            in_skills = True
            continue
        if in_skills:
            name = _clean_text(row[0])
            if not name:
                continue
            if name.lower() in {'training feature', 'trainer advancement bonuses', 'bonus features/edges'}:
                break
            if name.lower() in {'skill', 'stat', 'hp'}:
                continue
            skills.append(name)

skill_rules = {
    'ranks': ['Pathetic', 'Untrained', 'Novice', 'Adept', 'Expert', 'Master'],
    'rank_costs': {
        'Pathetic': -1,
        'Untrained': 0,
        'Novice': 1,
        'Adept': 2,
        'Expert': 3,
        'Master': 4,
    },
    'budget': None,
    'notes': 'Budget is unset by default. Use auto budget to mirror max skill edges or set manually.',
    'background': {
        'adept': 1,
        'novice': 1,
        'pathetic': 3,
        'lock_pathetic_level1': True,
    },
    'rank_caps_by_level': [
        {'level': 1, 'max': 'Novice'},
        {'level': 2, 'max': 'Adept'},
        {'level': 6, 'max': 'Expert'},
        {'level': 12, 'max': 'Master'},
    ],
    'edge_budget_level1': 4,
    'edge_per_even_level': 1,
    'bonus_skill_edge_levels': [2, 6, 12],
}

feature_slots_by_rank = {'1': 1, '2': 1, '3': 1, '4': 1}

def _normalize_key(value: str) -> str:
    return ''.join(ch for ch in value.lower() if ch.isalnum())


def _normalize_match_text(value: str) -> str:
    text = (value or '').lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('poké', 'poke').replace('pokemon', 'pokemon')
    text = text.replace('education', 'ed')
    text = re.sub(r"[\\._'’`\\-]+", ' ', text)
    text = re.sub(r"[^a-z0-9\\s]+", ' ', text)
    return re.sub(r"\\s+", ' ', text).strip()


def _split_tags(raw: str) -> list[str]:
    if not raw:
        return []
    cleaned = raw.replace('][', ',').replace('[', '').replace(']', '')
    return [part.strip() for part in cleaned.split(',') if part.strip()]


def _load_pdf_content(path: Path):
    if not path.exists():
        return {'features': [], 'edges': [], 'skills': []}
    raw = json.loads(path.read_text(encoding='utf-8'))
    return {
        'features': raw.get('features', []),
        'edges': raw.get('edges', []),
        'skills': raw.get('skills', []),
    }


def _load_rulebook_text():
    path = next((p for p in RULEBOOK_PATHS if p.exists()), None)
    if not path:
        return ''
    reader = PdfReader(str(path))
    pages = range(35, 52)
    chunks = []
    for page_num in pages:
        if page_num - 1 >= len(reader.pages):
            break
        text = reader.pages[page_num - 1].extract_text() or ''
        if text:
            chunks.append(text)
    raw = ' '.join(chunks)
    raw = raw.replace('PokÃ©mon', 'Pokemon').replace('Pokémon', 'Pokemon').replace('Poké', 'Poke')
    raw = raw.replace('Y ou', 'You').replace('Y ou', 'You').replace('Y ou', 'You')
    raw = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw)
    raw = re.sub(r"\s+", ' ', raw)
    return raw


def _extract_rulebook_skill_descriptions():
    text = _load_rulebook_text()
    if not text:
        return {}
    skill_names = [
        'Acrobatics',
        'Athletics',
        'Combat',
        'Intimidate',
        'Stealth',
        'Survival',
        'General Education',
        'Medicine Education',
        'Occult Education',
        'Pokemon Education',
        'Technology Education',
        'Guile',
        'Perception',
        'Charm',
        'Command',
        'Focus',
        'Intuition',
    ]
    positions = []
    for name in skill_names:
        match = re.search(rf"{re.escape(name)} is ", text)
        if match:
            positions.append((match.start(), name))
    positions.sort()
    descriptions = {}
    for idx, (start, name) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        snippet = text[start:end].strip()
        snippet = re.sub(r"Skills, Edges, Feats\s*\d+", '', snippet).strip()
        cut = re.search(r"\bPrerequisites?:", snippet)
        if cut:
            snippet = snippet[:cut.start()].strip()
        last_sentence = max(snippet.rfind('.'), snippet.rfind('?'), snippet.rfind('!'))
        if last_sentence != -1:
            snippet = snippet[:last_sentence + 1].strip()
        descriptions[name] = snippet
    return descriptions


def _load_item_models():
    payload = {
        'food_items': [],
        'held_items': [],
        'weather': [],
        'inventory': [],
        'weapons': _read_json(WEAPONS_PATH, []),
    }
    if ITEMS_CSV_PATH.exists():
        with ITEMS_CSV_PATH.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
        if rows:
            headers = [cell.strip() for cell in rows[0]]

            def idx(name: str, after: int = -1) -> int:
                for i in range(after + 1, len(headers)):
                    if headers[i] == name:
                        return i
                return -1

            food_name_i = idx('Food Item')
            food_buff_i = idx('Digestion/Food Buff')
            held_name_i = idx('Held Item')
            held_desc_i = idx('Description', held_name_i)
            weather_name_i = idx('Weather')
            weather_effect_i = idx('Effect')

            for row in rows[1:]:
                if not row:
                    continue
                while len(row) < len(headers):
                    row.append('')
                if food_name_i >= 0:
                    name = _clean_text(row[food_name_i])
                    if name:
                        payload['food_items'].append({
                            'name': name,
                            'buff': _clean_text(row[food_buff_i]) if food_buff_i >= 0 else '',
                            'source': 'fancy_items_csv',
                        })
                if held_name_i >= 0:
                    name = _clean_text(row[held_name_i])
                    if name:
                        payload['held_items'].append({
                            'name': name,
                            'description': _clean_text(row[held_desc_i]) if held_desc_i >= 0 else '',
                            'source': 'fancy_items_csv',
                        })
                if weather_name_i >= 0:
                    name = _clean_text(row[weather_name_i])
                    if name:
                        payload['weather'].append({
                            'name': name,
                            'effect': _clean_text(row[weather_effect_i]) if weather_effect_i >= 0 else '',
                            'source': 'fancy_items_csv',
                        })

    if INV_CSV_PATH.exists():
        with INV_CSV_PATH.open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.reader(f))
        if len(rows) >= 3:
            category_row = rows[0]
            header_row = rows[1]
            categories = []
            current = ''
            for cell in category_row:
                if _clean_text(cell):
                    current = _clean_text(cell)
                categories.append(current or 'Unknown')
            for row in rows[2:]:
                if not row or not any(_clean_text(cell) for cell in row):
                    continue
                while len(row) < len(header_row):
                    row.append('')
                per_category = {}
                for i, value in enumerate(row):
                    category = categories[i]
                    key = _clean_text(header_row[i]) or f'col_{i}'
                    per_category.setdefault(category, {})[key] = _clean_text(value)
                for category, fields in per_category.items():
                    name = fields.get('Name', '')
                    if not name:
                        continue
                    payload['inventory'].append({
                        'category': category,
                        'name': name,
                        'cost': fields.get('Cost', ''),
                        'description': fields.get('Description', ''),
                        'mod': fields.get('Mod', ''),
                        'slot': fields.get('Slot', ''),
                        'source': 'fancy_inventory_csv',
                    })
    existing_names = {
        _normalize_match_text(entry.get('name', ''))
        for bucket in ('food_items', 'held_items', 'inventory', 'weapons', 'weather')
        for entry in payload.get(bucket, [])
        if isinstance(entry, dict) and entry.get('name')
    }
    for entry in load_item_catalog().values():
        name = (entry.name or '').strip()
        if not name:
            continue
        norm = _normalize_match_text(name)
        if not norm or norm in existing_names:
            continue
        payload['inventory'].append({
            'category': 'Foundry Gear',
            'name': name,
            'cost': '',
            'description': (entry.description or '').strip(),
            'mod': '',
            'slot': '',
            'source': 'foundry_core_gear',
        })
        existing_names.add(norm)
    return payload


payload = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'classes': graph.get('classes', []),
    'nodes': graph.get('nodes', []),
    'edges': graph.get('edges', []),
    'features': features,
    'edges_catalog': edges,
    'poke_edges_catalog': poke_edges,
    'skills': skills,
    'skill_rules': skill_rules,
    'feature_slots_by_rank': feature_slots_by_rank,
    'pokemon': {
        'species': filter_user_selectable_species(_read_json(SPECIES_PATH, [])),
        'evolution_min_level': _read_json(EVOLUTION_MIN_LEVELS_PATH, {}),
    },
    'items': _load_item_models(),
}

if class_mechanics:
    for node in payload['nodes']:
        if node.get('type') != 'class':
            continue
        name = node.get('name') or ''
        if not name:
            continue
        mechanics = class_mechanics.get(name)
        if mechanics:
            node['mechanics'] = mechanics

skill_descriptions = _extract_rulebook_skill_descriptions()
if skill_descriptions:
    desc_by_norm = { _normalize_match_text(name): desc for name, desc in skill_descriptions.items() }
    skills_catalog = []
    for skill in skills:
        key = _normalize_match_text(skill)
        desc = desc_by_norm.get(key, '')
        if desc:
            skills_catalog.append({
                'name': skill,
                'description': desc,
                'source': 'PTU 1.05 Core',
            })
    if skills_catalog:
        payload['skills_catalog'] = skills_catalog

pdf_content = _load_pdf_content(PDF_CONTENT)

if pdf_content.get('features'):
    existing = {f['name'].lower() for f in payload['features'] if f.get('name')}
    for entry in pdf_content['features']:
        name = _clean_text(entry.get('name'))
        if not name or name.lower() in existing:
            continue
        tags = entry.get('tags') or []
        if isinstance(tags, list):
            tags_raw = ' '.join(f'[{tag}]' for tag in tags if tag)
        else:
            tags_raw = _clean_text(tags)
        payload['features'].append({
            'name': name,
            'tags': tags_raw,
            'prerequisites': _clean_text(entry.get('prerequisites')),
            'frequency': _clean_text(entry.get('frequency')),
            'effects': _clean_text(entry.get('effects')),
        })
        existing.add(name.lower())

if pdf_content.get('edges'):
    existing = {e['name'].lower() for e in payload['edges_catalog'] if e.get('name')}
    for entry in pdf_content['edges']:
        name = _clean_text(entry.get('name'))
        if not name or name.lower() in existing:
            continue
        payload['edges_catalog'].append({
            'name': name,
            'prerequisites': _clean_text(entry.get('prerequisites')),
            'effects': _clean_text(entry.get('effects')),
        })
        existing.add(name.lower())

if pdf_content.get('skills'):
    existing = {s.lower() for s in payload['skills'] if s}
    for entry in pdf_content['skills']:
        name = _clean_text(entry.get('name') or entry)
        if not name or name.lower() in existing:
            continue
        payload['skills'].append(name)
        existing.add(name.lower())

# Fill missing class tiers for classes without unlockables by inferring from feature prerequisites.
nodes_by_id = {node.get('id'): node for node in payload['nodes']}
edges = list(payload.get('edges', []))
for cls in payload['classes']:
    tiers = cls.get('tiers') or {}
    if tiers:
        continue
    class_name = cls.get('name') or ''
    class_key = _normalize_key(class_name)
    if not class_key:
        continue
    matched = []
    for feat in features:
        feat_name = feat.get('name') or ''
        prereq = feat.get('prerequisites') or ''
        if _normalize_key(feat_name) == class_key or class_key in _normalize_key(prereq):
            matched.append(feat)
    if not matched:
        continue
    tier_ids = []
    for feat in matched:
        feat_name = feat.get('name') or ''
        if not feat_name:
            continue
        node_id = f"feature:{feat_name}"
        tier_ids.append(node_id)
        if node_id not in nodes_by_id:
            node = {
                'id': node_id,
                'type': 'feature',
                'name': feat_name,
                'rank': 1,
                'tags': _split_tags(feat.get('tags') or ''),
                'prerequisites': feat.get('prerequisites', ''),
                'frequency': feat.get('frequency', ''),
                'effects': feat.get('effects', ''),
                'level_requirements': [],
                'prereq_options': [],
                'exceptions': [],
            }
            nodes_by_id[node_id] = node
            payload['nodes'].append(node)
        edges.append({
            'from': cls.get('id'),
            'to': node_id,
            'type': 'unlock',
            'rank': 1,
            'prerequisites': feat.get('prerequisites', ''),
            'exceptions': [],
        })
    cls['tiers'] = {'1': tier_ids}

# Ensure nodes exist for all features/edges so prereq links can be built.
for feat in payload['features']:
    node_id = f"feature:{feat.get('name') or ''}"
    if not feat.get('name') or node_id in nodes_by_id:
        continue
    node = {
        'id': node_id,
        'type': 'feature',
        'name': feat.get('name') or '',
        'rank': feat.get('rank', 1) or 1,
        'tags': _split_tags(feat.get('tags') or ''),
        'prerequisites': feat.get('prerequisites', ''),
        'frequency': feat.get('frequency', ''),
        'effects': feat.get('effects', ''),
        'level_requirements': [],
        'prereq_options': [],
        'exceptions': [],
    }
    nodes_by_id[node_id] = node
    payload['nodes'].append(node)

for edge in payload['edges_catalog']:
    node_id = f"edge:{edge.get('name') or ''}"
    if not edge.get('name') or node_id in nodes_by_id:
        continue
    node = {
        'id': node_id,
        'type': 'edge',
        'name': edge.get('name') or '',
        'rank': 1,
        'tags': [],
        'prerequisites': edge.get('prerequisites', ''),
        'frequency': '',
        'effects': edge.get('effects', ''),
        'level_requirements': [],
        'prereq_options': [],
        'exceptions': [],
    }
    nodes_by_id[node_id] = node
    payload['nodes'].append(node)


def _escape_regex(text: str) -> str:
    return re.escape(text or '')


def _match_names_in_prereq(prereq: str, names: list[str]) -> list[str]:
    if not prereq:
        return []
    text = _normalize_match_text(prereq)
    out = []
    for name in names:
        trimmed = (name or '').strip()
        if len(trimmed) < 3:
            continue
        norm = _normalize_match_text(trimmed)
        if not norm:
            continue
        padded = f" {text} "
        if f" {norm} " in padded:
            out.append(trimmed)
    return out


def _match_skill_prereqs(prereq: str, names: list[str]) -> list[str]:
    if not prereq:
        return []
    text = _normalize_match_text(prereq)
    ranks = r"(Pathetic|Untrained|Novice|Adept|Expert|Master)"
    out = []
    for name in names:
        trimmed = (name or '').strip()
        if len(trimmed) < 3:
            continue
        alias_list = skill_aliases.get(trimmed) or [_normalize_match_text(trimmed)]
        for alias in alias_list:
            if not alias:
                continue
            # Rank before skill
            pattern = re.compile(rf"{ranks}\\s+{re.escape(alias)}\\b", re.IGNORECASE)
            if pattern.search(text):
                out.append(trimmed)
                break
            # Skill before rank
            pattern = re.compile(rf"{re.escape(alias)}\\s+(at\\s+)?{ranks}\\b", re.IGNORECASE)
            if pattern.search(text):
                out.append(trimmed)
                break
    return out


def _match_generic_skill_groups(prereq: str) -> bool:
    if not prereq:
        return False
    text = _normalize_match_text(prereq)
    if re.search(r"\\bany\\s+\\d*\\s*skills?\\b", text):
        return True
    if re.search(r"\\b(one|two|three|four|five|six|seven|eight|nine|ten|\\d+)\\s+skills?\\b", text):
        return True
    if "type linked skill" in text or "type-linked skill" in text:
        return True
    if "mentor skill" in text:
        return True
    return False


def _match_stat_prereqs(prereq: str) -> list[str]:
    if not prereq:
        return []
    text = _normalize_match_text(prereq)
    out = []
    for stat_key, aliases in stat_aliases.items():
        for alias in aliases:
            alias_norm = _normalize_match_text(alias)
            if not alias_norm:
                continue
            pattern = re.compile(rf"\\b{re.escape(alias_norm)}\\b\\s*(\\d+)?", re.IGNORECASE)
            if pattern.search(text):
                out.append(stat_key)
                break
    return out


def _match_capability_prereqs(prereq: str) -> list[str]:
    if not prereq:
        return []
    text = _normalize_match_text(prereq)
    out = []
    for cap_key, aliases in capability_aliases.items():
        for alias in aliases:
            alias_norm = _normalize_match_text(alias)
            if not alias_norm:
                continue
            pattern = re.compile(rf"\\b{re.escape(alias_norm)}\\b\\s*(\\d+)?", re.IGNORECASE)
            if pattern.search(text):
                out.append(cap_key)
                break
    return out


feature_names = [f.get('name') for f in payload['features'] if f.get('name')]
edge_names = [e.get('name') for e in payload['edges_catalog'] if e.get('name')]
skill_names = [s for s in payload['skills'] if s]
class_names = [c.get('name') for c in payload['classes'] if c.get('name')]

class_by_norm = {}
for name in class_names:
    key = _normalize_key(name)
    if key:
        class_by_norm[key] = name
    if 'playtest' in name.lower():
        stripped = _normalize_key(name.replace('playtest', ''))
        if stripped:
            class_by_norm[stripped] = name

skill_aliases = {}
for skill in skill_names:
    normalized = _normalize_match_text(skill)
    alias_set = {normalized}
    if normalized.endswith(' ed'):
        alias_set.add(normalized.replace(' ed', ' education'))
        alias_set.add(normalized.replace(' ed', ' ed.'))
    if 'pokemon' in normalized:
        alias_set.add(normalized.replace('pokemon', 'pokemon'))
    skill_aliases[skill] = sorted(alias_set)

stat_nodes = {
    'hp': 'HP',
    'atk': 'Attack',
    'def': 'Defense',
    'spatk': 'Special Attack',
    'spdef': 'Special Defense',
    'spd': 'Speed',
}

capability_nodes = {
    'power': 'Power',
    'high_jump': 'High Jump',
    'long_jump': 'Long Jump',
    'overland': 'Overland',
    'swim': 'Swim',
    'throwing_range': 'Throwing Range',
}

stat_aliases = {
    'hp': ['hp', 'hit points'],
    'atk': ['atk', 'attack'],
    'def': ['def', 'defense'],
    'spatk': ['spatk', 'special attack', 'sp at', 'sp. atk', 'sp. attack'],
    'spdef': ['spdef', 'special defense', 'sp def', 'sp. def', 'sp. defense'],
    'spd': ['spd', 'speed'],
}

capability_aliases = {
    'power': ['power'],
    'high_jump': ['high jump'],
    'long_jump': ['long jump'],
    'overland': ['overland'],
    'swim': ['swim'],
    'throwing_range': ['throwing range', 'throw range', 'throw'],
}

# Ensure nodes for skills so prereq edges can connect.
for skill in skill_names:
    node_id = f"skill:{skill}"
    if node_id in nodes_by_id:
        continue
    node = {
        'id': node_id,
        'type': 'skill',
        'name': skill,
        'rank': 0,
        'tags': [],
        'prerequisites': '',
        'frequency': '',
        'effects': '',
        'level_requirements': [],
        'prereq_options': [],
        'exceptions': [],
    }
    nodes_by_id[node_id] = node
    payload['nodes'].append(node)

for stat_key, stat_label in stat_nodes.items():
    node_id = f"stat:{stat_key}"
    if node_id in nodes_by_id:
        continue
    node = {
        'id': node_id,
        'type': 'stat',
        'name': stat_label,
        'rank': 0,
        'tags': [],
        'prerequisites': '',
        'frequency': '',
        'effects': '',
        'level_requirements': [],
        'prereq_options': [],
        'exceptions': [],
    }
    nodes_by_id[node_id] = node
    payload['nodes'].append(node)

for cap_key, cap_label in capability_nodes.items():
    node_id = f"capability:{cap_key}"
    if node_id in nodes_by_id:
        continue
    node = {
        'id': node_id,
        'type': 'capability',
        'name': cap_label,
        'rank': 0,
        'tags': [],
        'prerequisites': '',
        'frequency': '',
        'effects': '',
        'level_requirements': [],
        'prereq_options': [],
        'exceptions': [],
    }
    nodes_by_id[node_id] = node
    payload['nodes'].append(node)


def _add_prereq_edges(entry_name: str, prereq: str, kind: str):
    if not entry_name or not prereq:
        return
    targets = (
        _match_names_in_prereq(prereq, feature_names)
        + _match_names_in_prereq(prereq, edge_names)
        + _match_names_in_prereq(prereq, skill_names)
        + _match_skill_prereqs(prereq, skill_names)
    )
    stat_targets = _match_stat_prereqs(prereq)
    capability_targets = _match_capability_prereqs(prereq)
    class_targets = set()
    # Class name matches (normalized, including playtest-stripped).
    normalized_prereq = _normalize_key(prereq)
    if normalized_prereq:
        for key, name in class_by_norm.items():
            if key and key in normalized_prereq:
                class_targets.add(name)
    # "X Class Features" patterns link to class.
    for match in re.findall(r"\b\d+\s+([A-Za-z][A-Za-z '\\-]+?)\s+Features?\b", prereq):
        key = _normalize_key(match)
        if key and key in class_by_norm:
            class_targets.add(class_by_norm[key])
    targets.extend(sorted(class_targets))
    for stat_key in stat_targets:
        targets.append(stat_key)
    for cap_key in capability_targets:
        targets.append(cap_key)
    if _match_generic_skill_groups(prereq):
        targets.extend(skill_names)
    for target in targets:
        if target in class_targets:
            from_id = f"class:{target}"
        elif target in feature_names:
            from_id = f"feature:{target}"
        elif target in edge_names:
            from_id = f"edge:{target}"
        elif target in skill_names:
            from_id = f"skill:{target}"
        elif target in stat_nodes:
            from_id = f"stat:{target}"
        elif target in capability_nodes:
            from_id = f"capability:{target}"
        else:
            from_id = f"class:{target}"
        to_id = f"{kind}:{entry_name}"
        edges.append({
            'from': from_id,
            'to': to_id,
            'type': 'prereq',
            'rank': 0,
            'prerequisites': prereq,
            'exceptions': [],
        })


for feat in payload['features']:
    _add_prereq_edges(feat.get('name'), feat.get('prerequisites', ''), 'feature')

for edge in payload['edges_catalog']:
    _add_prereq_edges(edge.get('name'), edge.get('prerequisites', ''), 'edge')

unique_edges = []
seen_edges = set()
for entry in edges:
    key = (
        entry.get('from'),
        entry.get('to'),
        entry.get('type'),
        entry.get('prerequisites', ''),
    )
    if key in seen_edges:
        continue
    seen_edges.add(key)
    unique_edges.append(entry)

payload['edges'] = unique_edges

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
STATIC_CHARACTER_DIR = STATIC_DIR / 'AutoPTUCharacter'
STATIC_CHARACTER_DIR.mkdir(parents=True, exist_ok=True)

out_reports = REPORTS_DIR / 'character_creation.json'
out_reports.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

out_static = STATIC_DIR / 'character_creation.json'
json_text = json.dumps(payload, indent=2, ensure_ascii=False)
out_static.write_text(json_text, encoding='utf-8')
out_static_character = STATIC_CHARACTER_DIR / 'character_creation.json'
out_static_character.write_text(json_text, encoding='utf-8')

create_path = STATIC_DIR / 'create.html'
if create_path.exists():
    html = create_path.read_text(encoding='utf-8')
    marker = '<!--CHARACTER_DATA-->'
    embedded = json.dumps(payload, ensure_ascii=False)
    script_tag = f'<script id="character-data" type="application/json">{embedded}</script>'
    if marker in html:
        html = html.replace(marker, script_tag)
    else:
        html = re.sub(
            r'<script id="character-data" type="application/json">.*?</script>',
            script_tag,
            html,
            count=1,
            flags=re.DOTALL,
        )
    create_path.write_text(html, encoding='utf-8')
