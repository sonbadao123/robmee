import sys
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
visited = set()
players = []
cams = []

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF:
    visited.add(node)
    count += 1
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        nptr = b.read_uint64(go + 0x50)
        if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
            name = b.read_string(nptr, 48)
            if name:
                if name.startswith('Player_Man') or name.startswith('Player_Woman') or 'charactertarget' in name.lower():
                    comp_arr = b.read_uint64(go + 0x20)
                    pTrans = b.read_uint64(comp_arr + 8) if comp_arr else 0
                    pHier = b.read_uint64(pTrans + 0x28) if pTrans else 0
                    pos = b.read_vec3(pHier + 0x90) if pHier else None
                    players.append((count, name, hex(go), pos))
                elif 'cam' in name.lower() and not any(x in name.lower() for x in ['collider', 'point', 'obstacle', 'monitor', 'lod']):
                    comp_arr = b.read_uint64(go + 0x20)
                    pTrans = b.read_uint64(comp_arr + 8) if comp_arr else 0
                    pHier = b.read_uint64(pTrans + 0x28) if pTrans else 0
                    pos = b.read_vec3(pHier + 0x90) if pHier else None
                    cams.append((count, name, hex(go), pos))
    node = b.read_uint64(node + 0x08)

print(f'Total nodes: {count}')
print(f'Players ({len(players)}):')
for c, name, g, pos in players:
    print(f'  [{c}] {name} (GO {g}): Pos = {pos}')

print(f'\nCameras ({len(cams)}):')
for c, name, g, pos in cams:
    print(f'  [{c}] {name} (GO {g}): Pos = {pos}')
