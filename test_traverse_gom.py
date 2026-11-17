import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

node = 0x2C9103D8CA8
visited = set()
count = 0
found_objects = []

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 300:
    visited.add(node)
    count += 1
    
    # Read GameObject from +0x10
    go = b.read_uint64(node + 0x10)
    name = ''
    if 0x10000000 < go < 0x7FFFFFFFFFFF:
        # Check name offsets
        for noff in (0x50, 0x60, 0x58, 0x48):
            nptr = b.read_uint64(go + noff)
            if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
                s = b.read_string(nptr, 64)
                if s and len(s) >= 2 and s.isprintable():
                    name = s
                    break
    
    next_node = b.read_uint64(node + 0x08)
    prev_node = b.read_uint64(node + 0x00)
    found_objects.append((count, hex(node), hex(go), name, hex(next_node)))
    node = next_node

print(f'Total nodes traversed: {len(found_objects)}')
for c, n, g, name, nxt in found_objects[:40]:
    print(f'[{c}] Node {n} -> GO {g}: "{name}" -> Next {nxt}')

print('...')
# Check if any have "player", "rob", "cop", "human", "character", "kedanhcaptraitim"
matching = [x for x in found_objects if any(k in x[3].lower() for k in ['player', 'cop', 'rob', 'kedanh', 'human', 'char', 'body', 'motel', 'car', 'truck'])]
print(f'Matching objects ({len(matching)}):')
for x in matching:
    print('  ', x)
