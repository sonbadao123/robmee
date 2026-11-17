"""
ROB RUN - PLAYER ENTITY & TARGET MODEL
Represents an entity/target in ROB RUN with world positions and 2D projected coordinates.
"""

import math
import config

class PlayerTarget:
    """Represents a humanoid target in ROB RUN with 3D and 2D properties."""
    def __init__(self, x, y, w, h, role, is_hostile, aim_point, dist_to_crosshair=None, distance_m=0.0, name="Player", health=100.0, is_local=False):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.role = role                    # 'TEAMMATE', 'POLICE', 'ROBBER', 'CITIZEN'
        self.is_hostile = is_hostile        # True if POLICE or ROBBER; False if TEAMMATE/CITIZEN
        self.aim_x = int(aim_point[0])
        self.aim_y = int(aim_point[1])
        self.distance_m = float(distance_m) # Khoảng cách thực tế (mét)
        self.name = str(name)               # Tên người chơi
        self.health = float(health)         # Lượng máu (0-100)
        self.is_local = bool(is_local)      # True nếu là nhân vật của chính mình
        if dist_to_crosshair is None:
            self.dist_to_crosshair = math.hypot(self.aim_x - config.CENTER_X, self.aim_y - config.CENTER_Y)
        else:
            self.dist_to_crosshair = float(dist_to_crosshair)
