"""
ROB RUN - PLAYER ENTITY & TARGET MODEL
Represents an entity/target in ROB RUN with world positions and 2D projected coordinates.
"""

import math
import config

class PlayerTarget:
    """Represents a humanoid target in ROB RUN."""
    def __init__(self, x, y, w, h, role, is_hostile, aim_point, dist_to_crosshair=None):
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.role = role                    # 'TEAMMATE', 'POLICE', 'ROBBER'
        self.is_hostile = is_hostile        # True if POLICE or ROBBER; False if TEAMMATE
        self.aim_x = int(aim_point[0])
        self.aim_y = int(aim_point[1])
        if dist_to_crosshair is None:
            self.dist_to_crosshair = math.hypot(self.aim_x - config.CENTER_X, self.aim_y - config.CENTER_Y)
        else:
            self.dist_to_crosshair = float(dist_to_crosshair)
