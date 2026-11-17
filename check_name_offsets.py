import sys
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)
print(f'GOM: 0x{gom:X}, Node: 0x{node:X}')

for i in range(10):
    go = b.read_uint64(node + 0x10)
    print(f'Node 0x{node:X} -> GO 0x{go:X}')
    for noff in (0x60, 0x58, 0x50, 0x48):
        nptr = b.read_uint64(go + noff)
        s = b.read_string(nptr, 32)
        if s and len(s) >= 2 and s.isprintable():
            print(f'   +0x{noff:X} -> ptr 0x{nptr:X}: "{s}"')
    node = b.read_uint64(node + 0x08)
