import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

def inspect_node(addr, name):
    print(f'=== {name}: 0x{addr:X} ===')
    data = b.read_bytes(addr, 0x40)
    if not data:
        print('  None')
        return
    q = struct.unpack('<8Q', data)
    for i, val in enumerate(q):
        go_name = ''
        if 0x10000000 < val < 0x7FFFFFFFFFFF:
            for noff in (0x60, 0x58, 0x50, 0x48):
                nptr = b.read_uint64(val + noff)
                if 0x10000000 < nptr < 0x7FFFFFFFFFFF:
                    s = b.read_string(nptr, 32)
                    if s and len(s) >= 2 and s.isprintable():
                        go_name = f' [GO Name: \"{s}\" via +0x{noff:X}]'
                        break
        print(f'  +0x{i*8:02X}: 0x{val:X}{go_name}')

inspect_node(0x2C9103D8CA8, 'LastActive (+0x20)')
inspect_node(0x2C93B328C48, 'MainCam (+0x18)')
inspect_node(0x2C93D4230D0, 'LastTagged (+0x00)')
