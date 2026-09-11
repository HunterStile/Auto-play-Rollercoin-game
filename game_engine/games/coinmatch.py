"""Coin Match: adaptive board reading and verified match-3 swaps."""
import time

import numpy as np
import pyautogui

from game_engine.base import BaseGame
from game_engine.coinmatch_vision import detect_board
from game_engine.registry import register_game


def matched_cells(grid):
    """Return unique cells in horizontal/vertical runs of at least three."""
    found = set()
    for vertical in (False, True):
        for line in range(8):
            run = []
            previous = None
            for index in range(9):
                pos = (index, line) if vertical else (line, index)
                coin = grid[pos[0]][pos[1]] if index < 8 else None
                if coin is None or coin != previous:
                    if len(run) >= 3:
                        found.update(run)
                    run = []
                if coin is not None:
                    run.append(pos)
                previous = coin
    return found


@register_game
class CoinMatchBot(BaseGame):
    game_id = 'coinmatch'
    display_name = 'CoinMatch'
    description = 'Adaptive 8x8 detection and match-3 swaps (seven coin types)'
    config_keys = {'position': 'COINMATCH_POSITION', 'start_position': 'COINMATCH_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.grid_size = 8
        self.game_duration = self.config.get('game_duration', 75)
        self.search_region = self.config.get('scan_region')
        self.board = None
        self._previous = None
        self._stable_since = None
        self._pending = None
        self._blocked = set()
        self._blocked_signature = None
        self._ready_move = None
        self._end_region = None
        self._end_seen = 0
        self._ended = False

    def _is_end_screen(self, frame):
        if self._end_region is None:
            return False
        box, size = self._end_region
        if frame.size != size:
            return False
        pixels = np.asarray(frame.crop(box), dtype=np.int16)
        return bool((np.max(np.abs(pixels-(3, 225, 228)), axis=2) <= 5).mean() > .65)

    def _scan_grid(self):
        frame = pyautogui.screenshot().convert('RGB')
        if self._is_end_screen(frame):
            self._end_seen += 1
            self._ended = self._end_seen >= 2
            self.board = None
            return None
        self._end_seen = 0
        self.board = detect_board(frame, self.search_region)
        if self.board:
            xs, ys = self.board.xs, self.board.ys
            dx, dy = (xs[-1]-xs[0])/7, (ys[-1]-ys[0])/7
            self._end_region = (tuple(round(v) for v in
                                     (xs[0]+1.5*dx, ys[0]+1.5*dy,
                                      xs[0]+5.5*dx, ys[0]+5.5*dy)), frame.size)
        return self.board.grid if self.board else None

    def _evaluate_move(self, grid, r1, c1, r2, c2):
        if (any(not 0 <= p < 8 for p in (r1, c1, r2, c2)) or
                abs(r1-r2)+abs(c1-c2) != 1):
            return 0, [], '', ''
        a, b = grid[r1][c1], grid[r2][c2]
        if a is None or b is None or a == b or matched_cells(grid):
            return 0, [], str(a), str(b)
        swapped = [list(row) for row in grid]
        swapped[r1][c1], swapped[r2][c2] = b, a
        matches = matched_cells(swapped)
        if not matches.intersection({(r1, c1), (r2, c2)}):
            return 0, [], str(a), str(b)
        return len(matches), sorted(matches), str(a), str(b)

    def _best_move(self, grid, excluded=()):
        if grid is None or any(c is None for row in grid for c in row) or matched_cells(grid):
            return None
        best_score, best = 0, None
        for row in range(8):
            for col in range(8):
                for dr, dc in ((0, 1), (1, 0)):
                    move = (row, col, row+dr, col+dc)
                    if move in excluded:
                        continue
                    score = self._evaluate_move(grid, *move)[0]
                    if score > best_score:
                        best_score, best = score, move
        return best

    def _find_best_move(self):
        """Only authorize input after repeated stable reads and swap feedback."""
        self._ready_move = None
        grid = self._scan_grid()
        now = time.monotonic()
        signature = self.board.signature if self.board else None
        if signature is None or matched_cells(grid):
            self._previous = self._stable_since = None
            return None
        if signature != self._previous:
            self._previous, self._stable_since = signature, now
            return None
        if now-self._stable_since < .3:
            return None
        if self._pending:
            before, move, sent = self._pending
            if now-sent < .8:
                return None
            if signature == before:
                if now-sent < 2.0:
                    return None
                self._blocked.add(move)
                print('Coin Match: swap unconfirmed; trying a different move.')
            else:
                print('Coin Match: board changed after swap.')
            self._pending = None
        if signature != self._blocked_signature:
            self._blocked.clear()
            self._blocked_signature = signature
        move = self._best_move(grid, self._blocked)
        self._ready_move = move
        return move

    def _grid_pos(self, row, col):
        return int(self.board.xs[col]), int(self.board.ys[row])

    def _make_move(self, r1, c1, r2, c2):
        move = (r1, c1, r2, c2)
        if self.board is None or self._ready_move != move:
            return False
        self._ready_move = None
        sw, sh = pyautogui.size()
        if self.board.frame_size != (sw, sh):
            return False
        if self._evaluate_move(self.board.grid, *move)[0] == 0:
            return False
        first, second = self._grid_pos(r1, c1), self._grid_pos(r2, c2)
        if not all(1 < x < sw-2 and 1 < y < sh-2 for x, y in (first, second)):
            return False
        pyautogui.moveTo(*first)
        try:
            pyautogui.mouseDown()
            time.sleep(.1)
            pyautogui.moveTo(*second, duration=.18)
        finally:
            pyautogui.mouseUp()
        self._pending = (self.board.signature, move, time.monotonic())
        self._previous = self._stable_since = None
        return True

    def play(self):
        print('START Coin Match: adaptive detection with seven coin types')
        self.board = None
        self._previous = self._stable_since = self._pending = None
        self._blocked.clear()
        self._blocked_signature = self._ready_move = None
        self._end_region = None
        self._end_seen = 0
        self._ended = False
        start = time.monotonic()
        last_available = start
        try:
            while time.monotonic()-start < self.game_duration:
                move = self._find_best_move()
                if self._ended:
                    print('END Coin Match: end panel detected; returning to reward collection.')
                    return True
                if move:
                    if not self._make_move(*move):
                        print('Coin Match: screen coordinates unavailable; stopped.')
                        return False
                    last_available = time.monotonic()
                elif self._pending and time.monotonic()-self._pending[2] > 3:
                    # A vanished grid must not keep renewing the inactivity timer.
                    self._pending = None
                if time.monotonic()-last_available > 8:
                    print('Coin Match: no playable board (possibly round ended); result unverified.')
                    return False
                time.sleep(.12)
            print('END Coin Match: time limit reached; result unverified.')
            return False
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            print(f'Coin Match error: {exc}')
            return False
