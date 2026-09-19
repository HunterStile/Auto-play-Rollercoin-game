"""Flappy Rocket MVP: one-frame vision and velocity-aware spacebar pulses."""
import time
from pathlib import Path

import keyboard
import pyautogui

from game_engine.base import BaseGame
from game_engine.registry import register_game
from game_engine.flappyrocket_vision import inspect_frame, is_end_panel


@register_game
class FlappyRocketBot(BaseGame):
    game_id = 'flappyrocket'
    display_name = 'Flappy Rocket'
    description = 'MVP: track the blue cockpit and fly through red/green pipe gaps'

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 65)
        self.jump_cooldown = self.config.get('jump_cooldown', .18)
        self.stop_reason = None
        self.detection_error = None
        self.detected_region = None
        self._reset_motion()

    def _reset_motion(self):
        self._previous = None
        self._velocity = 0.
        self._last_jump = float('-inf')

    def inspect(self, frame):
        """Read-only analysis; all object coordinates are local to region."""
        state, self.detection_error = inspect_frame(frame, self.config.get('scan_region'))
        self.detected_region = state['region'] if state else None
        return state

    def should_jump(self, state, now):
        """Aim at the next gap; maintain altitude even before pipes arrive."""
        _, _, w, h = state['region']
        rx, ry, rw, rh = state['rocket_box']
        _, cy = state['rocket']
        previous = self._previous
        if previous is not None:
            dt = now-previous['timestamp']
            if .015 <= dt <= .4 and previous['region'] == state['region']:
                measured = (cy-previous['rocket'][1])/dt
                self._velocity = .35*self._velocity + .65*max(-2*h, min(2*h, measured))
            else:
                self._velocity = 0.
        self._previous = dict(state, timestamp=now)
        upcoming = [p for p in state['pipes'] if p['right'] >= rx-w*.01]
        pipe = min(upcoming, key=lambda p: p['left']) if upcoming else None
        upper = rh/2+h*.035
        lower = h-rh/2-h*.035
        if pipe:
            upper = max(upper, pipe['gap_top']+rh/2+h*.035)
            lower = min(lower, pipe['gap_bottom']-rh/2-h*.035)
        target = (upper+lower)/2
        if upper >= lower or cy <= upper or now-self._last_jump < self.jump_cooldown:
            return False
        predicted = cy + self._velocity*.16 + .5*h*.9*.16**2
        emergency = cy > h-rh/2-h*.07 and self._velocity >= 0
        return emergency or (predicted > target+h*.012 and self._velocity > -h*.12)

    def play(self):
        """Play an already started, focused round; timeout is not a win."""
        self._reset_motion()
        self.detected_region = None
        started = time.monotonic()
        missing_since = None
        panel_since = None
        last_region = None
        last_frame = None
        self.stop_reason = 'tempo massimo raggiunto; risultato non verificato'
        print('START Flappy Rocket MVP - Q per fermare')
        try:
            while time.monotonic()-started < self.game_duration:
                if keyboard.is_pressed('q'):
                    self.stop_reason = 'arresto richiesto con Q'
                    break
                frame = pyautogui.screenshot()
                last_frame = frame
                now = time.monotonic()
                if tuple(pyautogui.size()) != frame.size:
                    self.stop_reason = 'dimensioni screenshot/schermo incompatibili'
                    break
                if is_end_panel(frame, last_region):
                    if panel_since is None:
                        panel_since = now
                    if now-panel_since >= .25:
                        self.stop_reason = 'pannello finale rilevato; vittoria non verificata'
                        return True
                    time.sleep(.04)
                    continue
                panel_since = None
                state = self.inspect(frame)
                if state is None:
                    self._previous = None
                    self._velocity = 0.
                    if missing_since is None:
                        missing_since = now
                    if now-missing_since >= 3:
                        self.stop_reason = 'riconoscimento assente: '+self.detection_error
                        break
                    time.sleep(.04)
                    continue
                missing_since = None
                last_region = state['region']
                if self.should_jump(state, now):
                    pyautogui.press('space', _pause=False)
                    self._last_jump = now
                time.sleep(.015)
            return False
        except pyautogui.FailSafeException:
            self.stop_reason = 'arresto richiesto con failsafe del mouse'
            return False
        except Exception as exc:
            self.stop_reason = f'errore: {type(exc).__name__}: {exc}'
            return False
        finally:
            print('END Flappy Rocket - '+self.stop_reason)
            directory = self.config.get('diagnostics_dir')
            if directory and last_frame is not None and not self.stop_reason.startswith(('arresto', 'pannello')):
                try:
                    path = Path(directory)
                    path.mkdir(parents=True, exist_ok=True)
                    last_frame.save(path/'last_failure.png')
                    (path/'last_failure.txt').write_text(self.stop_reason, encoding='utf-8')
                except OSError as exc:
                    print(f'Diagnostica non salvata: {exc}')
