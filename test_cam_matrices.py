import sys, struct
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

go_cam = 0x2cb27016fb0
print(f'Inspecting Camera GameObject 0x{go_cam:X}:')
pCompList = b.read_uint64(go_cam + 0x30)
print(f'pCompList: 0x{pCompList:X}')

# Dump components
for idx in range(12):
    for stride in (0x10, 0x08):
        off = idx * stride + (0x08 if stride == 0x10 else 0x00)
        pComp = b.read_uint64(pCompList + off)
        if pComp and 0x10000000 < pComp < 0x7FFFFFFFFFFF:
            # Check if this component has ViewMatrix at 0xDC or similar
            for m_off in (0xDC, 0xD8, 0x11C, 0x120, 0x160, 0x1E0, 0x214, 0x2E0, 0x308, 0x3E0):
                vm = b.read_matrix4x4(pComp + m_off)
                if vm:
                    # check if vm is plausible
                    det_check = not any(v == 0 for v in vm[:4])
                    print(f'  Comp[{idx}] 0x{pComp:X} + 0x{m_off:X}: {vm[:4]} ... {vm[12:]}')
                    break
