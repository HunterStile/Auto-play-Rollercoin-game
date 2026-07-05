"""
Backward-compatible re-exports from game_engine.

!! DEPRECATED: New code should import directly from game_engine.
This file exists so existing scripts (CoinClick.py, CoinFlip.py, etc.)
continue to work without changes.
"""

# Re-export everything from the new engine
from game_engine.utils import (
    click, muovi_mouse, click_doppio, click_dx,
    freccia, trascina, image_similarity, verifica_cambio,
    get_game_screenshot, press_key,
    wait_game_ready,
)

from game_engine.games.coinflip import CoinFlipBot as MemoryBot
from game_engine.games.coinclick import CoinClickBot
from game_engine.games.coin2048 import Coin2048Bot
from game_engine.games.hamsterclimber import HamsterClimberBot
from game_engine.games.coinmatch import CoinMatchBot

# Import common modules for backward compatibility
import pyautogui
from time import sleep
import numpy as np
from PIL import ImageGrab, ImageChops
from typing import List, Tuple
import random
import time

# -- Legacy aliases ----------------------------------------------------------

# Arrow key constants
giu = 'down'
su = 'up'
destro = 'right'
sinistra = 'left'
url = 'https://rollercoin.com/game/choose_game'

# Legacy function wrappers
def Game2048():
    """Legacy wrapper for 2048 Coins game."""
    bot = Coin2048Bot({})
    return bot.play()


def coinclick(a=1):
    """Legacy wrapper for CoinClick game."""
    bot = CoinClickBot({})
    return bot.play()


def hamsterClimber(a=1):
    """Legacy wrapper for Hamster Climber game."""
    bot = HamsterClimberBot({})
    return bot.play()


def space_click(wait=0.0):
    """Legacy: press spacebar."""
    pyautogui.press('space')
    time.sleep(wait)


def is_color_in_range(target_color, actual_color, tolerance):
    """Legacy: check if color is within tolerance range."""
    return all(abs(tc - ac) <= tolerance for tc, ac in zip(target_color, actual_color))


def mouse_click(x, y, wait=0.2):
    """Legacy: click and wait."""
    pyautogui.click(x, y)
    sleep(wait)


def verifico_cambio(screenshot_before, screenshot_after):
    """Legacy: check if screenshots are identical."""
    if ImageChops.difference(screenshot_before, screenshot_after).getbbox() is None:
        print("Images are identical, no change detected.")
        return True
    print("Images are different, change detected.")
    return False


def cerca_posizione():
    """Legacy: print current mouse position."""
    print('Position the cursor...')
    sleep(3)
    print(pyautogui.position())
    return input("Type 'stop' to stop, or Enter to continue...")
