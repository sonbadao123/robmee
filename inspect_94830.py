import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
visited = set()

while node and node not in visited and 0x10000000 < node < 0x7FFFFFFFFFFF:
    visited.add(node)
    count += 1
    if 94830 <= count <= 94865:
        go = b.read_uint64(node + 0x10)
        nptr = b.read_uint64(go + 0x50) if go else 0
        name = b.read_string(nptr, 48) if nptr else 'unknown'
        comp_arr = b.read_uint64(go + 0x20) if go else 0
        print(f'[{count}] {name} (GO 0x{go:X}, comp_arr 0x{comp_arr:X})')
        if comp_arr:
            for i in range(4):
                tid = b.read_uint64(comp_arr + i * 16)
                ptr = b.read_uint64(comp_arr + i * 16 + 8)
                if ptr:
                    print(f'   Comp[{i}]: Type=0x{tid:X}, Ptr=0x{ptr:X}')
    node = b.read_uint64(node + 0x08)
