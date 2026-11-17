"""
ROB RUN - DYNAMIC OS FONT & ACCENTED VIETNAMESE LOCALIZATION INJECTOR
"""

import os
import shutil
import json
import UnityPy
import psutil

GAME_DIR = r"D:\SteamLibrary\steamapps\common\Rob Run"
BUNDLE_DIR = os.path.join(GAME_DIR, r"ROB RUN_Data\StreamingAssets\aa\StandaloneWindows64")
INBUILD_BUNDLE = os.path.join(BUNDLE_DIR, "inbuild_assets_all.bundle")
INBUILD_BACKUP = INBUILD_BUNDLE + ".bak"
LOC_BUNDLE = os.path.join(BUNDLE_DIR, "localization-string-tables-english(unitedstates)(en-us)_assets_all.bundle")
LOC_BACKUP = LOC_BUNDLE + ".bak"
CACHE_PATH = r"d:\ESP robrun\viet_hoa\cache.json"

def is_game_running():
    for p in psutil.process_iter(['name']):
        if p.info['name'] and 'rob run' in p.info['name'].lower():
            return True
    return False

def apply_full_accented_patch():
    print("=" * 70)
    print("  ROB RUN - CAI DAT TIENG VIET CO DAU 100% (DYNAMIC OS FONT PATCH)")
    print("=" * 70)

    if is_game_running():
        print("\n[!] Game ROB RUN dang chay tren may! Vui long thoat game de tiep tuc...")
        while is_game_running():
            pass
        print("[OK] Game da tat. Dang tien hanh nap font va ban dich...")

    # Backups
    if not os.path.exists(INBUILD_BACKUP):
        print(f"[*] Tao ban sao luu font goc: {INBUILD_BACKUP}")
        shutil.copy2(INBUILD_BUNDLE, INBUILD_BACKUP)

    if not os.path.exists(LOC_BACKUP):
        print(f"[*] Tao ban sao luu ngon ngu goc: {LOC_BACKUP}")
        shutil.copy2(LOC_BUNDLE, LOC_BACKUP)

    # 1. Patch fonts in memory
    print(f"[*] Dang mo khoa Dynamic OS Font trong {INBUILD_BUNDLE}...")
    with open(INBUILD_BACKUP, "rb") as f:
        inbuild_bytes = f.read()

    env_fonts = UnityPy.load(inbuild_bytes)
    for obj in env_fonts.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
                if isinstance(tree, dict) and "m_CharacterTable" in tree:
                    tree["m_AtlasPopulationMode"] = 1
                    tree["InternalDynamicOS"] = 1
                    tree["m_IsMultiAtlasTexturesEnabled"] = 1
                    tree["m_SourceFontFilePath"] = r"C:\Windows\Fonts\arial.ttf"
                    obj.save_typetree(tree)
            except:
                pass

    repacked_fonts = env_fonts.file.save()
    with open(INBUILD_BUNDLE, "wb") as f:
        f.write(repacked_fonts)
    print("[+] Da mo khoa font TextMeshPro ho tro day du ky tu tieng Viet!")

    # 2. Patch accented strings
    print(f"[*] Dang nap 4.822 chuoi Tieng Viet co dau vao {LOC_BUNDLE}...")
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    with open(LOC_BACKUP, "rb") as f:
        loc_bytes = f.read()

    env_loc = UnityPy.load(loc_bytes)
    injected = 0
    for obj in env_loc.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
                if isinstance(tree, dict) and "m_TableData" in tree:
                    for item in tree["m_TableData"]:
                        orig = item.get("m_Localized")
                        if orig and orig.strip() in cache:
                            item["m_Localized"] = cache[orig.strip()]
                            injected += 1
                    obj.save_typetree(tree)
            except:
                pass

    repacked_loc = env_loc.file.save()
    with open(LOC_BUNDLE, "wb") as f:
        f.write(repacked_loc)

    print(f"[+] Da tiem thanh cong {injected} chuoi Tieng Viet co dau!")
    print("\n" + "=" * 70)
    print("  [HOAN TAT] DA CAI DAT TIENG VIET CO DAU 100% CUNG DYNAMIC FONT!")
    print("  Mo lai game ROB RUN de trai nghiem.")
    print("=" * 70)

if __name__ == "__main__":
    apply_full_accented_patch()
