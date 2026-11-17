import sys
sys.path.append(r'd:\ESP robrun')
from driver.driver_bridge import KernelDriverBridge

b = KernelDriverBridge()
b.attach_game('ROB RUN.exe')

gom = b.read_uint64(b.unity_player_base + 0x2230768)
node = b.read_uint64(gom + 0x20)

count = 0
cameras = []
while node and 0x10000000 < node < 0x7FFFFFFFFFFF and count < 15000:
    count += 1
    go = b.read_uint64(node + 0x10)
    if go:
        nptr = b.read_uint64(go + 0x50)
        s = b.read_string(nptr, 32)
        if s and ('camera' in s.lower() or 'cam' in s.lower()):
            if not any(x in s.lower() for x in ['collider', 'ui', 'point', 'bets', 'root']):
                cameras.append((count, s, hex(go)))
    node = b.read_uint64(node + 0x08)

print(f'Cameras found ({len(cameras)}):')
for c, s, g in cameras:
    print(f'  [{c}] "{s}" (GO: {g})')
