"""Standalone test for Flappy Rocket bot v2.
Make sure the RollerCoin Flappy Rocket game is open and started!
The bot will auto-press space to begin, then track the rocket
and jump through gaps intelligently."""
import sys
import pyautogui
from time import sleep

sys.path.insert(0, '.')

from game_engine.games.flappyrocket import FlappyRocketBot

print("=" * 55)
print("  Flappy Rocket v2 - Standalone Test")
print("=" * 55)
print()
print("  Make sure:")
print("  1. RollerCoin Flappy Rocket game is OPEN")
print("  2. Click on the game window after starting")
print("  3. The game area should be visible on screen")
print()
print("  Starting in 4 seconds...")
sleep(4)

bot = FlappyRocketBot({})
bot.play()

print()
print("Done! Check the output above for jump logs.")
