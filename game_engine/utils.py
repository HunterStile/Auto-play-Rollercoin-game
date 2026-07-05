"""
Utility functions for RollerCoin mini-game bots.

Pure pyautogui wrappers, image comparison, and common helpers.
Extracted from functions.py to keep game logic separate.
"""

import pyautogui
import numpy as np
from PIL import ImageGrab, ImageChops
from time import sleep
from typing import Tuple


# --- Mouse & Keyboard Wrappers -----------------------------------------------

def click(x: int, y: int):
    """Click at screen position."""
    pyautogui.click(x, y)


def muovi_mouse(x: int, y: int):
    """Move mouse to position."""
    pyautogui.moveTo(x, y)


def click_doppio(x: int, y: int):
    """Double-click at screen position."""
    pyautogui.doubleClick(x, y)


def click_dx(x: int, y: int):
    """Right-click at screen position."""
    pyautogui.rightClick(x, y)


def freccia(direzione: str):
    """Press an arrow key. Valid: 'up','down','left','right'."""
    pyautogui.press(direzione)


def trascina(x: int, y: int):
    """Drag to position."""
    pyautogui.dragTo(x, y)


def press_key(key: str):
    """Press any keyboard key."""
    pyautogui.press(key)


# --- Image Comparison --------------------------------------------------------

def image_similarity(image1, image2) -> float:
    """Return RMS difference between two PIL images. Lower = more similar."""
    diff = ImageChops.difference(image1, image2).convert('L')
    histogram = diff.histogram()
    total_pixels = float(image1.size[0] * image1.size[1])
    rms_sq = sum(value * ((idx % 256) ** 2) for idx, value in enumerate(histogram))
    return (rms_sq / total_pixels) ** 0.5


def verifica_cambio(screenshot_before, screenshot_after, threshold: float = 20) -> bool:
    """
    Check if two screenshots are significantly different.
    Returns True if similar (no change), False if different (change detected).
    """
    similarity = image_similarity(screenshot_before, screenshot_after)
    if similarity > threshold:
        return False  # change detected
    return True  # no significant change


def get_game_screenshot(region: Tuple[int, int, int, int] = None):
    """Take a screenshot, optionally of a specific region."""
    if region:
        return ImageGrab.grab(bbox=region)
    return ImageGrab.grab()


# --- Game Orchestrator Helpers ----------------------------------------------

def wait_game_ready(game_position: Tuple[int, int], max_attempts: int = 3) -> bool:
    """
    Click on a game and wait until it's ready (screen changes).
    Returns True if game loaded, False otherwise.
    """
    for attempt in range(max_attempts):
        try:
            muovi_mouse(game_position[0], game_position[1])
            screenshot_before = pyautogui.screenshot()
            click(game_position[0], game_position[1])
            sleep(2)
            screenshot_after = pyautogui.screenshot()

            if not verifica_cambio(screenshot_before, screenshot_after):
                print(f"Game ready at attempt {attempt + 1}")
                return True

        except Exception as e:
            print(f"Error preparing game: {e}")

        sleep(2)
    return False
