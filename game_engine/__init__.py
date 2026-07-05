"""
Game Engine for RollerCoin Auto-Play Bot.

Provides base classes, registry, and utilities for all mini-game bots.
"""

from game_engine.base import BaseGame
from game_engine.registry import GameRegistry, register_game
from game_engine.utils import (
    click, muovi_mouse, click_doppio, click_dx,
    freccia, trascina, image_similarity, verifica_cambio,
    get_game_screenshot, wait_game_ready,
)

__all__ = [
    'BaseGame', 'GameRegistry', 'register_game',
    'click', 'muovi_mouse', 'click_doppio', 'click_dx',
    'freccia', 'trascina', 'image_similarity', 'verifica_cambio',
    'get_game_screenshot', 'wait_game_ready',
]
