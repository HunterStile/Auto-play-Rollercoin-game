"""
Hamster Climber Game Bot.

Timing-based game: press spacebar when hamster reaches green bars.
Uses pixel color detection in a scan region.
"""

import pyautogui
from time import sleep
from game_engine.base import BaseGame
from game_engine.registry import register_game


# Target color for green bars (with tolerance)
TARGET_COLOR = (55, 173, 67)
COLOR_TOLERANCE = 2

# Scan region (from original: 575, 390, 828, 417)
SCAN_REGION = (575, 390, 828, 417)

# End-screen pixel
END_COLOR = (3, 225, 228)


@register_game
class HamsterClimberBot(BaseGame):
    game_id = 'hamsterclimber'
    display_name = 'Hamster Climber'
    description = 'Press spacebar when hamster reaches green bars'
    config_keys = {'position': 'HAMSTERCLIMBER_POSITION', 'start_position': 'HAMSTERCLIMBER_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.region = config.get('scan_region', SCAN_REGION) if config else SCAN_REGION
        self.target_color = config.get('target_color', TARGET_COLOR) if config else TARGET_COLOR
        self.tolerance = config.get('tolerance', COLOR_TOLERANCE) if config else COLOR_TOLERANCE

    @staticmethod
    def _is_color_match(target, actual, tolerance):
        """Check if actual color is within tolerance of target."""
        return all(abs(tc - ac) <= tolerance for tc, ac in zip(target, actual))

    def play(self) -> bool:
        """Play one round of Hamster Climber."""
        print("START Hamster Climber")
        try:
            running = True
            while running:
                pic = pyautogui.screenshot(region=self.region)
                width, height = pic.size
                found = False

                for x in range(0, width, 15):
                    for y in range(0, height, 15):
                        r, g, b = pic.getpixel((x, y))

                        # End screen
                        if (r, g, b) == END_COLOR:
                            running = False
                            break

                        # Green bar detected → jump
                        if self._is_color_match(self.target_color, (r, g, b), self.tolerance):
                            pyautogui.press('space')
                            found = True
                            break

                    if found:
                        break

            print("END Hamster Climber")
            return True
        except Exception as e:
            print(f"Error in Hamster Climber: {e}")
            return False
