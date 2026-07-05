"""
CoinClick Game Bot.

Auto-clicks coins based on pixel color detection.
"""

import pyautogui
from time import sleep
from game_engine.base import BaseGame
from game_engine.registry import register_game
from game_engine.utils import click


# Coin color signatures: (R, G, B)
COIN_COLORS = {
    'eth':    (66, 105, 207),
    'blue':   (0, 128, 184),
    'yellow': (200, 200, 64),
    'orange': (231, 128, 32),
    'grey':   (230, 230, 230),
}

# End-screen pixel
END_COLOR = (3, 225, 228)  # (R, G, B)

# Scan region (from original: 530, 430, 828, 417)
SCAN_REGION = (530, 430, 828, 417)


@register_game
class CoinClickBot(BaseGame):
    game_id = 'coinclick'
    display_name = 'CoinClick'
    description = 'Click coins based on color detection'
    config_keys = {'position': 'COINCLICK_POSITION', 'start_position': 'COINCLICK_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', SCAN_REGION) if config else SCAN_REGION

    def _mouse_click(self, x, y, wait=0.0):
        """Click at position (adjusted for region offset)."""
        click(x + self.region[0], y + self.region[1])
        if wait:
            sleep(wait)

    def play(self) -> bool:
        """Play one round of CoinClick."""
        print("START CoinClick")
        try:
            running = True
            while running:
                pic = pyautogui.screenshot(region=self.region)
                width, height = pic.size

                for x in range(0, width, 5):
                    for y in range(0, height, 5):
                        r, g, b = pic.getpixel((x, y))

                        # End screen detected
                        if (r, g, b) == END_COLOR:
                            running = False
                            break

                        # Check each coin color
                        if (r, g, b) == COIN_COLORS['eth']:
                            self._mouse_click(x + 5, y + 10)
                            break
                        if r == 0 and b == 184:  # blue coin
                            self._mouse_click(x, y + 10)
                            break
                        if b == 64 and r == 200:  # yellow coin
                            self._mouse_click(x, y + 10)
                            break
                        if b == 32 and r == 231:  # orange coin
                            self._mouse_click(x, y + 10)
                            break
                        if b == 230 and r == 230:  # grey coin
                            self._mouse_click(x + 5, y + 10)
                            break

            print("END CoinClick")
            return True
        except Exception as e:
            print(f"Error in CoinClick: {e}")
            return False
