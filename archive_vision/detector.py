"""
PLAYER DETECTION & TEAM FILTERING ENGINE (MULTI-SCALE DISTANCE ENHANCED)
Distinguishes Teammates (DO NOT AIM) from Cops and Robbers (VALID TARGETS).
Supports distant, medium, and close range humanoid targets across entire screen.
"""

import cv2
import numpy as np
import math
import config

class PlayerTarget:
    """Represents a detected humanoid entity in ROB RUN."""
    def __init__(self, x, y, w, h, role, is_hostile, aim_point, dist_to_crosshair):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.role = role                    # 'TEAMMATE', 'POLICE', 'ROBBER'
        self.is_hostile = is_hostile        # True if POLICE or ROBBER; False if TEAMMATE
        self.aim_x = aim_point[0]
        self.aim_y = aim_point[1]
        self.dist_to_crosshair = dist_to_crosshair

class TargetDetector:
    """
    High-performance Computer Vision Detection & Role Classifier:
    - Multi-scale contour and morphology processing for near and far entities.
    - Scalable Teammate overhead HUD marker identification in HSV space.
    - Scalable Police vs Robber uniform hue analysis.
    - Strict friendly player immunity (Zero aimbot lock on allies).
    """

    def __init__(self):
        # Friendly Green HUD Marker Thresholds (HSV)
        self.lower_green = np.array([config.TEAM_HUE_MIN, config.TEAM_SAT_MIN, config.TEAM_VAL_MIN], dtype=np.uint8)
        self.upper_green = np.array([config.TEAM_HUE_MAX, 255, 255], dtype=np.uint8)

        # Police Tactical/Navy Uniform Thresholds (HSV)
        self.lower_cop = np.array([config.COP_HUE_MIN, config.COP_SAT_MIN, config.COP_VAL_MIN], dtype=np.uint8)
        self.upper_cop = np.array([config.COP_HUE_MAX, 255, 255], dtype=np.uint8)

        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    def detect_entities(self, frame_bgr, origin_x=0, origin_y=0):
        """
        Processes frame and returns list of PlayerTarget objects with absolute screen coordinates.
        Supports both close combat and long-distance engagement.
        """
        targets = []
        if frame_bgr is None or frame_bgr.size == 0:
            return targets

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh1 = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 13, 3
        )
        _, thresh2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        combined = cv2.bitwise_or(thresh1, thresh2)

        morphed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, self.morph_kernel, iterations=2)
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = config.MIN_FAR_AREA if config.FAR_TARGET_DETECTION else 300
        min_h = config.MIN_FAR_HEIGHT if config.FAR_TARGET_DETECTION else 30

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < 55000:
                rx, ry, rw, rh = cv2.boundingRect(cnt)
                aspect_ratio = rh / float(max(1, rw))

                # Multi-scale humanoid aspect ratio validation:
                valid_humanoid = False
                if rh >= 45:
                    # Gần (Close range)
                    valid_humanoid = (1.4 <= aspect_ratio <= 4.2) and rw >= 12
                elif 25 <= rh < 45:
                    # Tầm trung (Medium range)
                    valid_humanoid = (1.2 <= aspect_ratio <= 4.8) and rw >= 7
                elif min_h <= rh < 25 and config.FAR_TARGET_DETECTION:
                    # Kẻ địch ở xa (Far distance target)
                    valid_humanoid = (1.1 <= aspect_ratio <= 5.5) and rw >= 4

                if valid_humanoid:
                    abs_x = origin_x + rx
                    abs_y = origin_y + ry

                    # Xác định vai trò (Role Classification)
                    is_teammate = self._check_teammate_marker(hsv, rx, ry, rw, rh)

                    if is_teammate:
                        role = "TEAMMATE"
                        is_hostile = False
                    else:
                        is_cop = self._check_police_uniform(hsv, rx, ry, rw, rh)
                        if is_cop:
                            role = "POLICE"
                            is_hostile = config.TARGET_POLICE
                        else:
                            role = "ROBBER"
                            is_hostile = config.TARGET_ROBBERS

                    # Tọa độ ngắm đầu / cổ (Head Aim Point)
                    head_x = abs_x + (rw // 2)
                    head_y = abs_y + int(rh * config.AIM_BONE_OFFSET)

                    dist = math.hypot(head_x - config.CENTER_X, head_y - config.CENTER_Y)

                    target = PlayerTarget(
                        x=abs_x,
                        y=abs_y,
                        w=rw,
                        h=rh,
                        role=role,
                        is_hostile=is_hostile,
                        aim_point=(head_x, head_y),
                        dist_to_crosshair=dist
                    )
                    targets.append(target)

        return targets

    def _check_teammate_marker(self, hsv, rx, ry, rw, rh):
        """
        Quét vùng đỉnh đầu để tìm Marker xanh lá của Đồng đội (thích ứng theo cự ly).
        """
        overhead_margin = 35 if rh >= 40 else max(10, int(rh * 0.7))
        marker_y1 = max(0, ry - overhead_margin)
        marker_y2 = max(0, ry)
        marker_x1 = max(0, rx - 8)
        marker_x2 = min(hsv.shape[1], rx + rw + 8)

        if marker_y2 <= marker_y1 or marker_x2 <= marker_x1:
            return False

        overhead_roi = hsv[marker_y1:marker_y2, marker_x1:marker_x2]
        green_mask = cv2.inRange(overhead_roi, self.lower_green, self.upper_green)
        green_pixels = cv2.countNonZero(green_mask)

        # Ngưỡng pixel xanh: mục tiêu gần cần >5 pixel, mục tiêu xa chỉ cần >=2 pixel
        required_green = 5 if rh >= 40 else 2
        return green_pixels >= required_green

    def _check_police_uniform(self, hsv, rx, ry, rw, rh):
        """
        Quét thân mình để tìm màu xanh navy đặc trưng của Cảnh sát (SWAT).
        """
        torso_y1 = ry + int(rh * 0.15)
        torso_y2 = ry + int(rh * 0.75)
        torso_x1 = rx
        torso_x2 = rx + rw

        torso_roi = hsv[torso_y1:torso_y2, torso_x1:torso_x2]
        if torso_roi.size == 0:
            return False

        cop_mask = cv2.inRange(torso_roi, self.lower_cop, self.upper_cop)
        cop_pixels = cv2.countNonZero(cop_mask)

        total_torso_pixels = (torso_y2 - torso_y1) * rw
        if total_torso_pixels > 0:
            ratio = cop_pixels / float(total_torso_pixels)
            return ratio > 0.08
        return False
