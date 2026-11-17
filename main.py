"""
ROB RUN - ESP & AIMBOT RUNNER (KERNEL DRIVER SUITE)
Pure Kernel Mode & Direct Memory Pipeline (All Vision Modules Removed).
Bypasses EAC EOS ObRegisterCallbacks via \\.\\RobRunMem.
"""

import sys
import time
import ctypes
import winsound
import win32api
import win32con

import config
from driver.driver_bridge import KernelDriverBridge
from engine.memory_reader import MemoryEntityManager
from engine.aimbot import AimbotController
from engine.overlay import EspOverlay

def disable_quick_edit():
    """Vô hiệu hóa QuickEdit mode trong Windows Console để chống nghẽn/đóng băng khi click chuột."""
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE = -10
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
            new_mode = mode.value & ~0x0040   # Bỏ cờ ENABLE_QUICK_EDIT_MODE (0x0040)
            new_mode |= 0x0080                # Bật ENABLE_EXTENDED_FLAGS (0x0080)
            kernel32.SetConsoleMode(h_stdin, new_mode)
    except Exception:
        pass

def play_beep(freq, duration):
    try:
        winsound.Beep(freq, duration)
    except Exception:
        pass

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    disable_quick_edit()
    print("=" * 75)
    print("  ROB RUN - BỘ CÔNG CỤ ESP OVERLAY (RING 0 KERNEL DMA)")
    print("  Cơ chế hoạt động: RING 0 DIRECT MEMORY (Bypass EAC EOS via \\\\.\\NUL)")
    print("  Chế độ: ESP ONLY (Đã tắt hoàn toàn Aimbot & Vòng ngắm FOV)")
    print("=" * 75)
    print("[HƯỚNG DẪN HIỂN THỊ CHUẨN XÁC KHI VÀO GAME]")
    print("  >> Vào Cài đặt (Settings) -> Đồ họa (Graphics) của game ROB RUN:")
    print("  >> Chọn chế độ màn hình: 'Không viền' (Borderless) hoặc 'Cửa sổ' (Windowed).")
    print("=" * 75)
    print("[DANH SÁCH PHÍM TẮT]")
    print("  [F1]         : Bật / Tắt hiển thị ESP (Có tiếng Bíp xác nhận)")
    print("  [F12]        : NÚT KHẨN CẤP (Panic Key - Thoát và đóng ngay)")
    print("=" * 75)
    print(f"[*] Đang khởi tạo kết nối Kernel Driver...")

    driver_bridge = KernelDriverBridge(config.KERNEL_DEVICE_PATH)
    if driver_bridge.connected:
        print(f"[+] KERNEL DRIVER ĐÃ KẾT NỐI QUA THIẾT BỊ: {driver_bridge.device_path}")
    else:
        print("[!] Không kết nối được Kernel Driver. Vui lòng chạy map_driver_kdmapper.bat trước!")
        return

    if driver_bridge.attach_game(config.GAME_EXE):
        print(f"[+] ĐÃ GẮN VÀO {config.GAME_EXE}: PID={driver_bridge.target_pid}, UnityPlayer=0x{driver_bridge.unity_player_base:X}, CR3=0x{driver_bridge.cr3:X}")
    else:
        print(f"[-] Thông báo: Chưa phát hiện tiến trình '{config.GAME_EXE}' đang chạy hoặc chưa phân giải được CR3/Base.")
        print(f"    (Driver '{driver_bridge.device_path}' đã sẵn sàng, hệ thống sẽ tự động hook ngay khi phát hiện game).")

    try:
        mem_manager = MemoryEntityManager(driver_bridge)
        overlay = EspOverlay()
    except Exception as e:
        print(f"[!] Lỗi khởi động module điều phối: {e}")
        return

    play_beep(1000, 120)
    play_beep(1500, 150)
    print("[+] Hệ thống ESP Kernel Suite đã sẵn sàng! Chuyển sang game ROB RUN.")

    last_f1 = False
    last_attach_attempt = 0.0

    frame_count = 0
    start_time = time.time()
    fps = 0.0

    try:
        while True:
            t0 = time.time()

            # 1. Thoát khẩn cấp (F12)
            if win32api.GetAsyncKeyState(config.KEY_PANIC) & 0x8000:
                print("\n[*] Đã bấm phím khẩn cấp (F12). Đang thoát hệ thống...")
                play_beep(600, 300)
                break

            # 2. Phím tắt Bật/Tắt ESP
            f1_state = win32api.GetAsyncKeyState(config.KEY_TOGGLE_ESP) & 0x8000 != 0
            if f1_state and not last_f1:
                config.ESP_ENABLED = not config.ESP_ENABLED
                state_str = 'BẬT' if config.ESP_ENABLED else 'TẮT'
                print(f"[*] ESP Bounding Box: {state_str}")
                play_beep(1200 if config.ESP_ENABLED else 700, 100)
            last_f1 = f1_state

            # Tự động kết nối Game nếu game mở sau bot hoặc chưa lấy được base/cr3
            if (not driver_bridge.unity_player_base or not driver_bridge.cr3) and (time.time() - last_attach_attempt > 1.5):
                last_attach_attempt = time.time()
                if driver_bridge.attach_game(config.GAME_EXE):
                    print(f"\n[+] TỰ ĐỘNG GẮN VÀO {config.GAME_EXE}: PID={driver_bridge.target_pid}, UnityPlayer=0x{driver_bridge.unity_player_base:X}, CR3=0x{driver_bridge.cr3:X}")
                    play_beep(1800, 150)

            # 3. Đọc dữ liệu thực thể trực tiếp từ Kernel Memory
            targets = mem_manager.update()

            # 4. Vẽ overlay DWM (Không Aimbot, Không FOV)
            overlay.update_data(targets, False, fps, False)
            overlay.render()

            # 5. Đo FPS
            frame_count += 1
            elapsed = time.time() - start_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                start_time = time.time()

            loop_time = time.time() - t0
            sleep_time = max(0.001, (1.0 / 120.0) - loop_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[*] Đang dừng...")
    finally:
        driver_bridge.close()
        overlay.close()
        print("[*] Đã đóng hệ thống an toàn.")

if __name__ == "__main__":
    main()
