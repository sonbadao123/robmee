"""
ANTI-CHEAT EVASION & INPUT HUMANIZATION MODULE
Bypasses EasyAntiCheat (EAC EOS) heuristic mouse analysis and process monitors.
"""

import math
import random
import time
import ctypes
from ctypes import wintypes

# Win32 SendInput constants
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000

user32 = ctypes.windll.user32

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION)
    ]

class AntiCheatEvasion:
    """
    EAC EOS Evasion & Stealth Input Dispatcher:
    - Zero Memory Attachment: Never uses OpenProcess with VM_READ/VM_WRITE.
    - Non-Linear Bezier Trajectory: Bypasses server-side and client-side aim heuristic trackers.
    - Variable Micro-Delays: Prevents perfectly uniform packet frequency detection.
    """

    @staticmethod
    def calculate_bezier_trajectory(start_x, start_y, target_x, target_y, steps=6):
        """
        Generates a cubic Bezier curve simulating natural human wrist and finger acceleration.
        P0 = Start (Current crosshair)
        P1 = Random control point 1 (arc curvature)
        P2 = Random control point 2 (corrective deceleration)
        P3 = Target
        """
        dx = target_x - start_x
        dy = target_y - start_y

        dist = math.hypot(dx, dy)
        if dist < 2:
            return [(target_x, target_y)]

        # Control point deviation scaled by distance
        spread = min(dist * 0.25, 20.0)
        p0 = (start_x, start_y)
        p1 = (
            start_x + dx * 0.33 + random.uniform(-spread, spread),
            start_y + dy * 0.33 + random.uniform(-spread, spread)
        )
        p2 = (
            start_x + dx * 0.66 + random.uniform(-spread * 0.5, spread * 0.5),
            start_y + dy * 0.66 + random.uniform(-spread * 0.5, spread * 0.5)
        )
        p3 = (target_x, target_y)

        trajectory = []
        cur_x, cur_y = 0, 0
        for i in range(1, steps + 1):
            t = i / steps
            # Công thức Bezier bậc 3: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
            bx = ((1 - t) ** 3) * p0[0] + 3 * ((1 - t) ** 2) * t * p1[0] + 3 * (1 - t) * (t ** 2) * p2[0] + (t ** 3) * p3[0]
            by = ((1 - t) ** 3) * p0[1] + 3 * ((1 - t) ** 2) * t * p1[1] + 3 * (1 - t) * (t ** 2) * p2[1] + (t ** 3) * p3[1]
            
            # Tính toán delta tương đối từng bước (incremental delta) để không bị nhân đôi khoảng cách
            if i == steps:
                step_dx = int(round(target_x)) - cur_x
                step_dy = int(round(target_y)) - cur_y
            else:
                step_dx = int(round(bx)) - cur_x
                step_dy = int(round(by)) - cur_y
            
            cur_x += step_dx
            cur_y += step_dy
            trajectory.append((step_dx, step_dy))

        return trajectory

    @staticmethod
    def move_mouse_relative(dx, dy):
        """
        Dispatches relative mouse movement with low-level Win32 API.
        """
        if dx == 0 and dy == 0:
            return

        # Subtle 1-pixel micro-jitter occasionally to defeat machine-detection vectors
        if random.random() < 0.15:
            dx += random.choice([-1, 1])
            dy += random.choice([-1, 1])

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi = MOUSEINPUT(
            dx=int(dx),
            dy=int(dy),
            mouseData=0,
            dwFlags=MOUSEEVENTF_MOVE,
            time=0,
            dwExtraInfo=None
        )
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    @staticmethod
    def human_sleep(min_ms=1, max_ms=4):
        """
        Random sleep to avoid constant frequency timing anomalies.
        """
        delay = random.uniform(min_ms, max_ms) / 1000.0
        time.sleep(delay)
