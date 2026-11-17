import winreg

def check_services():
    h = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services")
    i = 0
    services = []
    while True:
        try:
            subkey_name = winreg.EnumKey(h, i)
            i += 1
            try:
                sk = winreg.OpenKey(h, subkey_name)
                try:
                    img_path, _ = winreg.QueryValueEx(sk, "ImagePath")
                    # Check if suspicious or recently modified
                    services.append((subkey_name, img_path))
                except:
                    pass
                winreg.CloseKey(sk)
            except:
                pass
        except OSError:
            break
    winreg.CloseKey(h)
    return services

svcs = check_services()
print(f"Total services with ImagePath: {len(svcs)}")
for name, img in svcs:
    lower_img = img.lower()
    if any(k in lower_img for k in ['temp', 'appdata', 'robrun', 'kefir', 'gdrv', 'procexp', 'echo', 'mhyprot', 'dbutil']):
        print(f"Service: {name} -> {img}")
