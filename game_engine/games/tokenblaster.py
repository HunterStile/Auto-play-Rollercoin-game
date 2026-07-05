"""
Token Blaster Game Bot.

Space Invaders shooter - smart strategy:
- Stay still + auto-fire at aligned enemy
- Only move to: dodge projectiles OR aim at new enemy
- Tracks current target, switches when enemy is dead
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

COLOR_TOLERANCE = 30


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Smart shooter: auto-fire, projectile dodge, target tracking'

    def __init__(self, config=None):
        super().__init__(config)

    def _color_match(self, target, actual, tolerance=COLOR_TOLERANCE):
        return all(abs(t - a) <= tolerance for t, a in zip(target, actual))

    def _find_enemies(self, ship_x: int) -> List[Tuple[int, int, str]]:
        """Find all enemies, sorted by priority (closest to ship first, then closest X)."""
        enemies = []
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        scan_h = int(h * 0.55)

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
            if not any(abs(ex - dx) < 35 and abs(ey - dy) < 35 for dx, dy, _ in deduped):
                deduped.append((ex, ey, etype))

        # Sort: lowest (closest to ship) first, then nearest X
        deduped.sort(key=lambda e: (-e[1], abs(e[0] - ship_x)))
        return deduped

    def _has_projectile_near(self, ship_x: int, ship_y: int, margin: int = 120) -> bool:
        """
        Quick scan: are there any projectiles near the ship?
        Scans a thin strip above the ship for bright fast-moving dots.
        """
        screen_w = pyautogui.size()[0]
        scan_x = max(0, ship_x - margin)
        scan_w = min(margin * 2, screen_w - scan_x)
        scan_y = max(0, ship_y - 250)
        scan_h = ship_y - scan_y

        if scan_w < 10 or scan_h < 10:
            return False

        try:
            pic = pyautogui.screenshot(region=(scan_x, scan_y, scan_w, scan_h))
            threat_count = 0
            for x in range(0, scan_w, 10):
                for y in range(0, scan_h, 10):
                    r, g, b = pic.getpixel((x, y))
                    brightness = r + g + b
                    # Bright small dot = likely projectile
                    if brightness > 550 and r > 180 and g > 180:
                        # Not an enemy color?
                        is_enemy = any(
                            self._color_match(c, (r, g, b))
                            for c in ENEMY_COLORS.values()
                        )
                        if not is_enemy:
                            threat_count += 1
                            if threat_count > 4:
                                return True
        except Exception:
            pass
        return False

    def _is_end_screen(self) -> bool:
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size
        for px, py in [(w // 2, h // 2), (w // 2, h - 100)]:
            try:
                r, g, b = screenshot.getpixel((px, py))
                if abs(r - 3) <= 5 and abs(g - 225) <= 5 and abs(b - 228) <= 5:
                    return True
            except Exception:
                pass
        return False

    def play(self) -> bool:
        print("START Token Blaster")
        print("  SPACE=auto-fire, arrows=move, Q=quit")
        time.sleep(2)

        screen_w, screen_h = pyautogui.size()
        ship_y = int(screen_h * 0.88)
        ship_x = screen_w // 2

        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.3)
        pyautogui.keyDown('space')

        start_time = time.time()
        last_move = 0
        last_projectile_scan = 0
        target_ex = None  # current target X
        target_stuck_since = 0  # how long we've been on same target

        try:
            while time.time() - start_time < 65:
                if keyboard.is_pressed('q'):
                    print("\n  'q' - stopping!")
                    break

                if self._is_end_screen():
                    print("  Game complete!")
                    break

                now = time.time()

                # 1. Projectile check (every 0.2s to save CPU)
                if now - last_projectile_scan > 0.2:
                    last_projectile_scan = now
                    if self._has_projectile_near(ship_x, ship_y):
                        # Dodge: move sideways quickly
                        dodge_dir = 1 if ship_x < screen_w // 2 else -1
                        for _ in range(2):
                            pyautogui.press('right' if dodge_dir > 0 else 'left')
                            time.sleep(0.03)
                        ship_x = max(80, min(screen_w - 80, ship_x + dodge_dir * 50))
                        print(f"  Dodge! ship_x={ship_x}")
                        last_move = now
                        continue

                # 2. Find enemies
                enemies = self._find_enemies(ship_x)

                if enemies:
                    ex, ey, etype = enemies[0]

                    # Track target - if same enemy for too long, it's probably dead
                    if target_ex is not None and abs(ex - target_ex) < 40:
                        # Same target area
                        if now - target_stuck_since > 4.0:
                            # Been on this target too long, force switch
                            if len(enemies) > 1:
                                ex, ey, etype = enemies[1]  # switch to 2nd best
                                print(f"  Switching target: {ex},{ey} ({etype})")
                                target_stuck_since = now
                    else:
                        target_ex = ex
                        target_stuck_since = now

                    x_dist = ex - ship_x

                    # Move only if we need to aim at different enemy
                    if abs(x_dist) > 60 and now - last_move > 0.15:
                        if x_dist < 0:
                            pyautogui.press('left')
                            ship_x = max(80, ship_x - 20)
                        else:
                            pyautogui.press('right')
                            ship_x = min(screen_w - 80, ship_x + 20)
                        last_move = now
                    # else: aligned, stay still and fire

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
