"""Crypto Hex MVP: stable visual reads, one drag, then observed feedback."""
import time
import sys
from pathlib import Path

import keyboard
import pyautogui

from game_engine.base import BaseGame
from game_engine.coin2048_vision import detect_result as detect_reward_dialog
from game_engine.cryptohex_strategy import choose_move, top_count
from game_engine.cryptohex_vision import HIDDEN, detect_board, neighbors
from game_engine.registry import register_game


def detect_result(frame):
    # Live Crypto Hex uses a brighter cyan and slightly different antialiasing.
    # The surrounding dialog and CLAIM REWARD text are still required.
    return detect_reward_dialog(frame, button_colors=((3, 225, 228), (28, 249, 252)),
                                min_text_iou=.60, panel_button_aspect=6.55)


@register_game
class CryptoHexBot(BaseGame):
    game_id = 'cryptohex'
    display_name = 'Crypto Hex'
    description = 'MVP: recognize colored stacks and place adjacent matching colors'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 65)
        self.input_mode = self.config.get('input_mode', 'drag')
        if self.input_mode not in ('drag', 'click'):
            raise ValueError('input_mode must be drag or click')
        self.stop_reason = None
        self._reset()

    def _reset(self):
        self._candidate = self._pending = self._geometry = None
        self._last_board = None
        self.control_error = None

    def next_action(self, board, now):
        if board is None:
            self._candidate = None
            return None
        geometry = board.region, board.frame_size
        if self._geometry != geometry:
            if self._pending:
                self.control_error = 'griglia spostata durante una mossa non confermata'
                return None
            self._candidate = None
            self._geometry = geometry
        signature = board.signature
        if self._candidate is None or self._candidate[0] != signature:
            self._candidate = signature, now
            return None
        if now-self._candidate[1] < .12:
            return None
        if self._pending:
            before, move, sent = self._pending
            affected = (move.target,)+neighbors(move.target)
            changed = any(before[0][i] != board.stacks[i]
                          and HIDDEN not in (before[0][i], board.stacks[i]) for i in affected)
            cleared_on_arrival = (top_count(before[1][move.source]) >= 10
                                  and before[1][move.source] != board.trays[move.source])
            # Require local board change, not just a tray refill or animation.
            if changed or cleared_on_arrival:
                self._pending = None
            elif now-sent > 2:
                self.control_error = 'piazzamento non confermato; nessuna ripetizione automatica'
                return None
            else:
                return None
        move = choose_move(board)
        if move:
            self._pending = signature, move, now
            self._candidate = None
        return move

    def _place(self, board, move):
        # Click inside the top face, including tall mixed stacks in the tray.
        stack = board.trays[move.source]
        sx, sy = board.sources[move.source]
        sy += (9-len(stack)*9.5)*board.scale
        tx, ty = board.centers[move.target]
        try:
            pyautogui.moveTo(round(sx), round(sy), duration=.06, _pause=False)
            if self.input_mode == 'click':
                pyautogui.click(_pause=False)
                time.sleep(.06)
                if keyboard.is_pressed('q'):
                    return
                pyautogui.click(round(tx), round(ty), _pause=False)
            else:
                pyautogui.mouseDown(_pause=False)
                pyautogui.moveTo(round(tx), round(ty), duration=.18, _pause=False)
        finally:
            failsafe = pyautogui.FAILSAFE
            try:
                pyautogui.FAILSAFE = False
                pyautogui.mouseUp(_pause=False)
            finally:
                pyautogui.FAILSAFE = failsafe

    def play(self):
        self._reset()
        started = last_progress = time.monotonic()
        last_frame = None
        result_candidate = None
        self.stop_reason = 'tempo massimo raggiunto; risultato non verificato'
        print('START Crypto Hex MVP - Q per fermare')
        try:
            while time.monotonic()-started < self.game_duration:
                if keyboard.is_pressed('q'):
                    self.stop_reason = 'arresto richiesto con Q'
                    break
                last_frame = pyautogui.screenshot()
                now = time.monotonic()
                if last_frame.size != tuple(pyautogui.size()):
                    self.stop_reason = 'dimensioni screenshot/schermo incompatibili'
                    break
                result = detect_result(last_frame) if self._geometry else None
                if result:
                    if result_candidate and result_candidate[0] == result:
                        if now-result_candidate[1] >= .25:
                            self.stop_reason = 'pannello ricompensa confermato; vittoria non verificata'
                            return True
                    else:
                        result_candidate = result, now
                    time.sleep(.06)
                    continue
                result_candidate = None
                board = detect_board(last_frame, previous=self._last_board)
                if board is not None:
                    self._last_board = board
                    if not any(board.trays):
                        # This is a recognized refill state, not lost detection.
                        # Give the next batch time to produce two stable reads.
                        last_progress = now
                move = self.next_action(board, now)
                if self.control_error:
                    self.stop_reason = self.control_error
                    break
                if keyboard.is_pressed('q'):
                    self.stop_reason = 'arresto richiesto con Q'
                    break
                if time.monotonic()-started >= self.game_duration:
                    break
                if move:
                    print('Crypto Hex: pila', move.source+1,
                          ''.join(board.trays[move.source]), '-> casella', move.target)
                    self._place(board, move)
                    last_progress = time.monotonic()
                elif now-last_progress > 4:
                    self.stop_reason = 'nessuna mossa verificabile per 4 secondi'
                    break
                time.sleep(.06)
            return False
        except pyautogui.FailSafeException:
            self.stop_reason = 'arresto di emergenza con il mouse'
            raise
        except Exception as exc:
            self.stop_reason = 'errore: '+str(exc)
            return False
        finally:
            print('END Crypto Hex: '+self.stop_reason)
            diagnostics = self.config.get('diagnostics_dir')
            if diagnostics is None and getattr(sys, 'frozen', False):
                diagnostics = Path(sys.executable).parent/'debug'/'cryptohex'
            if diagnostics and last_frame is not None:
                try:
                    directory = Path(diagnostics)
                    directory.mkdir(parents=True, exist_ok=True)
                    last_frame.save(directory/'last_frame.png')
                    (directory/'last_reason.txt').write_text(self.stop_reason, encoding='utf-8')
                except OSError as exc:
                    print('Diagnostica non salvata:', exc)
