import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

node = 0x2C9103D8CA8
visited = set()
count = 0
found_objects = []

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 4000:
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
        found_objects.append((count, hex(node), hex(go), name))
    node = next_node

print(f'Total nodes traversed: {count}, named objects: {len(found_objects)}')

# Check keywords
keywords = ['kedanh', 'player', 'character', 'cop', 'robber', 'bot', 'pedestrian', 'human', 'actor', 'sparkasse', 'battle', 'model', 'mesh', 'unit', 'car', 'vehicle', 'pickup', 'truck']
matches = []
for idx, n, g, name in found_objects:
    low = name.lower()
    for kw in keywords:
        if kw in low:
            matches.append((idx, n, g, name))
            break

print(f'Matched {len(matches)} objects:')
for idx, n, g, name in matches[:50]:
    print(f'  [{idx}] {name} (GO: {g})')
