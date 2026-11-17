import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
visited = set()
candidates = []

print('Scanning all 18,398 nodes in GOM for 3D perspective camera...')

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF:
    visited.add(node)
    count += 1
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        comp_arr = b.read_uint64(go + 0x20)
        if comp_arr and 0x10000000 < comp_arr < 0x7FFFFFFFFFFF:
            for c_idx in range(1, 8):
                tid = b.read_uint64(comp_arr + c_idx * 16)
                pComp = b.read_uint64(comp_arr + c_idx * 16 + 8)
                if pComp and 0x10000000 < pComp < 0x7FFFFFFFFFFF:
                    # Read 0x200 bytes
                    raw = b.read_bytes(pComp, 0x200)
                    if not raw or len(raw) < 0x80: continue
                    for off in range(0, len(raw) - 64, 4):
                        vm = struct.unpack('<16f', raw[off:off+64])
                        if any(math.isnan(x) or math.isinf(x) for x in vm): continue
                        # Must have at least 8 non-zeros
                        if sum(1 for x in vm if abs(x) > 1e-4) < 8: continue
                        # A 3D camera in Unity has rotation where Row 1 is NOT (0, 0, 1, 0)
                        # and translation is NOT 10,000!
                        # Check translation row 3:
                        tx, ty, tz, tw = vm[12], vm[13], vm[14], vm[15]
                        if abs(tw - 1.0) < 0.01:
                            # Check if translation is within reasonable game world bounds [-5000, 5000]
                            # and NOT at 10000 or -14000
                            if all(abs(t) < 5000 for t in (tx, ty, tz)):
                                r0 = vm[0]**2 + vm[1]**2 + vm[2]**2
                                r1 = vm[4]**2 + vm[5]**2 + vm[6]**2
                                if 0.8 < r0 < 1.2 and 0.8 < r1 < 1.2:
                                    nptr = b.read_uint64(go + 0x50)
                                    name = b.read_string(nptr, 48) if nptr else 'unknown'
                                    candidates.append((count, name, hex(go), hex(pComp), hex(tid), hex(off), vm))
                                    print(f'[FOUND 3D MATRIX] [{count}] {name} (GO 0x{go:X}, Comp 0x{pComp:X}, Tid 0x{tid:X}) + 0x{off:X}')
                                    print(f'   Row 0: {vm[0:4]}')
                                    print(f'   Row 1: {vm[4:8]}')
                                    print(f'   Row 2: {vm[8:12]}')
                                    print(f'   Row 3: {vm[12:16]}')
    node = b.read_uint64(node + 0x08)

print(f'\nTotal 3D matrices found: {len(candidates)}')
