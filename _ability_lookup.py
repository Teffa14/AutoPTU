import csv
from pathlib import Path
root=Path(r'C:\Users\tefa1\AutoPTU')
abilities_csv=root/'files'/'Copia de Fancy PTU 1.05 Sheet - Version Hisui - Abilities Data.csv'
need={'Electric Surge','Grassy Surge','Misty Surge','Psychic Surge','Soundproof','Thick Fat','Volt Absorb','Water Veil','Water Bubble','Dragon\'s Maw','Transistor','Steelworker','Punk Rock','Tough Claws','Ice Scales','Full Metal Body','Mirror Armor','Storm Drain','Lightning Rod','Motor Drive'}
with abilities_csv.open(encoding='utf-8', errors='ignore') as f:
    reader=csv.DictReader(f)
    for row in reader:
        name=(row.get('Name') or row.get('name') or '').strip()
        if name in need:
            print(name, row.get('Frequency'), row.get('Effect'), row.get('Trigger'), row.get('Keywords'))
