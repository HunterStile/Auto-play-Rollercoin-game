"""Crypto Hamster: steer automatic jumps and keep firing upward."""

import time
from pathlib import Path

import keyboard
import pyautogui

from game_engine.base import BaseGame
from game_engine.cryptohamster_vision import inspect_frame
from game_engine.registry import register_game


@register_game
class CryptoHamsterBot(BaseGame):
    game_id = 'cryptohamster'
    display_name = 'Crypto Hamster'
    description = 'Climb on solid/fragile platforms, avoid fake ledges, shoot upward'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 75)
        self.fire_interval = self.config.get('fire_interval', .15)
        self.fire_key = self.config.get('fire_key', 'up')
        self.detection_error = None
        self.detected_region = None
        self.stop_reason = None
        self._held = set()
        self._last_fire = float('-inf')
        self._previous = None
        self._vertical_speed = 0.
        self._last_target = None

    def inspect(self, frame):
        state, self.detection_error = inspect_frame(frame, self.config.get('scan_region'))
        self.detected_region = state['region'] if state else None
        return state

    @staticmethod
    def _wrapped_offset(start, target, width):
        return min((target-start, target-start-width, target-start+width), key=abs)

    def _observe(self, state, now):
        previous = self._previous
        if previous:
            dt = now-previous['time']
            if .015 <= dt <= .4 and previous['region'] == state['region']:
                shifts = []
                for old in previous['platforms']:
                    near = [p for p in state['platforms']
                            if p['kind'] == old['kind'] and abs(p['x']-old['x']) < 12]
                    if near:
                        shifts.append(min(near, key=lambda p: abs(p['y']-old['y']))['y']-old['y'])
                camera_shift = sorted(shifts)[len(shifts)//2] if shifts else 0
                measured = (state['feet']-previous['feet']-camera_shift)/dt
                self._vertical_speed = .45*self._vertical_speed+.55*measured
            else:
                self._vertical_speed = 0.
        self._previous = {'time': now, 'region': state['region'],
                          'feet': state['feet'], 'platforms': state['platforms']}

    def choose_direction(self, state, now=None):
        """Prefer a reachable high ledge; catch a lower one while falling."""
        if now is not None:
            self._observe(state, now)
        _, _, w, h = state['region']
        px, _ = state['player']
        feet = state['feet']
        rising = self._vertical_speed < -h*.04
        candidates = []
        for p in state['platforms']:
            top = p['y']
            vertical = feet-top
            if not (-h*.29 <= vertical <= h*.35):
                continue
            # When descending, a ledge already above the feet cannot catch us.
            if not rising and vertical > h*.025:
                continue
            center = p['x']+p['width']/2
            offset = self._wrapped_offset(px, center, w)
            landing_half = max(0, p['width']/2-w*.035)
            gap = max(0, abs(offset)-landing_half)
            reach = w*(.11 if not rising else .20)+max(0, -vertical)*.65
            if gap > reach:
                continue
            # Higher ledges make progress; solid surfaces survive repeat jumps.
            score = (-top/h*3.0 - gap/w*2.2
                     + (.28 if p['kind'] == 'solid' else 0)
                     + (.25 if self._last_target == (p['kind'], round(center/w, 2)) else 0))
            candidates.append((score, offset, p))
        if not candidates:
            # Recover toward the closest real ledge, never toward visual debris.
            below = [p for p in state['platforms'] if p['y'] >= feet-h*.03]
            if not below:
                self._last_target = None
                return None
            p = min(below, key=lambda p: (p['y']-feet,
                    abs(self._wrapped_offset(px, p['x']+p['width']/2, w))))
            offset = self._wrapped_offset(px, p['x']+p['width']/2, w)
        else:
            _, offset, p = max(candidates, key=lambda item: item[0])
        center = p['x']+p['width']/2
        self._last_target = (p['kind'], round(center/w, 2))
        # Stop within the usable middle of a platform. This prevents overshoot.
        if abs(offset) <= max(w*.018, p['width']*.19):
            return None
        return 'right' if offset > 0 else 'left'

    def _set_input(self, direction, now):
        desired = {direction} if direction else set()
        for key in self._held-desired:
            pyautogui.keyUp(key, _pause=False)
        for key in desired-self._held:
            pyautogui.keyDown(key, _pause=False)
        self._held = desired
        # Hold Up between pulses, but also send fresh key-down events for
        # versions of the game that only shoot on a press event.
        if now-self._last_fire >= self.fire_interval:
            if self._last_fire != float('-inf'):
                pyautogui.keyUp(self.fire_key, _pause=False)
            pyautogui.keyDown(self.fire_key, _pause=False)
            self._last_fire = now

    def _release(self):
        guard = pyautogui.FAILSAFE
        try:
            pyautogui.FAILSAFE = False
            for key in (self.fire_key, 'left', 'right'):
                pyautogui.keyUp(key, _pause=False)
        finally:
            pyautogui.FAILSAFE = guard
            self._held.clear()

    def play(self):
        self._held.clear()
        self._last_fire = float('-inf')
        self._previous = None
        self._last_target = None
        started = time.monotonic()
        missing_since = None
        last_frame = None
        self.stop_reason = 'tempo massimo raggiunto; risultato non verificato'
        print('START Crypto Hamster - Q per fermare')
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
                state = self.inspect(frame)
                if state is None:
                    self._release()
                    self._previous = None
                    if missing_since is None:
                        missing_since = now
                    if now-missing_since >= 3:
                        self.stop_reason = 'riconoscimento assente: '+self.detection_error
                        break
                    time.sleep(.04)
                    continue
                missing_since = None
                direction = self.choose_direction(state, now)
                self._set_input(direction, now)
                time.sleep(.012)
            return False
        except pyautogui.FailSafeException:
            self.stop_reason = 'arresto richiesto con failsafe del mouse'
            return False
        except Exception as exc:
            self.stop_reason = f'errore: {type(exc).__name__}: {exc}'
            return False
        finally:
            self._release()
            print('END Crypto Hamster - '+self.stop_reason)
            directory = self.config.get('diagnostics_dir')
            if directory and last_frame is not None and not self.stop_reason.startswith('arresto'):
                try:
                    path = Path(directory)
                    path.mkdir(parents=True, exist_ok=True)
                    last_frame.save(path/'last_failure.png')
                    (path/'last_failure.txt').write_text(self.stop_reason, encoding='utf-8')
                except OSError as exc:
                    print(f'Diagnostica non salvata: {exc}')
