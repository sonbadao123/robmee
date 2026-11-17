import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

comp = 0x2CBCC016820
test_pos = (-304.8, 11.95, 538.12)

print(f'Testing Camera component 0x{comp:X}...')
raw = b.read_bytes(comp, 0x600)

for off in range(0, len(raw) - 64, 4):
    vm = struct.unpack('<16f', raw[off:off+64])
    if any(math.isnan(x) or math.isinf(x) for x in vm): continue
    screen = KernelDriverBridge.world_to_screen(test_pos, vm, 1920, 1080)
    if screen:
        x, y = screen
        if 0 <= x <= 1920 and 0 <= y <= 1080:
            print(f'  [!] HIT at +0x{off:X}! Screen = ({x}, {y})')
            # Print matrix
            print(f'      Row 0: {vm[0:4]}')
            print(f'      Row 1: {vm[4:8]}')
            print(f'      Row 2: {vm[8:12]}')
            print(f'      Row 3: {vm[12:16]}')
