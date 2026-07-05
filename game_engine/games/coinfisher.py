"""
Coin Fisher Game Bot.

Fishing game: click to shoot harpoon, grab coins on the way back.
Strategy: repeatedly click at the far end of the screen to maximize catch.
"""

import pyautogui
import time
from typing import Tuple

from game_engine.base import BaseGame
from game_engine.registry import register_game

# End-screen detection color
END_SCREEN_COLOR = (3, 225, 228)

# Default game region (approximate)
DEFAULT_REGION = (300, 200, 1200, 700)


@register_game
class CoinFisherBot(BaseGame):
    game_id = 'coinfisher'
    display_name = 'Coin Fisher'
    description = 'Fishing game: click to shoot harpoon, grab passing coins'

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', DEFAULT_REGION) if config else DEFAULT_REGION
        self.game_duration = 65  # seconds
        self.click_interval = 1.5  # seconds between harpoon shots

    def _is_end_screen(self) -> bool:
        """Check if the game has ended by looking for the end-screen color."""
        rx, ry, rw, rh = self.region
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 80),
            (rx + rw // 3, ry + rh // 2),
            (rx + 2 * rw // 3, ry + rh // 2),
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
        """Play one round of Coin Fisher."""
        print("START Coin Fisher")
        start_time = time.time()
        last_click = 0

        rx, ry, rw, rh = self.region

        # Target: click near the TOP of the play area to fire harpoon upward
        # The harpoon shoots up, hits the top, and collects coins on the way back
        target_x = rx + rw // 2
        target_y = ry + 80  # Near the top of the game area

        try:
            while time.time() - start_time < self.game_duration:
                # Check end screen
                if self._is_end_screen():
                    print("End screen detected - game complete!")
                    break

                now = time.time()
                if now - last_click > self.click_interval:
                    # Click to fire harpoon
                    pyautogui.click(target_x, target_y)
                    last_click = now

                    # Move target slightly for variety
                    target_x = rx + int(rw * 0.3) + int(rw * 0.4 * ((now * 0.7) % 1.0))

                time.sleep(0.1)

            print("END Coin Fisher")
            return True

        except Exception as e:
            print(f"Error in Coin Fisher: {e}")
            return False
