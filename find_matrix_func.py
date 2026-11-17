import pefile, capstone, struct

path = r'D:\SteamLibrary\steamapps\common\Rob Run\UnityPlayer.dll'
pe = pefile.PE(path)
raw = open(path, 'rb').read()

# In Unity, icalls are registered via Registration Table
# Let's search .text for LEA reg, [rip+disp] pointing to 0x1CC4F28
text_sec = [s for s in pe.sections if '.text' in s.Name.decode()][0]
text_data = text_sec.get_data()
text_va = text_sec.VirtualAddress
target_rva = 0x1CC4F28

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Search for any references to target_rva
for off in range(len(text_data) - 7):
    b0 = text_data[off]
    b1 = text_data[off+1]
    if b0 == 0x48 and (b1 & 0xC7 == 0x05):
        disp = struct.unpack('<i', text_data[off+3:off+7])[0]
        if text_va + off + 7 + disp == target_rva:
            instr_rva = text_va + off
            print(f'Found reference at RVA 0x{instr_rva:X}')
            code = text_data[off:off+80]
            for insn in md.disasm(code, instr_rva):
                print(f'  0x{insn.address:X}: {insn.mnemonic} {insn.op_str}')
