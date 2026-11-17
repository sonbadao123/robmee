import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
visited = set()
valid_cams = []

target_pos = (-10.86, 31.45, 43.43)

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 16000:
    visited.add(node)
    count += 1
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        comp_arr = b.read_uint64(go + 0x20)
        if comp_arr and 0x10000000 < comp_arr < 0x7FFFFFFFFFFF:
            for i in range(1, 4):
                tid = b.read_uint64(comp_arr + i * 16)
                if (tid & 0xFF) == 0x13: # Camera
                    pCam = b.read_uint64(comp_arr + i * 16 + 8)
                    if pCam and 0x10000000 < pCam < 0x7FFFFFFFFFFF:
                        nptr = b.read_uint64(go + 0x50)
                        name = b.read_string(nptr, 32) if nptr else 'unknown'
                        # Read matrices at 0x70, 0xDC, 0xF0, 0x11C, 0x2E0, 0x308
                        for off in (0x70, 0xDC, 0xF0, 0x11C, 0x160, 0x2E0, 0x308):
                            raw = b.read_bytes(pCam + off, 64)
                            if raw and len(raw) == 64:
                                vm = struct.unpack('<16f', raw)
                                if any(math.isnan(x) or math.isinf(x) for x in vm): continue
                                # Skip identity
                                if vm[0] == 1.0 and vm[5] == 1.0 and vm[10] == 1.0 and vm[15] == 1.0 and sum(abs(x) for x in vm) == 4.0:
                                    continue
                                non_zeros = sum(1 for x in vm if abs(x) > 1e-4)
                                if non_zeros >= 6:
                                    s = KernelDriverBridge.world_to_screen(target_pos, vm, 1920, 1080)
                                    valid_cams.append((name, hex(go), hex(pCam), hex(off), non_zeros, s))
    node = b.read_uint64(node + 0x08)

print(f'Done scanning. Found {len(valid_cams)} matrix entries:')
for name, g, cam, off, nz, s in valid_cams:
    print(f'  {name} (GO {g}, Cam {cam}) + {off} (non_zero={nz}): Screen = {s}')
