import sys
sys.path.append(r'd:\ESP robrun')
from test_find_players import found_objects

for idx, n, g, name in found_objects:
    if 'cam' in name.lower():
        print(f'[{idx}] Node: {n} -> GO {g}: "{name}"')
