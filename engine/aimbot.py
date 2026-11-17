"""
EVASIVE AIMBOT CONTROLLER
Precision targeting with strict teammate exclusion and anti-cheat evasion.
"""

import win32api
import config
from engine.anti_cheat import AntiCheatEvasion

class AimbotController:
    """
    Handles target selection, locking, and humanized mouse dispatch.
    """

    def __init__(self):
        self.enabled = config.AIM_ENABLED
        self.fov = config.AIM_FOV
        self.smooth = config.AIM_SMOOTH
        self.is_active = False

    def is_aim_key_pressed(self):
        """Checks if the configured aim trigger key (e.g. Right Mouse Button) is held down."""
        # GetAsyncKeyState returns negative if key is pressed down
        return win32api.GetAsyncKeyState(config.AIM_KEY) & 0x8000 != 0

    def select_best_target(self, targets):
        """
        Filters targets and picks the optimal hostile target:
        - Teammates are STRICTLY ignored (never targeted).
        - Must be within AIM_FOV radius.
        - Picks target closest to crosshair.
        """
        valid_hostiles = [
            t for t in targets
            if t.is_hostile and t.dist_to_crosshair <= self.fov
        ]

        if not valid_hostiles:
            return None

        # Sort by distance to crosshair (closest first)
        valid_hostiles.sort(key=lambda t: t.dist_to_crosshair)
        return valid_hostiles[0]

    def update(self, targets):
        """
        Core aimbot tick called every frame.
        """
        if not self.enabled:
            self.is_active = False
            return

        # Only activate when aim key is pressed
        if not self.is_aim_key_pressed():
            self.is_active = False
            return

        best_target = self.select_best_target(targets)
        if best_target is None:
            self.is_active = False
            return

        self.is_active = True

        # Calculate delta from center to target aim point
        delta_x = best_target.aim_x - config.CENTER_X
        delta_y = best_target.aim_y - config.CENTER_Y

        # Apply smoothing factor
        step_x = delta_x * self.smooth
        step_y = delta_y * self.smooth

        if config.BEZIER_CURVE_ENABLED:
            trajectory = AntiCheatEvasion.calculate_bezier_trajectory(
                start_x=0,
                start_y=0,
                target_x=step_x,
                target_y=step_y,
                steps=3
            )
            for (bx, by) in trajectory:
                AntiCheatEvasion.move_mouse_relative(bx, by)
                AntiCheatEvasion.human_sleep(config.AIM_MIN_DELAY_MS, config.AIM_MAX_DELAY_MS)
        else:
            AntiCheatEvasion.move_mouse_relative(int(step_x), int(step_y))
            AntiCheatEvasion.human_sleep(config.AIM_MIN_DELAY_MS, config.AIM_MAX_DELAY_MS)
