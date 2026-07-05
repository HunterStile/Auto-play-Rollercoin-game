"""Standalone test for Token Blaster bot - run this to test without the full routine."""
import sys
import pyautogui
from time import sleep

sys.path.insert(0, '.')

from game_engine.games.tokenblaster import TokenBlasterBot

print("=" * 50)
print("Token Blaster - Standalone Test")
print("=" * 50)
print("\nMake sure RollerCoin Token Blaster game is open and started!")
print("Starting in 3 seconds...")
sleep(3)

bot = TokenBlasterBot({})
bot.play()
