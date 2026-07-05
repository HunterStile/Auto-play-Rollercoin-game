"""
Token Blaster Game Bot.

Space Invaders-style shooter: ship follows cursor, click to shoot enemies.
Uses pixel color scanning to detect enemies and auto-aim.
"""

import pyautogui
import time
from typing import Tuple, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

# Enemy colors: (R, G, B) signatures
ENEMY_COLORS = {
    'red':   (220, 50, 50),
    'green': (50, 200, 50),
    'white': (240, 240, 240),
}

# End-screen detection color
END_SCREEN_COLOR = (3, 225, 228)

# Default scan region - will be calibrated
DEFAULT_REGION = (200, 150, 900, 600)

# Projectile detection color (bright yellow/white)
PROJECTILE_COLOR = (255, 255, 100)

COLOR_TOLERANCE = 25


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Space shooter: auto-aim and shoot enemies via color detection'

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', DEFAULT_REGION) if config else DEFAULT_REGION
        self.game_duration = 65  # seconds
        self.shoot_cooldown = 0.15  # seconds between shots

    def _in_region(self, x: int, y: int) -> bool:
        """Check if coordinates are within the game region."""
        rx, ry, rw, rh = self.region
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def _color_match(self, target: Tuple[int, int, int], actual: Tuple[int, int, int],
                     tolerance: int = COLOR_TOLERANCE) -> bool:
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _find_enemies(self) -> list:
        """Scan the game region and return list of enemy positions."""
        enemies = []
        rx, ry, rw, rh = self.region

        pic = pyautogui.screenshot(region=self.region)

        for x in range(0, rw, 10):  # step 10 for speed
            for y in range(0, rh, 10):
                r, g, b = pic.getpixel((x, y))

                # Check each enemy color
                for enemy_type, color in ENEMY_COLORS.items():
                    if self._color_match(color, (r, g, b)):
                        enemies.append((rx + x, ry + y))
                        break

        return enemies

    def _find_projectile(self) -> Optional[Tuple[int, int]]:
        """Scan near the ship for incoming projectiles."""
        ship_x, ship_y = pyautogui.position()
        rx, ry, rw, rh = self.region

        # Scan a small area above the ship
        scan_y_start = max(ry, ship_y - 100)
        scan_y_end = min(ry + rh, ship_y)
        scan_x_start = max(rx, ship_x - 80)
        scan_x_end = min(rx + rw, ship_x + 80)

        if scan_y_end <= scan_y_start or scan_x_end <= scan_x_start:
            return None

        region = (scan_x_start, scan_y_start,
                  scan_x_end - scan_x_start, scan_y_end - scan_y_start)

        try:
            pic = pyautogui.screenshot(region=region)
            for x in range(0, pic.size[0], 5):
                for y in range(0, pic.size[1], 5):
                    r, g, b = pic.getpixel((x, y))
                    if self._color_match(PROJECTILE_COLOR, (r, g, b), tolerance=40):
                        return (scan_x_start + x, scan_y_start + y)
        except Exception:
            pass

        return None

    def _is_end_screen(self) -> bool:
        """Check if the game has ended."""
        rx, ry, rw, rh = self.region
        # Check a few spots near the center
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 50),
            (rx + rw // 2, ry + 50),
        ]
        for px, py in check_points:
            r, g, b = pyautogui.pixel(px, py)
            if self._color_match(END_SCREEN_COLOR, (r, g, b), tolerance=5):
                return True
        return False

    def play(self) -> bool:
        """Play one round of Token Blaster."""
        print("START Token Blaster")
        start_time = time.time()
        last_shot = 0

        try:
            # Hold mouse button to activate ship following
            rx, ry, rw, rh = self.region
            center_x, center_y = rx + rw // 2, ry + rh // 2
            pyautogui.moveTo(center_x, center_y)
            pyautogui.mouseDown()

            while time.time() - start_time < self.game_duration:
                # Check end screen
                if self._is_end_screen():
                    print("End screen detected - game complete!")
                    break

                # Find enemies
                enemies = self._find_enemies()

                # Find projectiles
                projectile = self._find_projectile()

                if projectile:
                    # Dodge! Move away from projectile
                    px, py = projectile
                    ship_x, ship_y = pyautogui.position()
                    # Move horizontally away
                    dodge_x = ship_x + (80 if px < ship_x else -80)
                    dodge_x = max(rx, min(rx + rw, dodge_x))
                    pyautogui.moveTo(dodge_x, ship_y, duration=0.1)
                    continue

                if enemies:
                    # Aim at nearest enemy (highest y = closest to bottom = priority)
                    target = max(enemies, key=lambda e: e[1])

                    # Shoot if cooldown passed
                    now = time.time()
                    if now - last_shot > self.shoot_cooldown:
                        pyautogui.click(target[0], target[1])
                        last_shot = now
                else:
                    # No enemies visible, sweep
                    sweep_x = rx + ((time.time() * 100) % rw)
                    pyautogui.moveTo(sweep_x, ry + rh * 0.7)

                time.sleep(0.05)

            pyautogui.mouseUp()
            print("END Token Blaster")
            return True

        except Exception as e:
            print(f"Error in Token Blaster: {e}")
            try:
                pyautogui.mouseUp()
            except Exception:
                pass
            return False
