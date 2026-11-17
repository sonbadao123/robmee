import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

cam_comp = 0x2C93D789FA0
print(f'Inspecting Camera Component 0x{cam_comp:X}:')
data = b.read_bytes(cam_comp, 0x80)
q = struct.unpack('<16Q', data)
for i, val in enumerate(q):
    go_name = ''
    if 0x10000000 < val < 0x7FFFFFFFFFFF:
        for noff in (0x50, 0x60, 0x58, 0x48):
            nptr = b.read_uint64(val + noff)
            if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
                s = b.read_string(nptr, 32)
                if s and len(s) >= 2 and s.isprintable():
                    go_name = f' [GO: "{s}" via +0x{noff:X}]'
                    break
    print(f'  +0x{i*8:02X}: 0x{val:X}{go_name}')
