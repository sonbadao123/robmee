import pefile, re

dll_path = r'D:\SteamLibrary\steamapps\common\ROB RUN\UnityPlayer.dll'
raw = open(dll_path, 'rb').read()

cam_strings = [
    b'get_worldToCameraMatrix',
    b'get_projectionMatrix',
    b'get_cameraToWorldMatrix',
    b'WorldToScreenPoint',
    b'get_pixelWidth',
    b'get_pixelHeight',
    b'get_fieldOfView',
]

for s in cam_strings:
    pos = 0
    found = []
    while True:
        p = raw.find(s, pos)
        if p == -1: break
        found.append(p)
        pos = p + 1
    print(f"String '{s.decode()}': found {len(found)} times at {[hex(x) for x in found]}")
