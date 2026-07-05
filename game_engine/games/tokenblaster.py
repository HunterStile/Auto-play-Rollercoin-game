"""
Token Blaster Game Bot.

Space Invaders-style shooter controlled with ARROW KEYS:
- LEFT/RIGHT = move ship
- UP = shoot
Press 'q' at any time to stop the bot.
"""

import pyautogui
import time
import keyboard
from typing import Tuple, List

from game_engine.base import BaseGame
from game_engine.registry import register_game

# Disable fail-safe so mouse doesn't crash the bot
pyautogui.FAILSAFE = False

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
    description = 'Space shooter: arrow keys to move and shoot, color detection for enemies'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = 65
        self.shoot_cooldown = 0.15
        self.move_speed = 0.08  # how long to hold left/right

    def _color_match(self, target: Tuple[int, int, int], actual: Tuple[int, int, int],
                     tolerance: int = COLOR_TOLERANCE) -> bool:
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _find_enemies(self, ship_x: int) -> List[Tuple[int, int, str]]:
        """Scan the screen for enemies. Returns list of (x, y, type) sorted by priority."""
        enemies = []
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size

        scan_h = int(h * 0.6)
        step = 15

        for x in range(0, w, step):
            for y in range(0, scan_h, step):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    for etype, color in ENEMY_COLORS.items():
                        if self._color_match(color, (r, g, b)):
                            enemies.append((x, y, etype))
                            break
                except Exception:
                    pass

        # Deduplicate nearby hits
        deduped = []
        for ex, ey, etype in enemies:
            if not any(abs(ex - dx) < 30 and abs(ey - dy) < 30 for dx, dy, _ in deduped):
                deduped.append((ex, ey, etype))

        # Sort: closest to ship (highest Y) first, then closest X to ship
        deduped.sort(key=lambda e: (-e[1], abs(e[0] - ship_x)))

        return deduped

    def _is_end_screen(self) -> bool:
        """Check if the game has ended."""
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        check_points = [
            (w // 2, h // 2),
            (w // 2, h - 100),
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
        """Play one round of Token Blaster using arrow keys."""
        print("START Token Blaster")
        print("  Controls: LEFT/RIGHT = move, UP = shoot, Q = quit")

        screen_w = pyautogui.size()[0]
        ship_x = screen_w // 2  # assume ship starts at center
        last_shot = 0
        dodge_dir = 1
        dodge_timer = time.time()
        phase = 'dodge'  # 'dodge' or 'shoot'

        try:
            while True:
                if keyboard.is_pressed('q'):
                    print("\n  'q' pressed - stopping!")
                    break

                if self._is_end_screen():
                    print("  End screen detected - game complete!")
                    break

                # Find enemies
                enemies = self._find_enemies(ship_x)

                if enemies:
                    # Target the best enemy (already sorted by priority)
                    ex, ey, etype = enemies[0]
                    x_dist = ex - ship_x

                    if abs(x_dist) < 40:
                        # Aligned! Shoot
                        if time.time() - last_shot > self.shoot_cooldown:
                            pyautogui.press('up')
                            last_shot = time.time()
                            print(f"  Shot at {etype} enemy ({ex}, {ey})")
                            dodge_dir *= -1  # dodge after shooting
                    elif x_dist < 0:
                        # Enemy is left - move left
                        pyautogui.keyDown('left')
                        time.sleep(self.move_speed)
                        pyautogui.keyUp('left')
                        ship_x = max(50, ship_x - 20)
                    else:
                        # Enemy is right - move right
                        pyautogui.keyDown('right')
                        time.sleep(self.move_speed)
                        pyautogui.keyUp('right')
                        ship_x = min(screen_w - 50, ship_x + 20)
                else:
                    # No enemies - dodge
                    if time.time() - dodge_timer > 1.0:
                        dodge_dir *= -1
                        dodge_timer = time.time()

                    if dodge_dir > 0:
                        pyautogui.keyDown('right')
                        time.sleep(0.3)
                        pyautogui.keyUp('right')
                        ship_x = min(screen_w - 50, ship_x + 60)
                    else:
                        pyautogui.keyDown('left')
                        time.sleep(0.3)
                        pyautogui.keyUp('left')
                        ship_x = max(50, ship_x - 60)

                time.sleep(0.05)

            print("END Token Blaster")
            return True

        except Exception as e:
            print(f"  Error in Token Blaster: {e}")
            return False
        finally:
            # Always release keys on exit
            for key in ['up', 'down', 'left', 'right', 'space']:
                try:
                    pyautogui.keyUp(key)
                except Exception:
                    pass
