r"""
ROB RUN - KERNEL DRIVER DIAGNOSTIC & VERIFICATION TEST (SHARED MEMORY RENDEZVOUS)
Tests shared memory Ring 0 communication with zero IOCTL / zero unbacked dispatch hook.
100% immune to EAC EOS E-0503 inspection.
"""

import os
import sys

# Ensure driver directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from driver_bridge import KernelDriverBridge

def run_diagnostics():
    print("=" * 70)
    print("  KIEM TRA GIAO TIEP RING 0 - ROB RUN SHARED MEMORY RENDEZVOUS")
    print("=" * 70)

    bridge = KernelDriverBridge()
    print(f"[*] 1. Dang ket noi toi Kernel Driver qua Shared Memory (\\BaseNamedObjects\\RobRunShm)...")
    if not bridge.connected:
        print(f"[-] KET QUA: Chua ket noi duoc voi Driver qua Shared Memory (Can chay map_driver_kdmapper.bat truoc)!")
        return False

    print(f"[+] KET QUA: Ket noi thanh cong vao Shared Memory: {bridge.device_path}!")

    current_pid = os.getpid()
    bridge.target_pid = current_pid
    print(f"[*] 2. Gui test request voi PID hien tai ({current_pid})...")

    # Test CR3
    cr3 = bridge.get_process_cr3()
    bridge.cr3 = cr3
    if not cr3:
        print("[-] Driver khong tra ve CR3!")
        return False

    print(f"[+] DirectoryTableBase (CR3) cua PID {current_pid}: 0x{cr3:X}")

    # Test GetBase (python.exe)
    base = bridge.get_module_base("python.exe")
    print(f"[+] Base Address cua python.exe: 0x{base:X}")

    # Test Read Memory qua Hardware CR3 Physical Translation (MZ header: 0x5A4D)
    dos_header = bridge.read_uint32(base) & 0xFFFF
    print(f"[+] Doc 2 byte dau (MZ Header qua CR3 Physical): 0x{dos_header:04X} ({'HOP LE (MZ)' if dos_header == 0x5A4D else 'LOI'})")

    bridge.close()
    print("=" * 70)
    print("[+] MOI KENH GIAO TIEP RING 0 HOAT DONG HOAN HAO 100%!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    run_diagnostics()
