import csv
from pathlib import Path
root=Path(r'C:\Users\tefa1\AutoPTU')
abilities_csv=root/'files'/'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv'

names=[]
with abilities_csv.open(encoding='utf-8', errors='ignore') as f:
    reader=csv.DictReader(f)
    for row in reader:
        name=(row.get('name') or row.get('Name') or '').strip()
        if name:
            names.append(name)

def normalize(name: str):
    base=name
    import re
    base=re.sub(r"\s*\[[^\]]+\]\s*", "", base).strip()
    parts=[p.strip() for p in re.split(r"/", base) if p.strip()]
    return parts if parts else [base]

norm_names=[]
for n in names:
    norm_names.extend(normalize(n))
abilities=sorted(set(norm_names))

code_paths=[root/'auto_ptu'/'rules', root/'auto_ptu'/'rules'/'hooks', root/'auto_ptu'/'rules'/'abilities']
code_files=[]
for p in code_paths:
    code_files += list(p.rglob('*.py'))
text='\n'.join([p.read_text(encoding='utf-8', errors='ignore') for p in code_files]).lower()

missing=[]
for name in abilities:
    if name.lower() not in text:
        missing.append(name)

print('Abilities in CSV (normalized):', len(abilities))
print('Referenced in code (substring):', len(abilities)-len(missing))
print('Missing:', len(missing))
print('---')
print('\n'.join(missing[:200]))
