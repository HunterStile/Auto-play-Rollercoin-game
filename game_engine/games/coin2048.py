"""
2048 Coins Game Bot.

Simple arrow-key pattern strategy for the 2048 coin-merging game.
"""

import time
import pyautogui
from game_engine.base import BaseGame
from game_engine.coin2048_vision import detect_result
from game_engine.registry import register_game
from game_engine.utils import freccia


@register_game
class Coin2048Bot(BaseGame):
    game_id = 'coin2048'
    display_name = '2048 Coins'
    description = 'Arrow-key pattern with verified reward-dialog detection'
    config_keys = {'position': 'GIOCO2048_POSITION', 'start_position': 'GIOCO2048_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = self.config.get('game_duration', 120)
        self.move_delay = config.get('move_delay', 0.1) if config else 0.1

    def play(self) -> bool:
        """Keep the established pattern; stop on a stable result or deadline."""
        print("START 2048 Coins")
        pattern = ('down', 'left', 'down', 'right', 'down')
        start = time.monotonic()
        candidate = None
        candidate_since = None
        step = 0
        try:
            while time.monotonic()-start < self.game_duration:
                frame = pyautogui.screenshot()
                result = detect_result(frame)
                now = time.monotonic()
                if now-start >= self.game_duration:
                    break
                if result is not None:
                    signature = (frame.size, result)
                    if signature != candidate:
                        candidate, candidate_since = signature, now
                    elif now-candidate_since >= .25:
                        print('END 2048 Coins: reward dialog confirmed.')
                        return True
                    # Suppress arrows while confirming a possible result.
                    time.sleep(.1)
                    continue
                candidate = candidate_since = None
                freccia(pattern[step % len(pattern)])
                step += 1
                time.sleep(self.move_delay)
            print('END 2048 Coins: time limit; result unverified.')
            return False
        except pyautogui.FailSafeException:
            raise
        except Exception as e:
            print(f"Error in 2048 Coins: {e}")
            return False
