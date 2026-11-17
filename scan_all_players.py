import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

node = 0x2C9103D8CA8
visited = set()
count = 0
found_players = []

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 15000:
    visited.add(node)
    count += 1
    
    go = b.read_uint64(node + 0x10)
    name = ''
    if 0x10000000 < go < 0x7FFFFFFFFFFF:
        for noff in (0x50, 0x60, 0x58, 0x48):
            nptr = b.read_uint64(go + noff)
            if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
                s = b.read_string(nptr, 64)
                if s and len(s) >= 2 and s.isprintable():
                    name = s
                    break
    
    next_node = b.read_uint64(node + 0x08)
    if name:
        low = name.lower()
        # Look for character, humanoid, rob, cop, enemy, etc.
        if any(k in low for k in ['character', 'cops', 'robber', 'kedanh', 'human', 'actor', 'sparkasse', 'avatar', 'hero', 'agent', 'pawn', 'player', 'bot', 'ragdoll']):
            if not any(exc in low for exc in ['safe', 'delplayer', 'battlepass', 'caret', 'messagebody']):
                found_players.append((count, hex(node), hex(go), name))
    node = next_node

print(f'Total nodes traversed: {count}')
print(f'Found {len(found_players)} player candidates:')
for idx, n, g, name in found_players[:50]:
    print(f'  [{idx}] {name} (GO: {g})')
