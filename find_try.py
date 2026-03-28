lines = open('auto_ptu/rules/battle_state.py', encoding='utf-8').read().splitlines()
for i in range(7800, 7845):
    if 'try:' in lines[i]:
        print(i+1, lines[i])
