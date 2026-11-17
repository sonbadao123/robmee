import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

cam = 0x2CB270171A0
raw = b.read_bytes(cam, 0x400)
q = struct.unpack('<128Q', raw)

print(f'Pointer members in Camera 0x{cam:X}:')
for idx, val in enumerate(q):
    if 0x10000000 < val < 0x7FFFFFFFFFFF:
        # read 64 bytes at val
        target_raw = b.read_bytes(val, 64)
        if target_raw:
            # Check if target_raw has floats
            floats = struct.unpack('<16f', target_raw)
            float_str = ''
            if not any(f != 0 and (abs(f) < 1e-4 or abs(f) > 10000) for f in floats[:8]):
                float_str = f' [floats: {floats[:4]}]'
            print(f'  +0x{idx*8:03X}: 0x{val:X}{float_str}')
