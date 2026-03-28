import csv
import re
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

base_names=[]
for n in names:
    base=re.sub(r"\s*\[[^\]]+\]\s*", "", n).strip()
    parts=[p.strip() for p in re.split(r"/", base) if p.strip()]
    base_names.extend(parts if parts else [base])
abilities=sorted(set(base_names))

code_paths=[root/'auto_ptu'/'rules', root/'auto_ptu'/'rules'/'hooks', root/'auto_ptu'/'rules'/'abilities']
code_files=[]
for p in code_paths:
    code_files += list(p.rglob('*.py'))
text='\n'.join([p.read_text(encoding='utf-8', errors='ignore') for p in code_files]).lower()
missing=[n for n in abilities if n.lower() not in text]
Path(root/'_ability_missing.txt').write_text('\n'.join(missing), encoding='utf-8')
print('Missing', len(missing))
