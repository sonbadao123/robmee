"""
SCREEN CAPTURE ENGINE (FULL-SCREEN & DYNAMIC ROI DUAL-MODE)
Ultra-fast low-latency screen frame grabbing for ROB RUN with crash shields.
"""

import numpy as np
import mss
import win32gui
import win32ui
import win32con
import config

class ScreenCapture:
    """
    High-performance screen frame capture supporting both Full-Screen (1920x1080)
    and Focused ROI mode with graceful fallback.
    """

    def __init__(self):
        self.mode = config.SCAN_MODE
        if self.mode == "FULL":
            self.left = 0
            self.top = 0
            self.width = config.SCREEN_WIDTH
            self.height = config.SCREEN_HEIGHT
        else:
            self.left = config.ROI_LEFT
            self.top = config.ROI_TOP
            self.width = config.ROI_SIZE
            self.height = config.ROI_SIZE

        try:
            self.sct = mss.mss()
        except Exception:
            self.sct = None

        self.roi = {
            "top": self.top,
            "left": self.left,
            "width": self.width,
            "height": self.height
        }
        self.last_valid_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def grab_frame(self):
        """
        Grabs the current screen frame.
        Guaranteed to never raise an unhandled exception.
        """
        if self.sct:
            try:
                raw = self.sct.grab(self.roi)
                frame = np.array(raw, dtype=np.uint8)[:, :, :3]
                self.last_valid_frame = frame
                return frame, self.left, self.top
            except Exception:
                pass

        try:
            frame = self._grab_gdi()
            if frame is not None:
                self.last_valid_frame = frame
                return frame, self.left, self.top
        except Exception:
            pass

        return self.last_valid_frame, self.left, self.top

    def _grab_gdi(self):
        hdesktop = win32gui.GetDesktopWindow()
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        if not desktop_dc:
            return None

        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(img_dc, self.width, self.height)
        mem_dc.SelectObject(bmp)

        mem_dc.BitBlt(
            (0, 0),
            (self.width, self.height),
            img_dc,
            (self.left, self.top),
            win32con.SRCCOPY
        )

        signed_ints_array = bmp.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype=np.uint8)
        img.shape = (self.height, self.width, 4)

        win32gui.DeleteObject(bmp.GetHandle())
        mem_dc.DeleteDC()
        img_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)

        return img[:, :, :3]

    def close(self):
        if self.sct:
            try:
                self.sct.close()
            except Exception:
                pass
