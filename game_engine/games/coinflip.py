"""
CoinFlip (Memory) Game Bot.

Card-matching memory game with color detection.
Supports 3 difficulty levels (different grid sizes).
"""

import pyautogui
import numpy as np
import random
import time
from PIL import ImageGrab
from time import sleep
from typing import List, Tuple

from game_engine.base import BaseGame
from game_engine.registry import register_game


# Grid coordinates for each difficulty level
CELL_COORDS_LV1: List[List[Tuple[int, int]]] = [
    [(850, 350), (1000, 350), (1150, 350)],
    [(850, 500), (1000, 500), (1150, 500)],
    [(850, 650), (1000, 650), (1150, 650)],
    [(850, 800), (1000, 800), (1150, 800)],
]

CELL_COORDS_LV2: List[List[Tuple[int, int]]] = [
    [(750, 350), (900, 350), (1050, 350), (1200, 350)],
    [(750, 500), (900, 500), (1050, 500), (1200, 500)],
    [(750, 650), (900, 650), (1050, 650), (1200, 650)],
    [(750, 800), (900, 800), (1050, 800), (1200, 800)],
]

CELL_COORDS_LV3: List[List[Tuple[int, int]]] = [
    [(680, 360), (830, 360), (980, 360), (1130, 360), (1280, 360)],
    [(680, 520), (830, 520), (980, 520), (1130, 520), (1280, 520)],
    [(680, 670), (830, 670), (980, 670), (1130, 670), (1280, 670)],
    [(680, 820), (830, 820), (980, 820), (1130, 820), (1280, 820)],
]

CELL_COORDS_BY_LEVEL = {
    1: CELL_COORDS_LV1,
    2: CELL_COORDS_LV2,
    3: CELL_COORDS_LV3,
}


@register_game
class CoinFlipBot(BaseGame):
    game_id = 'coinflip'
    display_name = 'CoinFlip'
    description = 'Memory card matching with color detection'
    has_difficulty = True
    difficulty_min = 1
    difficulty_max = 3
    config_keys = {'position': 'MEMORY_POSITION', 'start_position': 'MEMORY_START'}

    def __init__(self, config=None):
        super().__init__(config)
        self.cell_coords = CELL_COORDS_BY_LEVEL.get(self.difficulty, CELL_COORDS_LV2)
        self.found_pairs = set()
        self.card_memory = {}
        self.game_duration = 60  # seconds

    @staticmethod
    def _get_card_color(x: int, y: int) -> tuple:
        """
        Capture the dominant NON-WHITE color at a card position.
        Filters out white/light pixels so the card's actual color
        isn't diluted by white background areas.
        """
        region = (x - 15, y - 15, x + 15, y + 15)
        screenshot = ImageGrab.grab(bbox=region)
        img_array = np.array(screenshot)

        # Filter out white/near-white pixels (R+G+B > 650)
        h, w, _ = img_array.shape
        colored_pixels = []
        for py in range(h):
            for px in range(w):
                r, g, b = img_array[py, px]
                if int(r) + int(g) + int(b) < 650:  # not white
                    colored_pixels.append((int(r), int(g), int(b)))

        if colored_pixels:
            avg_r = sum(p[0] for p in colored_pixels) // len(colored_pixels)
            avg_g = sum(p[1] for p in colored_pixels) // len(colored_pixels)
            avg_b = sum(p[2] for p in colored_pixels) // len(colored_pixels)
            return (avg_r, avg_g, avg_b)

        # Fallback: average everything
        return tuple(np.mean(img_array, axis=(0, 1)).astype(int))

    @staticmethod
    def _are_matching(color1: tuple, color2: tuple) -> bool:
        """Check if two colors represent matching cards."""
        diff = sum(abs(a - b) for a, b in zip(color1, color2))
        return diff < 100  # wider tolerance for card variations

    def _click_and_get_color(self, row: int, col: int) -> tuple:
        """Click a card and return its color."""
        x, y = self.cell_coords[row][col]
        pyautogui.click(x, y)
        sleep(0.5)
        return self._get_card_color(x, y)

    def _get_available_moves(self) -> List[Tuple[int, int]]:
        """Return all cells not yet matched."""
        moves = []
        for row in range(len(self.cell_coords)):
            for col in range(len(self.cell_coords[row])):
                if (row, col) not in self.found_pairs:
                    moves.append((row, col))
        return moves

    def _play_turn(self) -> bool:
        """Play one turn. Return False if game is over."""
        available = self._get_available_moves()
        if len(available) < 2:
            return False

        move1 = random.choice(available)
        color1 = self._click_and_get_color(move1[0], move1[1])

        # Try to find a match from memory
        move2 = None
        for pos, color in self.card_memory.items():
            if pos in available and pos != move1 and self._are_matching(color1, color):
                move2 = pos
                break

        if move2 is None:
            remaining = [m for m in available if m != move1]
            move2 = random.choice(remaining)

        color2 = self._click_and_get_color(move2[0], move2[1])

        self.card_memory[move1] = color1
        self.card_memory[move2] = color2

        if self._are_matching(color1, color2):
            print(f"Pair found! {move1}, {move2}")
            self.found_pairs.add(move1)
            self.found_pairs.add(move2)
        else:
            sleep(0.4)

        return True

    def play(self) -> bool:
        """Play a full game of Memory."""
        print("Starting CoinFlip game...")
        sleep(2)

        start_time = time.time()

        try:
            while True:
                if time.time() - start_time > self.game_duration:
                    print("Time's up!")
                    break

                if not self._play_turn():
                    break

                sleep(0.8)

            print("CoinFlip completed!")
            return True
        except Exception as e:
            print(f"Error in CoinFlip: {e}")
            return False
