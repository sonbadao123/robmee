import pefile, re

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\GameAssembly.dll'
raw = open(dll_path, 'rb').read()
print(f"GameAssembly.dll size: {len(raw)} bytes")

# Search for get_main in ASCII
matches = [m.start() for m in re.finditer(rb'Camera.*get_main', raw, re.IGNORECASE)]
print(f"Matches for Camera.*get_main: {len(matches)}")
for m in matches[:10]:
    start = max(0, m - 20)
    end = min(len(raw), m + 60)
    print(f"0x{m:X}: {raw[start:end]}")
