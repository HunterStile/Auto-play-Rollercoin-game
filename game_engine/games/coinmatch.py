"""
CoinMatch Game Bot v2.

Match-3 game on 8x8 grid with AI move evaluation.
Uses full-cell color sampling with calibrated coin colors.
"""

import pyautogui
import numpy as np
import time
from typing import List, Tuple, Optional

from game_engine.base import BaseGame
from game_engine.registry import register_game

# ── Coin RGB colors (calibrated from real game) ──────────────────────
# Format: (R, G, B)
COIN_COLORS_RGB = {
    'GOLD':   (190, 160, 55),   # Yellow/Gold coin
    'ORANGE': (230, 148, 60),   # Orange coin
    'BLUE':   (84, 119, 215),   # Medium blue coin
    'TEAL':   (0, 100, 163),    # Dark teal/cyan coin
}

COLOR_TOLERANCE = 45  # Per-channel tolerance


@register_game
class CoinMatchBot(BaseGame):
    game_id = 'coinmatch'
    display_name = 'CoinMatch'
    description = 'Match-3 puzzle with AI move evaluation on 8x8 grid'
    config_keys = {'position': 'COINMATCH_POSITION', 'start_position': 'COINMATCH_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.grid_x = config.get('grid_x', 600) if config else 600
        self.grid_y = config.get('grid_y', 250) if config else 250
        self.cell_size = config.get('cell_size', 50) if config else 50
        self.grid_size = 8
        self.game_duration = 60  # seconds
        self.sample_points = [
            (0.5, 0.5),   # center
            (0.25, 0.25), # top-left
            (0.75, 0.25), # top-right
            (0.25, 0.75), # bottom-left
            (0.75, 0.75), # bottom-right
        ]

    # ── Color detection ────────────────────────────────────────────────

    @staticmethod
    def _classify_color(r, g, b):
        """Classify an RGB pixel into a coin type."""
        best_type = None
        best_dist = float('inf')
        for coin_type, (tr, tg, tb) in COIN_COLORS_RGB.items():
            dist = abs(r - tr) + abs(g - tg) + abs(b - tb)
            if dist < best_dist:
                best_dist = dist
                best_type = coin_type
        if best_dist <= COLOR_TOLERANCE * 3:
            return best_type
        return None

    def _get_cell_coin_type(self, screenshot, col, row):
        """
        Sample multiple points in a cell and return majority-vote coin type.
        screenshot: numpy array (H, W, 3) of the game area.
        """
        h, w = screenshot.shape[:2]
        votes = []
        for fx, fy in self.sample_points:
            px = int(col * self.cell_size + fx * self.cell_size)
            py = int(row * self.cell_size + fy * self.cell_size)
            if 0 <= px < w and 0 <= py < h:
                r, g, b = screenshot[py, px]
                coin = self._classify_color(int(r), int(g), int(b))
                if coin:
                    votes.append(coin)

        if not votes:
            return None

        # Majority vote
        from collections import Counter
        return Counter(votes).most_common(1)[0][0]

    # ── Grid ───────────────────────────────────────────────────────────

    def _grid_pos(self, row: int, col: int) -> Tuple[int, int]:
        """Get screen position for a grid cell center."""
        return (
            self.grid_x + col * self.cell_size + self.cell_size // 2,
            self.grid_y + row * self.cell_size + self.cell_size // 2,
        )

    def _scan_grid(self) -> List[List[Optional[str]]]:
        """Screenshot entire grid area and classify all cells."""
        region = (self.grid_x, self.grid_y,
                  self.cell_size * self.grid_size,
                  self.cell_size * self.grid_size)

        try:
            pic = pyautogui.screenshot(region=region)
            arr = np.array(pic)
        except Exception as e:
            print(f"  Grid scan error: {e}")
            return [[None] * self.grid_size for _ in range(self.grid_size)]

        grid = [[None] * self.grid_size for _ in range(self.grid_size)]
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                grid[row][col] = self._get_cell_coin_type(arr, col, row)
        return grid

    # ── Move Evaluation ────────────────────────────────────────────────

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
                        matches.append(f"H-{count}x{current}")
                    count = 1
                    current = new_grid[row][col]
            if count >= 3:
                score += count
                matches.append(f"H-{count}x{current}")

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
                        matches.append(f"V-{count}x{current}")
                    count = 1
                    current = new_grid[row][col]
            if count >= 3:
                score += count
                matches.append(f"V-{count}x{current}")

        return score, matches, str(coin1), str(coin2)

    def _find_best_move(self) -> Optional[Tuple[int, int, int, int]]:
        """Find the best move by evaluating all possible swaps."""
        grid = self._scan_grid()
        best_score = 0
        best_move = None

        # Count recognized cells
        recognized = sum(1 for row in grid for c in row if c is not None)
        total = self.grid_size * self.grid_size
        print(f"  Grid: {recognized}/{total} recognized")

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
            r1, c1, r2, c2 = best_move
            coin1 = grid[r1][c1] if grid[r1][c1] else '?'
            coin2 = grid[r2][c2] if grid[r2][c2] else '?'
            print(f"  Best: ({r1},{c1}) {coin1} ↔ ({r2},{c2}) {coin2}  score={best_score}")
        return best_move if best_score > 0 else None

    # ── Actions ────────────────────────────────────────────────────────

    def _make_move(self, r1: int, c1: int, r2: int, c2: int):
        """Execute a swap on screen."""
        x1, y1 = self._grid_pos(r1, c1)
        x2, y2 = self._grid_pos(r2, c2)

        pyautogui.moveTo(x1, y1)
        pyautogui.mouseDown()
        time.sleep(0.15)
        pyautogui.moveTo(x2, y2, duration=0.15)
        pyautogui.mouseUp()
        time.sleep(0.4)

    # ── Main Loop ──────────────────────────────────────────────────────

    def play(self) -> bool:
        """Play one round of CoinMatch."""
        print("START CoinMatch v2")
        start_time = time.time()

        try:
            while time.time() - start_time < self.game_duration:
                move = self._find_best_move()
                if move is None:
                    print("  No moves available, waiting...")
                    time.sleep(1)
                    continue

                r1, c1, r2, c2 = move
                self._make_move(r1, c1, r2, c2)
                time.sleep(1.2)

            print("END CoinMatch (time's up)")
            return True
        except Exception as e:
            print(f"  Error in CoinMatch: {e}")
            return False