import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

go = 0x2cc8028d240
print(f'Inspecting Player_Man(Clone) GameObject 0x{go:X}:')

# In Unity, GameObject + 0x20 is component array
comp_array = b.read_uint64(go + 0x20)
print(f'Component array at +0x20: 0x{comp_array:X}')

# Component 0 is Transform
pTransform = b.read_uint64(comp_array + 0x08)
print(f'Transform: 0x{pTransform:X}')

# Dump 0x100 bytes of Transform
t_raw = b.read_bytes(pTransform, 0x100)
q = struct.unpack('<32Q', t_raw)
for i, val in enumerate(q):
    print(f'  Transform +0x{i*8:02X}: 0x{val:X}')

# Also check floats in Transform
for off in range(0, 0x100 - 12, 4):
    v = struct.unpack('<3f', t_raw[off:off+12])
    if any(abs(x) > 1.0 and abs(x) < 5000.0 for x in v):
        print(f'  Possible Vec3 at +0x{off:X}: {v}')
