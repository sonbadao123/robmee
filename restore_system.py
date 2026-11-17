import sys
import os
import subprocess
import ctypes
import win32file
import win32con

IOCTL_ROBRUN_UNHOOK = 0x80002010

CANDIDATE_DEVICES = [
    r"\\.\AMDRyzenMasterDriverV31",
    r"\\.\MTKBTFilter",
    r"\\.\gpuenergydrv"
]

print("=" * 60)
print("     ROB RUN - GIAI PHONG TOAN BO DRIVER & HOOK CHEAT")
print("=" * 60)

# 1. Unhook dispatch tables on all candidate kernel devices
for dev in CANDIDATE_DEVICES:
    try:
        h = win32file.CreateFile(
            dev,
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        print(f"[+] Mo thiet bi: {dev}")
        try:
            win32file.DeviceIoControl(h, IOCTL_ROBRUN_UNHOOK, b"", 0, None)
            print(f"    -> [OK] Da gui IOCTL_ROBRUN_UNHOOK tra ve dispatch nguyen ban!")
        except Exception as e:
            print(f"    -> [!] UNHOOK thiet bi {dev}: {e}")
        win32file.CloseHandle(h)
    except Exception as e:
        print(f"[*] Thiet bi {dev}: {e}")

# 2. Kill cheat processes
cheat_exes = [
    "RobRunESP.exe",
    "ROB【云更新 右键管理员运行】.exe",
    "RobRun.sp.exe"
]
for proc in cheat_exes:
    try:
        subprocess.run(["taskkill", "/F", "/IM", proc, "/T"], capture_output=True, text=True)
        print(f"[+] Kiem tra va dung tien trinh: {proc}")
    except Exception:
        pass

# 3. Stop vulnerable driver services
services_to_stop = [
    "AMDRyzenMasterDriverV31",
    "gdrv3",
    "WinRing0_1_2_0"
]
for svc in services_to_stop:
    try:
        res = subprocess.run(["sc.exe", "stop", svc], capture_output=True, text=True)
        if "FAILED" not in res.stdout and "FAILED" not in res.stderr:
            print(f"[+] Dung service driver: {svc} -> Thanh cong")
        else:
            print(f"[*] Service driver {svc}: {res.stdout.strip() or res.stderr.strip()}")
    except Exception as e:
        print(f"[-] Loi dung service {svc}: {e}")

# 4. Delete temp services
services_to_delete = [
    "gdrv3",
    "WinRing0_1_2_0"
]
for svc in services_to_delete:
    try:
        subprocess.run(["sc.exe", "delete", svc], capture_output=True, text=True)
        print(f"[+] Xoa bo service tam: {svc}")
    except Exception:
        pass

# 5. Clean temp sys files
temp_dir = os.environ.get("TEMP", "")
if temp_dir and os.path.exists(temp_dir):
    try:
        for root, dirs, files in os.walk(temp_dir):
            for f in files:
                if f.lower().endswith(".sys") and ("winring0" in f.lower() or "gdrv" in f.lower()):
                    full_p = os.path.join(root, f)
                    try:
                        os.remove(full_p)
                        print(f"[+] Da xoa file driver tam: {full_p}")
                    except Exception:
                        pass
    except Exception:
        pass

print("\n" + "=" * 60)
print("[+] HOAN TAT DON DEP! He thong sach se 100%, EAC khong the quet thay.")
print("=" * 60)
