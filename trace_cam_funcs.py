import pefile, struct
from capstone import *

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

def find_rva(raw_offset):
    for s in pe.sections:
        if s.PointerToRawData <= raw_offset < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (raw_offset - s.PointerToRawData)
    return None

def find_func_for_string(target_raw, name):
    rva = find_rva(target_raw)
    va = pe.OPTIONAL_HEADER.ImageBase + rva
    ref_bytes = struct.pack('<Q', va)
    pos = raw.find(ref_bytes)
    print(f"\n=== {name} ===")
    print(f"String raw: 0x{target_raw:X}, RVA: 0x{rva:X}, VA: 0x{va:X}")
    if pos != -1:
        print(f"Registered at raw: 0x{pos:X}")
        # Look around registration: often struct { char* name; void* func; }
        # or two parallel arrays: strings array, func pointers array
        # Let's check nearby QWORDs
        for off in range(-32, 40, 8):
            q = struct.unpack_from('<Q', raw, pos + off)[0]
            print(f"  [{off:+03d}] 0x{q:016X}")
    else:
        print("Not found in direct table")

find_func_for_string(0x1cc413c, "get_worldToCameraMatrix")
find_func_for_string(0x1cc4294, "get_projectionMatrix")
find_func_for_string(0x1cc443c, "WorldToScreenPoint")
