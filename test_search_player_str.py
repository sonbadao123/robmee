import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

target_str = b'kedanhcaptraitim'
print(f'Searching for {target_str} in process memory...')

# Search in heaps: let's scan common heap regions or scan via VirtualQuery/CR3
# In Unity mono/il2cpp, strings are in heap.
# Let's inspect where kedanhcaptraitim is located:
# We can search ranges where GameObjects live (around 0x2C900000000 to 0x2CC00000000)
found_addrs = []
chunk_size = 0x100000  # 1MB
for base_addr in range(0x2C900000000, 0x2CC00000000, chunk_size):
    buf = b.read_bytes(base_addr, chunk_size)
    if not buf:
        continue
    pos = 0
    while True:
        pos = buf.find(target_str, pos)
        if pos == -1: break
        addr = base_addr + pos
        print(f'Found "{target_str.decode()}" at 0x{addr:X}')
        found_addrs.append(addr)
        pos += 1
    if len(found_addrs) >= 5:
        break

print(f'Done scanning. Total occurrences: {len(found_addrs)}')
