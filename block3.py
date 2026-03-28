lines=open('auto_ptu/rules/battle_state.py', encoding='utf-8').read().splitlines()
for idx in range(6445, 6505):
    print(f'{idx+1:05d}: {lines[idx]}')
