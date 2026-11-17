import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

target_ptrs = [0x2CB9D9034B4, 0x2CB9DD084B4, 0x2CBBA3024B4, 0x2CBBA4044B4]
# In IL2CPP strings, the string object itself starts 0x14 bytes earlier (string header: +0x10 length, +0x14 chars)
# So ptr might be addr or addr - 0x14
search_bytes = []
for p in target_ptrs:
    search_bytes.append((p, struct.pack('<Q', p)))
    search_bytes.append((p - 0x14, struct.pack('<Q', p - 0x14)))

print('Searching for pointers to player name strings...')
found_refs = []
chunk_size = 0x100000
for base_addr in range(0x2C900000000, 0x2CC00000000, chunk_size):
    buf = b.read_bytes(base_addr, chunk_size)
    if not buf:
        continue
    for ptr_val, bts in search_bytes:
        pos = 0
        while True:
            pos = buf.find(bts, pos)
            if pos == -1: break
            ref_addr = base_addr + pos
            print(f'Reference to 0x{ptr_val:X} found at 0x{ref_addr:X}')
            found_refs.append(ref_addr)
            pos += 1

print(f'Total references: {len(found_refs)}')
