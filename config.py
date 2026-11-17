"""
ROB RUN - ESP & AIMBOT CONFIGURATION (KERNEL DRIVER SUITE)
Pure Memory & Kernel Mode Architecture (Vision Modules Removed)
"""

import win32con

# ==============================================================================
# TARGET GAME CONFIGURATION
# ==============================================================================
GAME_NAME = "ROB RUN"
GAME_EXE = "ROB RUN.exe"
STEAM_APP_ID = "Rob Run"

# ==============================================================================
# OPERATION MODE: KERNEL DMA / MEMORY
# ==============================================================================
OPERATING_MODE = "KERNEL"
KERNEL_DEVICE_PATH = None  # Tự động chọn thiết bị kernel đang hoạt động

# ==============================================================================
# SCREEN & DISPLAY SETTINGS
# ==============================================================================
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2
CAMERA_FOV = 75.0

# ==============================================================================
# AIMBOT SETTINGS (DISABLED - ESP ONLY MODE)
# ==============================================================================
AIM_ENABLED = False
AIM_KEY = win32con.VK_RBUTTON
AIM_FOV = 0
AIM_SMOOTH = 0.0
AIM_BONE_OFFSET = 0.18

# Chống phát hiện EAC Heuristics
BEZIER_CURVE_ENABLED = False
HUMAN_JITTER_PIXELS = 0
AIM_MIN_DELAY_MS = 0
AIM_MAX_DELAY_MS = 0

# ==============================================================================
# QUY TẮC LỌC MỤC TIÊU (STRICT REQUIREMENTS)
# ==============================================================================
# Tuyệt đối KHÔNG ngắm đồng đội! Chỉ ngắm Cướp và Cảnh sát!
TARGET_ROBBERS = True
TARGET_POLICE = True
TARGET_TEAMMATES = False        # KHÓA CHẶT: Không bao giờ ngắm đồng đội

# ==============================================================================
# ESP OVERLAY SETTINGS (ROB VISION CYBERPUNK SUITE)
# ==============================================================================
ESP_ENABLED = True
DRAW_FOV_CIRCLE = False
DRAW_BOXES = True
BOX_STYLE = "CORNER"             # "CORNER" (Khung bo góc kiểu Trung), "FULL" (Khung viền liền)
DRAW_SKELETON = True             # Khung xương người chơi
DRAW_HEAD_DOT = True             # Điểm ngắm đầu
DRAW_SNAPLINES = True            # Vạch kẻ chỉ hướng
SNAPLINE_ORIGIN = "BOTTOM"       # "BOTTOM" (Đáy màn hình), "CENTER" (Giữa màn hình)
DRAW_NAMES = True                # Tên nhân vật
DRAW_ROLES = True                # Nghề nghiệp / Vai trò (Cảnh sát, Cướp, Dân)
DRAW_DISTANCE = True             # Khoảng cách (mét)
DRAW_HEALTH = True               # Thanh máu
DRAW_WEAPON = True               # Tên vũ khí

# Bộ lọc mục tiêu & Khoảng cách
MAX_DISTANCE = 250.0             # Khoảng cách vẽ tối đa (mét) - mặc định 250m
IGNORE_TEAMMATES = True          # Bỏ qua đồng đội
FILTER_ROBBERS = True            # Vẽ Cướp
FILTER_POLICE = True             # Vẽ Cảnh sát
FILTER_CITIZENS = True           # Vẽ Dân thường

# Màu sắc hiển thị chuẩn ROB VISION
COLOR_TEAMMATE = (0, 255, 127)   # Xanh lục ngọc (Đồng đội an toàn)
COLOR_POLICE = (255, 60, 60)     # Đỏ neon (Cảnh sát)
COLOR_ROBBER = (0, 229, 255)     # Xanh lơ Cyan (Tên cướp)
COLOR_CITIZEN = (255, 215, 0)    # Vàng kim (Dân thường / Trung lập)
COLOR_FOV = (255, 255, 255)

# ==============================================================================
# PHÍM TẮT ĐIỀU KHIỂN
# ==============================================================================
KEY_TOGGLE_ESP = win32con.VK_F1     # F1: Bật / Tắt ESP Overlay
KEY_TOGGLE_AIM = win32con.VK_F2     # F2: Bật / Tắt Aimbot
KEY_TOGGLE_FOV = win32con.VK_F3     # F3: Bật / Tắt Vòng tròn FOV
KEY_PANIC = win32con.VK_F12         # F12: Phím thoát khẩn cấp (Panic Key)
