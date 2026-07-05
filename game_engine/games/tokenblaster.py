"""
Token Blaster Game Bot.

Space Invaders-style shooter:
- LEFT/RIGHT arrow keys = move ship
- SPACE held continuously = auto-fire
Press 'q' at any time to stop the bot.
"""

import pyautogui
import time
import keyboard
from typing import Tuple, List

from game_engine.base import BaseGame
from game_engine.registry import register_game

pyautogui.FAILSAFE = False

# Enemy colors: (R, G, B)
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
    description = 'Space shooter: arrow keys to move, space held for auto-fire'

    def __init__(self, config=None):
        super().__init__(config)
        self.move_speed = 0.06

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

        # Deduplicate
        deduped = []
        for ex, ey, etype in enemies:
            if not any(abs(ex - dx) < 30 and abs(ey - dy) < 30 for dx, dy, _ in deduped):
                deduped.append((ex, ey, etype))

        deduped.sort(key=lambda e: (-e[1], abs(e[0] - ship_x)))
        return deduped

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
        print("  SPACE held = auto-fire, LEFT/RIGHT = move, Q = quit")
        print("  Focusing browser in 2s... CLICK ON THE GAME NOW!")

        time.sleep(2)

        # Click center of screen to focus the browser
        screen_w, screen_h = pyautogui.size()
        game_center = (screen_w // 2, screen_h // 2)
        pyautogui.click(game_center[0], game_center[1])
        time.sleep(0.3)

        # Start holding space for continuous auto-fire
        pyautogui.keyDown('space')
        space_held = True
        print("  Space held - auto-fire active")

        ship_x = screen_w // 2
        dodge_dir = 1
        dodge_timer = time.time()
        start_time = time.time()

        try:
            while time.time() - start_time < 65:
                if keyboard.is_pressed('q'):
                    print("\n  'q' pressed - stopping!")
                    break

                if self._is_end_screen():
                    print("  End screen detected - game complete!")
                    break

                enemies = self._find_enemies(ship_x)

                if enemies:
                    ex, ey, etype = enemies[0]
                    x_dist = ex - ship_x

                    if abs(x_dist) > 50:
                        # Move towards enemy
                        if x_dist < 0:
                            pyautogui.keyDown('left')
                            time.sleep(self.move_speed)
                            pyautogui.keyUp('left')
                            ship_x = max(50, ship_x - 15)
                        else:
                            pyautogui.keyDown('right')
                            time.sleep(self.move_speed)
                            pyautogui.keyUp('right')
                            ship_x = min(screen_w - 50, ship_x + 15)
                    # If aligned, space is already held = shooting continuously
                else:
                    # Dodge
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
            print(f"  Error: {e}")
            return False
        finally:
            # Always release space and other keys
            for key in ['space', 'up', 'down', 'left', 'right']:
                try:
                    pyautogui.keyUp(key)
                except Exception:
                    pass
