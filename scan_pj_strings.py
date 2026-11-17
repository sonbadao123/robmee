import pefile, re

pe = pefile.PE(r'd:\ESP robrun\ROB【云更新 右键管理员运行】.exe')
for s in pe.sections:
    name = s.Name.decode('latin1').strip('\x00')
    if name == '.pj':
        data = s.get_data()
        
        # Regex for ASCII strings >= 5 chars
        ascii_strings = re.findall(rb'[A-Za-z0-9_\-\.\/\\:]{5,}', data)
        print(f"Total ASCII strings found in .pj: {len(ascii_strings)}")
        
        # Check interesting keywords
        keywords = [b'http', b'.sys', b'.exe', b'.dll', b'RobRun', b'driver', b'camera', b'matrix', b'transform', b'Player', b'GameAssembly', b'UnityPlayer', b'GOM', b'GameObjectManager', b'ViewMatrix', b'WorldToScreen']
        for kw in keywords:
            matches = [st.decode('latin1') for st in ascii_strings if kw.lower() in st.lower()]
            if matches:
                print(f"\nKeyword [{kw.decode()}]: {len(matches)} matches")
                for m in list(set(matches))[:15]:
                    print("  ", m)
