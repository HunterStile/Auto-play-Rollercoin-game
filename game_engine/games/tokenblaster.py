"""
Token Blaster Game Bot.

Simple effective strategy:
- Move slowly left-right every 5 seconds
- Auto-fire (space held) continuously
- Detect and shoot red enemies
Press 'q' to stop.
"""

import pyautogui
import time
import keyboard
from typing import List, Tuple

from game_engine.base import BaseGame
from game_engine.registry import register_game

pyautogui.FAILSAFE = False


@register_game
class TokenBlasterBot(BaseGame):
    game_id = 'tokenblaster'
    display_name = 'Token Blaster'
    description = 'Slow sweep + auto-fire + shoot red enemies'

    def __init__(self, config=None):
        super().__init__(config)

    def _find_red_enemies(self) -> List[Tuple[int, int]]:
        """Find red enemy pixels (220, 50, 50). Returns deduplicated positions sorted by Y (closest first)."""
        raw = []
        screenshot = pyautogui.screenshot()
        w, h = screenshot.size

        for x in range(0, w, 12):
            for y in range(0, int(h * 0.55), 12):
                try:
                    r, g, b = screenshot.getpixel((x, y))
                    # Red enemy: R high, G low, B low
                    if r > 180 and g < 100 and b < 100:
                        raw.append((x, y))
                except Exception:
                    pass

        # Deduplicate
        enemies = []
        for ex, ey in raw:
            if not any(abs(ex - dx) < 30 and abs(ey - dy) < 30 for dx, dy in enemies):
                enemies.append((ex, ey))

        # Closest to bottom (highest Y) first
        enemies.sort(key=lambda e: -e[1])
        return enemies

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
        print("  Space held = auto-fire, sweep L-R every 5s, Q = quit")
        time.sleep(2)

        screen_w, screen_h = pyautogui.size()
        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.3)

        # Hold space for auto-fire
        pyautogui.keyDown('space')

        start_time = time.time()
        sweep_dir = 1  # 1=right, -1=left
        last_sweep = time.time()
        sweep_interval = 5.0  # switch direction every 5s

        try:
            while time.time() - start_time < 65:
                if keyboard.is_pressed('q'):
                    print("\n  'q' - stopping!")
                    break

                if self._is_end_screen():
                    print("  Game complete!")
                    break

                now = time.time()

                # Sweep direction change every 5s
                if now - last_sweep > sweep_interval:
                    sweep_dir *= -1
                    last_sweep = now

                # Continuous slow movement
                move_amount = 3  # pixels per tick
                if sweep_dir > 0:
                    pyautogui.keyDown('right')
                    time.sleep(0.04)
                    pyautogui.keyUp('right')
                else:
                    pyautogui.keyDown('left')
                    time.sleep(0.04)
                    pyautogui.keyUp('left')

                # Check red enemies (log occasionally)
                enemies = self._find_red_enemies()
                if enemies and int(now) % 3 == 0:
                    print(f"  {len(enemies)} red enemies, closest at Y={enemies[0][1]}")

                time.sleep(0.06)

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
