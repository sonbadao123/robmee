import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

target_pos = (-10.86, 31.45, 43.43)

base = b.unity_player_base
print(f'Scanning UnityPlayer.dll (Base 0x{base:X}) .data segment for ViewProjection matrix...')

# Read .data segment: RVA 0x2100000 to 0x2300000 (about 2MB)
chunk_size = 0x8000 # 32KB
found = []

for rva in range(0x2100000, 0x2300000, chunk_size):
    buf = b.read_bytes(base + rva, chunk_size)
    if not buf: continue
    for off in range(0, len(buf) - 64, 4):
        vm = struct.unpack('<16f', buf[off:off+64])
        if any(math.isnan(x) or math.isinf(x) for x in vm): continue
        # Must have no subnormals
        if any(0 < abs(x) < 1e-6 for x in vm): continue
        # Must have at least 8 non-zeros
        if sum(1 for x in vm if abs(x) > 1e-4) < 8: continue
        # Try projecting
        s = KernelDriverBridge.world_to_screen(target_pos, vm, 1920, 1080)
        if s:
            sx, sy = s
            if 250 <= sx <= 450 and 350 <= sy <= 550:
                addr = base + rva + off
                found.append((hex(addr), hex(rva + off), sx, sy, vm))
                print(f'[!] HIT at UnityPlayer + 0x{rva + off:X} (0x{addr:X}): Screen = ({sx}, {sy})')

print(f'Total matches in UnityPlayer .data: {len(found)}')
