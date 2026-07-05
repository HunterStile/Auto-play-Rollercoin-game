"""
Token Blaster Game Bot.

Space Invaders-style shooter:
- LEFT/RIGHT arrow keys = move ship
- SPACE held continuously = auto-fire
- Projectile detection: scans for enemy bullets and dodges
Press 'q' to stop.
"""

import pyautogui
import time
import keyboard
from typing import Tuple, List, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

pyautogui.FAILSAFE = False

ENEMY_COLORS = {
    'red':    (220, 50, 50),
    'green':  (50, 200, 50),
    'white':  (240, 240, 240),
    'yellow': (220, 220, 50),
    'pink':   (220, 50, 200),
}

END_SCREEN_COLOR = (3, 225, 228)
COLOR_TOLERANCE = 30


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Space shooter: auto-fire + projectile detection + dodge'

    def __init__(self, config=None):
        super().__init__(config)

    def _color_match(self, target, actual, tolerance=COLOR_TOLERANCE):
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _find_enemies(self, ship_x: int) -> List[Tuple[int, int, str]]:
        enemies = []
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        scan_h = int(h * 0.6)

        for x in range(0, w, 15):
            for y in range(0, scan_h, 15):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    for etype, color in ENEMY_COLORS.items():
                        if self._color_match(color, (r, g, b)):
                            enemies.append((x, y, etype))
                            break
                except Exception:
                    pass

        deduped = []
        for ex, ey, etype in enemies:
            if not any(abs(ex - dx) < 30 and abs(ey - dy) < 30 for dx, dy, _ in deduped):
                deduped.append((ex, ey, etype))

        deduped.sort(key=lambda e: (-e[1], abs(e[0] - ship_x)))
        return deduped

    def _detect_projectile_near_ship(self, ship_x: int, ship_y: int) -> Optional[str]:
        """
        Scan a box around/above the ship for enemy projectiles.
        Projectiles are bright white/yellow dots, smaller than enemies.
        Returns 'left', 'right', or None if no threat.
        """
        screen_w, screen_h = pyautogui.size()
        # Scan a rectangle above the ship
        scan_w = 200
        scan_h = int(ship_y * 0.5)  # from top of screen down to ship area
        scan_x = max(0, ship_x - scan_w // 2)
        scan_y = max(0, ship_y - scan_h)
        scan_width = min(scan_w, screen_w - scan_x)
        scan_height = ship_y - scan_y

        if scan_width <= 0 or scan_height <= 0:
            return None

        try:
            region = (scan_x, scan_y, scan_width, scan_height)
            pic = pyautogui.screenshot(region=region)

            left_threats = 0
            right_threats = 0

            for x in range(0, pic.size[0], 6):
                for y in range(0, pic.size[1], 6):
                    r, g, b = pic.getpixel((x, y))
                    # Projectiles are bright (R+G+B > 500) but not the same as enemy colors
                    brightness = r + g + b
                    if brightness > 500:
                        # Check it's not an enemy (enemies have specific colors)
                        is_enemy = False
                        for ecolor in ENEMY_COLORS.values():
                            if self._color_match(ecolor, (r, g, b)):
                                is_enemy = True
                                break
                        if not is_enemy:
                            # It's a projectile! Is it on left or right side?
                            if x < pic.size[0] // 2:
                                left_threats += 1
                            else:
                                right_threats += 1

            if left_threats > right_threats and left_threats > 5:
                return 'left'
            elif right_threats > left_threats and right_threats > 5:
                return 'right'

        except Exception:
            pass

        return None

    def _is_end_screen(self) -> bool:
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        for px, py in [(w // 2, h // 2), (w // 2, h - 100)]:
            try:
                r, g, b = screenshot.getpixel((px, py))
                if (abs(r - 3) <= 5 and abs(g - 225) <= 5 and abs(b - 228) <= 5):
                    return True
            except Exception:
                pass
        return False

    def play(self) -> bool:
        print("START Token Blaster")
        print("  SPACE held = auto-fire, LEFT/RIGHT = move/dodge, Q = quit")
        time.sleep(2)

        screen_w, screen_h = pyautogui.size()
        ship_y = int(screen_h * 0.88)  # ship near bottom
        ship_x = screen_w // 2

        # Click to focus browser
        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.3)

        # Hold space for continuous fire
        pyautogui.keyDown('space')

        start_time = time.time()
        last_move_time = 0
        move_cooldown = 0.15  # don't spam movement keys

        try:
            while time.time() - start_time < 65:
                if keyboard.is_pressed('q'):
                    print("\n  'q' - stopping!")
                    break

                if self._is_end_screen():
                    print("  Game complete!")
                    break

                now = time.time()

                # 1. Check for projectiles - DODGE is highest priority
                threat = self._detect_projectile_near_ship(ship_x, ship_y)

                if threat and now - last_move_time > move_cooldown:
                    if threat == 'left':
                        # Projectiles on left - dodge RIGHT
                        pyautogui.press('right')
                        ship_x = min(screen_w - 50, ship_x + 30)
                        print(f"  Dodge RIGHT! (threat: {threat})")
                    else:
                        # Projectiles on right - dodge LEFT
                        pyautogui.press('left')
                        ship_x = max(50, ship_x - 30)
                        print(f"  Dodge LEFT! (threat: {threat})")
                    last_move_time = now
                    time.sleep(0.1)
                    continue

                # 2. Find enemies
                enemies = self._find_enemies(ship_x)

                if enemies:
                    ex, ey, etype = enemies[0]
                    x_dist = ex - ship_x

                    # Only move if not aligned (enemy is far horizontally)
                    if abs(x_dist) > 50 and now - last_move_time > move_cooldown:
                        if x_dist < 0:
                            pyautogui.press('left')
                            ship_x = max(50, ship_x - 15)
                        else:
                            pyautogui.press('right')
                            ship_x = min(screen_w - 50, ship_x + 15)
                        last_move_time = now
                    # If aligned: stay still, space is held = shooting

                # 3. If no enemies and no threats: stay completely still

                time.sleep(0.05)

            print("END Token Blaster")
            return True

        except Exception as e:
            print(f"  Error: {e}")
            return False
        finally:
            for key in ['space', 'up', 'down', 'left', 'right']:
                try:
                    pyautogui.keyUp(key)
                except Exception:
                    pass
