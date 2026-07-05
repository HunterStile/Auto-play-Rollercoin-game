"""Standalone test for Coin Fisher bot - run this to test without the full routine."""
import sys
import pyautogui
from time import sleep

# Make sure game_engine is importable
sys.path.insert(0, '.')

from game_engine.games.coinfisher import CoinFisherBot

print("=" * 50)
print("Coin Fisher - Standalone Test")
print("=" * 50)
print("\nMake sure RollerCoin Coin Fisher game is open and started!")
print("Starting in 3 seconds...")
sleep(3)

bot = CoinFisherBot({})
bot.play()
