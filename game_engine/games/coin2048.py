"""
2048 Coins Game Bot.

Simple arrow-key pattern strategy for the 2048 coin-merging game.
"""

from time import sleep
from game_engine.base import BaseGame
from game_engine.registry import register_game
from game_engine.utils import freccia


@register_game
class Coin2048Bot(BaseGame):
    game_id = 'coin2048'
    display_name = '2048 Coins'
    description = 'Arrow-key pattern strategy for tile merging'
    config_keys = {'position': 'GIOCO2048_POSITION', 'start_position': 'GIOCO2048_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.game_duration = config.get('game_duration', 64) if config else 64
        self.move_delay = config.get('move_delay', 0.1) if config else 0.1

    def play(self) -> bool:
        """Play one round of 2048 Coins."""
        print("START 2048 Coins")
        try:
            for second in range(self.game_duration):
                if second % 10 == 0:
                    print(f"  Second: {second}")

                freccia('down')
                sleep(self.move_delay)
                freccia('left')
                sleep(self.move_delay)
                freccia('down')
                sleep(self.move_delay)
                freccia('right')
                sleep(self.move_delay)
                freccia('down')
                sleep(self.move_delay)

            print("END 2048 Coins")
            return True
        except Exception as e:
            print(f"Error in 2048 Coins: {e}")
            return False
