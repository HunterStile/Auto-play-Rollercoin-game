"""
Flappy Rocket Game Bot.

Flappy Bird clone: press space/click to fly up, navigate through obstacles.
Uses pixel scanning to detect obstacles ahead and time jumps.
"""

import pyautogui
import time
from typing import Tuple, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

# End-screen detection color
END_SCREEN_COLOR = (3, 225, 228)

# Default scan region (game area)
DEFAULT_REGION = (400, 100, 800, 700)

# Common obstacle colors on RollerCoin (green pipes / dark blocks)
OBSTACLE_COLORS = [
    (50, 180, 50),    # green
    (30, 150, 30),    # dark green
    (80, 80, 80),     # grey
    (40, 40, 40),     # dark grey
]

# Sky/background color (space = dark)
BACKGROUND_COLOR = (20, 20, 40)

COLOR_TOLERANCE = 30


@register_game
class FlappyRocketBot(BaseGame):
    game_id = 'flappyrocket'
    display_name = 'Flappy Rocket'
    description = 'Flappy Bird clone: detect obstacles and jump through gaps'

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', DEFAULT_REGION) if config else DEFAULT_REGION
        self.game_duration = 65  # seconds
        self.jump_cooldown = 0.3  # seconds between jumps
        self.scan_ahead_x = 120   # pixels ahead to scan
        self.scan_height = 30     # height of scan line

    def _color_match(self, target: Tuple[int, int, int], actual: Tuple[int, int, int],
                     tolerance: int = COLOR_TOLERANCE) -> bool:
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _is_obstacle(self, r: int, g: int, b: int) -> bool:
        """Check if a pixel is part of an obstacle."""
        # Very bright pixels are probably coins/items, not obstacles
        if r > 200 and g > 200 and b > 200:
            return False
        # Very dark background
        if self._color_match(BACKGROUND_COLOR, (r, g, b), tolerance=40):
            return False
        # Check against known obstacle colors
        for color in OBSTACLE_COLORS:
            if self._color_match(color, (r, g, b)):
                return True
        # Any non-background, non-bright pixel is likely an obstacle
        brightness = r + g + b
        if brightness > 100 and brightness < 520:
            return True
        return False

    def _scan_ahead(self, rocket_y: int) -> Optional[int]:
        """
        Scan ahead of the rocket for the nearest obstacle.
        Returns the Y position of the top edge of the gap, or None if clear.
        """
        rx, ry, rw, rh = self.region

        # Scan a vertical strip ahead of the rocket
        scan_x = rx + rw // 2 + self.scan_ahead_x
        if scan_x >= rx + rw - 10:
            scan_x = rx + rw - 30

        scan_y_start = ry + 20
        scan_y_end = ry + rh - 20

        if scan_y_end <= scan_y_start:
            return None

        region = (scan_x - 5, scan_y_start, 10, scan_y_end - scan_y_start)

        try:
            pic = pyautogui.screenshot(region=region)
            height = pic.size[1]

            # Scan from top to bottom looking for obstacle -> gap -> obstacle pattern
            in_obstacle = False
            last_obstacle_end = scan_y_start

            for y in range(0, height, 3):
                obstacle_count = 0
                for x in range(0, 10, 2):
                    try:
                        r, g, b = pic.getpixel((x, y))
                        if self._is_obstacle(r, g, b):
                            obstacle_count += 1
                    except Exception:
                        pass

                is_obs = obstacle_count >= 3  # majority of pixels are obstacle

                if is_obs and not in_obstacle:
                    in_obstacle = True
                elif not is_obs and in_obstacle:
                    # Found gap! This is the end of an obstacle
                    gap_top = scan_y_start + y
                    return gap_top
                    in_obstacle = False

                last_obstacle_end = scan_y_start + y if not is_obs else last_obstacle_end

        except Exception:
            pass

        return None

    def _is_end_screen(self) -> bool:
        """Check if the game has ended."""
        rx, ry, rw, rh = self.region
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 60),
        ]
        for px, py in check_points:
            try:
                r, g, b = pyautogui.pixel(px, py)
                if (abs(r - END_SCREEN_COLOR[0]) <= 5 and
                    abs(g - END_SCREEN_COLOR[1]) <= 5 and
                    abs(b - END_SCREEN_COLOR[2]) <= 5):
                    return True
            except Exception:
                pass
        return False

    def play(self) -> bool:
        """Play one round of Flappy Rocket."""
        print("START Flappy Rocket")
        start_time = time.time()
        last_jump = 0

        try:
            while time.time() - start_time < self.game_duration:
                if self._is_end_screen():
                    print("End screen detected - game complete!")
                    break

                # Estimate rocket Y position (center of game area)
                rx, ry, rw, rh = self.region
                rocket_y = ry + rh // 2

                # Scan ahead
                gap_top = self._scan_ahead(rocket_y)

                now = time.time()
                if gap_top is not None and (now - last_jump) > self.jump_cooldown:
                    # Obstacle detected ahead - jump!
                    pyautogui.press('space')
                    last_jump = now

                time.sleep(0.05)

            print("END Flappy Rocket")
            return True

        except Exception as e:
            print(f"Error in Flappy Rocket: {e}")
            return False
