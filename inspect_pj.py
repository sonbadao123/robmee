import pefile

pe = pefile.PE(r'd:\ESP robrun\ROB【云更新 右键管理员运行】.exe')
for s in pe.sections:
    name = s.Name.decode('latin1').strip('\x00')
    if name == '.pj':
        data = s.get_data()
        print(f"Section .pj length: {len(data)}")
        print("First 64 bytes (hex):", data[:64].hex())
        print("First 64 bytes (repr):", repr(data[:64]))
        print("Last 64 bytes (hex):", data[-64:].hex())
        print("Last 64 bytes (repr):", repr(data[-64:]))
        
        # Check if there is an uncompressed or partially compressed header
        # Check for strings
        import string
        printable = set(bytes(string.printable, 'ascii'))
        words = []
        cur = bytearray()
        for b in data[:100000]: # first 100k
            if b in printable and b >= 32:
                cur.append(b)
            else:
                if len(cur) >= 6:
                    words.append(cur.decode('ascii'))
                cur = bytearray()
        print("Sample strings in first 100k of .pj:", words[:30])
