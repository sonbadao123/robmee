import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

cam = 0x2CB270171A0
raw = b.read_bytes(cam, 0x800)

for off in [0x71C, 0x720, 0x728, 0x72C, 0x730]:
    vm = struct.unpack('<16f', raw[off:off+64])
    print(f'=== Offset +0x{off:X} ===')
    for row in range(4):
        print(f'  {vm[row*4:row*4+4]}')
