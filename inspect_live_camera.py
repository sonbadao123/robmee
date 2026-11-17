import sys
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge
import struct

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')
print(f"Connected: {b.connected}, PID: {b.target_pid}, CR3: 0x{b.cr3:X}, UnityPlayer: 0x{b.unity_player_base:X}")

# 1. Check static VP at UnityPlayer + 0x2111C90
if b.unity_player_base:
    raw_static = b.read_bytes(b.unity_player_base + 0x2111C90, 64)
    if raw_static and len(raw_static) == 64:
        floats = struct.unpack('<16f', raw_static)
        print("\n=== STATIC VP (UnityPlayer + 0x2111C90) ===")
        for r in range(4):
            print(f"  [{r}] " + " ".join(f"{floats[r*4 + c]:10.4f}" for c in range(4)))

# 2. Check Camera at 0x2CFF2ABA780
cam = 0x2CFF2ABA780
print(f"\n=== CAMERA 0x{cam:X} ===")
for off in [0x70, 0xB0, 0xDC, 0x11C, 0xF0, 0x140, 0x160]:
    raw = b.read_bytes(cam + off, 64)
    if raw and len(raw) == 64:
        floats = struct.unpack('<16f', raw)
        non_zero = sum(1 for x in floats if abs(x) > 1e-4)
        print(f"Offset 0x{off:X} (non_zero={non_zero}):")
        for r in range(4):
            print(f"    " + " ".join(f"{floats[r*4 + c]:10.4f}" for c in range(4)))
