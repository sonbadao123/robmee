"""
CLICK-THROUGH TRANSPARENT ESP OVERLAY (FLAWLESS WIN32 DWM COMPOSITION)
Vẽ khung 2D, nhãn vai trò, vạch chỉ hướng (snaplines) và vòng ngắm FOV.
100% trong suốt qua Win32 WS_EX_LAYERED + WS_EX_TRANSPARENT trên Top-Level HWND.
Triệt tiêu hoàn toàn lỗi đen màn hình và xanh màn hình.
"""

import time
import ctypes
import secrets
import tkinter as tk
import win32gui
import win32con
import config

user32 = ctypes.windll.user32

HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

# Màu khóa đục trong suốt (Chroma Key): Dùng #010101 (RGB: 1, 1, 1 -> COLORREF: 0x00010101)
# Đối xứng 100% giữa RGB và BGR, triệt tiêu hoàn toàn lỗi lệch màu và cắn màu vẽ
CHROMA_KEY_HEX = "#010101"
CHROMA_KEY_COLORREF = 0x00010101  # RGB(1, 1, 1)

class EspOverlay:
    """
    Cửa sổ overlay xuyên thấu (click-through) trong suốt 100%.
    Gán cờ chuẩn xác lên Top-Level HWND (TkTopLevel) thay vì Child HWND.
    Không chiếm chuột, không che màn hình game.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(secrets.token_hex(8))
        self.root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Nền màu Chroma Key để Windows DWM đục thủng thành vô hình
        self.root.config(bg=CHROMA_KEY_HEX)

        self.canvas = tk.Canvas(
            self.root,
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            bg=CHROMA_KEY_HEX,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Đăng ký màu trong suốt với Tkinter engine
        try:
            self.root.wm_attributes("-transparentcolor", CHROMA_KEY_HEX)
        except Exception:
            pass

        self.root.update_idletasks()
        self.root.update()

        # Tìm chính xác Top-Level HWND (TkTopLevel) qua GetAncestor (GA_ROOT = 2)
        self.child_hwnd = self.root.winfo_id()
        top = user32.GetAncestor(self.child_hwnd, 2)
        self.top_hwnd = top if top else (win32gui.GetParent(self.child_hwnd) or self.child_hwnd)

        self._init_win32_transparency()

        self.targets = []
        self.aim_active = False
        self.fps = 0.0
        self.last_topmost_time = 0.0

    def _init_win32_transparency(self):
        """Khởi tạo cờ Win32 và nạp mã màu trong suốt chuẩn xác lên cả TopLevel và Child."""
        for hwnd in set([self.top_hwnd, self.child_hwnd]):
            if not hwnd:
                continue
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style |= (
                    win32con.WS_EX_LAYERED |
                    win32con.WS_EX_TRANSPARENT |
                    win32con.WS_EX_TOPMOST |
                    win32con.WS_EX_TOOLWINDOW
                )
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
                # Gán thuộc tính Layered Window Attributes (LWA_COLORKEY = 1)
                user32.SetLayeredWindowAttributes(hwnd, CHROMA_KEY_COLORREF, 0, 1)
            except Exception:
                pass

        try:
            # Đặt Z-Order TopMost không chiếm kích hoạt
            user32.SetWindowPos(
                self.top_hwnd, HWND_TOPMOST,
                0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT,
                SWP_SHOWWINDOW | SWP_NOACTIVATE
            )
        except Exception:
            pass

    def update_data(self, targets, aim_active, fps, aim_enabled=True):
        self.targets = targets
        self.aim_active = aim_active
        self.fps = fps
        self.aim_enabled = aim_enabled

    def render(self):
        self.canvas.delete("all")

        # Duy trì Z-Order trên cùng định kỳ mỗi 5.0 giây (chống EAC phát hiện spam hook cửa sổ)
        now = time.time()
        if now - self.last_topmost_time > 5.0:
            self.last_topmost_time = now
            try:
                user32.SetWindowPos(
                    self.top_hwnd, HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                )
            except Exception:
                pass

        # 1. Vẽ vòng tròn ngắm FOV
        if config.DRAW_FOV_CIRCLE:
            r = config.AIM_FOV
            cx, cy = config.CENTER_X, config.CENTER_Y
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="#FFFFFF", width=1
            )

        # 2. Vẽ trạng thái HUD tiếng Việt ở góc trên trái
        target_count = len(self.targets)
        f1_tag = "[BẬT]" if config.ESP_ENABLED else "[TẮT]"

        status_text = f"FPS: {self.fps:.1f} | ESP[F1]: {f1_tag} | THỰC THỂ: {target_count}"
        self.canvas.create_text(
            25, 25, anchor="nw",
            text=status_text,
            fill="#00FFFF",
            font=("Segoe UI", 11, "bold")
        )

        if not config.ESP_ENABLED:
            self.root.update_idletasks()
            self.root.update()
            return

        # 3. Vẽ danh sách mục tiêu (hỗ trợ cả mục tiêu ở xa)
        for t in self.targets:
            # Triệt để loại bỏ mọi mục tiêu tính toán sai bị văng ra ngoài màn hình (âm Y hoặc tràn viền)
            if t.y + t.h < 0 or t.y > config.SCREEN_HEIGHT or t.x + t.w < 0 or t.x > config.SCREEN_WIDTH:
                continue

            if t.role == "TEAMMATE":
                color = "#00FF00"  # Xanh lá (Đồng đội - KHÔNG AIM)
                label = "ĐỒNG ĐỘI [AN TOÀN]"
            elif t.role == "CITIZEN":
                color = "#FFFF33"  # Vàng tươi (Dân thường / NPC - KHÔNG AIM)
                label = "DÂN THƯỜNG [AN TOÀN]"
            elif t.role == "POLICE":
                color = "#FF3333"  # Đỏ tươi (Cảnh sát - BẬT AIM)
                label = "CẢNH SÁT [MỤC TIÊU]"
            else:
                color = "#FFA500"  # Cam đậm (Tên cướp - BẬT AIM)
                label = "TÊN CƯỚP [MỤC TIÊU]"

            # Khung Bounding Box
            if config.DRAW_BOXES:
                # Độ dày viền: 2px khi ở gần, 1px khi ở xa
                box_width = 2 if t.h > 40 else 1
                self.canvas.create_rectangle(
                    t.x, t.y, t.x + t.w, t.y + t.h,
                    outline=color, width=box_width
                )

            # Điểm ngắm đầu (Head Aim Dot)
            if config.DRAW_HEAD_DOT:
                hr = 3 if t.h > 40 else 2
                self.canvas.create_oval(
                    t.aim_x - hr, t.aim_y - hr, t.aim_x + hr, t.aim_y + hr,
                    fill=color, outline="#FFFFFF", width=1
                )

            # Nhãn vai trò & Khoảng cách (không bao giờ ghim cứng lên mép đỉnh Y=12)
            if config.DRAW_NAMES:
                font_size = 9 if t.h > 40 else 8
                dist_str = f"{label} ({int(t.dist_to_crosshair)}px)"
                y_label = t.y - 12 if t.y >= 20 else t.y + t.h + 14
                self.canvas.create_text(
                    t.x + (t.w // 2), y_label,
                    text=dist_str,
                    fill=color,
                    font=("Segoe UI", font_size, "bold")
                )

            # Đường kẻ Snapline tới mục tiêu thù địch (chỉ vẽ khi nằm trong vùng hiển thị an toàn, không bắn lên trời)
            if config.DRAW_SNAPLINES and t.is_hostile:
                if 20 <= t.aim_x <= (config.SCREEN_WIDTH - 20) and 40 <= t.aim_y <= (config.SCREEN_HEIGHT - 10):
                    self.canvas.create_line(
                        config.CENTER_X, config.SCREEN_HEIGHT,
                        t.aim_x, t.aim_y,
                        fill=color, width=1, dash=(4, 2)
                    )

        self.root.update_idletasks()
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass
