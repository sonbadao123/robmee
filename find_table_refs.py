import pefile, struct
from capstone import *

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

target_va = pe.OPTIONAL_HEADER.ImageBase + 0x1D00370 # VA of raw 0x1CFF570

# Search for references to table around 0x181D00370
ref_bytes = struct.pack('<Q', target_va)
p = raw.find(ref_bytes)
print(f"Ref to table VA: {hex(p) if p != -1 else 'None'}")

# Also search for lea reg, [rip + disp] pointing to 0x1D00370
table_rva = 0x1D00370
# Look in .text section
for s in pe.sections:
    name = s.Name.decode('latin1').strip('\x00')
    if name == '.text':
        text_data = s.get_data()
        text_va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        print(f"Scanning .text ({len(text_data)} bytes)...")
        # Search for rip-relative lea/mov
        # disp = target_rva - (ip + len)
        # We can search in 4-byte increments or disassemble
        # Let's search for exact target_rva in dwords or qwords
        break
