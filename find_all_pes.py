import pefile, struct

with open(r'd:\ESP robrun\ROB【云更新 右键管理员运行】.exe', 'rb') as f:
    data = f.read()

print(f"Total size: {len(data)} bytes")

# Find all 'MZ'
offset = 0
found_pes = []
while True:
    pos = data.find(b'MZ', offset)
    if pos == -1:
        break
    if pos + 0x40 <= len(data):
        e_lfanew = struct.unpack_from('<I', data, pos + 0x3C)[0]
        if pos + e_lfanew + 4 <= len(data) and e_lfanew < 0x1000:
            pe_sig = data[pos + e_lfanew : pos + e_lfanew + 4]
            if pe_sig == b'PE\x00\x00':
                found_pes.append((pos, e_lfanew))
    offset = pos + 2

print(f"Found valid PE headers: {len(found_pes)}")
for pos, elf in found_pes:
    print(f"  Offset: 0x{pos:X}, e_lfanew: 0x{elf:X}")
