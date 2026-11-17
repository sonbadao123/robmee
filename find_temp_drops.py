import os, time

temp_dir = os.environ.get('TEMP', r'C:\Users\vphoa\AppData\Local\Temp')
now = time.time()
recent_files = []

for root, dirs, files in os.walk(temp_dir):
    for f in files:
        fp = os.path.join(root, f)
        try:
            mtime = os.path.getmtime(fp)
            if now - mtime < 4 * 3600: # last 4 hours
                recent_files.append((mtime, os.path.getsize(fp), fp))
        except:
            pass

recent_files.sort(key=lambda x: x[0], reverse=True)
print(f"Total recent files in TEMP: {len(recent_files)}")
for mt, sz, fp in recent_files[:40]:
    tstr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))
    print(f"[{tstr}] {sz:10d} B : {fp}")
