"""
Coin Fisher Game Bot.

Fishing game: click to shoot harpoon where coins are.
Scans for coin colors (same as CoinClick) and clicks
at the position with the highest coin density.
"""

import pyautogui
import time
from typing import Tuple, List, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

# Coin color signatures - same as CoinClick
COIN_COLORS = {
    'eth':    (66, 105, 207),
    'blue':   (0, 128, 184),
    'yellow': (200, 200, 64),
    'orange': (231, 128, 32),
    'grey':   (230, 230, 230),
}

# End-screen detection color
END_SCREEN_COLOR = (3, 225, 228)

COLOR_TOLERANCE = 5


@register_game
class CoinFisherBot(BaseGame):
    game_id = 'coinfisher'
    display_name = 'Coin Fisher'
    description = 'Fishing game: scans for coins and clicks where they are'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = 65  # seconds
        self.click_cooldown = 1.5  # seconds between harpoon shots

    @staticmethod
    def _is_coin(r: int, g: int, b: int) -> bool:
        """Check if a pixel matches any coin color."""
        for color in COIN_COLORS.values():
            tr, tg, tb = color
            if (abs(r - tr) <= COLOR_TOLERANCE and
                abs(g - tg) <= COLOR_TOLERANCE and
                abs(b - tb) <= COLOR_TOLERANCE):
                return True
        return False

    def _scan_coins(self, region: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
        """
        Scan a region for coins. Returns list of (x, y) coin positions.
        Uses grid-based scanning to find coin clusters.
        """
        coins = []
        rx, ry, rw, rh = region

        try:
            pic = pyautogui.screenshot(region=region)
            width, height = pic.size

            for x in range(0, width, 8):
                for y in range(0, height, 8):
                    r, g, b = pic.getpixel((x, y))
                    if self._is_coin(r, g, b):
                        coins.append((rx + x, ry + y))
        except Exception as e:
            print(f"  Scan error: {e}")

        return coins

    def _find_best_shot(self, region: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """
        Find the best position to click:
        - Divide area into vertical columns
        - Count coins in each column
        - Click at the top of the column with most coins
        """
        coins = self._scan_coins(region)

        if not coins:
            # No coins visible - click center-top as fallback
            rx, ry, rw, rh = region
            return (rx + rw // 2, ry + 60)

        # Group coins by X position (vertical columns)
        NUM_COLUMNS = 8
        rx, ry, rw, rh = region
        column_width = rw / NUM_COLUMNS

        columns = [[] for _ in range(NUM_COLUMNS)]
        for cx, cy in coins:
            col_idx = int((cx - rx) / column_width)
            if 0 <= col_idx < NUM_COLUMNS:
                columns[col_idx].append((cx, cy))

        # Find column with most coins
        best_col = max(range(NUM_COLUMNS), key=lambda i: len(columns[i]))

        if columns[best_col]:
            # Average X of coins in best column, click at top
            avg_x = int(sum(c[0] for c in columns[best_col]) / len(columns[best_col]))
            # Click near the top where coins are densest
            min_y = min(c[1] for c in columns[best_col])
            return (avg_x, min_y - 10)
        else:
            col_center_x = int(rx + (best_col + 0.5) * column_width)
            return (col_center_x, ry + 60)

    def _is_end_screen(self, region: Tuple[int, int, int, int]) -> bool:
        """Check if the game has ended."""
        rx, ry, rw, rh = region
        check_points = [
            (rx + rw // 2, ry + rh // 2),
            (rx + rw // 2, ry + rh - 80),
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

        # Get the game region from screenshot
        screenshot = pyautogui.screenshot()
        sw, sh = screenshot.size
        # Use full screen area for coin scanning
        game_region = (0, 100, sw, sh - 200)

        try:
            while time.time() - start_time < self.game_duration:
                if self._is_end_screen(game_region):
                    print("End screen detected - game complete!")
                    break

                now = time.time()
                if now - last_click > self.click_cooldown:
                    # Find best shot position based on coin density
                    target = self._find_best_shot(game_region)
                    if target:
                        pyautogui.click(target[0], target[1])
                        print(f"  Shot at: {target}")
                        last_click = now

                time.sleep(0.3)

            print("END Coin Fisher")
            return True

        except Exception as e:
            print(f"Error in Coin Fisher: {e}")
            return False
