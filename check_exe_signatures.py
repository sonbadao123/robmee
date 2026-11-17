import os

file_path = r'd:\ESP robrun\ROB【云更新 右键管理员运行】.exe'
size = os.path.getsize(file_path)
print(f"File size: {size} bytes")

with open(file_path, 'rb') as f:
    header = f.read(4096)
    print("DOS Header MZ:", header[:2] == b'MZ')
    
    # Check common archive headers anywhere in the file
    signatures = {
        b'PK\x03\x04': 'ZIP archive',
        b'7z\xbc\xaf\x27\x1c': '7-Zip archive',
        b'Rar!\x1a\x07': 'RAR archive',
        b'MEI\x0c\x0b\x0a\x0b': 'PyInstaller',
        b'Inno Setup': 'Inno Setup',
        b'Nullsoft': 'NSIS installer',
        b'Unity': 'Unity engine',
        b'EasyAntiCheat': 'EAC mention',
        b'EAC': 'EAC',
        b'\\Device\\': 'Device path',
        b'IOCTL': 'IOCTL',
        b'\\\\.\\': 'Named device'
    }

    f.seek(0)
    data = f.read()
    
    for sig, desc in signatures.items():
        pos = data.find(sig)
        if pos != -1:
            print(f"Found {desc} ({sig}) at offset 0x{pos:X}")
