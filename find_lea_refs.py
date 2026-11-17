import pefile, struct

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
raw = open(dll_path, 'rb').read()

# Let's find where table around 0x1CFF000 starts
# It's in .rdata. Let's find any code reference (LEA reg, [rip + disp]) to anything between 0x1D00000 and 0x1D00500!
target_min = 0x1D00000
target_max = 0x1D00500

for s in pe.sections:
    name = s.Name.decode('latin1').strip('\x00')
    if name == '.text':
        text_data = s.get_data()
        text_rva = s.VirtualAddress
        print(f"Scanning .text from RVA 0x{text_rva:X}...")
        
        # In x64, LEA reg, [rip + disp32] has opcode:
        # 48 8D reg [disp32]
        # target_rva = rip + disp32 = (insn_rva + insn_len) + disp32
        for i in range(len(text_data) - 7):
            b0 = text_data[i]
            b1 = text_data[i+1]
            b2 = text_data[i+2]
            # 48 8D 05 / 0D / 15 / 1D / 25 / 2D / 35 / 3D (LEA rax..rdi, [rip + disp32])
            # 4C 8D 05 ... (LEA r8..r15, [rip + disp32])
            if (b0 in (0x48, 0x4C)) and b1 == 0x8D and (b2 & 0xC7 == 0x05):
                disp = struct.unpack_from('<i', text_data, i + 3)[0]
                insn_rva = text_rva + i
                next_rip = insn_rva + 7
                dest_rva = next_rip + disp
                if target_min <= dest_rva <= target_max:
                    print(f"Found LEA at RVA 0x{insn_rva:X} pointing to RVA 0x{dest_rva:X}")
