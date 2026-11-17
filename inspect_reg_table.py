import pefile, struct

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

# Let's inspect the table around 0x1CFF498
base = 0x1CFF498 - 32
for i in range(12):
    off = base + i * 8
    q = struct.unpack_from('<Q', raw, off)[0]
    # Check if q is a pointer into .rdata (string) or .text (function)
    # RVA of q
    q_rva = q - pe.OPTIONAL_HEADER.ImageBase if q >= pe.OPTIONAL_HEADER.ImageBase else 0
    sec_name = "N/A"
    for s in pe.sections:
        if s.VirtualAddress <= q_rva < s.VirtualAddress + s.Misc_VirtualSize:
            sec_name = s.Name.decode('latin1').strip('\x00')
            break
    print(f"raw 0x{off:X} (RVA 0x{off + 0xE00:X}): 0x{q:016X} -> {sec_name}")
