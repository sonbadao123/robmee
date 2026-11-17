import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)
print(f'GOM: 0x{gom:X}, Node: 0x{node:X}')

cameras = []
characters = []
count = 0
visited = set()

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 16000:
    visited.add(node)
    count += 1
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        nptr = b.read_uint64(go + 0x50)
        if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
            name = b.read_string(nptr, 64)
            if name:
                low = name.lower()
                # Check for camera
                if 'cam' in low or 'camera' in low:
                    if not any(x in low for x in ['collider', 'point', 'obstacle', 'monitor', 'lod']):
                        cameras.append((count, name, hex(go)))
                # Check for character / player
                if 'charactertarget' in low or 'kedanhcaptraitim' in low or (('player' in low or 'rob' in low or 'man' in low or 'character' in low) and not any(x in low for x in ['safe', 'delplayer', 'card', 'video', 'pack', 'lod', 'probe', 'reflection', 'light', 'body', 'rigidbody', 'interact', 'action', 'anim'])):
                    # Get position
                    pComp = b.read_uint64(go + 0x20)
                    pos = None
                    if pComp and 0x10000000 < pComp < 0x7FFFFFFFFFFF:
                        pTrans = b.read_uint64(pComp + 8)
                        if pTrans and 0x10000000 < pTrans < 0x7FFFFFFFFFFF:
                            pHier = b.read_uint64(pTrans + 0x28)
                            if pHier and 0x10000000 < pHier < 0x7FFFFFFFFFFF:
                                pos = b.read_vec3(pHier + 0x90)
                    characters.append((count, name, hex(go), pos))
    node = b.read_uint64(node + 0x08)

print(f'\nTotal nodes: {count}')
print(f'Cameras ({len(cameras)}):')
for c, n, g in cameras:
    print(f'  [{c}] {n} (GO: {g})')

print(f'\nCharacters ({len(characters)}):')
for c, n, g, pos in characters:
    print(f'  [{c}] {n} (GO: {g}): Pos = {pos}')
