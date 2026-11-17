import pefile, struct, capstone

path = r'D:\SteamLibrary\steamapps\common\ROB RUN\GameAssembly.dll'
pe = pefile.PE(path)
raw = open(path, 'rb').read()

target_str = b'UnityEngine.Camera::get_main_Injected()'
pos = raw.find(target_str)
print(f'String at raw 0x{pos:X}')

sec = [s for s in pe.sections if s.PointerToRawData <= pos < s.PointerToRawData + s.SizeOfRawData][0]
str_rva = sec.VirtualAddress + (pos - sec.PointerToRawData)
str_va = pe.OPTIONAL_HEADER.ImageBase + str_rva
print(f'String RVA: 0x{str_rva:X}, VA: 0x{str_va:X}')

# Find pointer in raw
p = 0
found_ptrs = []
while True:
    p = raw.find(struct.pack('<Q', str_va), p)
    if p == -1: break
    found_ptrs.append(p)
    p += 1

print(f'Found {len(found_ptrs)} pointers to string:')
for p in found_ptrs:
    rva = pe.get_rva_from_offset(p)
    # Check the function pointer right next to it or near it
    nearby = struct.unpack('<4Q', raw[p-8:p+24])
    print(f'  raw 0x{p:X} (RVA 0x{rva:X}): {[hex(x) for x in nearby]}')
