import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

cam_comp = 0x2CB270171A0
test_pos = (-304.8, 11.95, 538.12)

print(f'Scanning Camera component 0x{cam_comp:X} for valid ViewMatrix...')

raw = b.read_bytes(cam_comp, 0x800)
found_matrices = []

for off in range(0, len(raw) - 64, 4):
    vm = struct.unpack('<16f', raw[off:off+64])
    if any(math.isnan(x) or math.isinf(x) for x in vm):
        continue
    screen = KernelDriverBridge.world_to_screen(test_pos, vm, 1920, 1080)
    if screen:
        x, y = screen
        if -200 < x < 2100 and -200 < y < 1200:
            print(f'  [!] HIT at Camera + 0x{off:X}! Projects to Screen ({x}, {y})')
            found_matrices.append((off, vm, screen))

print(f'Total valid projection hits: {len(found_matrices)}')
