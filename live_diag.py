r"""
ROB RUN - RING 0 LIVE MEMORY DIAGNOSTIC & GROUND-TRUTH PROBER
Scans the live running game via Kernel Driver (\\.\RobRun_Live) to verify
GOM pointers, Camera matrices, GameObject names, and 3D Transforms in real-time.
"""

import sys
import time
import math
import struct
import win32file
import config
from driver.driver_bridge import KernelDriverBridge
from engine.memory_reader import MemoryEntityManager

GOM_CANDIDATES = (0x21C9130, 0x21C8530, 0x22522B0, 0x21C9000, 0x21C9200)

def read_unity_name(bridge, pGO):
    """Reads GameObject name supporting both inline MSVC std::string SSO and pointer."""
    for off in (0x60, 0x58, 0x50, 0x48, 0x40):
        # 1. Thử dạng con trỏ heap
        ptr = bridge.read_uint64(pGO + off)
        if 0x10000 < ptr < 0x7FFFFFFFFFFF:
            s = bridge.read_string(ptr, 48)
            if s and len(s) >= 2 and s.isprintable():
                return s

        # 2. Thử dạng Inline SSO (MSVC lưu trực tiếp tối đa 15 ký tự trong buffer)
        raw = bridge.read_bytes(pGO + off, 16)
        if raw:
            inline = raw.split(b"\x00")[0]
            if inline and len(inline) >= 2 and all(32 <= b <= 126 for b in inline):
                try:
                    return inline.decode('ascii', 'ignore')
                except Exception:
                    pass
    return ""

def probe_live():
    print("=" * 75)
    print("  ROB RUN - RING 0 LIVE GROUND-TRUTH DIAGNOSTIC TOOL")
    print("  Driver: " + config.KERNEL_DEVICE_PATH)
    print("=" * 75)

    bridge = KernelDriverBridge(config.KERNEL_DEVICE_PATH)
    if not bridge.connected and not bridge.connect():
        print(f"[-] LỖI: Không thể kết nối với Kernel Driver ({bridge.last_error}). Hãy kiểm tra kdmapper!")
        return

    print("[+] Driver kết nối thành công!")
    print("[*] Đang tìm kiếm tiến trình 'ROB RUN.exe'...")

    if not bridge.attach_game("ROB RUN.exe"):
        print("[-] Game 'ROB RUN.exe' chưa được bật! Vui lòng khởi động game trước khi chạy diagnostic.")
        return

    print(f"[+] ĐÃ GẮN VÀO ROB RUN:")
    print(f"    - PID: {bridge.target_pid}")
    print(f"    - CR3: 0x{bridge.cr3:X}")
    print(f"    - GameAssembly.dll: 0x{bridge.game_assembly_base:X}")
    print(f"    - UnityPlayer.dll:  0x{bridge.unity_player_base:X}")

    up_base = bridge.unity_player_base
    if not up_base:
        print("[-] Không tìm thấy UnityPlayer.dll!")
        return

    print("\n" + "=" * 50)
    print("1. KHẢO SÁT CON TRỎ GAMEOBJECTMANAGER (GOM)")
    print("=" * 50)

    found_gom = 0
    for off in GOM_CANDIDATES:
        addr = up_base + off
        val = bridge.read_uint64(addr)
        print(f"[*] Candidate RVA 0x{off:X} (VA 0x{addr:X}):")
        print(f"    -> [base + off] = 0x{val:X}")

        # Test as pointer to GOM
        if val and val > 0x10000:
            n0 = bridge.read_uint64(val + 0x00)
            n1 = bridge.read_uint64(val + 0x08)
            n2 = bridge.read_uint64(val + 0x18)
            n3 = bridge.read_uint64(val + 0x28)
            print(f"    -> Dạng Pointer: Tagged={hex(n1)}, MainCam={hex(n2)}, ActiveNodes={hex(n3)}")
            if (n1 > 0x10000) or (n3 > 0x10000):
                print(f"    >>> PHÁT HIỆN GOM HỢP LỆ (DẠNG POINTER) TẠI RVA 0x{off:X}! <<<")
                found_gom = val
                break

        # Test as embedded GOM struct
        s1 = bridge.read_uint64(addr + 0x08)
        s2 = bridge.read_uint64(addr + 0x18)
        s3 = bridge.read_uint64(addr + 0x28)
        if (s1 > 0x10000 and s1 < 0x7FFFFFFFFFFF) or (s3 > 0x10000 and s3 < 0x7FFFFFFFFFFF):
            print(f"    -> Dạng Direct Struct: Tagged={hex(s1)}, MainCam={hex(s2)}, ActiveNodes={hex(s3)}")
            print(f"    >>> PHÁT HIỆN GOM HỢP LỆ (DẠNG STRUCT) TẠI RVA 0x{off:X}! <<<")
            found_gom = addr
            break

    if not found_gom:
        print("[-] Chưa tìm thấy GOM trong các candidate cố định. Đang quét vùng nhớ lân cận...")
        # Quét vùng .data của UnityPlayer quanh 0x21C0000 - 0x2260000
        for scan_off in range(0x21B0000, 0x2280000, 0x100):
            ptr = bridge.read_uint64(up_base + scan_off)
            if ptr > 0x10000 and ptr < 0x7FFFFFFFFFFF:
                n1 = bridge.read_uint64(ptr + 0x08)
                n3 = bridge.read_uint64(ptr + 0x28)
                if (n1 > 0x10000 and n1 < 0x7FFFFFFFFFFF) and (n3 > 0x10000 and n3 < 0x7FFFFFFFFFFF):
                    # Check if node + 0x10 points to a valid GameObject
                    go1 = bridge.read_uint64(n3 + 0x10)
                    if go1 > 0x10000 and go1 < 0x7FFFFFFFFFFF:
                        print(f"[+] TÌM THẤY GOM BẰNG QUÉT BỘ NHỚ: RVA 0x{scan_off:X} -> GOM 0x{ptr:X}")
                        found_gom = ptr
                        break

    if not found_gom:
        print("[-] Không xác định được GOM! Cần phân tích sâu thêm.")
        return

    print("\n" + "=" * 50)
    print("2. KHẢO SÁT CAMERA VÀ VIEW-PROJECTION MATRIX")
    print("=" * 50)

    mem_mgr = MemoryEntityManager(bridge)
    mem_mgr._update_camera(found_gom)
    if mem_mgr.camera_matrix:
        print(f"[+] ĐÃ TÌM THẤY CAMERA TẠI 0x{mem_mgr.camera_ptr:X}!")
        vm = mem_mgr.camera_matrix
        print(f"    Ma trận View-Projection 4x4:")
        for r in range(4):
            row_str = " ".join(f"{vm[r*4 + c]:10.4f}" for c in range(4))
            print(f"    [ {row_str} ]")
    else:
        print("[-] Chưa đọc được Camera Matrix từ GOM!")

    print("\n" + "=" * 50)
    print("3. QUÉT CÁC GAMEOBJECT TRONG ACTIVE NODES")
    print("=" * 50)

    active_node = bridge.read_uint64(found_gom + 0x28)
    print(f"[*] ActiveNodes Head: 0x{active_node:X}")

    scanned = 0
    visited = set()
    humanoids = []

    while active_node and active_node not in visited and scanned < 500:
        visited.add(active_node)
        scanned += 1

        pGO = bridge.read_uint64(active_node + 0x10)
        if not pGO or pGO < 0x10000:
            pGO = bridge.read_uint64(active_node + 0x18)

        if pGO and pGO > 0x10000:
            name = read_unity_name(bridge, pGO)
            if name:
                low = name.lower()
                # Check for interesting objects or print all to see
                if scanned < 20 or any(k in low for k in ("player", "character", "cop", "police", "robber", "citizen", "sparkasse", "kedanhcaptraitim", "battle", "cam")):
                    pos = mem_mgr._get_gameobject_position(pGO)
                    print(f"    [!] GameObject: '{name}' | GO: 0x{pGO:X} | Pos: {pos}")
                    if any(k in low for k in ("player", "character", "cop", "police", "robber", "citizen", "sparkasse", "kedanhcaptraitim", "battle")):
                        humanoids.append((name, pGO, pos))

        # Node + 0x00 là pointer tới node kế tiếp trong Unity 6
        next_node = bridge.read_uint64(active_node + 0x00)
        if not next_node or next_node < 0x10000:
            next_node = bridge.read_uint64(active_node + 0x08)
        active_node = next_node

    print(f"\n[*] Tổng số GameObject quét được: {scanned}")
    print(f"[*] Tổng số thực thể người chơi/NPC khớp: {len(humanoids)}")

    if mem_mgr.camera_matrix and humanoids:
        print("\n" + "=" * 50)
        print("4. KIỂM TRA PHÉP CHIẾU TỌA ĐỘ (WORLD-TO-SCREEN)")
        print("=" * 50)
        for name, go, pos in humanoids:
            if pos:
                screen = KernelDriverBridge.world_to_screen(pos, mem_mgr.camera_matrix, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
                print(f"    '{name}' -> World {pos} => Màn hình {screen}")

    bridge.close()
    print("\n[+] Hoàn tất chẩn đoán Ground-Truth!")

if __name__ == "__main__":
    probe_live()
