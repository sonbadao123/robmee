"""
ROB RUN - RESTORE ORIGINAL ENGLISH LOCALIZATION
Restores the original game bundle from backup.
"""

import os
import shutil

DEFAULT_GAME_BUNDLE = r"D:\SteamLibrary\steamapps\common\Rob Run\ROB RUN_Data\StreamingAssets\aa\StandaloneWindows64\localization-string-tables-english(unitedstates)(en-us)_assets_all.bundle"

def restore_original():
    backup_path = DEFAULT_GAME_BUNDLE + ".bak"
    if not os.path.exists(backup_path):
        print("[!] Không tìm thấy tệp sao lưu (.bak) của trò chơi.")
        return False

    print(f"[*] Đang khôi phục tệp gốc từ: {backup_path}")
    shutil.copy2(backup_path, DEFAULT_GAME_BUNDLE)
    print("[OK] ĐÃ KHÔI PHỤC TIẾNG ANH GỐC THÀNH CÔNG!")
    return True

if __name__ == "__main__":
    restore_original()
