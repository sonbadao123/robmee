import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

# Target player visible on screen
# Standing near building on the left:
target_pos = (-10.86, 31.45, 43.43)
# Expected screen position roughly:
# X around 300..450, Y around 380..520

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
visited = set()
found_matrices = []

print(f'Searching all GameObjects in GOM for matrix projecting {target_pos} to (~355, ~445)...')

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 16000:
    visited.add(node)
    count += 1
    go = b.read_uint64(node + 0x10)
    if go and 0x10000000 < go < 0x7FFFFFFFFFFF:
        comp_arr = b.read_uint64(go + 0x20)
        if comp_arr and 0x10000000 < comp_arr < 0x7FFFFFFFFFFF:
            # Check up to 8 components per GameObject
            for c_idx in range(8):
                pComp = b.read_uint64(comp_arr + c_idx * 16 + 8)
                if pComp and 0x10000000 < pComp < 0x7FFFFFFFFFFF:
                    # Read 0x400 bytes of component
                    raw = b.read_bytes(pComp, 0x400)
                    if not raw or len(raw) < 64: continue
                    for off in range(0, len(raw) - 64, 4):
                        vm = struct.unpack('<16f', raw[off:off+64])
                        if any(math.isnan(x) or math.isinf(x) for x in vm): continue
                        # Must have at least 6 non-zeros
                        if sum(1 for x in vm if abs(x) > 1e-4) < 6: continue
                        # Project
                        s = KernelDriverBridge.world_to_screen(target_pos, vm, 1920, 1080)
                        if s:
                            sx, sy = s
                            # Check if matches the player on the left!
                            if 200 <= sx <= 500 and 300 <= sy <= 600:
                                nptr = b.read_uint64(go + 0x50)
                                name = b.read_string(nptr, 48) if nptr else 'unknown'
                                found_matrices.append((name, hex(go), hex(pComp), hex(off), sx, sy, vm))
                                print(f'[*** MATCH ***] GO: "{name}" (0x{go:X}), Comp: 0x{pComp:X} + 0x{off:X} -> Screen: ({sx}, {sy})')
    node = b.read_uint64(node + 0x08)

print(f'\nTotal matches found: {len(found_matrices)}')
