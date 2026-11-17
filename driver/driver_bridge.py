"""
ROB RUN — Kernel Driver Client (Shared Memory Rendezvous)

EAC E-0503 fix: zero IOCTL / zero hooked dispatch table on any registered driver object.
Communication via named shared memory section: \\BaseNamedObjects\\RobRunShm.
Kernel side: system thread polls the shared region (ShmWorkerThread in driver.c).
User side:   this module maps the same section, writes request, waits for response.

CR3 translation: 100% physical walk in kernel — zero ETW-TI, zero cross-handle.
"""

import ctypes
import ctypes.wintypes as wt
import struct
import time
import os

# ---------------------------------------------------------------------------
# Windows API bindings
# ---------------------------------------------------------------------------
kernel32    = ctypes.windll.kernel32
ntdll       = ctypes.windll.ntdll

FILE_MAP_ALL_ACCESS  = 0xF001F
PAGE_READWRITE       = 0x04
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# ---------------------------------------------------------------------------
# Shared memory layout constants (must match driver.h)
# ---------------------------------------------------------------------------
ROBRUN_SHM_NAME      = "\\BaseNamedObjects\\RobRunShm"
ROBRUN_SHM_SIZE      = 0x2000   # 8 KB
SHM_HEADER_FMT       = "<IIIIQQQq"  # RequestReady, OpCode, ProcessId, Pad0,
                                      # DirectoryTableBase, Address, Size, _align
SHM_HEADER_BASE_SIZE = struct.calcsize(SHM_HEADER_FMT)

# Op-codes
OP_NOP          = 0x00
OP_READ_MEM     = 0x01
OP_GET_BASE     = 0x02
OP_GET_CR3      = 0x03
OP_PING         = 0x04
OP_SHUTDOWN     = 0xFF

# Status
RSTAT_OK        = 0x00
RSTAT_ERR       = 0x01
RSTAT_BUSY      = 0x02
RSTAT_INVALID   = 0x03

# Backward compatibility definitions for legacy diagnostic scripts
IOCTL_ROBRUN_READ_MEM  = 0x80002000
IOCTL_ROBRUN_WRITE_MEM = 0x80002004
IOCTL_ROBRUN_GET_BASE  = 0x80002008
IOCTL_ROBRUN_GET_CR3   = 0x8000200C
IOCTL_ROBRUN_UNHOOK    = 0x80002010

class RobRunModuleRequest(ctypes.Structure):
    _fields_ = [("ProcessId", wt.DWORD), ("ModuleName", wt.WCHAR * 260), ("BaseAddress", ctypes.c_uint64)]

class RobRunCr3Request(ctypes.Structure):
    _fields_ = [("ProcessId", wt.DWORD), ("DirectoryTableBase", ctypes.c_uint64)]

# Header layout in shared memory (all offsets in bytes)
#  0  RequestReady   UINT32   (volatile, written by user→kernel, cleared by kernel)
#  4  OpCode         UINT32
#  8  ProcessId      UINT32
# 12  Pad0           UINT32
# 16  DirectoryTableBase  UINT64
# 24  Address        UINT64
# 32  Size           UINT64
# 40  ModuleName     WCHAR[260] = 520 bytes
# 560 ResponseReady  UINT32
# 564 Status         UINT32
# 568 ResultBase     UINT64
# 576 ResultCr3      UINT64
# 584 (end of header)
# 584+ data region (read payload)

OFF_REQUEST_READY   = 0
OFF_OPCODE          = 4
OFF_PROCESSID       = 8
OFF_PAD0            = 12
OFF_DTB             = 16
OFF_ADDRESS         = 24
OFF_SIZE            = 32
OFF_MODULE_NAME     = 40          # WCHAR[260] = 520 bytes
OFF_RESPONSE_READY  = 40 + 520   # = 560
OFF_STATUS          = 564
OFF_RESULT_BASE     = 568
OFF_RESULT_CR3      = 576
SHM_HEADER_END      = 584
SHM_MAX_READ        = ROBRUN_SHM_SIZE - SHM_HEADER_END

TIMEOUT_S     = 2.0    # max wait for kernel response (seconds)
POLL_SLEEP_S  = 0.0001 # 100 µs poll interval

# ---------------------------------------------------------------------------
# ctypes helper: open named section
# ---------------------------------------------------------------------------
def _open_shm_section(name: str):
    """Opens a named section created by the kernel driver. Returns (handle, view)."""
    # Try OpenFileMapping first (works for sections exposed in BaseNamedObjects)
    h = kernel32.OpenFileMappingW(FILE_MAP_ALL_ACCESS, False, name)
    if not h or h == INVALID_HANDLE_VALUE:
        return None, None

    view = kernel32.MapViewOfFile(h, FILE_MAP_ALL_ACCESS, 0, 0, ROBRUN_SHM_SIZE)
    if not view:
        kernel32.CloseHandle(h)
        return None, None

    return h, view

# ---------------------------------------------------------------------------
# Low-level shared memory read/write helpers
# ---------------------------------------------------------------------------
class _ShmView:
    """Thin wrapper around a raw MapViewOfFile pointer for structured I/O."""

    def __init__(self, base_addr: int):
        self._base = base_addr

    def _ptr(self, offset: int) -> ctypes.c_void_p:
        return ctypes.c_void_p(self._base + offset)

    def read_u32(self, offset: int) -> int:
        return ctypes.c_uint32.from_address(self._base + offset).value

    def write_u32(self, offset: int, val: int):
        ctypes.c_uint32.from_address(self._base + offset).value = val

    def read_u64(self, offset: int) -> int:
        return ctypes.c_uint64.from_address(self._base + offset).value

    def write_u64(self, offset: int, val: int):
        ctypes.c_uint64.from_address(self._base + offset).value = val

    def write_wstr(self, offset: int, text: str, max_wchars: int = 260):
        encoded = (text + "\x00")[:max_wchars]
        buf = encoded.encode("utf-16-le")
        ctypes.memmove(self._base + offset, buf, len(buf))

    def read_bytes(self, offset: int, size: int) -> bytes:
        buf = (ctypes.c_uint8 * size).from_address(self._base + offset)
        return bytes(buf)

    def zero_header(self):
        ctypes.memset(self._base, 0, SHM_HEADER_END)

# ---------------------------------------------------------------------------
# KernelDriverBridge — shared memory rendezvous client
# ---------------------------------------------------------------------------
class KernelDriverBridge:
    """
    Python client for RobRunMem Kernel Driver (Shared Memory Rendezvous).

    Zero IOCTL, zero device handle open, zero hooked MajorFunction pointer.
    EAC E-0503: cannot trigger because the kernel side never modifies any
    registered driver object's dispatch table.
    """

    def __init__(self, device_path=None):
        self.device_path = ROBRUN_SHM_NAME
        self._shm_handle = None
        self._shm_view_addr = 0
        self._view: _ShmView = None
        self.target_pid = None
        self.game_assembly_base = 0
        self.unity_player_base  = 0
        self.cr3                = 0
        self.connected          = False
        self.last_error         = None
        self.connect()

    # -----------------------------------------------------------------------
    def connect(self) -> bool:
        """Maps shared section and verifies kernel side is alive (OP_PING)."""
        h, view_addr = _open_shm_section(ROBRUN_SHM_NAME)
        if not h or not view_addr:
            self.last_error = f"OpenFileMapping failed: {kernel32.GetLastError()}"
            return False

        self._shm_handle   = h
        self._shm_view_addr = view_addr
        self._view          = _ShmView(view_addr)

        # Ping the kernel worker to verify it is running
        ok = self._ping()
        if not ok:
            self.last_error = "PING failed — kernel worker not responding"
            self._cleanup_view()
            return False

        self.connected  = True
        self.last_error = None
        return True

    # -----------------------------------------------------------------------
    def _cleanup_view(self):
        if self._shm_view_addr:
            kernel32.UnmapViewOfFile(self._shm_view_addr)
            self._shm_view_addr = 0
        if self._shm_handle:
            kernel32.CloseHandle(self._shm_handle)
            self._shm_handle = None
        self._view = None

    # -----------------------------------------------------------------------
    def _send_request(self, op: int, pid: int = 0, dtb: int = 0,
                      addr: int = 0, size: int = 0,
                      module_name: str = "") -> dict | None:
        """
        Writes a request into the shared region, waits for the kernel to
        process it, and returns a dict with status/ResultBase/ResultCr3/data.
        Thread-unsafe (single-client design).
        """
        v = self._view
        if v is None:
            return None

        # Ensure no stale response from previous cycle
        v.write_u32(OFF_RESPONSE_READY, 0)
        v.write_u32(OFF_REQUEST_READY,  0)
        ctypes.c_long(0)  # compiler fence hint

        # Write request fields
        v.write_u32(OFF_OPCODE,    op)
        v.write_u32(OFF_PROCESSID, pid & 0xFFFFFFFF)
        v.write_u32(OFF_PAD0,      0)
        v.write_u64(OFF_DTB,       dtb)
        v.write_u64(OFF_ADDRESS,   addr)
        v.write_u64(OFF_SIZE,      size)
        if module_name:
            v.write_wstr(OFF_MODULE_NAME, module_name, 260)
        else:
            # zero the name slot
            ctypes.memset(self._shm_view_addr + OFF_MODULE_NAME, 0, 520)

        # Commit request (atomic store — signals kernel)
        v.write_u32(OFF_REQUEST_READY, 1)

        # Spin-wait for response
        deadline = time.monotonic() + TIMEOUT_S
        while time.monotonic() < deadline:
            if v.read_u32(OFF_RESPONSE_READY) == 1:
                stat     = v.read_u32(OFF_STATUS)
                res_base = v.read_u64(OFF_RESULT_BASE)
                res_cr3  = v.read_u64(OFF_RESULT_CR3)
                # Grab data payload before clearing ResponseReady
                data_size = int(size) if op == OP_READ_MEM and stat == RSTAT_OK else 0
                data = b""
                if data_size > 0:
                    data = v.read_bytes(SHM_HEADER_END, min(data_size, SHM_MAX_READ))
                # Clear response flag for next round
                v.write_u32(OFF_RESPONSE_READY, 0)
                return {
                    "status":      stat,
                    "result_base": res_base,
                    "result_cr3":  res_cr3,
                    "data":        data,
                }
            time.sleep(POLL_SLEEP_S)

        # Timeout: cancel by clearing request ready
        v.write_u32(OFF_REQUEST_READY, 0)
        self.last_error = f"Timeout waiting for op=0x{op:02X}"
        return None

    # -----------------------------------------------------------------------
    def _ping(self) -> bool:
        resp = self._send_request(OP_PING)
        return resp is not None and resp["status"] == RSTAT_OK

    # -----------------------------------------------------------------------
    def attach_game(self, process_name: str = "ROB RUN.exe") -> bool:
        """Finds target PID and resolves GameAssembly.dll / UnityPlayer.dll bases."""
        if not self.connected and not self.connect():
            return False

        self.target_pid = self._find_pid(process_name)
        if not self.target_pid:
            return False

        self.cr3 = self.get_process_cr3()
        if not self.cr3:
            return False

        self.game_assembly_base = self.get_module_base("GameAssembly.dll")
        self.unity_player_base  = self.get_module_base("UnityPlayer.dll")
        return self.unity_player_base != 0

    # -----------------------------------------------------------------------
    def _find_pid(self, process_name: str) -> int | None:
        try:
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize',          wt.DWORD),
                    ('cntUsage',        wt.DWORD),
                    ('th32ProcessID',   wt.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID',    wt.DWORD),
                    ('cntThreads',      wt.DWORD),
                    ('th32ParentProcessID', wt.DWORD),
                    ('pcPriClassBase',  wt.LONG),
                    ('dwFlags',         wt.DWORD),
                    ('szExeFile',       ctypes.c_char * 260),
                ]

            k32 = ctypes.windll.kernel32
            snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
            if snap and snap != wt.HANDLE(-1).value:
                pe = PROCESSENTRY32()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                target_low = process_name.lower().encode("utf-8", "ignore")
                if k32.Process32First(snap, ctypes.byref(pe)):
                    while True:
                        if target_low in pe.szExeFile.lower():
                            pid = pe.th32ProcessID
                            k32.CloseHandle(snap)
                            return pid
                        if not k32.Process32Next(snap, ctypes.byref(pe)):
                            break
                k32.CloseHandle(snap)
        except Exception:
            pass
        return None

    # -----------------------------------------------------------------------
    def get_process_cr3(self) -> int:
        """Sends OP_GET_CR3 via shared memory."""
        if not self.connected or not self.target_pid:
            return 0
        resp = self._send_request(OP_GET_CR3, pid=self.target_pid)
        if resp and resp["status"] == RSTAT_OK:
            return resp["result_cr3"]
        return 0

    # -----------------------------------------------------------------------
    def get_module_base(self, module_name: str = "GameAssembly.dll") -> int:
        """Sends OP_GET_BASE via shared memory — returns DLL base address."""
        if not self.connected or not self.target_pid:
            return 0
        resp = self._send_request(OP_GET_BASE, pid=self.target_pid, module_name=module_name)
        if resp and resp["status"] == RSTAT_OK:
            return resp["result_base"]
        return 0

    # -----------------------------------------------------------------------
    def read_bytes(self, address: int, size: int) -> bytes | None:
        """Reads raw bytes from target process VA via kernel physical walk."""
        if not self.connected or not self.target_pid or not address or size <= 0:
            return None
        if size > SHM_MAX_READ:
            size = SHM_MAX_READ

        resp = self._send_request(
            OP_READ_MEM,
            pid=self.target_pid,
            dtb=self.cr3,
            addr=address,
            size=size,
        )
        if resp and resp["status"] == RSTAT_OK and resp["data"]:
            return resp["data"]
        return None

    # -----------------------------------------------------------------------
    def read_uint64(self, address: int) -> int:
        d = self.read_bytes(address, 8)
        return struct.unpack("<Q", d)[0] if d and len(d) == 8 else 0

    def read_uint32(self, address: int) -> int:
        d = self.read_bytes(address, 4)
        return struct.unpack("<I", d)[0] if d and len(d) == 4 else 0

    def read_float(self, address: int) -> float:
        d = self.read_bytes(address, 4)
        return struct.unpack("<f", d)[0] if d and len(d) == 4 else 0.0

    def read_vec3(self, address: int) -> tuple:
        d = self.read_bytes(address, 12)
        return struct.unpack("<fff", d) if d and len(d) == 12 else (0.0, 0.0, 0.0)

    def read_vec4(self, address: int) -> tuple | None:
        d = self.read_bytes(address, 16)
        return struct.unpack("<ffff", d) if d and len(d) == 16 else None

    def read_matrix4x4(self, address: int) -> tuple | None:
        d = self.read_bytes(address, 64)
        return struct.unpack("<16f", d) if d and len(d) == 64 else None

    def read_string(self, address: int, max_len: int = 64) -> str:
        if not address:
            return ""
        raw = self.read_bytes(address, max_len)
        if not raw:
            return ""
        null_idx = raw.find(b"\x00")
        if null_idx != -1:
            raw = raw[:null_idx]
        try:
            return raw.decode("utf-8", "ignore")
        except Exception:
            return ""

    # -----------------------------------------------------------------------
    # Projection helpers — column-major Unity 6 layout
    # -----------------------------------------------------------------------
    @staticmethod
    def world_to_screen(world_pos, view_matrix, screen_width=1920, screen_height=1080):
        """
        Project with column-major VP matrix (Unity 6000.3.18f1 IL2CPP 64-bit).
        struct.unpack('<16f') yields column-major: m[col*4+row].

        clip_x = m[0]*x + m[4]*y + m[ 8]*z + m[12]
        clip_y = m[1]*x + m[5]*y + m[ 9]*z + m[13]
        clip_w = m[3]*x + m[7]*y + m[11]*z + m[15]
        """
        import math
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
        """Same as world_to_screen but also returns clip_w for depth filtering."""
        import math
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

    @staticmethod
    def world_to_screen_vectors(world_pos, cam_pos, cam_forward, cam_right, cam_up,
                                 fov=75.0, screen_width=1920, screen_height=1080):
        import math
        if not all([world_pos, cam_pos, cam_forward, cam_right, cam_up]):
            return None
        dx = world_pos[0] - cam_pos[0]
        dy = world_pos[1] - cam_pos[1]
        dz = world_pos[2] - cam_pos[2]
        cam_z = dx*cam_forward[0] + dy*cam_forward[1] + dz*cam_forward[2]
        if cam_z <= 0.1:
            return None
        cam_x = dx*cam_right[0] + dy*cam_right[1] + dz*cam_right[2]
        cam_y = dx*cam_up[0]    + dy*cam_up[1]    + dz*cam_up[2]
        aspect = screen_width / screen_height
        tan_h  = math.tan(math.radians(fov * 0.5))
        if tan_h <= 0.0001:
            return None
        nx = cam_x / (cam_z * aspect * tan_h)
        ny = cam_y / (cam_z * tan_h)
        return (int(screen_width * 0.5 * (1.0 + nx)),
                int(screen_height * 0.5 * (1.0 - ny)))

    # -----------------------------------------------------------------------
    def unhook(self):
        """Sends OP_SHUTDOWN to signal the kernel worker thread to exit."""
        if self._view:
            try:
                self._view.write_u32(OFF_OPCODE, OP_SHUTDOWN)
                self._view.write_u32(OFF_REQUEST_READY, 0xDEAD)
                time.sleep(0.05)
            except Exception:
                pass

    def close(self):
        """Unmaps the shared section view — does NOT shutdown the kernel worker."""
        self._cleanup_view()
        self.connected = False
