import pefile

pe = pefile.PE(r'd:\ESP robrun\ROB【云更新 右键管理员运行】.exe', fast_load=True)
for s in pe.sections:
    name = s.Name.decode('latin1', errors='ignore').strip('\x00')
    print(f"Section {name:10s} VirtAddr: 0x{s.VirtualAddress:08X} VirtSize: 0x{s.Misc_VirtualSize:08X} RawSize: 0x{s.SizeOfRawData:08X} Entropy: {s.get_entropy():.4f}")
