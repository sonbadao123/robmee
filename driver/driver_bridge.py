"""
ROB RUN - KERNEL DRIVER CLIENT & HARDWARE DMA MEMORY BRIDGE
Pure Ring 0 Physical Memory Translation via Hardware CR3 (PML4 -> PDPT -> PD -> PT).
Zero user-mode process handles (PROCESS_VM_READ/WRITE). Zero ETW-TI telemetry.
Communicates via stealth candidate devices outside EAC EOS inspection range:
  - \\\\.\\MTKBTFilter (MediaTek Bluetooth Driver - 100% immune to anti-cheat scans)
  - \\\\.\\AMDRyzenMasterDriverV31 (AMD Ryzen Master Driver)
  - \\\\.\\gpuenergydrv (GPU Energy Driver)
"""

import os
import ctypes
import struct
import win32file
import win32con
import math
import time

# IOCTL Definitions matching driver.h
IOCTL_ROBRUN_READ_MEM  = 0x80002000
IOCTL_ROBRUN_WRITE_MEM = 0x80002004
IOCTL_ROBRUN_GET_BASE  = 0x80002008
IOCTL_ROBRUN_GET_CR3   = 0x8000200C
IOCTL_ROBRUN_UNHOOK    = 0x80002010

CANDIDATE_DEVICES = [
    r"\\.\MTKBTFilter",
    r"\\.\AMDRyzenMasterDriverV31",
    r"\\.\gpuenergydrv"
]

class RobRunReadRequest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("DirectoryTableBase", ctypes.c_uint64),
        ("Address", ctypes.c_uint64),
        ("Response", ctypes.c_void_p),
        ("Size", ctypes.c_size_t),
    ]

class RobRunModuleRequest(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ProcessId", ctypes.c_uint32),
        ("ModuleName", ctypes.c_wchar * 260),
        ("BaseAddress", ctypes.c_uint64),
    ]

class RobRunCr3Request(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ProcessId", ctypes.c_uint32),
        ("DirectoryTableBase", ctypes.c_uint64),
    ]

class KernelDriverBridge:
    """
    High-performance Windows Kernel DMA bridge.
    Reads memory through physical CR3 translation directly.
    """

    def __init__(self, device_path=None):
        self.device_path = device_path
        self.handle = None
        self.target_pid = None
        self.cr3 = 0
        self.game_assembly_base = 0
        self.unity_player_base = 0
        self.connected = False
        self.last_error = None
        self.connect()

    def connect(self):
        """Attempts to open device handle across stealth candidate devices."""
        if self.handle:
            try:
                win32file.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None

        devices_to_try = [self.device_path] if self.device_path else CANDIDATE_DEVICES

        for path in devices_to_try:
            if not path:
                continue
            try:
                h = win32file.CreateFile(
                    path,
                    win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                if h and h != win32file.INVALID_HANDLE_VALUE:
                    # Test probe with current process PID for CR3 response
                    curr_pid = os.getpid()
                    req = RobRunCr3Request(ProcessId=curr_pid, DirectoryTableBase=0)
                    in_buf = bytes(req)
                    try:
                        out_buf = win32file.DeviceIoControl(
                            h,
                            IOCTL_ROBRUN_GET_CR3,
                            in_buf,
                            ctypes.sizeof(RobRunCr3Request),
                            None
                        )
                        if out_buf and len(out_buf) >= ctypes.sizeof(RobRunCr3Request):
                            res = RobRunCr3Request.from_buffer_copy(out_buf)
                            if res.DirectoryTableBase != 0:
                                self.handle = h
                                self.device_path = path
                                self.connected = True
                                self.last_error = None
                                return True
                    except Exception:
                        pass
                    win32file.CloseHandle(h)
            except Exception as e:
                self.last_error = str(e)

        self.handle = None
        self.connected = False
        return False

    def attach_game(self, process_name="ROB RUN.exe"):
        """Finds target PID and resolves UnityPlayer.dll base and CR3."""
        if not self.connected and not self.connect():
            return False

        self.target_pid = self._find_pid(process_name)
        if not self.target_pid:
            return False

        self.cr3 = self.get_process_cr3()
        if not self.cr3:
            return False

        self.game_assembly_base = self.get_module_base("GameAssembly.dll")
        self.unity_player_base = self.get_module_base("UnityPlayer.dll")
        return self.unity_player_base != 0

    def _find_pid(self, process_name):
        try:
            from ctypes import wintypes
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', wintypes.DWORD),
                    ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
                    ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD),
                    ('szExeFile', ctypes.c_char * 260)
                ]

            hSnap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
            if hSnap == -1:
                return None

            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            if ctypes.windll.kernel32.Process32First(hSnap, ctypes.byref(pe)):
                while True:
                    exe_name = pe.szExeFile.decode('utf-8', errors='ignore')
                    if exe_name.lower() == process_name.lower():
                        pid = pe.th32ProcessID
                        ctypes.windll.kernel32.CloseHandle(hSnap)
                        return pid
                    if not ctypes.windll.kernel32.Process32Next(hSnap, ctypes.byref(pe)):
                        break
            ctypes.windll.kernel32.CloseHandle(hSnap)
        except Exception:
            pass
        return None

    def get_process_cr3(self):
        """Retrieves hardware CR3 DirectoryTableBase for stealth physical translation."""
        if not self.handle or not self.target_pid:
            return 0
        req = RobRunCr3Request(ProcessId=self.target_pid, DirectoryTableBase=0)
        try:
            out_buf = win32file.DeviceIoControl(
                self.handle,
                IOCTL_ROBRUN_GET_CR3,
                bytes(req),
                ctypes.sizeof(RobRunCr3Request),
                None
            )
            if out_buf and len(out_buf) >= ctypes.sizeof(RobRunCr3Request):
                res = RobRunCr3Request.from_buffer_copy(out_buf)
                return res.DirectoryTableBase
        except Exception as e:
            self.last_error = str(e)
        return 0

    def get_module_base(self, module_name):
        """Resolves module base address via kernel-side physical PEB traversal."""
        if not self.handle or not self.target_pid:
            return 0
        req = RobRunModuleRequest(ProcessId=self.target_pid, ModuleName=module_name, BaseAddress=0)
        try:
            out_buf = win32file.DeviceIoControl(
                self.handle,
                IOCTL_ROBRUN_GET_BASE,
                bytes(req),
                ctypes.sizeof(RobRunModuleRequest),
                None
            )
            if out_buf and len(out_buf) >= ctypes.sizeof(RobRunModuleRequest):
                res = RobRunModuleRequest.from_buffer_copy(out_buf)
                return res.BaseAddress
        except Exception as e:
            self.last_error = str(e)
        return 0

    def read_bytes(self, address, size):
        """Reads raw bytes via Hardware CR3 Physical Memory Translation."""
        if not self.handle or not self.cr3 or not address or size <= 0:
            return None

        buf = ctypes.create_string_buffer(size)
        req = RobRunReadRequest(
            DirectoryTableBase=self.cr3,
            Address=address,
            Response=ctypes.addressof(buf),
            Size=size
        )
        try:
            out_buf = win32file.DeviceIoControl(
                self.handle,
                IOCTL_ROBRUN_READ_MEM,
                bytes(req),
                0,
                None
            )
            return buf.raw
        except Exception as e:
            self.last_error = str(e)
            return None

    def read_uint32(self, address):
        data = self.read_bytes(address, 4)
        return struct.unpack('<I', data)[0] if data and len(data) >= 4 else 0

    def read_uint64(self, address):
        data = self.read_bytes(address, 8)
        return struct.unpack('<Q', data)[0] if data and len(data) >= 8 else 0

    def read_float(self, address):
        data = self.read_bytes(address, 4)
        return struct.unpack('<f', data)[0] if data and len(data) >= 4 else 0.0

    def read_vec3(self, address):
        data = self.read_bytes(address, 12)
        return struct.unpack('<3f', data) if data and len(data) >= 12 else None

    def read_vec4(self, address):
        data = self.read_bytes(address, 16)
        return struct.unpack('<4f', data) if data and len(data) >= 16 else None

    def read_matrix4x4(self, address):
        data = self.read_bytes(address, 64)
        return struct.unpack('<16f', data) if data and len(data) >= 64 else None

    def read_string(self, address, max_len=64):
        raw = self.read_bytes(address, max_len)
        if not raw:
            return ""
        inline = raw.split(b"\x00")[0]
        try:
            return inline.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    @staticmethod
    def world_to_screen(world_pos, view_matrix, screen_width=1920, screen_height=1080):
        """
        DirectX / Unity Column-Major 4x4 ViewProjection transformation:
        clip = P*V * world
        """
        if not view_matrix or len(view_matrix) < 16:
            return None
        m = view_matrix
        x, y, z = world_pos
        clip_x = m[0]*x + m[4]*y + m[8]*z  + m[12]
        clip_y = m[1]*x + m[5]*y + m[9]*z  + m[13]
        clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]

        if clip_w < 0.01 or math.isnan(clip_w) or math.isinf(clip_w):
            return None
        inv_w = 1.0 / clip_w
        nx, ny = clip_x * inv_w, clip_y * inv_w
        if any(math.isnan(v) or math.isinf(v) for v in (nx, ny)):
            return None
        cx, cy = screen_width * 0.5, screen_height * 0.5
        return (int(cx * (1.0 + nx)), int(cy * (1.0 - ny)))

    @staticmethod
    def world_to_screen_depth(world_pos, view_matrix, screen_width=1920, screen_height=1080):
        if not view_matrix or len(view_matrix) < 16:
            return None
        m = view_matrix
        x, y, z = world_pos
        clip_x = m[0]*x + m[4]*y + m[8]*z  + m[12]
        clip_y = m[1]*x + m[5]*y + m[9]*z  + m[13]
        clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]

        if clip_w < 0.01 or math.isnan(clip_w) or math.isinf(clip_w):
            return None
        inv_w = 1.0 / clip_w
        nx, ny = clip_x * inv_w, clip_y * inv_w
        if any(math.isnan(v) or math.isinf(v) for v in (nx, ny)):
            return None
        cx, cy = screen_width * 0.5, screen_height * 0.5
        return (int(cx * (1.0 + nx)), int(cy * (1.0 - ny)), float(clip_w))

    def unhook(self):
        """Restores original driver dispatch table."""
        if self.handle:
            try:
                win32file.DeviceIoControl(
                    self.handle,
                    IOCTL_ROBRUN_UNHOOK,
                    b"",
                    0,
                    None
                )
            except Exception:
                pass

    def close(self):
        if self.handle:
            try:
                win32file.CloseHandle(self.handle)
            except Exception:
                pass
            self.handle = None
        self.connected = False
