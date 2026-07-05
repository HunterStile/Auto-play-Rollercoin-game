"""
CoinMatch Game Bot.

Match-3 game on 8x8 grid with AI move evaluation.
Swaps adjacent coins to create matches of 3+.
"""

import pyautogui
import numpy as np
import time
from PIL import ImageGrab
from typing import List, Tuple, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game


# Coin color definitions: (R, B) tuples
COIN_COLORS = {
    'ETH': (66, 207),
    'BLUE': (0, 184),
    'YELLOW': (200, 64),
    'ORANGE': (231, 32),
}


@register_game
class CoinMatchBot(BaseGame):
    game_id = 'coinmatch'
    display_name = 'CoinMatch'
    description = 'Match-3 puzzle with AI move evaluation on 8x8 grid'
    config_keys = {'position': 'COINMATCH_POSITION', 'start_position': 'COINMATCH_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.grid_start_x = config.get('grid_x', 600) if config else 600
        self.grid_start_y = config.get('grid_y', 250) if config else 250
        self.cell_size = 50
        self.grid_size = 8
        self.color_tolerance = 20
        self.game_duration = 60  # seconds

    # ── Color Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _are_colors_similar(color1: tuple, color2: tuple) -> bool:
        """Check if two (R, B) colors are similar."""
        r1, b1 = color1[0], color1[2] if len(color1) > 2 else color1[1]
        r2, b2 = color2
        return abs(r1 - r2) <= 20 and abs(b1 - b2) <= 20

    def _get_position_color(self, x: int, y: int) -> tuple:
        """Get average color at a position."""
        region = (x - 3, y - 3, x + 3, y + 3)
        screenshot = ImageGrab.grab(bbox=region)
        img_array = np.array(screenshot)
        return tuple(np.mean(img_array, axis=(0, 1)).astype(int))

    def _get_coin_type(self, x: int, y: int) -> Optional[str]:
        """Identify coin type by color."""
        color = self._get_position_color(x, y)
        r, b = color[0], color[2]

        for coin_type, (tr, tb) in COIN_COLORS.items():
            if abs(r - tr) <= self.color_tolerance and abs(b - tb) <= self.color_tolerance:
                return coin_type
        return None

    # ── Grid ─────────────────────────────────────────────────────────────

    def _grid_pos(self, row: int, col: int) -> Tuple[int, int]:
        """Get screen position for a grid cell."""
        return (
            self.grid_start_x + col * self.cell_size,
            self.grid_start_y + row * self.cell_size,
        )

    def _scan_grid(self) -> List[List[Optional[str]]]:
        """Scan the entire grid and return a matrix of coin types."""
        grid = [[None] * self.grid_size for _ in range(self.grid_size)]
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x, y = self._grid_pos(row, col)
                grid[row][col] = self._get_coin_type(x, y)
        return grid

    # ── Move Evaluation ──────────────────────────────────────────────────

    def _evaluate_move(self, grid, r1, c1, r2, c2) -> Tuple[int, list, str, str]:
        """Simulate a swap and return the score it would produce."""
        if not (0 <= r1 < self.grid_size and 0 <= c1 < self.grid_size and
                0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size):
            return 0, [], '', ''

        new_grid = [row[:] for row in grid]
        coin1, coin2 = new_grid[r1][c1], new_grid[r2][c2]
        new_grid[r1][c1], new_grid[r2][c2] = coin2, coin1

        score = 0
        matches = []

        # Horizontal matches
        for row in range(self.grid_size):
            count = 1
            current = None
            for col in range(self.grid_size):
                if new_grid[row][col] == current and current is not None:
                    count += 1
                else:
                    if count >= 3:
                        score += count
                        matches.append(f"H-match of {count} {current} in row {row}")
                    count = 1
                    current = new_grid[row][col]
            if count >= 3:
                score += count
                matches.append(f"H-match of {count} {current} in row {row}")

        # Vertical matches
        for col in range(self.grid_size):
            count = 1
            current = None
            for row in range(self.grid_size):
                if new_grid[row][col] == current and current is not None:
                    count += 1
                else:
                    if count >= 3:
                        score += count
                        matches.append(f"V-match of {count} {current} in col {col}")
                    count = 1
                    current = new_grid[row][col]
            if count >= 3:
                score += count
                matches.append(f"V-match of {count} {current} in col {col}")

        return score, matches, str(coin1), str(coin2)

    def _find_best_move(self) -> Optional[Tuple[int, int, int, int]]:
        """Find the best move by evaluating all possible swaps."""
        grid = self._scan_grid()
        best_score = 0
        best_move = None

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                # Horizontal swap
                if col < self.grid_size - 1:
                    score, _, _, _ = self._evaluate_move(grid, row, col, row, col + 1)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, row, col + 1)

                # Vertical swap
                if row < self.grid_size - 1:
                    score, _, _, _ = self._evaluate_move(grid, row, col, row + 1, col)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, row + 1, col)

        if best_move:
            print(f"Best move: {best_move}, score: {best_score}")
        return best_move if best_score > 0 else None

    # ── Actions ──────────────────────────────────────────────────────────

    def _make_move(self, r1: int, c1: int, r2: int, c2: int):
        """Execute a swap on screen."""
        x1, y1 = self._grid_pos(r1, c1)
        x2, y2 = self._grid_pos(r2, c2)

        pyautogui.moveTo(x1, y1)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.moveTo(x2, y2, duration=0.2)
        pyautogui.mouseUp()
        time.sleep(0.5)

    # ── Main Loop ────────────────────────────────────────────────────────

    def play(self) -> bool:
        """Play one round of CoinMatch."""
        print("START CoinMatch")
        start_time = time.time()

        try:
            while time.time() - start_time < self.game_duration:
                move = self._find_best_move()
                if move is None:
                    print("No moves available")
                    time.sleep(1)
                    continue

                r1, c1, r2, c2 = move
                print(f"Move: ({r1},{c1}) -> ({r2},{c2})")
                self._make_move(r1, c1, r2, c2)
                time.sleep(1.5)

            print("END CoinMatch (time's up)")
            return True
        except Exception as e:
            print(f"Error in CoinMatch: {e}")
            return False
