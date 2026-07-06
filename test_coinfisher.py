"""Standalone test for Coin Fisher bot v2 (Cluster Mode).
Make sure RollerCoin Coin Fisher game is open and started!
The bot will scan all coins, group them into clusters,
and shoot at the center of the biggest cluster."""
import sys
import pyautogui
from time import sleep

sys.path.insert(0, '.')

from game_engine.games.coinfisher import CoinFisherBot

print("=" * 55)
print("  Coin Fisher v2 - Cluster Mode")
print("=" * 55)
print()
print("  Make sure:")
print("  1. RollerCoin Coin Fisher game is OPEN")
print("  2. Click on the game window after starting")
print()
print("  Starting in 4 seconds...")
sleep(4)

bot = CoinFisherBot({})
bot.play()

print()
print("Done!")