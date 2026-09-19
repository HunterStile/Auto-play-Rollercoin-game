"""Dr. Hamster MVP: visual pair tracking and verified arrow-key control."""
import math
import time
from pathlib import Path

import keyboard
import pyautogui

from game_engine.base import BaseGame
from game_engine.coin2048_vision import detect_result
from game_engine.drhamster_strategy import choose_placement, fits
from game_engine.drhamster_vision import ROWS, detect_board, piece_candidates
from game_engine.registry import register_game


@register_game
class DrHamsterBot(BaseGame):
    game_id = 'drhamster'
    display_name = 'Dr. Hamster'
    description = 'MVP: match four colors with visually verified pair placement'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 65)
        self.stop_reason = None
        self.control_error = None
        self._region = None
        self._reset_tracking()

    def _reset_tracking(self):
        self._base = self._piece = self._plan = self._pending = None
        self._candidate = None
        self._targets = frozenset()
        self._rotations = self._retries = 0

    def _acquire(self, board):
        candidates = list(piece_candidates(board, spawning=True))
        if len(candidates) != 1:
            self._candidate = None
            return False
        piece, grid, targets = candidates[0]
        signature = (grid, targets, piece.col, piece.orientation)
        previous = self._candidate
        self._candidate = signature, piece.row
        if (previous is None or previous[0] != signature or
                not -.15 <= piece.row-previous[1] <= 1.1):
            return False
        self._base, self._targets, self._piece = grid, targets, piece
        self._plan = choose_placement(grid, piece, targets)
        self._candidate = None
        return self._plan is not None

    def next_action(self, board, now):
        """Pure control decision. A key is acknowledged by the next board read."""
        if board is None:
            self._candidate = None
            return None
        geometry = (board.region, board.frame_size)
        if geometry != self._region:
            self._reset_tracking()
            self._region = geometry
        if self._base is None:
            if not self._acquire(board):
                return None
        else:
            rotating = self._pending and self._pending[0] == 'up'
            candidates = [(p, g, t) for p, g, t in piece_candidates(board)
                          if g == self._base and t == self._targets
                          and sorted(p.colors) == sorted(self._piece.colors)
                          and (-1.2 if rotating else -.2) <= p.row-self._piece.row < ROWS]
            if len(candidates) != 1:
                # Lock, clear animation, or a new pair: discard the old plan.
                self._reset_tracking()
                self._acquire(board)
                return None
            self._piece = candidates[0][0]
        piece = self._piece
        if self._pending:
            key, before, sent = self._pending
            acknowledged = (piece.orientation != before.orientation if key == 'up'
                            else piece.col != before.col)
            if acknowledged:
                self._pending = None
                self._retries = 0
                if key == 'up':
                    self._rotations += 1
            elif now-sent < .4:
                return None
            elif self._retries >= 1:
                self.control_error = 'comando non confermato a video: '+key
                return None
            else:
                self._retries += 1
                self._pending = key, piece, now
                return key
        if self._plan is None:
            return None
        if piece.orientation != self._plan.orientation:
            if self._rotations >= 4:
                self.control_error = 'rotazione richiesta non raggiunta'
                return None
            key = 'up'
        elif piece.col != self._plan.col:
            direction = 1 if self._plan.col > piece.col else -1
            row = max(0, math.ceil(piece.row-.15))
            if not fits(self._base, row, piece.col+direction, piece.vertical):
                self._plan = choose_placement(self._base, piece, self._targets)
                self._rotations = 0
                return None
            key = 'right' if direction > 0 else 'left'
        else:
            return 'down'
        self._pending = key, piece, now
        return key

    @staticmethod
    def _pulse(key, duration=None):
        # Release after a bounded pulse: never carry DOWN across a lost read.
        try:
            pyautogui.keyDown(key, _pause=False)
            time.sleep(duration if duration is not None else (.055 if key == 'down' else .035))
        finally:
            # PyAutoGUI's corner failsafe also applies to keyUp. Cleanup must
            # still release a held key before the original exception propagates.
            failsafe = pyautogui.FAILSAFE
            try:
                pyautogui.FAILSAFE = False
                pyautogui.keyUp(key, _pause=False)
            finally:
                pyautogui.FAILSAFE = failsafe

    def _drop_burst(self, deadline):
        """Spam DOWN only after observed alignment, then read the board again.

        Far from landing use up to four fast presses. Reserve the final cell
        for a single press and a new screenshot to limit input at piece spawn.
        """
        if (self._piece is None or self._plan is None or self._pending is not None
                or self._piece.col != self._plan.col
                or self._piece.orientation != self._plan.orientation):
            return
        distance = self._plan.row-self._piece.row
        presses = min(4, max(1, math.floor(distance)-1))
        for _ in range(presses):
            if time.monotonic() >= deadline or keyboard.is_pressed('q'):
                break
            self._pulse('down', duration=.012)
            time.sleep(.008)

    def play(self):
        self._reset_tracking()
        self._region = None
        self.control_error = None
        started = time.monotonic()
        last_progress = started
        last_frame = None
        result_candidate = None
        result_since = None
        self.stop_reason = 'tempo massimo raggiunto; risultato non verificato'
        print('START Dr. Hamster MVP - Q per fermare')
        try:
            while time.monotonic()-started < self.game_duration:
                if keyboard.is_pressed('q'):
                    self.stop_reason = 'arresto richiesto con Q'
                    break
                frame = pyautogui.screenshot()
                last_frame = frame
                now = time.monotonic()
                if frame.size != tuple(pyautogui.size()):
                    self.stop_reason = 'dimensioni screenshot/schermo incompatibili'
                    break
                result = detect_result(frame) if self._region is not None else None
                if result:
                    signature = (frame.size, result)
                    if signature != result_candidate:
                        result_candidate, result_since = signature, now
                    elif now-result_since >= .25:
                        self.stop_reason = 'pannello ricompensa confermato; vittoria non verificata'
                        return True
                    time.sleep(.06)
                    continue
                result_candidate = result_since = None
                board = detect_board(frame)
                action = self.next_action(board, now)
                if self.control_error:
                    self.stop_reason = self.control_error
                    break
                # Include analysis time in the deadline; do not send a late key.
                if time.monotonic()-started >= self.game_duration:
                    break
                if action:
                    if action == 'down':
                        self._drop_burst(started+self.game_duration)
                    else:
                        self._pulse(action)
                    last_progress = time.monotonic()
                elif now-last_progress > 4:
                    self.stop_reason = 'griglia o coppia attiva non riconosciuta per 4 secondi'
                    break
                time.sleep(.008 if action == 'down' else .035)
            return False
        except pyautogui.FailSafeException:
            self.stop_reason = 'arresto di emergenza con il mouse'
            raise
        except Exception as exc:
            self.stop_reason = 'errore: '+str(exc)
            return False
        finally:
            # _pulse releases its key even when interrupted or an input fails.
            print('END Dr. Hamster: '+self.stop_reason)
            diagnostics = self.config.get('diagnostics_dir')
            if diagnostics and last_frame is not None:
                try:
                    directory = Path(diagnostics)
                    directory.mkdir(parents=True, exist_ok=True)
                    last_frame.save(directory/'last_frame.png')
                    (directory/'last_reason.txt').write_text(self.stop_reason, encoding='utf-8')
                except OSError as exc:
                    print('Diagnostica non salvata:', exc)
