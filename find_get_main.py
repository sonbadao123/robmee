import pefile, re

path = r'D:\SteamLibrary\steamapps\common\ROB RUN\GameAssembly.dll'
print('Loading GameAssembly.dll...')
pe = pefile.PE(path, fast_load=True)

with open(path, 'rb') as f:
    raw = f.read()

# Search for "get_main"
pos = 0
matches = []
while len(matches) < 10:
    pos = raw.find(b'get_main', pos)
    if pos == -1: break
    matches.append(hex(pos))
    pos += 1

print('get_main matches in GameAssembly:', matches)
