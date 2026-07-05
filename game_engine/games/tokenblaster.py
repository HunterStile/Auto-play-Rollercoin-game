"""
Token Blaster Game Bot.

Space Invaders-style shooter: move ship with mouse, click to shoot enemies.
Uses pixel color scanning to detect enemies and auto-aim.
Press 'q' at any time to stop the bot.
"""

import pyautogui
import time
import keyboard
from typing import Tuple, List

from game_engine.base import BaseGame
from game_engine.registry import register_game

# Enemy colors: (R, G, B) signatures
ENEMY_COLORS = {
    'red':    (220, 50, 50),
    'green':  (50, 200, 50),
    'white':  (240, 240, 240),
    'yellow': (220, 220, 50),
    'pink':   (220, 50, 200),
}

# End-screen detection color
END_SCREEN_COLOR = (3, 225, 228)

COLOR_TOLERANCE = 30


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Space shooter: auto-aim and shoot enemies via color detection'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = 65  # seconds
        self.shoot_cooldown = 0.2  # seconds between shots
        self.dodge_direction = 1  # 1 = right, -1 = left

    def _color_match(self, target: Tuple[int, int, int], actual: Tuple[int, int, int],
                     tolerance: int = COLOR_TOLERANCE) -> bool:
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _find_enemies(self) -> List[Tuple[int, int]]:
        """Scan the screen for enemy positions and return them sorted by priority (closest to bottom)."""
        enemies = []
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size

        # Scan the upper 60% of the screen where enemies are
        scan_h = int(h * 0.6)
        step = 12  # scan step for speed

        for x in range(0, w, step):
            for y in range(0, scan_h, step):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    for enemy_type, color in ENEMY_COLORS.items():
                        if self._color_match(color, (r, g, b)):
                            enemies.append((x, y, enemy_type))
                            break
                except Exception:
                    pass

        # Remove duplicates (nearby pixels of same enemy)
        deduped = []
        for ex, ey, etype in enemies:
            if not any(abs(ex - dx) < 30 and abs(ey - dy) < 30 for dx, dy, _ in deduped):
                deduped.append((ex, ey, etype))

        # Sort: closest to bottom = highest priority
        deduped.sort(key=lambda e: -e[1])

        return deduped

    def _is_end_screen(self) -> bool:
        """Check if the game has ended."""
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        check_points = [
            (w // 2, h // 2),
            (w // 2, h - 100),
            (w // 3, h // 2),
            (2 * w // 3, h // 2),
        ]
        for px, py in check_points:
            try:
                r, g, b = screenshot.getpixel((px, py))
                if (abs(r - END_SCREEN_COLOR[0]) <= 5 and
                    abs(g - END_SCREEN_COLOR[1]) <= 5 and
                    abs(b - END_SCREEN_COLOR[2]) <= 5):
                    return True
            except Exception:
                pass
        return False

    def play(self) -> bool:
        """Play one round of Token Blaster."""
        print("START Token Blaster")
        print("  Press 'q' to stop the bot")

        screen_w, screen_h = pyautogui.size()
        ship_y = int(screen_h * 0.85)  # Ship is near bottom
        dodge_x = screen_w // 2
        last_shot = 0
        dodge_timer = time.time()

        try:
            while time.time() - dodge_timer < self.game_duration:
                # Check 'q' key to quit
                if keyboard.is_pressed('q'):
                    print("\n  'q' pressed - stopping!")
                    break

                start_time = time.time()

                # Check end screen
                if self._is_end_screen():
                    print("  End screen detected - game complete!")
                    break

                # Find enemies
                enemies = self._find_enemies()

                # Dodge: continuous horizontal zig-zag at ship level
                now_dodge = time.time()
                if now_dodge - dodge_timer > 0.5:
                    self.dodge_direction *= -1
                    dodge_timer = now_dodge

                dodge_speed = 8  # pixels per frame
                dodge_x += dodge_speed * self.dodge_direction
                # Keep in bounds
                margin = 100
                dodge_x = max(margin, min(screen_w - margin, dodge_x))

                if enemies:
                    # Aim at the lowest enemy (closest to ship = highest priority)
                    _, ey, etype = enemies[0]
                    aim_x = enemies[0][0]
                    aim_y = ey

                    # Move ship under the enemy for a clear shot
                    pyautogui.moveTo(aim_x, ship_y, duration=0.05)

                    # Shoot if cooldown passed
                    now = time.time()
                    if now - last_shot > self.shoot_cooldown:
                        pyautogui.click(aim_x, aim_y)
                        last_shot = now
                        print(f"  Shot at {etype} enemy ({aim_x}, {aim_y})")

                else:
                    # No enemies - just dodge at ship level
                    pyautogui.moveTo(dodge_x, ship_y, duration=0.05)

                # Maintain ~20fps
                elapsed = time.time() - start_time
                if elapsed < 0.05:
                    time.sleep(0.05 - elapsed)

            print("END Token Blaster")
            return True

        except Exception as e:
            print(f"  Error in Token Blaster: {e}")
            return False
