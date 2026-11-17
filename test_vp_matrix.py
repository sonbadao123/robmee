import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

base = b.unity_player_base
vp_addr = base + 0x2111C90
raw = b.read_bytes(vp_addr, 64)
vm = struct.unpack('<16f', raw)

print(f'View-Projection Matrix at UnityPlayer + 0x2111C90 (0x{vp_addr:X}):')
for r in range(4):
    print(' ', [f'{x:12.6f}' for x in vm[r*4:r*4+4]])

# Test known player positions
players = [
    ('Player on left (backpack)', (-10.86, 31.45, 43.43)),
    ('Player 2', (-11.19, 31.45, 35.68)),
    ('Player 3', (-2.56, 31.45, 40.05)),
    ('Player 4', (-2.52, 31.45, 40.20)),
    ('Player 5', (-0.92, 31.78, 2.75)),
    ('My Car', (1.22, 31.45, 37.14)),
]

print('\nProjected Screen Coordinates:')
for name, pos in players:
    s = KernelDriverBridge.world_to_screen(pos, vm, 1920, 1080)
    print(f'  {name:30} {str(pos):30} -> Screen: {s}')
