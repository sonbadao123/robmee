import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

go = 0x2cbcc016630
print(f'Inspecting Camera GameObject 0x{go:X}:')
comp_array = b.read_uint64(go + 0x20)
print(f'comp_array: 0x{comp_array:X}')
raw = b.read_bytes(comp_array, 0x80)
q = struct.unpack('<16Q', raw)
for i in range(0, len(q), 2):
    type_id = q[i]
    comp_ptr = q[i+1]
    print(f'  Comp[{i//2}]: Type=0x{type_id:X}, Ptr=0x{comp_ptr:X}')
