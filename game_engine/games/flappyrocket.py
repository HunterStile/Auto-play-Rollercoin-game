"""
Flappy Rocket Game Bot v2.

Flappy Bird clone: press space/click to fly up, navigate through obstacles.

v2 improvements:
- Tracks the actual rocket position (searches for bright pixel clusters)
- Scans ahead of the rocket, not from region center
- Stricter obstacle detection to reduce false positives
- Smart jump: only when obstacle is in rocket's path
- Adaptive cooldown
"""

import pyautogui
import time
from typing import Tuple, Optional, List

from game_engine.base import BaseGame
from game_engine.registry import register_game

# End-screen detection color (RollerCoin cyan)
END_SCREEN_COLOR = (3, 225, 228)

# Default scan region (game area)
DEFAULT_REGION = (400, 100, 800, 700)

# Obstacle colors - pipes/asteroids in Flappy Rocket
OBSTACLE_COLORS = [
    (50, 180, 50),    # green pipe
    (30, 150, 30),    # dark green
    (60, 190, 60),    # lighter green
    (80, 170, 40),    # green variant
    (100, 100, 100),  # grey asteroid
    (80, 80, 80),     # dark grey
    (60, 60, 60),     # darker grey
    (140, 140, 140),  # light grey
]

# Rocket color range (bright white/silver)
ROCKET_COLORS = [
    (220, 220, 240),  # silver/white
    (200, 200, 220),  # slightly darker
    (180, 200, 230),  # blueish silver
]

# Background (space = very dark)
BACKGROUND_MAX_BRIGHTNESS = 80  # R+G+B max for background

COLOR_TOLERANCE = 25
OBSTACLE_TOLERANCE = 30


@register_game
class FlappyRocketBot(BaseGame):
    game_id = 'flappyrocket'
    display_name = 'Flappy Rocket'
    description = 'Flappy Bird clone: detect obstacles and jump through gaps'

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', DEFAULT_REGION) if config else DEFAULT_REGION
        self.game_duration = 65  # seconds
        self.jump_cooldown = 0.35  # seconds between jumps
        self.scan_ahead_min = 60   # min pixels ahead of rocket to scan
        self.scan_ahead_max = 110  # max pixels ahead
        self._rocket_history = []  # for position smoothing

    # ── Color utilities ───────────────────────────────────────────────

    def _color_match(self, target: Tuple[int, int, int], actual: Tuple[int, int, int],
                     tolerance: int = COLOR_TOLERANCE) -> bool:
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _is_background(self, r: int, g: int, b: int) -> bool:
        """Check if pixel is background (dark space)."""
        return (r + g + b) <= BACKGROUND_MAX_BRIGHTNESS

    def _is_rocket_color(self, r: int, g: int, b: int) -> bool:
        """Check if pixel looks like the rocket (bright white/silver)."""
        for color in ROCKET_COLORS:
            if self._color_match(color, (r, g, b), tolerance=30):
                return True
        # Also accept any very bright pixel in left area
        if r > 190 and g > 190 and b > 180:
            return True
        return False

    def _is_obstacle(self, r: int, g: int, b: int) -> bool:
        """Strict obstacle check - only known obstacle colors."""
        # Skip background
        if self._is_background(r, g, b):
            return False
        # Skip very bright (rocket, coins, UI)
        if r > 200 and g > 200 and b > 200:
            return False
        # Match known obstacle colors
        for color in OBSTACLE_COLORS:
            if self._color_match(color, (r, g, b), tolerance=OBSTACLE_TOLERANCE):
                return True
        return False

    # ── Rocket tracking ───────────────────────────────────────────────

    def _find_rocket(self) -> Optional[Tuple[int, int]]:
        """
        Find the rocket position by scanning for bright pixel clusters
        in the left-center portion of the game area.
        Returns (x, y) or None if not found.
        """
        rx, ry, rw, rh = self.region

        # Scan left portion of game area (rocket is on the left side)
        scan_left = rx + 20
        scan_top = ry + 30
        scan_width = rw // 3  # left third
        scan_height = rh - 60

        try:
            pic = pyautogui.screenshot(region=(scan_left, scan_top, scan_width, scan_height))
        except Exception:
            return None

        w, h = pic.size
        rocket_pixels = []

        # Coarse scan for bright pixels
        for x in range(0, w, 6):
            for y in range(0, h, 6):
                try:
                    r, g, b = pic.getpixel((x, y))
                    if self._is_rocket_color(r, g, b):
                        rocket_pixels.append((scan_left + x, scan_top + y))
                except Exception:
                    pass

        if not rocket_pixels:
            return None

        # Find the cluster center (rocket should be a tight cluster)
        avg_x = sum(p[0] for p in rocket_pixels) / len(rocket_pixels)
        avg_y = sum(p[1] for p in rocket_pixels) / len(rocket_pixels)

        # Smooth with history
        self._rocket_history.append((avg_x, avg_y))
        if len(self._rocket_history) > 5:
            self._rocket_history.pop(0)

        smooth_x = sum(p[0] for p in self._rocket_history) / len(self._rocket_history)
        smooth_y = sum(p[1] for p in self._rocket_history) / len(self._rocket_history)

        return (int(smooth_x), int(smooth_y))

    # ── Obstacle scanning ─────────────────────────────────────────────

    def _scan_column(self, scan_x: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Scan a vertical column at scan_x for obstacles.
        Returns: (has_obstacle, gap_center_y, obstacle_top_y)
        """
        rx, ry, rw, rh = self.region
        scan_y_start = ry + 15
        scan_height = rh - 30
        col_width = 8

        try:
            pic = pyautogui.screenshot(region=(scan_x - col_width // 2, scan_y_start,
                                                col_width, scan_height))
        except Exception:
            return (False, None, None)

        w, h = pic.size
        rows = []

        for y in range(0, h, 4):
            obs_count = 0
            total = 0
            for x in range(0, w, 2):
                try:
                    r, g, b = pic.getpixel((x, y))
                    total += 1
                    if self._is_obstacle(r, g, b):
                        obs_count += 1
                except Exception:
                    pass
            rows.append({
                'y': scan_y_start + y,
                'is_obs': obs_count >= max(2, total // 2),  # majority
            })

        # Find obstacle segments and gaps
        obstacles = []  # list of (top_y, bottom_y)
        in_obs = False
        obs_start = 0

        for row in rows:
            if row['is_obs'] and not in_obs:
                in_obs = True
                obs_start = row['y']
            elif not row['is_obs'] and in_obs:
                obstacles.append((obs_start, row['y']))
                in_obs = False

        if in_obs:
            obstacles.append((obs_start, rows[-1]['y']))

        if not obstacles:
            return (False, None, None)

        # Find gaps between obstacles
        gaps = []
        for i in range(len(obstacles) - 1):
            gap_top = obstacles[i][1]
            gap_bottom = obstacles[i + 1][0]
            gap_size = gap_bottom - gap_top
            if gap_size > 30:  # significant gap
                gap_center = (gap_top + gap_bottom) // 2
                gaps.append((gap_center, gap_size))

        # Also check gap above first obstacle and below last
        if obstacles[0][0] - scan_y_start > 30:
            gaps.append(((scan_y_start + obstacles[0][0]) // 2,
                        obstacles[0][0] - scan_y_start))
        if (scan_y_start + scan_height) - obstacles[-1][1] > 30:
            gaps.append(((obstacles[-1][1] + scan_y_start + scan_height) // 2,
                        (scan_y_start + scan_height) - obstacles[-1][1]))

        if gaps:
            # Return largest gap
            best_gap = max(gaps, key=lambda g: g[1])
            return (True, best_gap[0], obstacles[0][0])

        return (True, None, obstacles[0][0])

    # ── Jump decision ─────────────────────────────────────────────────

    def _should_jump(self, rocket_y: int, gap_center: Optional[int],
                     obstacle_top: Optional[int]) -> bool:
        """
        Decide whether to jump based on rocket position relative to obstacles.
        """
        if gap_center is not None:
            # There's a gap - jump if rocket is below the gap center
            # (rocket is falling, needs to go up to reach the gap)
            margin = 30  # pixels of tolerance
            if rocket_y > gap_center - margin:
                return True

        if obstacle_top is not None:
            # No clear gap but obstacles present - jump if obstacle is close
            # and rocket is near the top of the obstacle
            if rocket_y > obstacle_top - 20:
                return True

        return False

    # ── End screen detection ──────────────────────────────────────────

    def _is_end_screen(self) -> bool:
        """Check if the game has ended (cyan end screen)."""
        rx, ry, rw, rh = self.region
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 60),
            (rx + rw // 4, ry + rh - 40),
            (rx + 3 * rw // 4, ry + rh - 40),
        ]
        matches = 0
        for px, py in check_points:
            try:
                r, g, b = pyautogui.pixel(px, py)
                if (abs(r - END_SCREEN_COLOR[0]) <= 5 and
                    abs(g - END_SCREEN_COLOR[1]) <= 5 and
                    abs(b - END_SCREEN_COLOR[2]) <= 5):
                    matches += 1
            except Exception:
                pass
        return matches >= 2

    # ── Main play loop ────────────────────────────────────────────────

    def play(self) -> bool:
        """Play one round of Flappy Rocket."""
        print("START Flappy Rocket v2")
        start_time = time.time()
        last_jump = 0
        self._rocket_history = []
        no_rocket_count = 0

        try:
            # Initial jump to get started
            pyautogui.press('space')
            time.sleep(0.5)

            while time.time() - start_time < self.game_duration:
                if self._is_end_screen():
                    print("  End screen detected - game complete!")
                    break

                now = time.time()

                # Find rocket
                rocket_pos = self._find_rocket()
                if rocket_pos is None:
                    no_rocket_count += 1
                    if no_rocket_count > 30:  # ~3 seconds without rocket
                        print("  Rocket not found for too long - ending")
                        break
                    time.sleep(0.1)
                    continue
                no_rocket_count = 0

                rocket_x, rocket_y = rocket_pos

                # Determine scan position (ahead of rocket)
                scan_x = rocket_x + self.scan_ahead_min

                # If rocket is visible and we have recent position,
                # scan even further ahead if we just jumped
                if now - last_jump < 0.5:
                    scan_x = rocket_x + self.scan_ahead_max

                rx, ry, rw, rh = self.region
                if scan_x > rx + rw - 20:
                    scan_x = rx + rw - 30

                # Scan
                has_obs, gap_center, obstacle_top = self._scan_column(scan_x)

                # Decide
                if has_obs and (now - last_jump) > self.jump_cooldown:
                    if self._should_jump(rocket_y, gap_center, obstacle_top):
                        pyautogui.press('space')
                        last_jump = now
                        gap_str = f"gap@{gap_center}" if gap_center else "no-gap"
                        print(f"  JUMP! rocket_y={rocket_y} {gap_str} obs_top={obstacle_top}")

                # Adaptive sleep: faster when obstacles are close
                if has_obs:
                    time.sleep(0.04)
                else:
                    time.sleep(0.08)

            print("END Flappy Rocket v2")
            return True

        except Exception as e:
            print(f"  Error in Flappy Rocket: {e}")
            return False
