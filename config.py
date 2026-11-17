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
# ESP OVERLAY SETTINGS
# ==============================================================================
ESP_ENABLED = True
DRAW_FOV_CIRCLE = False
DRAW_BOXES = True
DRAW_HEAD_DOT = True
DRAW_SNAPLINES = True
DRAW_NAMES = True

# Màu sắc hiển thị
COLOR_TEAMMATE = (0, 255, 0)      # Xanh lá (Đồng đội an toàn)
COLOR_POLICE = (0, 0, 255)        # Đỏ (Cảnh sát)
COLOR_ROBBER = (0, 165, 255)      # Cam (Tên cướp)
COLOR_FOV = (255, 255, 255)

# ==============================================================================
# PHÍM TẮT ĐIỀU KHIỂN
# ==============================================================================
KEY_TOGGLE_ESP = win32con.VK_F1     # F1: Bật / Tắt ESP Overlay
KEY_TOGGLE_AIM = win32con.VK_F2     # F2: Bật / Tắt Aimbot
KEY_TOGGLE_FOV = win32con.VK_F3     # F3: Bật / Tắt Vòng tròn FOV
KEY_PANIC = win32con.VK_F12         # F12: Phím thoát khẩn cấp (Panic Key)
