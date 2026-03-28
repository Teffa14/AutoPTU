lines=open('auto_ptu/rules/battle_state.py', encoding='utf-8').read().splitlines()
for idx in range(6470, 6480):
    print(idx+1, repr(lines[idx]))
