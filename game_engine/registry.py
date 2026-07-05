"""
Game Registry for auto-discovery of mini-game bots.

Games register themselves using the @register_game decorator.
The GUI and orchestrator use this registry to discover available games dynamically.
"""

from typing import Dict, Type, List, Optional
from game_engine.base import BaseGame


class GameRegistry:
    """
    Central registry for all game bot classes.

    Usage:
        @register_game
        class CoinClickBot(BaseGame):
            game_id = 'coinclick'
            display_name = 'CoinClick'
            ...

        # Get all registered games:
        games = GameRegistry.list_games()

        # Instantiate a game:
        bot = GameRegistry.create('coinclick', config)
    """

    _games: Dict[str, Type[BaseGame]] = {}

    @classmethod
    def register(cls, game_cls: Type[BaseGame]) -> Type[BaseGame]:
        """Register a game bot class."""
        if not game_cls.game_id:
            raise ValueError(f"Game class {game_cls.__name__} must define 'game_id'")
        cls._games[game_cls.game_id] = game_cls
        return game_cls

    @classmethod
    def get(cls, game_id: str) -> Optional[Type[BaseGame]]:
        """Get a game class by its ID."""
        return cls._games.get(game_id)

    @classmethod
    def create(cls, game_id: str, config: dict = None) -> Optional[BaseGame]:
        """Create an instance of a game by its ID."""
        game_cls = cls.get(game_id)
        if game_cls:
            return game_cls(config or {})
        return None

    @classmethod
    def list_games(cls) -> List[Type[BaseGame]]:
        """Return all registered game classes."""
        return list(cls._games.values())

    @classmethod
    def list_game_ids(cls) -> List[str]:
        """Return all registered game IDs."""
        return list(cls._games.keys())

    @classmethod
    def list_game_info(cls) -> List[dict]:
        """Return info dicts for all games (for GUI display)."""
        return [
            {
                'game_id': g.game_id,
                'display_name': g.display_name,
                'description': g.description,
                'has_difficulty': g.has_difficulty,
                'difficulty_min': g.difficulty_min,
                'difficulty_max': g.difficulty_max,
            }
            for g in cls._games.values()
        ]

    @classmethod
    def clear(cls):
        """Clear all registered games (for testing)."""
        cls._games.clear()


# Decorator shortcut
def register_game(cls):
    """Decorator to register a game class with the registry."""
    return GameRegistry.register(cls)
