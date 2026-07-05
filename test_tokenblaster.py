"""Standalone test for Token Blaster bot.
IMPORTANT: After starting, click on the browser game window immediately!
The bot will auto-click the center to focus, then hold SPACE for auto-fire.
Press 'q' at any time to stop."""
import sys
import pyautogui
from time import sleep

sys.path.insert(0, '.')

from game_engine.games.tokenblaster import TokenBlasterBot

print("=" * 50)
print("Token Blaster - Standalone Test")
print("=" * 50)
print("\n!! Make sure the game is open and click on it AFTER starting !!")
print("The bot will auto-focus the browser in 2 seconds.")
print("\nStarting in 3 seconds...")
sleep(3)

bot = TokenBlasterBot({})
bot.play()
