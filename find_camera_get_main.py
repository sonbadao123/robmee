import pefile
from capstone import *

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

# We found Camera::get_main_Injected at raw offset 0x1CC47EC earlier.
# Let's find the RVA of that string
target_str = b'UnityEngine.Camera::get_main_Injected'
str_pos = raw.find(target_str)
print(f"String pos in raw: 0x{str_pos:X}")

str_rva = None
for s in pe.sections:
    if s.PointerToRawData <= str_pos < s.PointerToRawData + s.SizeOfRawData:
        str_rva = s.VirtualAddress + (str_pos - s.PointerToRawData)
        break

print(f"String RVA: 0x{str_rva:X}")
str_va = pe.OPTIONAL_HEADER.ImageBase + str_rva
print(f"String VA: 0x{str_va:X}")

# Search for references to str_va in .rdata or .data (registration table)
import struct
ref_bytes = struct.pack('<Q', str_va)
pos = 0
refs = []
while True:
    p = raw.find(ref_bytes, pos)
    if p == -1: break
    refs.append(p)
    pos = p + 1

print(f"Found {len(refs)} references to string VA:")
for r in refs:
    # In Unity internal registration tables, the function pointer is usually right next to the string pointer
    print(f"Ref at raw 0x{r:X}")
    nearby = raw[r-32:r+64]
    qwords = struct.unpack('<12Q', nearby)
    for i, q in enumerate(qwords):
        print(f"  [{i-4:+02d}] 0x{q:016X}")
