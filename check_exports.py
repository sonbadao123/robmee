import pefile

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
pe = pefile.PE(dll_path, fast_load=True)
if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
    print(f"Total exports: {len(pe.DIRECTORY_ENTRY_EXPORT.symbols)}")
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols[:30]:
        name = exp.name.decode() if exp.name else str(exp.ordinal)
        print(f"  {name} at RVA 0x{exp.address:X}")
