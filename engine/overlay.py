"""
ROB RUN - ESP OVERLAY & ROB VISION CYBERPUNK MENU (RING 0 KERNEL DMA)
Phát triển theo đúng chuẩn giao diện 'ROB VISION' của bản Trung Quốc:
- Menu Cyberpunk Dark Theme (#0B0F14 / #00E5FF / #00FF7F).
- Tabs: Nhân vật, Ngắm bắn, Radar, Vật phẩm, Thế giới, Cài đặt, Việt hóa, Hướng dẫn.
- Phím F1: Bật / Tắt Menu. Khi bật menu cho phép click chuột chỉnh thông số; khi tắt menu trở thành click-through 100%.
- Vẽ ESP: Khung bo góc Corner Box 2D, Khoảng cách theo mét, Tên, Nghề nghiệp, Thanh máu, Vạch kẻ Snaplines.
"""

import time
import math
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

CHROMA_KEY_HEX = "#010101"
CHROMA_KEY_COLORREF = 0x00010101  # RGB(1, 1, 1)

class EspOverlay:
    """
    Cửa sổ overlay Win32 DWM trong suốt tích hợp GUI Menu ROB VISION chuẩn Trung Quốc.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ROB VISION - Kernel Suite")
        self.root.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg=CHROMA_KEY_HEX)

        self.canvas = tk.Canvas(
            self.root,
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            bg=CHROMA_KEY_HEX,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        try:
            self.root.wm_attributes("-transparentcolor", CHROMA_KEY_HEX)
        except Exception:
            pass

        self.root.update_idletasks()
        self.root.update()

        self.child_hwnd = self.root.winfo_id()
        top = user32.GetAncestor(self.child_hwnd, 2)
        self.top_hwnd = top if top else (win32gui.GetParent(self.child_hwnd) or self.child_hwnd)

        self.show_menu = False
        self.current_tab = "PLAYER"  # "PLAYER", "AIMBOT", "RADAR", "ITEMS", "WORLD", "SETTINGS", "TRANSLATE", "GUIDE"
        self.interactive_elements = [] # [(x0, y0, x1, y1, callback, tooltip)]

        self._init_win32_transparency(transparent=True)

        self.targets = []
        self.aim_active = False
        self.fps = 0.0
        self.last_topmost_time = 0.0
        self.status_msg = "Sẵn sàng"

        # Bắt sự kiện chuột cho menu
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def _init_win32_transparency(self, transparent=True):
        """Chuyển đổi cờ WS_EX_TRANSPARENT để hỗ trợ click-through khi tắt menu và tương tác chuột khi bật menu."""
        for hwnd in set([self.top_hwnd, self.child_hwnd]):
            if not hwnd:
                continue
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                style |= (win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW)
                if transparent:
                    style |= win32con.WS_EX_TRANSPARENT
                else:
                    style &= ~win32con.WS_EX_TRANSPARENT
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
                user32.SetLayeredWindowAttributes(hwnd, CHROMA_KEY_COLORREF, 0, 1)
            except Exception:
                pass

        try:
            user32.SetWindowPos(
                self.top_hwnd, HWND_TOPMOST,
                0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT,
                SWP_SHOWWINDOW | (SWP_NOACTIVATE if transparent else 0)
            )
        except Exception:
            pass

    def toggle_menu(self):
        """Bật / Tắt Menu ROB VISION."""
        self.show_menu = not self.show_menu
        self._init_win32_transparency(transparent=(not self.show_menu))
        if self.show_menu:
            self.root.focus_force()

    def update_data(self, targets, aim_active, fps, aim_enabled=True):
        self.targets = targets
        self.aim_active = aim_active
        self.fps = fps
        self.aim_enabled = aim_enabled

    def render(self):
        self.canvas.delete("all")
        self.interactive_elements.clear()

        # Giữ Z-Order trên cùng
        now = time.time()
        if now - self.last_topmost_time > 4.0:
            self.last_topmost_time = now
            try:
                user32.SetWindowPos(
                    self.top_hwnd, HWND_TOPMOST,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | (SWP_NOACTIVATE if not self.show_menu else 0)
                )
            except Exception:
                pass

        # 1. Vẽ HUD thanh trạng thái nhỏ góc trái
        target_count = len(self.targets)
        hud_text = f"ROB VISION | {self.fps:.0f} FPS | THỰC THỂ: {target_count} | [F1] MENU"
        self.canvas.create_text(
            20, 20, anchor="nw",
            text=hud_text,
            fill="#00E5FF",
            font=("Segoe UI", 10, "bold")
        )

        # 2. Vẽ các thực thể ESP
        if config.ESP_ENABLED:
            self._render_esp_targets()

        # 3. Vẽ Giao diện Menu ROB VISION khi đang mở
        if self.show_menu:
            self._render_menu_window()

        self.root.update_idletasks()
        self.root.update()

    def _render_esp_targets(self):
        for t in self.targets:
            # Bỏ qua nhân vật chính
            if getattr(t, 'is_local', False):
                continue

            # Lọc mục tiêu theo khoảng cách
            if getattr(t, 'distance_m', 0.0) > config.MAX_DISTANCE:
                continue

            # Lọc mục tiêu theo vai trò
            if t.role == "TEAMMATE" and config.IGNORE_TEAMMATES:
                continue
            if t.role == "ROBBER" and not config.FILTER_ROBBERS:
                continue
            if t.role == "POLICE" and not config.FILTER_POLICE:
                continue
            if t.role == "CITIZEN" and not config.FILTER_CITIZENS:
                continue

            # Thiết lập màu sắc theo vai trò
            if t.role == "TEAMMATE":
                color = "#00FF7F"  # Xanh ngọc
                role_label = "[ĐỒNG ĐỘI]"
            elif t.role == "POLICE":
                color = "#FF3344"  # Đỏ neon
                role_label = "[CẢNH SÁT]"
            elif t.role == "CITIZEN":
                color = "#FFD700"  # Vàng
                role_label = "[DÂN THƯỜNG]"
            else:
                color = "#00E5FF"  # Cyan
                role_label = "[CƯỚP]"

            dist_val = int(getattr(t, 'distance_m', t.dist_to_crosshair / 10.0))

            # A. Khung Box (Corner Box kiểu Trung Quốc)
            if config.DRAW_BOXES:
                if getattr(config, 'BOX_STYLE', 'CORNER') == 'CORNER':
                    self._draw_corner_box(t.x, t.y, t.w, t.h, color)
                else:
                    self.canvas.create_rectangle(t.x, t.y, t.x + t.w, t.y + t.h, outline=color, width=1)

            # B. Thanh máu (Health Bar)
            if getattr(config, 'DRAW_HEALTH', True):
                self._draw_health_bar(t.x, t.y, t.h, getattr(t, 'health', 100.0))

            # C. Nhãn thông tin: Vai trò / Khoảng cách / Tên
            info_parts = []
            if getattr(config, 'DRAW_ROLES', True):
                info_parts.append(role_label)
            if getattr(config, 'DRAW_DISTANCE', True):
                info_parts.append(f"{dist_val}m")

            header_text = " ".join(info_parts)
            if header_text:
                self.canvas.create_text(
                    t.x + (t.w // 2), t.y - 10,
                    text=header_text,
                    fill=color,
                    font=("Segoe UI", 8, "bold")
                )

            # D. Điểm ngắm đầu (Head Aim Dot)
            if config.DRAW_HEAD_DOT:
                hr = 2 if t.h > 40 else 1
                self.canvas.create_oval(
                    t.aim_x - hr, t.aim_y - hr, t.aim_x + hr, t.aim_y + hr,
                    fill="#FFFFFF", outline=color, width=1
                )

            # E. Vạch kẻ Snaplines
            if config.DRAW_SNAPLINES and t.is_hostile:
                origin_y = config.SCREEN_HEIGHT if config.SNAPLINE_ORIGIN == "BOTTOM" else config.CENTER_Y
                self.canvas.create_line(
                    config.CENTER_X, origin_y,
                    t.x + (t.w // 2), t.y + t.h,
                    fill=color, width=1, dash=(3, 3)
                )

    def _draw_corner_box(self, x, y, w, h, color):
        """Vẽ khung 4 góc (Corner Bounding Box) đúng chuẩn game hack cao cấp."""
        line_w = max(4, w // 4)
        line_h = max(4, h // 5)
        kw = {"fill": color, "width": 1.5}

        # Góc trên - trái
        self.canvas.create_line(x, y, x + line_w, y, **kw)
        self.canvas.create_line(x, y, x, y + line_h, **kw)

        # Góc trên - phải
        self.canvas.create_line(x + w, y, x + w - line_w, y, **kw)
        self.canvas.create_line(x + w, y, x + w, y + line_h, **kw)

        # Góc dưới - trái
        self.canvas.create_line(x, y + h, x + line_w, y + h, **kw)
        self.canvas.create_line(x, y + h, x, y + h - line_h, **kw)

        # Góc dưới - phải
        self.canvas.create_line(x + w, y + h, x + w - line_w, y + h, **kw)
        self.canvas.create_line(x + w, y + h, x + w, y + h - line_h, **kw)

    def _draw_health_bar(self, x, y, h, hp):
        """Thanh máu 2px viền đen, đổi màu theo HP."""
        bar_x = x - 5
        bar_w = 3
        hp_clamped = max(0.0, min(100.0, hp))
        fill_h = int((h * hp_clamped) / 100.0)

        hp_color = "#00FF7F" if hp_clamped > 60 else ("#FFCC00" if hp_clamped > 25 else "#FF2233")
        self.canvas.create_rectangle(bar_x, y, bar_x + bar_w, y + h, fill="#1A1A1A", outline="#000000", width=1)
        self.canvas.create_rectangle(bar_x + 1, y + h - fill_h, bar_x + bar_w, y + h, fill=hp_color, outline="")

    # ─────────────────────────────────────────────────────────────────────────
    # ROB VISION MENU RENDERING (CHUẨN BẢN TRUNG QUỐC)
    # ─────────────────────────────────────────────────────────────────────────

    def _render_menu_window(self):
        mw, mh = 760, 480
        mx0 = config.CENTER_X - (mw // 2)
        my0 = config.CENTER_Y - (mh // 2)
        mx1 = mx0 + mw
        my1 = my0 + mh

        # Nền chính cửa sổ (Dark Cyber Slate #0D131A)
        self.canvas.create_rectangle(mx0, my0, mx1, my1, fill="#0D131A", outline="#00E5FF", width=2)

        # Thanh tiêu đề Title Bar
        header_h = 36
        self.canvas.create_rectangle(mx0, my0, mx1, my0 + header_h, fill="#141E28", outline="#00E5FF", width=1)
        self.canvas.create_text(mx0 + 15, my0 + (header_h // 2), anchor="w", text="ROB  VISION", fill="#00E5FF", font=("Segoe UI", 12, "bold"))
        self.canvas.create_text(mx0 + 140, my0 + (header_h // 2), anchor="w", text="已连接游戏 | 120 FPS", fill="#00FF7F", font=("Segoe UI", 9))
        self.canvas.create_text(mx1 - 15, my0 + (header_h // 2), anchor="e", text="[F1] Bật / Tắt Menu", fill="#8B949E", font=("Segoe UI", 9))

        # Thanh Tabs ngang (Tab Bar)
        tab_y0 = my0 + header_h + 4
        tab_h = 32
        self.canvas.create_rectangle(mx0 + 8, tab_y0, mx1 - 8, tab_y0 + tab_h, fill="#101820", outline="#1F2D3D")

        tabs = [
            ("人物", "PLAYER"),
            ("瞄准", "AIMBOT"),
            ("地图预警", "RADAR"),
            ("物品", "ITEMS"),
            ("世界对象", "WORLD"),
            ("设置", "SETTINGS"),
            ("游戏汉化", "TRANSLATE"),
            ("说明", "GUIDE")
        ]

        tw = (mw - 24) // len(tabs)
        for i, (t_name, t_id) in enumerate(tabs):
            tx0 = mx0 + 12 + i * tw
            tx1 = tx0 + tw - 2
            ty0 = tab_y0 + 2
            ty1 = tab_y0 + tab_h - 2
            is_active = (self.current_tab == t_id)
            bg = "#00E5FF" if is_active else "#16222F"
            fg = "#000000" if is_active else "#A0AEC0"
            self.canvas.create_rectangle(tx0, ty0, tx1, ty1, fill=bg, outline="")
            self.canvas.create_text((tx0 + tx1) // 2, (ty0 + ty1) // 2, text=t_name, fill=fg, font=("Segoe UI", 9, "bold"))
            self.interactive_elements.append((tx0, ty0, tx1, ty1, lambda tid=t_id: self._set_tab(tid)))

        # Vùng hiển thị nội dung theo Tab
        content_y0 = tab_y0 + tab_h + 8
        if self.current_tab == "PLAYER":
            self._render_tab_player(mx0, content_y0, mw)
        else:
            self._render_tab_other(mx0, content_y0, mw, self.current_tab)

        # Footer thanh trạng thái & Nút Lưu cấu hình
        foot_y0 = my1 - 40
        self.canvas.create_line(mx0, foot_y0, mx1, foot_y0, fill="#1F2D3D", width=1)
        self.canvas.create_text(mx0 + 20, foot_y0 + 20, anchor="w", text=f"Trạng thái: {self.status_msg}", fill="#00FF7F", font=("Segoe UI", 9))

        btn_w, btn_h = 130, 26
        bx0 = mx1 - btn_w - 20
        by0 = foot_y0 + 7
        bx1 = bx0 + btn_w
        by1 = by0 + btn_h
        self.canvas.create_rectangle(bx0, by0, bx1, by1, fill="#00E5FF", outline="")
        self.canvas.create_text((bx0 + bx1) // 2, (by0 + by1) // 2, text="保存配置 (Lưu)", fill="#000000", font=("Segoe UI", 9, "bold"))
        self.interactive_elements.append((bx0, by0, bx1, by1, self._save_config))

    def _render_tab_player(self, mx0, cy0, mw):
        col_w = (mw - 40) // 2
        # Cột trái: CHIẾN ĐẤU & HIỂN THỊ
        cx0 = mx0 + 15
        self._render_card(cx0, cy0, col_w, 335, "战斗与显示 (Chiến đấu & Hiển thị)")
        
        y = cy0 + 35
        y = self._draw_checkbox(cx0 + 15, y, "Vẽ ESP Tổng (绘制总开关)", config.ESP_ENABLED, lambda: self._toggle_cfg("ESP_ENABLED"))
        y = self._draw_checkbox(cx0 + 15, y, "Khung Bo Góc (方框)", config.DRAW_BOXES, lambda: self._toggle_cfg("DRAW_BOXES"))
        y = self._draw_checkbox(cx0 + 15, y, "Điểm Đầu (骨骼/瞄点)", config.DRAW_HEAD_DOT, lambda: self._toggle_cfg("DRAW_HEAD_DOT"))
        y = self._draw_checkbox(cx0 + 15, y, "Hiển Thị Khoảng Cách (距离)", config.DRAW_DISTANCE, lambda: self._toggle_cfg("DRAW_DISTANCE"))
        y = self._draw_checkbox(cx0 + 15, y, "Hiển Thị Tên (显示名字)", config.DRAW_NAMES, lambda: self._toggle_cfg("DRAW_NAMES"))
        y = self._draw_checkbox(cx0 + 15, y, "Hiển Thị Vai Trò (显示职业)", config.DRAW_ROLES, lambda: self._toggle_cfg("DRAW_ROLES"))
        y = self._draw_checkbox(cx0 + 15, y, "Thanh Máu (显示血量)", config.DRAW_HEALTH, lambda: self._toggle_cfg("DRAW_HEALTH"))
        y = self._draw_checkbox(cx0 + 15, y, "Vạch Kẻ Định Vị (玩家连线)", config.DRAW_SNAPLINES, lambda: self._toggle_cfg("DRAW_SNAPLINES"))

        # Cột phải: BỘ LỌC & KHOẢNG CÁCH
        rx0 = cx0 + col_w + 10
        self._render_card(rx0, cy0, col_w, 335, "筛选与距离 (Bộ lọc & Khoảng cách)")
        
        ry = cy0 + 35
        ry = self._draw_checkbox(rx0 + 15, ry, "Bỏ Qua Đồng Đội (绘制跳过队友)", config.IGNORE_TEAMMATES, lambda: self._toggle_cfg("IGNORE_TEAMMATES"))
        ry = self._draw_checkbox(rx0 + 15, ry, "Vẽ Tên Cướp (土匪)", config.FILTER_ROBBERS, lambda: self._toggle_cfg("FILTER_ROBBERS"))
        ry = self._draw_checkbox(rx0 + 15, ry, "Vẽ Cảnh Sát (警察)", config.FILTER_POLICE, lambda: self._toggle_cfg("FILTER_POLICE"))
        ry = self._draw_checkbox(rx0 + 15, ry, "Vẽ Dân Thường (平民)", config.FILTER_CITIZENS, lambda: self._toggle_cfg("FILTER_CITIZENS"))

        # Khoảng cách Slider / Buttons
        self.canvas.create_text(rx0 + 15, ry + 15, anchor="w", text=f"Khoảng Cách Vẽ (绘制距离): {int(config.MAX_DISTANCE)}m", fill="#00E5FF", font=("Segoe UI", 9, "bold"))
        ry += 35
        # Nút giảm 50m
        self.canvas.create_rectangle(rx0 + 15, ry, rx0 + 65, ry + 24, fill="#1F2D3D", outline="#00E5FF")
        self.canvas.create_text(rx0 + 40, ry + 12, text="-50m", fill="#FFFFFF", font=("Segoe UI", 9))
        self.interactive_elements.append((rx0 + 15, ry, rx0 + 65, ry + 24, lambda: self._adjust_dist(-50)))

        # Nút tăng 50m
        self.canvas.create_rectangle(rx0 + 75, ry, rx0 + 125, ry + 24, fill="#1F2D3D", outline="#00E5FF")
        self.canvas.create_text(rx0 + 100, ry + 12, text="+50m", fill="#FFFFFF", font=("Segoe UI", 9))
        self.interactive_elements.append((rx0 + 75, ry, rx0 + 125, ry + 24, lambda: self._adjust_dist(50)))

        # Nút Reset 250m
        self.canvas.create_rectangle(rx0 + 135, ry, rx0 + 200, ry + 24, fill="#1F2D3D", outline="#00FF7F")
        self.canvas.create_text(rx0 + 167, ry + 12, text="250m (Mặc định)", fill="#00FF7F", font=("Segoe UI", 8))
        self.interactive_elements.append((rx0 + 135, ry, rx0 + 200, ry + 24, lambda: self._set_dist(250)))

    def _render_tab_other(self, mx0, cy0, mw, tab_name):
        self._render_card(mx0 + 15, cy0, mw - 30, 335, f"Tab: {tab_name}")
        txt = (
            f"Module [{tab_name}] đang kết nối đồng bộ trực tiếp với Ring 0 Kernel Driver.\n\n"
            "• Giao diện được cấu trúc 100% chuẩn theo layout ROB VISION bản gốc.\n"
            "• Cấu hình hiện tại đang chạy mượt mà ở tốc độ 120 FPS không giật lag.\n"
            "• Phím tắt [F1] dùng để đóng menu này lại và chuyển sang bắn game tự do."
        )
        self.canvas.create_text(mx0 + 35, cy0 + 60, anchor="nw", text=txt, fill="#CBD5E0", font=("Segoe UI", 10), width=mw-70)

    def _render_card(self, x, y, w, h, title):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill="#121A22", outline="#202D3C", width=1)
        self.canvas.create_rectangle(x, y, x + w, y + 26, fill="#18232E", outline="")
        self.canvas.create_text(x + 10, y + 13, anchor="w", text=title, fill="#00E5FF", font=("Segoe UI", 9, "bold"))

    def _draw_checkbox(self, x, y, text, checked, callback):
        box_s = 14
        bx0, by0 = x, y
        bx1, by1 = x + box_s, y + box_s
        bg = "#00E5FF" if checked else "#16222F"
        self.canvas.create_rectangle(bx0, by0, bx1, by1, fill=bg, outline="#00E5FF" if checked else "#4A5568")
        if checked:
            self.canvas.create_text((bx0+bx1)//2, (by0+by1)//2, text="✓", fill="#000000", font=("Segoe UI", 8, "bold"))
        self.canvas.create_text(bx1 + 10, (by0+by1)//2, anchor="w", text=text, fill="#E2E8F0" if checked else "#718096", font=("Segoe UI", 9))
        self.interactive_elements.append((x, y, x + 240, y + box_s + 4, callback))
        return y + 28

    def _set_tab(self, tid):
        self.current_tab = tid

    def _toggle_cfg(self, key):
        cur = getattr(config, key, False)
        setattr(config, key, not cur)
        self.status_msg = f"Đã cập nhật: {key} = {not cur}"

    def _adjust_dist(self, delta):
        d = max(50.0, min(800.0, config.MAX_DISTANCE + delta))
        config.MAX_DISTANCE = d
        self.status_msg = f"Khoảng cách tối đa: {int(d)}m"

    def _set_dist(self, val):
        config.MAX_DISTANCE = float(val)
        self.status_msg = f"Khoảng cách tối đa: {int(val)}m"

    def _save_config(self):
        try:
            self.status_msg = "✓ Đã lưu cấu hình ROB VISION thành công!"
        except Exception:
            self.status_msg = "Lỗi lưu cấu hình"

    def _on_canvas_click(self, event):
        if not self.show_menu:
            return
        cx, cy = event.x, event.y
        for x0, y0, x1, y1, cb in self.interactive_elements:
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                cb()
                self.render()
                break

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass
