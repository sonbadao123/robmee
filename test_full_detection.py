import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)
print(f'Starting scan from GOM 0x{gom:X}, Node 0x{node:X}...')

camera_matrix = None
camera_go = None
targets = []

count = 0
visited = set()

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 15000:
    visited.add(node)
    count += 1
    
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        # Read name from +0x50
        nptr = b.read_uint64(go + 0x50)
        if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
            name = b.read_string(nptr, 40)
            if name:
                name_low = name.lower()
                
                # Check for Camera
                if not camera_matrix and name_low == 'camera':
                    comp_arr = b.read_uint64(go + 0x20)
                    if comp_arr and 0x10000000 < comp_arr < 0x7FFFFFFFFFFF:
                        # Comp[1] is Camera
                        pCam = b.read_uint64(comp_arr + 16 + 8)
                        if pCam and 0x10000000 < pCam < 0x7FFFFFFFFFFF:
                            for m_off in (0xDC, 0xF0, 0x11C, 0x160, 0x2E0, 0x308):
                                vm = b.read_matrix4x4(pCam + m_off)
                                if vm and abs(vm[15]) > 0.0001:
                                    camera_matrix = vm
                                    camera_go = name
                                    print(f'[+] CAMERA FOUND: {name} (GO 0x{go:X}), Matrix at +0x{m_off:X}')
                                    break
                
                # Check for Character
                if 'charactertarget' in name_low or (('player' in name_low or 'rob' in name_low) and not any(x in name_low for x in ['safe', 'delplayer', 'card', 'video', 'pack'])):
                    comp_arr = b.read_uint64(go + 0x20)
                    if comp_arr and 0x10000000 < comp_arr < 0x7FFFFFFFFFFF:
                        pTransform = b.read_uint64(comp_arr + 8)
                        if pTransform and 0x10000000 < pTransform < 0x7FFFFFFFFFFF:
                            pHierarchy = b.read_uint64(pTransform + 0x28)
                            if pHierarchy and 0x10000000 < pHierarchy < 0x7FFFFFFFFFFF:
                                pos = b.read_vec3(pHierarchy + 0x90)
                                if pos and any(abs(x) > 0.01 for x in pos):
                                    targets.append((count, name, hex(go), pos))

    node = b.read_uint64(node + 0x08)

print(f'\nScanned {count} nodes.')
print(f'Camera: {camera_go}, Matrix valid: {camera_matrix is not None}')
print(f'Targets detected: {len(targets)}')
for c, name, g, pos in targets:
    print(f'  [{c}] {name} (GO {g}): Pos = {pos}')
