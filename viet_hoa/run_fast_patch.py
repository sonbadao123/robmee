import json
import time
import requests
import concurrent.futures
import re
import os
import shutil
import UnityPy

print("=" * 65)
print("  ROB RUN - FAST MULTITHREADED AI TRANSLATION & REPACK")
print("=" * 65)

DUMP_PATH = r"d:\ESP robrun\english_strings_dump.json"
GLOSSARY_PATH = r"d:\ESP robrun\viet_hoa\glossary.json"
CACHE_PATH = r"d:\ESP robrun\viet_hoa\cache.json"
GAME_BUNDLE = r"D:\SteamLibrary\steamapps\common\Rob Run\ROB RUN_Data\StreamingAssets\aa\StandaloneWindows64\localization-string-tables-english(unitedstates)(en-us)_assets_all.bundle"
BACKUP_BUNDLE = GAME_BUNDLE + ".bak"

# 1. Ensure backup exists
if not os.path.exists(BACKUP_BUNDLE):
    print(f"[*] Creating backup: {BACKUP_BUNDLE}")
    shutil.copy2(GAME_BUNDLE, BACKUP_BUNDLE)
else:
    print(f"[*] Backup already exists: {BACKUP_BUNDLE}")

with open(DUMP_PATH, "r", encoding="utf-8") as f:
    dump = json.load(f)

with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
    glossary = json.load(f)

# Load existing cache if any
cache = {}
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except:
        cache = {}

# Collect unique strings that need translation
unique_strings = []
seen = set()
for tname, items in dump.items():
    for item in items:
        s = item["en"].strip()
        if s and s not in seen:
            seen.add(s)
            if s not in cache:
                unique_strings.append(s)

print(f"[*] Strings in cache: {len(cache)} | Strings to translate: {len(unique_strings)}")

DELIM = "\n===\n"

def translate_chunk(chunk):
    results = {}
    needed = []
    for s in chunk:
        if s in glossary:
            results[s] = glossary[s]
        else:
            needed.append(s)

    if not needed:
        return results

    joined = DELIM.join(needed)
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "vi",
        "dt": "t",
        "q": joined
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        if r.status_code == 200:
            res = r.json()
            full_vi = "".join([part[0] for part in res[0] if part and part[0]])
            parts = full_vi.split(DELIM)
            if len(parts) == len(needed):
                for en, vi in zip(needed, parts):
                    vi_clean = vi.strip()
                    for g_en, g_vi in glossary.items():
                        if len(g_en) >= 4 and g_en.lower() in en.lower():
                            vi_clean = re.sub(re.escape(g_en), g_vi, vi_clean, flags=re.IGNORECASE)
                    results[en] = vi_clean
            else:
                for en in needed:
                    results[en] = en
    except Exception as e:
        for en in needed:
            results[en] = en
    return results

if unique_strings:
    t0 = time.time()
    chunk_size = 35
    chunks = [unique_strings[i:i + chunk_size] for i in range(0, len(unique_strings), chunk_size)]
    print(f"[*] Translating {len(chunks)} chunks with 6 worker threads...")

    completed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(translate_chunk, c): c for c in chunks}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            cache.update(res)
            completed_count += len(res)
            pct = (completed_count / len(unique_strings)) * 100
            print(f"    Progress: {completed_count}/{len(unique_strings)} ({pct:.1f}%)", end="\r")

    t1 = time.time()
    print(f"\n[+] Translation finished in {t1 - t0:.2f}s! Total cached strings: {len(cache)}")
    
    # Save cache
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# Now repack into game bundle
print(f"[*] Loading clean backup bundle: {BACKUP_BUNDLE}")
env = UnityPy.load(BACKUP_BUNDLE)

total_injected = 0
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            if isinstance(tree, dict) and "m_TableData" in tree:
                tname = tree.get("m_Name")
                table_data = tree["m_TableData"]
                modified = False
                for item in table_data:
                    orig = item.get("m_Localized")
                    if orig:
                        orig_stripped = orig.strip()
                        if orig_stripped in cache:
                            item["m_Localized"] = cache[orig_stripped]
                            modified = True
                            total_injected += 1
                        elif orig_stripped in glossary:
                            item["m_Localized"] = glossary[orig_stripped]
                            modified = True
                            total_injected += 1
                if modified:
                    obj.save_typetree(tree)
                    print(f"[+] Injected table '{tname}' ({len(table_data)} entries)")
        except Exception as e:
            print(f"[!] Error in table: {e}")

print(f"[*] Total strings injected into bundle: {total_injected}")
print(f"[*] Saving repacked bundle to game...")
temp_bundle = GAME_BUNDLE + ".tmp"
with open(temp_bundle, "wb") as f:
    f.write(env.file.save())

shutil.move(temp_bundle, GAME_BUNDLE)
print(f"[SUCCESS] VIỆT HÓA ĐÃ ĐƯỢC CÀI ĐẶT TRỰC TIẾP VÀO GAME 100%!")
