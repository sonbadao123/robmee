import sys, struct, math
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

cam = 0x2CB270171A0
raw = b.read_bytes(cam, 0x1000)

print('Scanning Camera 0x{:X} for true 4x4 matrix...'.format(cam))
for off in range(0, len(raw) - 64, 4):
    vm = struct.unpack('<16f', raw[off:off+64])
    # A true matrix has:
    # 1. No subnormals (abs(x) > 1e-7 or x == 0.0)
    # 2. Values in reasonable range [-50.0, 50.0] except maybe depth/translation [-10000, 10000]
    # 3. At least 8 non-zero values
    # 4. First 3 elements of row 0: rotation (norm around 0.5 to 2.0)
    if any(math.isnan(x) or math.isinf(x) for x in vm):
        continue
    if any(0.0 < abs(x) < 1e-6 for x in vm):
        continue # subnormal / junk
    non_zeros = sum(1 for x in vm if abs(x) > 1e-4)
    if non_zeros >= 8:
        # Check if values are reasonable
        if all(abs(x) < 50000.0 for x in vm):
            r0_norm = math.sqrt(vm[0]**2 + vm[1]**2 + vm[2]**2)
            r1_norm = math.sqrt(vm[4]**2 + vm[5]**2 + vm[6]**2)
            if 0.1 < r0_norm < 10.0 and 0.1 < r1_norm < 10.0:
                print(f'[!] MATCH at Camera + 0x{off:X} (non_zeros={non_zeros}, r0={r0_norm:.2f}, r1={r1_norm:.2f}):')
                for r in range(4):
                    print(f'   {vm[r*4:r*4+4]}')
