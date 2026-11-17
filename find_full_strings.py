import pefile, struct

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

def find_full_string_and_ref(sub):
    idx = raw.find(sub)
    if idx == -1:
        print(f"Substring {sub} not found")
        return
    # find start of null-terminated string
    start = raw.rfind(b'\x00', 0, idx) + 1
    end = raw.find(b'\x00', idx)
    full_str = raw[start:end]
    
    # RVA
    rva = None
    for s in pe.sections:
        if s.PointerToRawData <= start < s.PointerToRawData + s.SizeOfRawData:
            rva = s.VirtualAddress + (start - s.PointerToRawData)
            break
    va = pe.OPTIONAL_HEADER.ImageBase + rva
    print(f"\nFull string: {full_str.decode('latin1', errors='ignore')}")
    print(f"Raw: 0x{start:X}, RVA: 0x{rva:X}, VA: 0x{va:X}")
    
    ref_bytes = struct.pack('<Q', va)
    pos = 0
    while True:
        p = raw.find(ref_bytes, pos)
        if p == -1: break
        print(f"  Reference at raw 0x{p:X} (RVA 0x{find_rva(p):X})")
        pos = p + 1

def find_rva(raw_offset):
    for s in pe.sections:
        if s.PointerToRawData <= raw_offset < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (raw_offset - s.PointerToRawData)
    return None

find_full_string_and_ref(b'get_worldToCameraMatrix')
find_full_string_and_ref(b'get_projectionMatrix')
find_full_string_and_ref(b'WorldToScreenPoint')
