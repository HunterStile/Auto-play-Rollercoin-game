"""
Base class for all RollerCoin mini-game bots.

Every game must subclass BaseGame and implement play().
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any


class BaseGame(ABC):
    """
    Abstract base for all mini-game bots.

    Subclasses must define:
        game_id: str       - unique identifier (e.g. 'coinclick')
        display_name: str  - human-readable name (e.g. 'CoinClick')
        description: str   - short description of the game

    Optional class attributes:
        has_difficulty: bool  - whether the game supports difficulty levels
        difficulty_min: int   - minimum difficulty level
        difficulty_max: int   - maximum difficulty level
    """

    # -- Subclass must set these ------------------------------------------
    game_id: str = ""
    display_name: str = ""
    description: str = ""

    # -- Optional settings ------------------------------------------------
    has_difficulty: bool = False
    difficulty_min: int = 1
    difficulty_max: int = 1

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the game bot.

        Args:
            config: Dictionary with game configuration values.
                    Typically includes position, start_position, etc.
        """
        self.config = config or {}

    # -- Properties from config -------------------------------------------

    @property
    def position(self) -> Optional[Tuple[int, int]]:
        """Game icon position on the choose_game screen."""
        return self.config.get('position')

    @property
    def start_position(self) -> Optional[Tuple[int, int]]:
        """Start button position."""
        return self.config.get('start_position')

    @property
    def gain_power_position(self) -> Optional[Tuple[int, int]]:
        """Gain Power button position."""
        return self.config.get('gain_power_position')

    @property
    def difficulty(self) -> int:
        """Difficulty level (if game supports it)."""
        return self.config.get('difficulty', 1)

    # -- Abstract methods -------------------------------------------------

    @abstractmethod
    def play(self) -> bool:
        """
        Play one round of the game.

        Returns:
            True if the game completed successfully, False on error.
        """
        ...

    # -- Optional hooks ---------------------------------------------------

    def pre_game(self) -> None:
        """Called before play(). Override for setup (e.g. clicking start)."""
        pass

    def post_game(self) -> None:
        """Called after play(). Override for cleanup (e.g. clicking gain power)."""
        pass

    # -- Config key mapping (override in subclasses for legacy key names) -
    # Maps internal config names to the actual key names in Routine_config.py
    # Example: {'position': 'COINCLICK_POSITION', 'start_position': 'COINCLICK_START'}
    config_keys: Dict[str, str] = {}

    @classmethod
    def get_required_config_keys(cls) -> Dict[str, str]:
        """
        Return the config keys this game needs.

        If config_keys is set on the class, use those.
        Otherwise, derive from game_id: {GAME_ID}_POSITION, {GAME_ID}_START
        """
        if cls.config_keys:
            return dict(cls.config_keys)
        gid = cls.game_id.upper()
        return {
            'position': f'{gid}_POSITION',
            'start_position': f'{gid}_START',
        }

    @classmethod
    def get_config_prefix(cls) -> str:
        """Get the config key prefix for this game (for GUI generation)."""
        keys = cls.get_required_config_keys()
        pos_key = keys.get('position', '')
        if pos_key.endswith('_POSITION'):
            return pos_key[:-len('_POSITION')]
        return cls.game_id.upper()

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.game_id!r})>"
