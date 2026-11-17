import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

node = 0x2C9103D8CA8
visited = set()
count = 0
characters = []

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 15000:
    visited.add(node)
    count += 1
    
    go = b.read_uint64(node + 0x10)
    if 0x10000000 < go < 0x7FFFFFFFFFFF:
        name_ptr = b.read_uint64(go + 0x50)
        if 0x10000000 < name_ptr < 0x7FFFFFFFFFFF:
            name = b.read_string(name_ptr, 64)
            if name and ('charactertarget' in name.lower() or 'character' in name.lower() or 'player' in name.lower()):
                if not any(x in name.lower() for x in ['safe', 'delplayer', 'battlepass', 'video', 'card']):
                    # Read position: go + 0x20 -> comp_array -> comp[0] (+0x08) -> pTransform
                    pCompArray = b.read_uint64(go + 0x20)
                    pos = None
                    if 0x10000000 < pCompArray < 0x7FFFFFFFFFFF:
                        pTransform = b.read_uint64(pCompArray + 0x08)
                        if 0x10000000 < pTransform < 0x7FFFFFFFFFFF:
                            pHierarchy = b.read_uint64(pTransform + 0x28)
                            if 0x10000000 < pHierarchy < 0x7FFFFFFFFFFF:
                                pos = b.read_vec3(pHierarchy + 0x90)
                    characters.append((count, hex(node), hex(go), name, pos))
    
    node = b.read_uint64(node + 0x08)

print(f'Total characters found: {len(characters)}')
for c, n, g, name, pos in characters:
    print(f'  [{c}] {name} (GO: {g}): Position = {pos}')
