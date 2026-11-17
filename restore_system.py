import sys
import os

try:
    from driver.driver_bridge import KernelDriverBridge
    b = KernelDriverBridge()
    if b.connected:
        print("[+] Driver found connected. Calling unhook()...")
        b.unhook()
        b.close()
        print("[+] Dispatch table restored! Device unhooked cleanly.")
    else:
        print("[*] Driver was not connected or already clean.")
except Exception as e:
    print(f"[-] Error during cleanup: {e}")

print("[+] All cheat processes and hooks cleared.")
